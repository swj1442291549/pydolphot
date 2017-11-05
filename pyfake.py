import subprocess
import pandas as pd
import numpy as np
from astropy.io import fits
import argparse
import glob


def kroupa_mf(ms):
    p = np.zeros_like(ms)
    for i, m in enumerate(ms):
        if m >= 0.5:
            p[i] = m**-2.35
        elif m >= 0.08:
            p[i] = 2 * m**-1.35
        else:
            p[i] = 25 * m**-0.35
    return p


def pick_iso():
    iso_files = sorted(glob.glob("isochrone/*.dat"))
    filenames = [j.replace('isochrone/', "") for j in iso_files]
    for i, j in enumerate(filenames):
        print("{0}: {1}".format(i, j))
    index = input('Use which isochrone file as the reference: ')
    if index.isdigit():
        index = int(index)
    else:
        raise ValueError('Please input an integer!')
    return iso_files[index]


def generate_fakelist(iso_file, chip_num, filter1, filter2, num_input, dm):
    hdu_list = fits.open('final/o.gst.fits')
    data = hdu_list[1].data
    df_o = pd.DataFrame(np.array(data).byteswap().newbyteorder())
    df_chip = df_o[df_o['chip'] == chip_num]
    X_min = min(df_chip['X'])
    Y_min = min(df_chip['Y'])
    X_max = max(df_chip['X'])
    Y_max = max(df_chip['Y'])

    f1_mag_max = max(df_chip['{0}_VEGA'.format(filter1)])
    df_iso = pd.read_table(
        iso_file, comment='#', delim_whitespace=True)
    df = df_iso[df_iso['log(age/yr)'] == 9.21]
    df = df[df[filter1] < f1_mag_max + 1 - dm]
    df = df.assign(num=np.random.poisson(
        (kroupa_mf(df['M_ini'])) * num_input / sum(kroupa_mf(df['M_ini']))))
    num = sum(df['num'])
    hdu_list = fits.open('final/o.gst.fits')
    data = hdu_list[1].data
    df_o = pd.DataFrame(np.array(data).byteswap().newbyteorder())
    df_chip = df_o[df_o['chip'] == chip_num]
    X_min = min(df_chip['X'])
    Y_min = min(df_chip['Y'])
    X_max = max(df_chip['X'])
    Y_max = max(df_chip['Y'])
    X_fake = np.random.uniform(X_min, X_max, num)
    Y_fake = np.random.uniform(Y_min, Y_max, num)
    num_i = 0
    with open('fake{0}.list'.format(chip_num), 'w') as f:
        for i in range(len(df)):
            for index_item in range(int(df.iloc[i]['num'])):
                f.write('0 1 {0} {1} {2} {3}\n'.format(X_fake[num_i], Y_fake[
                    num_i], df.iloc[i][filter1] + dm, df.iloc[i][filter2] + dm))
                num_i += 1


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
    parser.add_argument("dm", type=float, help='Distance Modulus')
    parser.add_argument(
        '-n', type=int, default=10000, help='Number of fake stars')
    args = parser.parse_args()
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    dm = args.dm
    num = args.n

    iso_file = pick_iso()

    generate_fakelist(iso_file, 1, filter1, filter2, num, dm)
    generate_fakelist(iso_file, 2, filter1, filter2, num, dm)

    generate_fake_param(1)
    generate_fake_param(2)

    run_script()
