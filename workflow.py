import subprocess
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('index', type=int, help='Index of anonymous')
    args = parser.parse_args()
    index = args.index

    subprocess.call('python $dol/download.py {0}'.format(index), shell=True)
    subprocess.call('python $dol/dol.py', shell=True)
    subprocess.call('python $dol/phot.py', shell=True)
    subprocess.call('python $dol/comp.py', shell=True)
    subprocess.call('python $dol/fake.py', shell=True)
    subprocess.call('python $dol/photfake.py', shell=True)

