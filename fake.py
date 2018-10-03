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
import random


def generate_fakelist(df, fake_num, filter_list, folder):
    """Generate the fakelist
    
    Args:
        df (DataFrame): data
        fake_num (int): fake index
        filter_list (list): filter list
        folder (string): output folder
    """
    with open('{0}/fake.list{1:0>4}'.format(folder, fake_num),
              'w') as f:
        for i in range(len(df)):
            f.write('0 1 {0} {1}'.format(
                df.iloc[i]['X'], df.iloc[i]['Y']))
            for filter in filter_list:
                f.write(' {0}'.format(df.iloc[i]['{0}_VEGA'.format(filter)]))
            f.write('\n')


def generate_fake_param(folder):
    """Generate parameter file for fake star
    
    Args:
        folder (string): output folder
    """
    subprocess.call(
        'cp phot.param phot.{0}.param'.format(folder),
        shell=True)
    with open('phot.{0}.param'.format(folder), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        '--file',
        default='complete',
        help='Input fake star fits file (complete)')
    parser.add_argument(
        '-r', '--run', type=int, default=100, help='Number of fake stars per run (100)')
    parser.add_argument(
        '-c', type=int, default=30, help='Number of cores (30)')
    parser.add_argument('--force', action='store_true', help='Force (False)')
    parser.add_argument('--con', action='store_true', help='Continuum (False)')
    args = parser.parse_args()
    folder = args.file
    num_step = args.run
    core = args.c
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
            filter_list = get_filters(df)

            generate_fake_param(folder)

            print('Generating fake ...')
            fake_num = int(len(df) / num_step)
            for i in tqdm(range(fake_num)):
                df_sel = df.iloc[i * num_step:(i + 1) * num_step]
                generate_fakelist(df_sel, i, filter_list, folder)

            print('Running ...')
            output_names = glob.glob('{0}/fake*'.format(folder))

            def inner_dolphot(output_name):
                index = int(output_name.split('list')[1])
                subprocess.call(
                    [
                        'dolphot', 'output',
                        '-pphot.{0}.param'.format(folder),
                        'FakeStars={0}/fake.list{1:0>4}'.format(
                            folder,
                            index), 'FakeOut={0}/output.fake{1:0>4}'.format(
                                folder, index)
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
                index = int(output_name.split('list')[1])
                fake_name = '{0}/output.fake{1:0>4}'.format(folder, index)
                if fake_name not in fake_names:
                    output_names.append(output_name)

            def inner_dolphot(output_name):
                index = int(output_name.split('list')[1])
                subprocess.call(
                    [
                        'dolphot', 'output',
                        '-pphot.{0}.param'.format(folder),
                        'FakeStars={0}/fake.list{1:0>4}'.format(
                            folder,
                            index), 'FakeOut={0}/output.fake{1:0>4}'.format(
                                folder, index)
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

            with Pool(core) as p:
                with tqdm(total=len(output_names)) as pbar:
                    for i, _ in tqdm(
                            enumerate(
                                p.imap_unordered(inner_dolphot, output_names))):
                        pbar.update()
