import subprocess
import os
import pandas as pd
import numpy as np
from astropy.io import fits
from astropy.table import Table
import argparse
import glob
import random
import pickle
from multiprocessing import Pool
from tqdm import tqdm


def generate_fakelist(df, chip_num, fake_num, filter1, filter2, folder):
    """Generate the fakelist
    
    Args:
        df (DataFrame): data
        chip_num (int): chip 1 or 2
        fake_num (int): fake index
        filter1 (string): filter1
        filter2 (string): filter2
        folder (string): output folder
    """
    with open('{0}/fake{1}.list{2:0>4}'.format(folder, chip_num, fake_num),
              'w') as f:
        for i in range(len(df)):
            f.write('0 1 {0} {1} {2} {3}\n'.format(
                df.iloc[i]['X'], df.iloc[i]['Y'],
                df.iloc[i]['{0}_VEGA'.format(filter1)],
                df.iloc[i]['{0}_VEGA'.format(filter2)]))


def generate_fake_param(chip_num, folder):
    """Generate parameter file for fake star
    
    Args:
        chip_num (int): chip number 1 or 2
        folder (string): output folder
    """
    subprocess.call(
        'cp phot{0}.param phot{0}.{1}.param'.format(chip_num, folder),
        shell=True)
    with open('phot{0}.fake.param'.format(chip_num), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        '--folder',
        default='complete',
        help='Output folder name (complete)')
    parser.add_argument(
        '-n', '--num', type=int, default=100, help='Number of fake stars (100)')
    parser.add_argument(
        '--core', type=int, default=30, help='Number of core (30)')
    parser.add_argument('--force', action='store_true', help='Force (False)')
    parser.add_argument('--con', action='store_true', help='Continuum (False)')
    args = parser.parse_args()
    folder = args.folder
    num_step = args.num
    core = args.core
    con = args.con
    force = args.force
    file_name = '{0}.fits'.format(folder)

    if not os.path.exists(file_name):
        print('No {0} is found. Make sure the directory is correct.'.format(
            file_name))
    else:
        is_cal = 'n'
        if force == True:
            subprocess.call('rm -rf {0}'.format(folder), shell=True)
            subprocess.call('mkdir {0}'.format(folder), shell=True)
            is_cal = 'y'
        elif not con:
            if os.path.isdir(folder):
                is_cal = input(
                    'Folder {0} already exists. Are you sure to remove it? (y/n) '.
                    format(folder))
                if is_cal == 'y':
                    subprocess.call('rm -rf {0}'.format(folder), shell=True)
                    subprocess.call('mkdir {0}'.format(folder), shell=True)
            else:
                print("{0} is not found. Create a new one.".format(folder))
                subprocess.call('mkdir {0}'.format(folder), shell=True)
                is_cal = 'y'

        if is_cal == 'y':
            print('Reading ...')
            df = read_fits(file_name)
            filter1, filter2 = get_filters(df)

            df1 = df[df['chip'] == 1]
            df2 = df[df['chip'] == 2]

            generate_fake_param(1, folder)
            generate_fake_param(2, folder)

            print('Generating fake 1 ...')
            fake1_num = int(len(df1) / num_step)
            for i in tqdm(range(fake1_num)):
                df1_sel = df1.iloc[i * num_step:(i + 1) * num_step]
                generate_fakelist(df1_sel, 1, i, filter1, filter2, folder)
            print('Generating fake 2 ...')
            fake2_num = int(len(df2) / num_step)
            for i in tqdm(range(fake2_num)):
                df2_sel = df2.iloc[i * num_step:(i + 1) * num_step]
                generate_fakelist(df2_sel, 2, i, filter1, filter2, folder)

            print('Running ...')
            output_names = glob.glob('{0}/fake*'.format(folder))

            def inner_dolphot(output_name):
                chip_num = int(output_name.split('list')[0][-2])
                index = int(output_name.split('list')[1])
                subprocess.call(
                    [
                        'dolphot', 'output{0}'.format(chip_num),
                        '-pphot{0}.{1}.param'.format(chip_num, folder),
                        'FakeStars={0}/fake{1}.list{2:0>4}'.format(
                            folder, chip_num,
                            index), 'FakeOut={0}/output{1}.fake{2:0>4}'.format(
                                folder, chip_num, index)
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

            with Pool(core) as p:
                with tqdm(total=len(output_names)) as pbar:
                    for i, _ in tqdm(
                            enumerate(
                                p.imap_unordered(inner_dolphot, output_names))):
                        pbar.update()
        if con:

            print('Running ...')
            output_names = list()
            fake_names = glob.glob('{0}/output*'.format(folder))
            for output_name in glob.glob('{0}/fake*'.format(folder)):
                chip_num = int(output_name.split('list')[0][-2])
                index = int(output_name.split('list')[1])
                fake_name = '{0}/output{1}.fake{2:0>4}'.format(folder, chip_num, index)
                if fake_name not in fake_names:
                    output_names.append(output_name)


            def inner_dolphot(output_name):
                chip_num = int(output_name.split('list')[0][-2])
                index = int(output_name.split('list')[1])
                subprocess.call(
                    [
                        'dolphot', 'output{0}'.format(chip_num),
                        '-pphot{0}.{1}.param'.format(chip_num, folder),
                        'FakeStars={0}/fake{1}.list{2:0>4}'.format(
                            folder, chip_num,
                            index), 'FakeOut={0}/output{1}.fake{2:0>4}'.format(
                                folder, chip_num, index)
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

            with Pool(core) as p:
                with tqdm(total=len(output_names)) as pbar:
                    for i, _ in tqdm(
                            enumerate(
                                p.imap_unordered(inner_dolphot, output_names))):
                        pbar.update()
