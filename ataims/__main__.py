import sys
import argparse
import logging

from ataims import parse_outputfile


def main():
    parser = argparse.ArgumentParser(
                    prog='outputparser',
                    description='Parses FHI-aims, Exciting and Quantum Espresso outputs',
    )
    parser.add_argument('filename', type=str, help='Path to the output file')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    fname = args.filename
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') 
    sys.stdout.write(parse_outputfile(fname, as_set=False).dump() + '\n')


if __name__ == '__main__':
    main()