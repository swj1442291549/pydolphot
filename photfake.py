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
import random


def read_fits(file_name):
    """Read fits and sort by seed 1442291549
    
    Args:
        file_name (string): file name

    Returns:
        df (DataFrame): data frame
    """
    df = Table.read(file_name).to_pandas()
    random.seed(1442291549)
    tag = np.arange(0, len(df))
    random.shuffle(tag)
    df = df.assign(tag=tag)
    df = df.sort_values(by=['tag'])
    del df['tag']
    return df


def get_filters(df):
    """Get filters name
    
    Args:
        df (DataFrame): dataframe

    Returns:
        filter1, filter2 (string): filter1 and filter2 name
    """
    filter_list = []
    for key in df.keys():
        if '_VEGA' in key:
            filter_list.append(key[:-5])
    filter_list.sort()
    return filter_list


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
        '-r',
        '--run',
        type=int,
        default=100,
        help='Number of fake stars per run (default)')
    parser.add_argument(
        '-c', type=int, default=30, help='Number of cores (30)')
    args = parser.parse_args()
    folder = args.folder
    num_step = args.run
    core = args.c
    file_name = '{0}.fits'.format(folder)

    print('Reading ...')
    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    df_fake = read_fits(file_name)
    filter_list = get_filters(df_fake)

    for filter in filter_list:
        filter_index = list(df_fake.columns).index('{0}_VEGA'.format(filter))
        df_fake.columns.values[filter_index] = '{0}_VEGA_IN'.format(filter)

    df_fake = add_coordinate(df_fake, w)

    print('Extracting ...')
    filter_labels = [
        '_VEGA', '_ERR', '_SNR', '_SHARP', '_ROUND', '_CROWD', '_FLAG'
    ]
    nimg = len(glob.glob('*flt.fits'))
    index_array = np.array([15, 17, 19, 20, 21, 22, 23]) + 2 * (nimg + 2)
    labels_list = list()
    for filter in filter_list:
        for label in filter_labels:
            labels_list.append('{0}{1}'.format(filter, label))

    columns = list(df_fake.columns)
    columns.remove('RA')
    columns.remove('DEC')

    output_names = glob.glob('{0}/output*'.format(folder))

    def inner_extract(output_name):
        df_raw = pd.DataFrame(columns=labels_list + columns)
        if os.stat(output_name).st_size != 0:
            try:
                data = np.loadtxt(output_name)
            except:
                subprocess.call('rm {0}'.format(output_name), shell=True)
                print(output_name)
            else:
                chip = int(output_name.split('.')[0][-1])
                step = int(output_name.split('fake')[-1])
                df_sel = df_fake[df_fake.chip == chip].iloc[num_step * step:num_step * (
                    step + 1)]
                if len(data.shape) == 1:
                    data = [data]
                for data_item in data:
                    x_data = data_item[2]
                    y_data = data_item[3]
                    f = np.zeros(len(labels_list))
                    for j in range(len(filter_list)):
                        for i, index in enumerate(index_array):
                            f[i + 7 * j] = data_item[index + 13 * j] # BUG
                    data_series = pd.Series(f, index=labels_list)
                    item = df_sel[(x_data - df_sel['X'])**2 +
                                  (y_data - df_sel['Y'])**2 < 0.0002].iloc[0]
                    df_raw = df_raw.append(item.append(data_series), ignore_index=True)
                return df_raw

    pool = Pool(core)
    result = pool.map(inner_extract, output_names)
    pool.close()

    df = pd.concat(result)
    df.reset_index(drop=True, inplace=True)

    print('Selecting ...')
    snr = 5
    sharp = 0.04
    crowd = 0.5
    flag = np.zeros(len(df))

    index = (df['X'] >= 0).all()
    for filter in filter_list:
        index = index & (df['{0}_SNR'.format(filter)] > snr) & (df['{0}_SHARP'.format(filter)]**2 < sharp) & (df['{0}_CROWD'.format(filter)] < crowd) 

    df = df.assign(flag=index.values)

    print('Saving ...')

    t = Table.from_pandas(df)
    t.write('final/f.{0}.fits'.format(folder), overwrite=True)
