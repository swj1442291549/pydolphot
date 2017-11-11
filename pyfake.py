import subprocess
import os
import pandas as pd
import numpy as np
from astropy.io import fits
import argparse
import glob
import random
import pickle


    

def generate_fakelist(df, chip_num, fake_num, filter1, filter2):
    with open('fake/fake{0}.list{1:0>4}'.format(chip_num, fake_num), 'w') as f:
        for i in range(len(df)):
            f.write('0 1 {0} {1} {2} {3}\n'.format(df.iloc[i]['X'], df.iloc[i]['Y'], df.iloc[i]['{0}_VEGA'.format(filter1)], df.iloc[i]['{0}_VEGA'.format(filter2)]))


def generate_fake_param(chip_num):
    subprocess.call(
        'cp phot{0}.param phot{0}.fake.param'.format(chip_num), shell=True)
    with open('phot{0}.fake.param'.format(chip_num), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")


def run_script():
    subprocess.call('chmod a+x run_fake.sh', shell=True)
    print('Running dolphot ...')
    subprocess.call('./run_fake.sh', shell=True)


def read_pickle(file_name):
    df = pickle.load(open(file_name, 'rb'))
    df = df.sort_values(by=['X'])
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help='DataFrame pickle file name')
    parser.add_argument("Bfilter", help='Blue Filter name (first)')
    parser.add_argument("Rfilter", help='Red Filter name (second)')
    parser.add_argument('-n', type=int, default=100, help='Number of fake stars')
    args = parser.parse_args()
    file_name = args.name
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num_step = args.n

    if os.path.isdir('fake'):
        subprocess.call('rm -rf fake', shell=True)
    subprocess.call('mkdir fake', shell=True)

    df = read_pickle(file_name)

    df1 = df[df['chip'] == 1]
    df2 = df[df['chip'] == 2]

    generate_fake_param(1)
    generate_fake_param(2)

    fake1_num = int(len(df1) / num_step)
    for i in range(fake1_num):
        df1_sel = df1.iloc[i * num_step: (i+1) * num_step]
        generate_fakelist(df1_sel, 1, i, filter1, filter2)
    fake2_num = int(len(df2) / num_step)
    for i in range(fake2_num):
        df2_sel = df2.iloc[i * num_step: (i+1) * num_step]
        generate_fakelist(df2_sel, 2, i, filter1, filter2)

    with open('run_fake.sh', 'w') as f:
        for i in range(fake1_num):
            if i % 20 == 19:
                f.write("dolphot output1 -pphot1.fake.param FakeStars=fake/fake1.list{0:0>4} FakeOut=fake/output1.fake{0:0>4} >> fake1.log\n".format(i))
            else:
                f.write("dolphot output1 -pphot1.fake.param FakeStars=fake/fake1.list{0:0>4} FakeOut=fake/output1.fake{0:0>4} >> fake1.log&\n".format(i))
        for i in range(fake2_num):
            if i % 20 == 19:
                f.write("dolphot output2 -pphot2.fake.param FakeStars=fake/fake2.list{0:0>4} FakeOut=fake/output2.fake{0:0>4} >> fake2.log\n".format(i))
            else:
                f.write("dolphot output2 -pphot2.fake.param FakeStars=fake/fake2.list{0:0>4} FakeOut=fake/output2.fake{0:0>4} >> fake2.log&\n".format(i))
    run_script()
