# pydolphot
A python wrapper for [DOLPHOT](http://americano.dolphinsim.com/dolphot/).
pydolphot inspired by [dweisz](https://github.com/dweisz/pydolphot).

Support WFC3, ACS and WFPC2.
Support handle more than two filters.

## Instruction

### Preparation

If it's the first time you use the code, please remember to set `dol` variable to the location of this repository on your computer. Here is an example using `bash`
```bash
export dol="/data/Github/pydolphot"
```

It uses [axel](https://github.com/axel-download-accelerator/axel) to accelerate the download process. Be sure to install it before running the code.

### Download the data (optional)

Get access for the data from [HST archieve](http://archive.stsci.edu/hst/search.php) and ask for an anonymous download using email (This is only format support by this script). You can use your favorite ways to download the data, just put them under folder `raw` once you finish the download.

Use the following command to download the data (change the last 5 figures to your request)
```bash
python download.py index [-h] [-c connection numbers] index
```
`index` is the anonymous number of your request. 
**Remember to change the email to yours.**

All the raw data downloaded will appear in the folder `raw` and remain unchanged. Feel free to remove them after the you have reduced the data. 

### Run the dolphot
`dol.py` combine all the procedures into one file
```bash
python $dol/dol.py [-ih] [--force]
```
It will ask you to select one the `drz` fits file as the template. If no drizzle is required, any one should work.

If `force` is enable, then it will just pick the first drz it find, which is useful when you want it be automatic.
`-i`, `--info` would print the basic information of this data, including the PI's name (if available), Proposal ID, filters and exposure time.

This file will do `mask`, `split`, `calsky` and `dolphot` automatically and generate the output files `output1` and `output2` (`output3` and `output4` if you are working on WFPC2 data).

After the previous command finishes, we need to combine the output files into a single file
```bash
python $dol/phot.py
```
It will read the filters from `output{chip}.columns` and save the result into `o.summary.fits` in folder `final`.

In the meantime, it will also make a selection on signal-to-noise ratio, sharpness, crowdness and object type. The corresponding result is saved in `o.gst.fits`.

If you want to know more about the selection criteria, please refer to [dolphot](https://github.com/dstndstn/dolphot) for more information. And if you change the criteria here, remember to make the same change in `photfake.py`.

### Completeness test
Use the following command to generate a fake star list automatically in the name of `complete.fits`

```bash
python $dol/comp.py [-h] [-n fake star number]
```

It would generate a fake star list span all the magnitude range with weighted number. The data set is composed of 5 columns: `chip`, `X`, `Y` and brightness in all the filters. The filter name should end with `_VEGA`, for example `F475W_VEGA` or `F814W_VEGA`.

### Fake star test
```bash
python $dol/fake.py [-f fakefile] [-r run] [-c num] [--force] [--con]
```
The fakefile is set to complete by default
`--run` control the number of fake stars per run. This is designed to control the influence of brightness variance from the fake star.

`-c` control the number of core used. This code use multiple-core to acceleration the fake star test, which can save a lot of time.

`--force` if enabled, it would clear up the output folder from the last run and begin a new start

`--con` if enabled, it would continue the last run, which may be terminated for any cause.

During the fake star test, a folder named after the fake star file will be created and store all the middle files. Be sure not to delete it before you run `photfake.py` command. Please don't name the fake star file as `final.fits`, which would leave a lot of trash in folder `final`.

`photfake.py` is used to generate the result from fake star tests. The parameters should keep the same as `fake.py`
```bash
python $dol/photfake.py [-f outputfolder] [-r run] [-c num]
```
`--folder` is the output folder's name from `fake.py`

`-r` which be the same as the parameter in `fake.py`

`-c` control the number of core used.

The output files will be saved as `f.complete.fits` (the middle part is the same as fake star file name) in folder `final`. The column `flag` present whether the fake star is detected or not.

Both `fake.py` and `photfake.py` utilize multiple cores to accelerate the calculation. You may want to change the size of pool depending on the condition of your computer.

## Cheatsheet
If you are lazy and don't want try this code step by step, you can also use the workflow I have built
```bash
python $dol/workflow.py index
```
`index` is the anonymous number of your request. 



