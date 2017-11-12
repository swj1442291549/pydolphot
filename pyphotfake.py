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
    parser.add_argument("name", help='DataFrame pickle file name')
    parser.add_argument("Bfilter", help='Blue Filter name')
    parser.add_argument("Rfilter", help='Red Filter name')
    parser.add_argument('n', type=int, default=100, help='Number of fake stars')
    args = parser.parse_args()
    file_name = args.name
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num_step = args.n

    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    df = read_pickle(file_name, filter1, filter2)
    df_dict = {1: df[df['chip'] == 1], 2: df[df['chip'] == 2]}



    final_list = list()
    output_names = glob.glob('fake/output*')
    for output_name in output_names:
        if os.stat(output_name).st_size == 0:
            continue
        else:
            data = np.loadtxt(output_name)
            chip_num = int(output_name.split('.')[0][-1])
            step = int(output_name[-4:])
            df_sel = df_dict[chip_num].iloc[num_step * step: num_step * (step + 1)]
            df_start_index = 0
            if len(data.shape) == 1:
                data = [data]
            for data_item in data:
                x_data = data_item[2]
                y_data = data_item[3]
                f1 = data_item[31]
                f2 = data_item[44]
                if f1 > 99 or f2 > 99:
                    continue
                else:
                    data_series = pd.Series([f1, f2], index=['{0}_VEGA'.format(filter1), '{0}_VEGA'.format(filter2)])
                    for i in range(df_start_index, num_step):
                        item = df_sel.iloc[i]
                        if np.abs(x_data - item['X']) < 0.01 and np.abs(y_data - item['Y']) < 0.01:
                            df_start_index = i
                            final_list.append(pd.DataFrame(item.append(data_series).to_dict(), index=[0]))
                            break

    df = pd.concat(final_list)
    df.reset_index(drop=True, inplace=True)
    df.to_pickle('df_fake.pickle')

    subprocess.call('mv df.pickle final', shell=True)
    subprocess.call('mv df_fake.pickle final', shell=True)
