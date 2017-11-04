import subprocess
import pandas as pd
import numpy as np
from astropy.io import fits
import argparse


def generate_fakelist(chip_num, filter1, filter2, num):
    hdu_list = fits.open('final/o.gst.fits')
    data = hdu_list[1].data
    df = pd.DataFrame(np.array(data).byteswap().newbyteorder())
    df_chip = df[df['chip'] == chip_num]
    X_min = min(df_chip['X'])
    Y_min = min(df_chip['Y'])
    X_max = max(df_chip['X'])
    Y_max = max(df_chip['Y'])
    X_fake = np.random.uniform(X_min, X_max, num)
    Y_fake = np.random.uniform(Y_min, Y_max, num)
    f1_list = [19, 20, 21, 22]
    c12_list = [0.25, 0.5, 0.75, 1, 1.25, 1.5]
    with open('fake{0}.list'.format(chip_num), 'w') as f:
        for f1_mag in f1_mag:
            for c12 in c12_list:
                for i in range(num):
                    f.write('0 1 {0} {1} {2} {3}\n'.format(
                        X_fake[i], Y_fake[i], f1_mag, f1_mag - c12))


def generate_fake_param(chip_num):
    subprocess.call(
        'cp phot{0}.param phot{0}.fake.param'.format(chip_num), shell=True)
    with open('phot{0}.fake.param'.format(chip_num), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")
        f.write('FakeStars=fake{0}.list'.format(chip_num))


def run_script():
    with open('run_fake.sh', 'w') as f:
        f.write("dolphot output1 -pphot1.fake.param >> fake1.log&\n")
        f.write("dolphot output2 -pphot2.fake.param >> fake2.log&\n")
    subprocess.call('chmod a+x run_fake.sh', shell=True)
    subprocess.call('./run_fake.sh', shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Bfilter", help='Blue Filter name')
    parser.add_argument("Rfilter", help='Red Filter name')
    parser.add_argument(
        '-n', type=int, default=1000, help='Number of fake stars')
    args = parser.parse_args()
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num = args.n

    generate_fakelist(1, filter1, filter2, num)
    generate_fakelist(2, filter1, filter2, num)

    generate_fake_param(1)
    generate_fake_param(2)

    run_script()
