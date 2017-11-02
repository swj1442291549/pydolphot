import subprocess
import argparse




def generate_fakelist(chip_num, filter1, filter2, f1_min, f2_max, c_min, c_max, n_star):
    subprocess.call('fakelist output{0} {1} {2} {3} {4} {5} {6} -nstar={7} > fakelist{0}'.format(chip_num, filter1, filter2, f1_min, f1_max, c_min, c_max, n_star), shell=True)
    


def generate_fake_param(chip_num):
    subprocess.call('cp phot{0}.param phot{0}.fake.param'.format(chip_num), shell=True)
    with open('phot{0}.fake.param'.format(chip_num), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")
        f.write('FakeStars=fakelist{0}'.format(chip_num))


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
    parser.add_argument("Magmin", help='Minimum mag')
    parser.add_argument("Magmax", help='Maximum mag')
    parser.add_argument("Colormin", help='Minimum color')
    parser.add_argument("Colormax", help='Maximum color')
    parser.add_argument("nstar", help='Nstar')
    args = parser.parse_args()
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    f1_min = args.Magmin
    f1_max = args.Magmax
    c_min = args.Colormin
    c_max = args.Colormax
    n_star = args.nstar

    generate_fakelist(1, filter1, filter2, f1_min, f1_max, c_min, c_max, n_star)
    generate_fakelist(2, filter1, filter2, f1_min, f1_max, c_min, c_max, n_star)

    generate_fake_param(1)
    generate_fake_param(2)

    run_script()
