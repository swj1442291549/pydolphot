import numpy as np
import sys
import astropy.table
from astropy import units as u
from astropy.io import fits
from astropy import wcs
import pandas as pd
from collections import Counter
import subprocess
import os
import glob

if __name__ == "__main__":
    refname = glob.glob("*drz.fits")[0]

    global_labels = ["Number", "RA", "DEC", "X", "Y", "OBJECT_TYPE"]
    filter_labels = ["_VEGA", "_ERR", "_SNR", "_SHARP", "_ROUND", "_CROWD", "_FLAG"]
    formats = ["f8", "f8", "f8", "f8", "f8", "f8", "f8"]

    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)
    chip_num = len(glob.glob("output[0-9]"))

    # read filters from output.columns
    df_column = pd.read_table("output1.columns", names=["column"])
    filters = []
    for i in range(int((len(df_column) - 11) / 13)):
        column = df_column.iloc[11 + 13 * i]["column"]
        if "(" in column:
            column_filter = column.split("(")[1].split(",")[0]  # ACS
        else:
            column_filter = column.split(",")[1].strip()  # WFC3
        if column_filter not in filters:
            filters.append(column_filter)
    nfilters = len(filters)

    t_list = list()
    for chip in range(1, 1 + chip_num):
        data_name = "output{0:d}".format(chip)
        print("Loading raw DOLPHOT file...")
        data = np.loadtxt(data_name)
        print("Loaded {0} objects from chip {1:d}".format(len(data), chip))
        num = np.arange(len(data[:, 0])) + 1
        world = w.wcs_pix2world(data[:, 2], data[:, 3], 1)

        ra = world[0]
        dec = world[1]
        chips = np.ones_like(ra) * chip

        t = astropy.table.Table()
        t.add_column(astropy.table.Column(name="chip", data=chips))  # chip number
        t.add_column(astropy.table.Column(name=global_labels[1], data=ra))  # RA
        t.add_column(astropy.table.Column(name=global_labels[2], data=dec))  # DEC
        t.add_column(astropy.table.Column(name=global_labels[3], data=data[:, 2]))  # X
        t.add_column(astropy.table.Column(name=global_labels[4], data=data[:, 3]))  # Y
        t.add_column(
            astropy.table.Column(name=global_labels[5], data=data[:, 10])
        )  # ObjType
        cols = np.int_(np.asarray((15, 17, 19, 20, 21, 22, 23)))

        # loops over number of filters, names of filters to generate output columns
        for i in range(nfilters):
            for j, k in enumerate(filter_labels):
                t.add_column(
                    astropy.table.Column(
                        name=filters[i] + k, data=data[:, cols[j] + (i * 13)]
                    )
                )
        t_list.append(t)

    t = astropy.table.vstack(t_list)

    t.write("o.summary.fits", overwrite=True)

    snr = 5.0
    sharp = 0.04
    crowd = 0.5
    objtype = 1
    flag = 99

    wgood_list = list()
    for i in range(nfilters):
        wgood = np.where(
            (t[filters[i] + "_SNR"] >= snr)
            & (t[filters[i] + "_SHARP"] ** 2 < sharp)
            & (t[filters[i] + "_CROWD"] < crowd)
            & (t["OBJECT_TYPE"] == objtype)
            & (t[filters[i] + "_FLAG"] <= flag)
        )
        wgood_list.append(wgood[0])
    cnt = Counter(np.concatenate(wgood_list))
    wgood_index = [k for k, v in cnt.items() if v >= nfilters]

    t1 = t[wgood_index]
    t1.write("o.gst.fits", overwrite=True)

    if not os.path.isdir("final"):
        subprocess.call("mkdir final", shell=True)
    subprocess.call("mv o.summary.fits final", shell=True)
    subprocess.call("mv o.gst.fits final", shell=True)
