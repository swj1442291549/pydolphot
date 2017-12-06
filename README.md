# pydolphot
pydolphot inspired by [dweisz](https://github.com/dweisz/pydolphot)

## Instruction


### Download the data

Download the data from [HST archieve](http://archive.stsci.edu/hst/search.php).

Use the following command to download the data (change the last 5 figures to your request)
```bash
wget -r --password swj1442291549@gmail.com ftp://stdatu.stsci.edu/stage/anonymous/anonymous90320
```

### Prepare for dolphot
After finishing the download, move the data to folder `raw` and remove the extra folders
```bash
mv -f stdatu.stsci.edu/stage/anonymous/anonymous90320 raw
rm -rf stdatu.stsci.edu
```

If it's the first time, remember to setup `dol` variable to the location of this repository on your computer. Here I show an example using `bash`
```bash
export dol="/data/Github/pydolphot"
```

### Run the dolphot
```bash
python $dol/dol.py
```
It will ask you to select one the drz fits file as the template. If no drizzle is required, any one should work.


After the previous command finishes, we need to combine the `output1` and `output2` into a single file
```bash
python $dol/phot.py
```
It will read the filter from `output1.columns` and save the result into `o.summary.fits` in folder `final`.

In the meantime, it will also made a selection on signal-to-noise ratio, sharpness, crowdness and object type. The corresponding result is saved in `o.gst.fits`.

If you want to know more about the selection creteria, please refer to [dolphot](https://github.com/dstndstn/dolphot) for more information. And if you change the creteria here, remember to make the same change in `photfake.py`.

### Fask star test
`fake.py` accept a pickle file as the main input (default file name: `fake.pickle`, `.pickle` is not required as part of the input). The pickle is composed of 5 columns: `chip`, `X`, `Y` and two filters. The filter name should end with `_VEGA`. A sample filter name looks like `F475W_VEGA` or `F814W_VEGA`. 

Right now, the filters name has to be given explicitly in the order from blue to red. Another additional parameter is the number of fake stars each run. The default value is 100.

The following command run fake stars for `fake.pickle` in filters `F475W` and `F814W`, with 100 stars each run.
```bash
python $dol/fake.py F475W F814W -f fake -n 100
```

`photfake.py` is used to generate the result from fake star tests. The parameters should keep the same as `fake.py`
```bash
python $dol/photfake.py F475W F814W -f fake -n 100
```

Both `fake.py` and `photfake.py` utilize multiple core to accerelate the calculation. You may want to change the size of pool depending on the condition of your computer.




