import subprocess
import pandas as pd
import numpy as np
from astropy.io import fits
import argparse
import glob
from scipy import integrate
import random
from scipy.interpolate import interp1d


def kroupa_mf(m):
    if m >= 0.5:
        p = m**-2.35
    elif m >= 0.08:
        p = 2 * m**-1.35
    else:
        p = 25 * m**-0.35
    return p


def kroupa_pdf(m, min_m, max_m):
    if m < min_m or m > max_m:
        return 0
    else:
        return kroupa_mf(m) / integrate.quad(lambda x: kroupa_mf(x), min_m, max_m)[0]


def kroupa_gen(num, min_m, max_m):
    result = []
    for i in range(num):
        flag = 0
        c = kroupa_pdf(min_m, min_m, max_m)
        while flag == 0:
            x = random.uniform(min_m, max_m)
            y = random.uniform(0, 1)
            if y < kroupa_pdf(x, min_m, max_m) / c:
                result.append(x)
                flag = 1
    return result


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

    df_iso = pd.read_table(
        iso_file, comment='#', delim_whitespace=True)
    df = df_iso[df_iso['log(age/yr)'] == 9.21]
    df = df[df[filter1] < max(df_chip['{0}_VEGA'.format(filter1)]) + 1 - dm]
    min_m = min(df['M_ini'])
    max_m = max(df['M_ini'])
    print('Generating fake masses ...')
    mass_fake = kroupa_gen(num, min_m, max_m)
    f1 = interp1d(df['M_ini'], df[filter1])
    f2 = interp1d(df['M_ini'], df[filter2])
    filter1_fake = f1(mass_fake)
    filter2_fake = f2(mass_fake)
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
    with open('fake{0}.list'.format(chip_num), 'w') as f:
        for i in range(num):
            f.write('0 1 {0} {1} {2} {3}\n'.format(X_fake[i], Y_fake[i], filter1_fake[i] + dm, filter2_fake[i] + dm))


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
    parser.add_argument("Bfilter", help='Blue Filter name (first)')
    parser.add_argument("Rfilter", help='Red Filter name (second)')
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