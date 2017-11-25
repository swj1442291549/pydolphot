import numpy as np
import sys
import astropy.table
from astropy import units as u
from astropy.io import fits
from astropy import wcs
import argparse
import subprocess
import os
import glob
import pickle
import pandas as pd
from tqdm import tqdm


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
        "-p", '--pkl', default='df.pickle', help='DataFrame pickle file name')
    parser.add_argument(
        '-f', "--folder", default='fake', help='Output folder name')
    parser.add_argument(
        '-n', '--num', type=int, default=100, help='Number of fake stars')
    args = parser.parse_args()
    file_name = args.pkl
    folder = args.folder
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num_step = args.num

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

    final_list = list()
    output_names = glob.glob('{0}/output*'.format(folder))
    for output_name in tqdm(output_names):
        if os.stat(output_name).st_size == 0:
            continue
        else:
            data = np.loadtxt(output_name)
            chip_num = int(output_name.split('.')[0][-1])
            step = int(output_name[-4:])
            df_sel = df_dict[chip_num].iloc[num_step * step:num_step * (
                step + 1)]
            df_start_index = 0
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
                for i in range(df_start_index, num_step):
                    item = df_sel.iloc[i]
                    if np.abs(x_data - item['X']) < 0.01 and np.abs(
                            y_data - item['Y']) < 0.01:
                        df_start_index = i
                        final_list.append(
                            pd.DataFrame(
                                item.append(data_series).to_dict(), index=[0]))
                        break
    df = pd.concat(final_list)
    df.reset_index(drop=True, inplace=True)

    print('Selecting ...')
    snr = 5
    sharp = 0.04
    crowd = 0.5
    flag = np.zeros(len(df))
    for i in range(len(df)):
        item = df.iloc[i]
        if (item[filter1 + '_SNR'] >=
                snr) and (item[filter2 + '_SNR'] >=
                          snr) and (item[filter1 + '_SHARP']**2 < sharp) and (
                              item[filter2 + '_SHARP']**2 < sharp) and (
                                  item[filter1 + '_CROWD'] <
                                  crowd) and (item[filter2 + "_CROWD"] < crowd):
            flag[i] = 1
    df = df.assign(flag=flag)

    print('Saving ...')
    df.to_pickle('df_{0}.pickle'.format(folder))

    subprocess.call('mv {0} final'.format(file_name), shell=True)
    subprocess.call('mv df_{0}.pickle final'.format(folder), shell=True)
