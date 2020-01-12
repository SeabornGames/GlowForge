import os
import sys
from argparse import ArgumentParser
from shutil import copyfile
from seaborn_table import SeabornTable
from seaborn_glowforge.diagram import Cell, Special, Door, Virtual, Window, Wall


def main(cli_args=sys.argv[1:]):
    args = parse_args(cli_args)
    if args.backup_file and args.backup_file != '-':
        if os.path.exists(args.output_file):
            copyfile(args.output_file, args.backup_file)

    if args.input_file and os.path.exists(args.input_file):
        args = Cell.parse_file(args)



def parse_args(cli_args):
    parser = ArgumentParser(description='The seaborn_glowforge.glowforge will'
                                        ' create the walls for glowforge.')
    parser.add_argument('--wall-file', default=None,
                        help='table file from seaborn_table defining the wall'
                             ' dimensions, which will be created if it does not'
                             ' exist. Defaults to the input file plus wall.md')
    parser.add_argument('--wall-height', type=float, default=10.0,
                        help='default height of the walls when creating the'
                             ' wall file.')
    parser.add_argument('--blank', default=' ',
                        help='character to use to represent blank space')
    parser.add_argument('--checker', default='░',
                        help='character of the oscillating foot spaces')
    parser.add_argument('--ten-checker', default='▒',
                        help='character of the oscillating 10 foot spaces')
    parser.add_argument('--no-header', action='store_true', default=False,
                        help='skip putting the header in the file')
    parser.add_argument('--backup-file', '-b', default=None,
                        help='Path to save the old file to back it up, defaults'
                             ' to the <basename>.bck.')
    parser.add_argument('--input-file', '-i',
                        help='Path to the input file which will be cleaned'
                             ' checkered grid corners and centere / space the'
                             ' name of the rooms.')
    parser.add_argument('--output-file', '-o', default=None,
                        help='Path to the output file default to the input'
                             ' file.')
    args = parser.parse_args(cli_args)
    if args.input_file and args.output_file is None:
        args.output_file = args.input_file
    if args.output_file and args.backup_file is None:
        args.backup_file = f"{args.output_file.rsplit('.', 1)[0]}.bck"
    return args


if __name__ == '__main__':
    main()
