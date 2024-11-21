import sys
import argparse
import logging

from ataims import parse_outputfile


def main():
    """Basic CLI. For programmatic use `from ataims import parse_outputfile` ."""
    parser = argparse.ArgumentParser(
                    prog='ataims',
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
    try:
        out = parse_outputfile(fname, as_set=False).model_dump_json() + '\n'
    except Exception as e:
        sys.stdout.write(f"Error parsing output file: {e}\n")
        sys.exit(1)
    sys.stdout.write(out)


if __name__ == '__main__':
    main()
