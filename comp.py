import numpy as np
import pandas as pd
from astropy.table import Table
import argparse
from random import shuffle
from collections import Counter


def histogram_equal(x, nbin):
    """Histogram objects into equal number

    Args;
        x (array): objects
        nbin (int): number of bin

    Returns:
        rad_bin (array): radius bins
    """
    npt = len(x)
    rad_bin = np.interp(
        np.linspace(0, npt, nbin + 1), np.arange(npt), np.sort(x))
    rad_bin[0] = int(rad_bin[0])
    rad_bin[-1] = rad_bin[-1] + 0.0001
    return rad_bin


def get_data(file_name):
    """Get data from o.gst.files

    Args:
        file_name (string): fielname

    Returns:
        df (DataFrame): data
    """
    df = Table.read(file_name).to_pandas()
    return df


def generate_complete(df, filter_list, total_num):
    fake_dict = dict()
    multiple = int(np.ceil(total_num / len(df)))
    for filter_name in filter_list:
        fake_dict['{0}_VEGA'.format(filter_name)] = np.array(multiple * list(df['{0}_VEGA'.format(
            filter_name)])) + np.random.random(len(df) * multiple) * 0.5 - 0.25
    df_fake = pd.DataFrame(fake_dict)
    return df_fake


def add_xy(df_fake, df):
    """Add fake XY to data

    Args:
        df_fake (DataFrame): fake data
        df (DataFrame): data
    """
    num = len(df_fake)
    X_min = min(df['X'])
    Y_min = min(df['Y'])
    X_max = max(df['X'])
    Y_max = max(df['Y'])
    X_fake = np.random.uniform(X_min, X_max, num)
    Y_fake = np.random.uniform(Y_min, Y_max, num)
    df_fake = df_fake.assign(X=X_fake)
    df_fake = df_fake.assign(Y=Y_fake)
    return df_fake


def get_filters(df):
    filter_list = []
    for key in df.keys():
        if '_VEGA' in key:
            filter_list.append(key[:-5])
    filter_list.sort()
    return filter_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n',
        '--num',
        type=int,
        default=50000,
        help='Num of fake stars (50000)')
    args = parser.parse_args()
    total_num = args.num
    df = get_data('final/o.gst.fits')
    filter_list = get_filters(df)
    chip_num = len(Counter(df['chip']))

    for chip in range(1, chip_num + 1):
        df_chip = df[df.chip == chip]
        df_fake = generate_complete(df_chip, filter_list, total_num / chip_num)
        df_fake = add_xy(df_fake, df_chip)
        t = Table.from_pandas(df_fake)
        t.write('complete{0:d}.fits'.format(chip), overwrite=True)

