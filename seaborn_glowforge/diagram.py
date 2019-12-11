import sys
from argparse import ArgumentParser


def main(cli_args=sys.argv[1:]):
    parser = ArgumentParser(description='The seaborn_glowforge.diagram will'
                                        ' create a layout file')
    parser.add_argument('--width', type=int, default=100,
                        help='number of feet per row in the file. round to the'
                             'nearest ten.')
    parser.add_argument('--height', type=int, default=100,
                        help='number of feet of rows in the file.')
    parser.add_argument('--blank', default=' ',
                        help='character to use to represent blank space')
    parser.add_argument('--no-header', action='store_true', default=False,
                        help='skip putting the header in the file')
    parser.add_argument('--checker', default=None,
                        help='if specified will checker the blank spaces')
    parser.add_argument('--output-file', '-o', default=None,
                        help='Path to the output file default to print to the'
                             ' screen.')
    args = parser.parse_args(cli_args)
    args.width = args.width + (10 - args.width%10 if args.width%10 else 0)
    data = []
    row = args.blank*args.width
    if not args.no_header:
        data = [' '*5]*3
        for w in range(args.width // 10):
            data[0] += str(w%10)*40
        data[1] += '0000111122223333444455556666777788889999'*(args.width//10)
        data[2] += ' ¼½¾'*args.width
        for i in range(args.height):
            blank = args.blank
            for r in [' ', '½']:
                data.append(str(i).rjust(4, ' ')+r)
                if args.checker is None:
                    data[-1] += args.blank*args.width*4
                elif i%2:
                    data[-1] += (args.blank*4 + args.checker*4)*(args.width//2)
                else:
                    data[-1] += (args.checker*4 + args.blank*4)*(args.width//2)
    else:
        data += [row]*args.height
    if args.output_file:
        with open(args.output_file, 'w') as fn:
            fn.write('\n'.join(data))
    else:
        print('\n'.join(data))


if __name__ == '__main__':
    main()
