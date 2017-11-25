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


def read_data(data_name, w):
    data = np.loadtxt(data_name)
    num = np.arange(len(data[:, 0])) + 1
    world = w.wcs_pix2world(data[:, 2], data[:, 3], 1)
    ra = world[0]
    dec = world[1]
    chip_num = int(data_name.split('.')[0][-1])
    chip = np.array([chip_num] * len(num))
    return {'ra': ra, 'dec': dec, 'data': data, 'chip': chip}


def read_pickle(file_name, filter1, filter2):
    df = pickle.load(open(file_name, 'rb'))
    df = df.sort_values(by=['X'])
    f1_index = list(df.columns).index('{0}_VEGA'.format(filter1))
    f2_index = list(df.columns).index('{0}_VEGA'.format(filter2))
    df.columns.values[f1_index] = '{0}_VEGA_IN'.format(filter1)
    df.columns.values[f2_index] = '{0}_VEGA_IN'.format(filter2)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Bfilter", help='Blue Filter name')
    parser.add_argument("Rfilter", help='Red Filter name')
    parser.add_argument(
        '-f', "--folder", default='fake', help='Output folder name (fake)')
    parser.add_argument(
        '-n', '--num', type=int, default=100, help='Number of fake stars (100)')
    args = parser.parse_args()
    folder = args.folder
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num_step = args.num
    file_name = '{0}.pickle'.format(folder)

    print('Reading ...')
    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    df = read_pickle(file_name, filter1, filter2)
    df_dict = {1: df[df['chip'] == 1], 2: df[df['chip'] == 2]}

    print('Extracting ...')
    filter_labels = [
        '_VEGA', '_ERR', '_SNR', '_SHARP', '_ROUND', '_CROWD', '_FLAG'
    ]
    index_array = np.array([31, 33, 35, 36, 37, 38, 39])
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

    with Pool(30) as p:
        with tqdm(total=len(output_names)) as pbar:
            for i, _ in tqdm(enumerate(p.imap_unordered(inner_extract, output_names))):
                pbar.update()

    df = pd.concat(result)
    df.reset_index(drop=True, inplace=True)

    print('Selecting ...')
    snr = 5
    sharp = 0.04
    crowd = 0.5
    flag = np.zeros(len(df))
    for item in df.itertuples():
        if (item[3] >= snr) and (item[10] >= snr) and (item[4]**2 < sharp) and (
                item[11]**2 < sharp) and (item[6] < crowd) and (item[13] <
                                                                crowd):
            flag[item[0]] = 1
    df = df.assign(flag=flag)

    print('Saving ...')

    t = Table.from_pandas(df)
    t.write('f.{0}.fits'.format(folder), overwrite=True)

    subprocess.call('mv f.{0}.fits final'.format(folder), shell=True)
