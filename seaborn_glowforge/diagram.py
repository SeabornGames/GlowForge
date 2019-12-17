import os
import sys
from argparse import ArgumentParser
from shutil import copyfile
from collections import OrderedDict


def main(cli_args=sys.argv[1:]):
    args = parse_args(cli_args)
    if args.backup_file and args.backup_file != '-':
        if os.path.exists(args.output_file):
            copyfile(args.output_file, args.backup_file)
    if args.input_file and os.path.exists(args.input_file):
        args = Cell.parse_file(args)
    grid = create_diagram(args)
    Cell.update(grid)

    if not args.no_header:
        grid = add_header(grid)

    if args.output_file and args.output_file != '-':
        with open(args.output_file, 'w') as fn:
            fn.write('\n'.join(grid))
    else:
        print('\n'.join(grid))


def create_diagram(args):
    grid = []
    odd = even = ''
    for w in range(args.width):
        odd += (args.blank * 4) if w % 2 else (args.checker * 4)
        if w%10 == 9:
            even += args.ten_checker * 4
        else:
            even += (args.checker * 4) if w % 2 else (args.blank * 4)
    for i in range(args.height):
        if i % 10 == 9:
            grid += [odd.replace(args.checker, args.ten_checker)]*2
        else:
            grid += [odd, odd] if i % 2 else [even, even]
    return grid


def add_header(grid):
    width = len(grid[0]) // 4
    header = [' ' * 5] * 3
    for w in range(width):
        header[0] += str(w // 10) + str(w // 10) + str(w // 10) + str(w // 10)
    for w in range(width):
        header[1] += str(w % 10) + str(w % 10) + str(w % 10) + str(w % 10)
    header[2] += ' ¼½¾' * width
    for i, row in enumerate(grid):
        grid[i] = str(i // 2).rjust(4, ' ') + [' ', '½'][i % 2] + grid[i]
    return header + grid


def parse_args(cli_args):
    parser = ArgumentParser(description='The seaborn_glowforge.diagram will'
                                        ' create a layout file or clean an'
                                        ' existing one.')
    parser.add_argument('--width', type=int, default=None,
                        help='number of feet per row in the file.')
    parser.add_argument('--height', type=int, default=None,
                        help='number of feet of rows in the file.')
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
    if args.input_file is None:
        if args.height is None:
            args.height = 100
        if args.width is None:
            args.width = 100
    return args


class Cell:
    GRID = OrderedDict()
    SPECIALS = OrderedDict()

    def __init__(self, c, x, y):
        self.c = c
        self.x = x
        self.y = y

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__,
                                   self.c, self.x, self.y)

    @classmethod
    def parse_file(cls, args):
        with open(args.input_file, 'r') as fn:
            grid = fn.read().split('\n')
        if grid[0].startswith('     000000'):  # then strip header:
            grid = [row[5:] for row in grid[3:]]
        if args.height is None:
            args.height = len(grid) // 2
        else:
            grid = grid[:args.height * 2]
        if args.width is None:
            args.width = len(grid[0]) // 4
        else:
            grid = [g[:args.width * 4] for g in grid]

        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c in [args.blank, args.checker, args.ten_checker]:
                    pass
                elif c in Door.characters:
                    cls.GRID[x, y] = Door(c, x, y)
                elif c in Window.characters:
                    cls.GRID[x, y] = Window(c, x, y)
                elif c in Wall.characters:
                    cls.GRID[x, y] = Wall(c, x, y)
                elif c in Special.characters:
                    cls.SPECIALS[x, y] = Special(c, x, y)
        return args

    @classmethod
    def update(cls, grid):
        for v in cls.GRID.values():
            v.clean()
        for k in list(cls.SPECIALS.keys()):
            v = cls.SPECIALS.get(k)
            if v is not None:  # specials are popped out with other specials
                v.clean(grid)
        for v in cls.GRID.values():
            row = list(grid[v.y])
            row[v.x] = v.c
            grid[v.y] = ''.join(row)

    def clean(self):
        if (self.x, self.y + 1) in self.GRID:
            if (self.x, self.y - 1) in self.GRID:
                if (self.x - 1, self.y) in self.GRID:
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = self.internal
                    else:  # not right
                        self.c = self.right_intersect
                else:  # not left
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = self.left_intersect
                    else:  # not right or left
                        self.c = self.vertical
            else:  # not below
                if (self.x - 1, self.y) in self.GRID:
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = self.top_intersect
                    else:  # not right
                        self.c = getattr(self, 'top_right_corner', self.c)
                else:  # not left
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = getattr(self, 'top_left_corner', self.c)
                    else:  # not right
                        pass
        else:  # not above
            if (self.x, self.y - 1) in self.GRID:
                if (self.x - 1, self.y) in self.GRID:
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = self.bottom_intersect
                    else:  # not right
                        self.c = getattr(self, 'bottom_right_corner', self.c)
                else:  # not left
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = getattr(self, 'bottom_left_corner', self.c)
                    else:  # not right or left
                        pass
            else:  # not below
                if (self.x - 1, self.y) in self.GRID:
                    if (self.x + 1, self.y) in self.GRID:
                        self.c = self.horizontal
                    else:  # not right
                        pass
                else:  # not left
                    pass


class Special(Cell):
    abc = 'abcdefghijklmnopqrstuvwxyz'
    characters = abc + abc.upper() + '0123456789[]_-'
    horizontal_buffer = ' '
    verticle_buffer = ' '
    buffer_size = 2

    def clean(self, grid):
        word = ''
        i = l = r = 0
        for i in range(100):
            _next = self.SPECIALS.get((self.x + i, self.y), None)
            if isinstance(_next, Special):
                self.SPECIALS.pop((self.x + i, self.y))
                word += _next.c
            elif (_next is None and
                    (self.x + i, self.y) not in self.GRID and word[-1] != ' '):
                word += ' '
            else:
                break
        for r in range(self.x + i, min(len(grid[0]), self.x + i + 400)):
            if self.GRID.get((r, self.y), None):
                break
        for l in range(self.x, max(-1, self.x - 400), -1):
            if l and self.GRID.get((l, self.y), None):
                break
        word = (self.verticle_buffer * self.buffer_size + word.strip() +
                self.verticle_buffer * self.buffer_size)
        ljust = (r - l - len(word)) // 2
        indexes = [self.y]
        for r in range(1, self.buffer_size + 1):
            indexes += [self.y+r, self.y-r]
        for r in indexes:
            if 0 <= r < len(grid):
                row = grid[r]
                grid[r] = row[:l + ljust] + word + row[l+ljust+len(word):]
                word = self.horizontal_buffer * len(word)


class Door(Cell):
    horizontal = '⏺'
    internal = '⏭'
    left_intersect = '⏩'
    right_intersect = '⏪'
    top_intersect = '⏬'
    bottom_intersect = '⏫'
    vertical = '⏹'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical + vertical)


class Virtual(Cell):
    horizontal = '┈'
    internal = '⟊'
    left_intersect = '╟'
    right_intersect = '╢'
    top_intersect = '╤'
    bottom_intersect = '⟂'
    vertical = '┆'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical)


class Window(Cell):
    horizontal = '─'
    internal = '┼'
    left_intersect = '╟'
    right_intersect = '╢'
    top_intersect = '╤'
    bottom_intersect = '╧'
    vertical = '│'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical)


class Wall(Cell):
    horizontal = '═'
    internal = '╬'
    top_left_corner = '╔'
    top_intersect = '╦'
    top_right_corner = '╗'
    bottom_left_corner = '╚'
    bottom_intersect = '╩'
    bottom_right_corner = '╝'
    left_intersect = '╠'
    vertical = '║'
    right_intersect = '╣'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical +
                  top_left_corner + top_right_corner + bottom_left_corner +
                  bottom_right_corner)


if __name__ == '__main__':
    main()
