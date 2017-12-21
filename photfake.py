import numpy as np
import astropy.table
from astropy.io import fits
from astropy import wcs
import argparse
import subprocess
import os
import glob
import pickle
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool
from astropy.table import Table


def read_fits(file_name):
    """Read fits and sort by X
    
    Args:
        file_name (string): file name

    Returns:
        df (DataFrame): data frame
    """
    df = Table.read(file_name).to_pandas()
    df = df.sort_values(by=['X'])
    return df


def get_filters(df):
    """Get filters name
    
    Args:
        df (DataFrame): dataframe

    Returns:
        filter1, filter2 (string): filter1 and filter2 name
    """
    filters = []
    for key in df.keys():
        if '_VEGA' in key:
            filters.append(key.replace('_VEGA', ''))

    if int(filters[1][1:-1]) > int(filters[0][1:-1]):
        filter1 = filters[0]
        filter2 = filters[1]
    return filter1, filter2


def add_coordinate(df, w):
    """Add coordinate X and Y
    
    Args:
        df (DataFrame): data frame
        w (wcs): wcs
    """
    world = w.wcs_pix2world(df['X'], df['Y'], 1)
    df = df.assign(RA=world[0])
    df = df.assign(DEC=world[1])
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        "--folder",
        default='complete',
        help='Output folder name (complete)')
    parser.add_argument(
        '-n',
        '--num',
        type=int,
        default=100,
        help='Number of fake stars (default)')
    args = parser.parse_args()
    folder = args.folder
    num_step = args.num
    file_name = '{0}.fits'.format(folder)

    print('Reading ...')
    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    df = read_fits(file_name)
    filter1, filter2 = get_filters(df)

    f1_index = list(df.columns).index('{0}_VEGA'.format(filter1))
    f2_index = list(df.columns).index('{0}_VEGA'.format(filter2))
    df.columns.values[f1_index] = '{0}_VEGA_IN'.format(filter1)
    df.columns.values[f2_index] = '{0}_VEGA_IN'.format(filter2)

    df = add_coordinate(df, w)

    df_dict = {1: df[df['chip'] == 1], 2: df[df['chip'] == 2]}

    print('Extracting ...')
    filter_labels = [
        '_VEGA', '_ERR', '_SNR', '_SHARP', '_ROUND', '_CROWD', '_FLAG'
    ]
    nimg = len(glob.glob('*flt.fits'))
    index_array = np.array([15, 17, 19, 20, 21, 22, 23]) + 2 * (nimg + 2)
    labels_list = list()
    for label in filter_labels:
        labels_list.append('{0}{1}'.format(filter1, label))
    for label in filter_labels:
        labels_list.append('{0}{1}'.format(filter2, label))
    df_raw = pd.DataFrame(columns=labels_list + [
        'X', 'Y', 'chip', '{0}_VEGA_IN'.format(filter1), '{0}_VEGA_IN'.format(
            filter2)
    ])

    final_list = list()
    output_names = glob.glob('{0}/output*'.format(folder))

    def inner_extract(output_name):
        df = df_raw
        if os.stat(output_name).st_size != 0:
            data = np.loadtxt(output_name)
            chip_num = int(output_name.split('.')[0][-1])
            step = int(output_name.split('fake')[-1])
            df_sel = df_dict[chip_num].iloc[num_step * step:num_step * (
                step + 1)]
            final_list = []
            if len(data.shape) == 1:
                data = [data]
            for data_item in data:
                x_data = data_item[2]
                y_data = data_item[3]
                f = np.zeros(14)
                for i, index in enumerate(index_array):
                    f[i] = data_item[index]
                for i, index in enumerate(index_array):
                    f[i + 7] = data_item[index + 13]
                data_series = pd.Series(f, index=labels_list)
                item = df_sel[(x_data - df_sel['X'])**2 +
                              (y_data - df_sel['Y'])**2 < 0.0002].iloc[0]
                df = df.append(item.append(data_series), ignore_index=True)
        return df

    pool = Pool(20)
    result = pool.map(inner_extract, output_names)
    pool.close()

    df = pd.concat(result)
    df.reset_index(drop=True, inplace=True)

    print('Selecting ...')
    snr = 5
    sharp = 0.04
    crowd = 0.5
    flag = np.zeros(len(df))

    index = (df['{0}_SNR'.format(filter1)] > snr) & (df['{0}_SNR'.format(
        filter2)] > snr) & (df['{0}_SHARP'.format(filter1)]**2 < sharp) & (
            df['{0}_SHARP'.format(filter2)]**2 <
            sharp) & (df['{0}_CROWD'.format(filter1)] <
                      crowd) & (df['{0}_CROWD'.format(filter2)] < crowd)

    df = df.assign(flag=index.values)

    print('Saving ...')

    t = Table.from_pandas(df)
    t.write('final/f.{0}.fits'.format(folder), overwrite=True)