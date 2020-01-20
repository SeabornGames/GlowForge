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

    diagram = Diagram(**vars(args))
    if not args.no_header:
        diagram.add_header()

    if args.output_file and args.output_file != '-':
        with open(args.output_file, 'w') as fn:
            fn.write(str(diagram))
    else:
        print(diagram)


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


class Diagram:
    def __init__(self, width, height, checker, ten_checker, blank, input_file,
                 **kwargs):
        self.layout = OrderedDict()
        self.names = OrderedDict()
        self.width = width
        self.height = height
        self.checker = checker
        self.ten_checker = ten_checker
        self.blank = blank
        if input_file:
            self.grid = self.parse_file(input_file)
            self.update()
        else:
            self.grid = self.create_grid()

    def create_grid(self):
        grid = []
        odd = even = ''
        for w in range(self.width):
            odd += (self.blank * 4) if w % 2 else (self.checker * 4)
            if w % 10 == 9:
                even += self.ten_checker * 4
            else:
                even += (self.checker * 4) if w % 2 else (self.blank * 4)
        for i in range(self.height):
            if i % 10 == 9:
                grid += [odd.replace(self.checker, self.ten_checker)] * 2
            else:
                grid += [odd, odd] if i % 2 else [even, even]
        return grid

    def parse_file(self, input_file):
        with open(input_file, 'r') as fn:
            grid = fn.read().split('\n')
        if grid[0].startswith('     000000'):  # then strip header:
            grid = [row[5:] for row in grid[3:]]
        if self.height is None:
            self.height = len(grid) // 2
        else:
            grid = grid[:self.height * 2]
        if self.width is None:
            self.width = max(*[len(g) for g in grid]) // 4
        else:
            grid = [g[:self.width * 4] for g in grid]

        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c in [self.blank, self.checker, self.ten_checker]:
                    pass
                elif c in Door.characters:
                    self.layout[x, y] = Door(c, x, y)
                elif c in Window.characters:
                    self.layout[x, y] = Window(c, x, y)
                elif c in Wall.characters:
                    self.layout[x, y] = Wall(c, x, y)
                elif c in Virtual.characters:
                    self.layout[x, y] = Virtual(c, x, y)
                elif c in RoomName.characters:
                    self.names[x, y] = RoomName(c, x, y)
                elif c in Name.characters:
                    self.names[x, y] = Name(c, x, y)
        return grid

    def update(self):
        for v in self.layout.values():
            v.clean(self)
        for k in list(self.names.keys()):
            v = self.names.get(k)
            if v is not None:  # names are popped out with other names
                v.clean(self)
        for v in self.layout.values():
            row = list(self.grid[v.y])
            row[v.x] = v.c
            self.grid[v.y] = ''.join(row)

    def add_header(self):
        header = [' ' * 5] * 3
        for w in range(self.width):
            header[0] += str(w // 10)[-1] + str(w // 10)[-1] + str(w // 10)[
                -1] + str(
                w // 10)[-1]
        for w in range(self.width):
            header[1] += str(w % 10) + str(w % 10) + str(w % 10) + str(w % 10)
        header[2] += ' ¼½¾' * self.width
        for i, row in enumerate(self.grid):
            self.grid[i] = str(i // 2).rjust(4, ' ') + [' ', '½'][i % 2] + \
                           self.grid[i]
        self.grid = header + self.grid

    def __str__(self):
        return '\n'.join(self.grid)


class Cell:
    def __init__(self, c, x, y):
        self.c = c
        self.x = x
        self.y = y

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__,
                                   self.c, self.x, self.y)

    def __str__(self):
        return self.c

    def clean(self, diagram):
        if (self.x, self.y + 1) in diagram.layout:
            if (self.x, self.y - 1) in diagram.layout:
                if (self.x - 1, self.y) in diagram.layout:
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = self.internal
                    else:  # not right
                        self.c = self.right_intersect
                else:  # not left
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = self.left_intersect
                    else:  # not right or left
                        self.c = self.vertical
            else:  # not below
                if (self.x - 1, self.y) in diagram.layout:
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = self.top_intersect
                    else:  # not right
                        self.c = getattr(self, 'top_right_corner', self.c)
                else:  # not left
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = getattr(self, 'top_left_corner', self.c)
                    else:  # not right
                        pass
        else:  # not above
            if (self.x, self.y - 1) in diagram.layout:
                if (self.x - 1, self.y) in diagram.layout:
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = self.bottom_intersect
                    else:  # not right
                        self.c = getattr(self, 'bottom_right_corner', self.c)
                else:  # not left
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = getattr(self, 'bottom_left_corner', self.c)
                    else:  # not right or left
                        pass
            else:  # not below
                if (self.x - 1, self.y) in diagram.layout:
                    if (self.x + 1, self.y) in diagram.layout:
                        self.c = self.horizontal
                    else:  # not right
                        pass
                else:  # not left
                    pass


class RoomName(Cell):
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]_-'
    horizontal_buffer = ' '
    vertical_buffer = ' '
    buffer_size = 2

    def clean(self, diagram):
        word = ''
        i = l = r = 0
        for i in range(100):
            _next = diagram.names.get((self.x + i, self.y), None)
            if isinstance(_next, RoomName):
                diagram.names.pop((self.x + i, self.y))
                word += _next.c
            elif (_next is None and (self.x + i, self.y) not in diagram.layout
                  and word[-1] != ' '):
                word += ' '
            else:
                break

        for r in range(self.x + i, min(diagram.width * 4, self.x + i + 400)):
            if diagram.layout.get((r, self.y), None):
                break
        for l in range(self.x, max(-1, self.x - 400), -1):
            if l and diagram.layout.get((l, self.y), None):
                break
        word = (self.vertical_buffer * self.buffer_size + word.strip() +
                self.vertical_buffer * self.buffer_size)
        _ljust = (r - l - len(word)) // 2 + 1
        indexes = [self.y]
        for r in range(1, self.buffer_size + 1):
            indexes += [self.y + r, self.y - r]
        for r in indexes:
            if 0 <= r < len(diagram.grid):
                row = diagram.grid[r]
                left_side = row[:l + _ljust]
                right_side = row[l + _ljust + len(word):]
                diagram.grid[r] = left_side + word + right_side
                word = self.horizontal_buffer * len(word)


class Name(RoomName):
    characters = 'abcdefghijklmnopqrstuvwxyz'


class Door(Cell):
    horizontal = '█'
    internal = '█'
    left_intersect = '█'
    right_intersect = '█'
    top_intersect = '█'
    bottom_intersect = '█'
    vertical = '█'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical + vertical)


class Virtual(Cell):
    horizontal = '┈'
    internal = '⟊'
    left_intersect = '╟'
    right_intersect = '╢'
    top_intersect = '╤'
    bottom_intersect = '╧'
    vertical = '┆'
    top_right_corner = '┐'
    top_left_corner = '┌'
    bottom_right_corner = '┘'
    bottom_left_corner = '└'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical +
                  top_right_corner + top_left_corner + bottom_left_corner +
                  bottom_right_corner)


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
