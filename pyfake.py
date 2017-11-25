import subprocess
import os
import pandas as pd
import numpy as np
from astropy.io import fits
import argparse
import glob
import random
import pickle
from multiprocessing import Pool
from tqdm import tqdm


def generate_fakelist(df, chip_num, fake_num, filter1, filter2, folder):
    with open('{0}/fake{1}.list{2:0>4}'.format(folder, chip_num, fake_num),
              'w') as f:
        for i in range(len(df)):
            f.write('0 1 {0} {1} {2} {3}\n'.format(
                df.iloc[i]['X'], df.iloc[i]['Y'],
                df.iloc[i]['{0}_VEGA'.format(filter1)],
                df.iloc[i]['{0}_VEGA'.format(filter2)]))


def generate_fake_param(chip_num, folder):
    subprocess.call(
        'cp phot{0}.param phot{0}.{1}.param'.format(chip_num, folder),
        shell=True)
    with open('phot{0}.fake.param'.format(chip_num), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")


def read_pickle(file_name):
    df = pickle.load(open(file_name, 'rb'))
    df = df.sort_values(by=['X'])
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Bfilter", help='Blue Filter name (first)')
    parser.add_argument("Rfilter", help='Red Filter name (second)')
    parser.add_argument(
        "-f", '--folder', default='fake', help='Output folder name (fake)')
    parser.add_argument(
        '-n', '--num', type=int, default=100, help='Number of fake stars (100)')
    args = parser.parse_args()
    folder = args.folder
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num_step = args.num
    file_name = '{0}.pickle'.format(folder)

    if os.path.isdir(folder):
        subprocess.call('rm -rf {0}'.format(folder), shell=True)
    subprocess.call('mkdir {0}'.format(folder), shell=True)

    print('Reading ...')
    df = read_pickle(file_name)

    df1 = df[df['chip'] == 1]
    df2 = df[df['chip'] == 2]

    generate_fake_param(1, folder)
    generate_fake_param(2, folder)

    print('Generating fake 1...')
    fake1_num = int(len(df1) / num_step)
    for i in tqdm(range(fake1_num)):
        df1_sel = df1.iloc[i * num_step:(i + 1) * num_step]
        generate_fakelist(df1_sel, 1, i, filter1, filter2, folder)
    print('Generating fake 2...')
    fake2_num = int(len(df2) / num_step)
    for i in tqdm(range(fake2_num)):
        df2_sel = df2.iloc[i * num_step:(i + 1) * num_step]
        generate_fakelist(df2_sel, 2, i, filter1, filter2, folder)

    print('Running ...')
    output_names = glob.glob('{0}/fake*'.format(folder))
    def inner_dolphot(output_name):
        chip_num = int(output_name.split('list')[0][-2])
        index = int(output_name.split('list')[1])
        subprocess.call(['dolphot', 'output{0}'.format(chip_num), '-pphot{0}.{1}.param'.format(chip_num, folder), 'FakeStars={0}/fake{1}.list{2:0>4}'.format(folder, chip_num, index), 'FakeOut={0}/output{1}.fake{2:0>4}'.format(folder, chip_num, index)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with Pool(30) as p:
        with tqdm(total=len(output_names)) as pbar:
            for i, _ in tqdm(enumerate(p.imap_unordered(inner_dolphot, output_names))):
                pbar.update()
