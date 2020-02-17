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

    if args.remove_objects:
        diagram.remove_objects()

    if args.input_file:
        for highlight in (args.highlight_room or []):
            for room in diagram.rooms + diagram.objects:
                if room.name == highlight:
                    room.highlight(diagram)
        if not args.remove_names:
            diagram.add_names_to_grid()
        diagram.add_layout_to_grid()

    if args.ruler:
        diagram.add_ruler()

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
    parser.add_argument('--ruler',
                        action='store_true', default=False,
                        help='puts a header of a ruler values in the file')
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
    parser.add_argument('--highlight-room', default=None, nargs='+',
                        help='Highlights a room with this name to test room'
                             ' dimensions for debugging')
    parser.add_argument('--remove-objects', default=None, action='store_true',
                        help='Remove objects and boundaries for debugging')
    parser.add_argument('--remove-names', default=None, action='store_true',
                        help='Remove names from rooms')
    args = parser.parse_args(cli_args)
    if args.input_file and args.output_file is None:
        args.output_file = args.input_file
    if args.output_file and args.backup_file is None:
        args.backup_file = f"{args.output_file.rsplit('.', 1)[0]}.bck"
    if args.input_file is None:
        if args.height is None:
            args.height = 400
        if args.width is None:
            args.width = 200
    return args


class Diagram:
    def __init__(self, checker, ten_checker, blank, input_file,
                 width=None, height=None, **kwargs):
        self.layout = OrderedDict()
        self.name_characters = OrderedDict()
        self.rooms = []
        self.objects = []
        self.width = width
        self.height = height
        self.checker = checker
        self.ten_checker = ten_checker
        self.blank = blank
        if input_file:
            self.parse_file(input_file)
        self.grid = self.create_grid(blank, checker, ten_checker)

    def create_grid(self, blank=" ", checker=" ", ten_checker=" "):
        grid = []
        odd = even = ''
        for w in range(self.width):
            odd += (self.blank * 4) if w % 2 else (checker * 4)
            if w % 10 == 9:
                even += ten_checker * 4
            else:
                even += (checker * 4) if w % 2 else (blank * 4)
        for i in range(self.height):
            if i % 10 == 9:
                grid += [odd.replace(checker, ten_checker)] * 2
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
                elif c in DoorCell.characters:
                    self.layout[x, y] = DoorCell(c, x, y)
                elif c in VirtualCell.characters:
                    self.layout[x, y] = VirtualCell(c, x, y)
                elif c in WindowCell.characters:
                    self.layout[x, y] = WindowCell(c, x, y)
                elif c in WallCell.characters:
                    self.layout[x, y] = WallCell(c, x, y)
                elif c in RoomName.characters:
                    self.name_characters[x, y] = RoomName(c, x, y)
                elif c in ObjectName.characters:
                    self.name_characters[x, y] = ObjectName(c, x, y)

        for v in self.layout.values():
            v.clean(diagram=self)
        for k in list(self.name_characters.keys()):
            v = self.name_characters.get(k)
            if v is not None:  # character was popped out with other names
                v.clean(diagram=self)

    def remove_objects(self):
        self.layout = self.create_room_only_layout()
        self.objects.clear()
        for v in self.layout.values():
            v.clean(self)

    def create_room_only_layout(self):
        room_layout = OrderedDict()
        removed_walls = []
        for object in self.objects:
            if not object.walls:
                object.calc_room_dimensions(self.layout, self.width * 4,
                                            self.height * 2)
            for location in object.walls:
                wall = self.layout.get(location)
                if isinstance(wall, VirtualCell) and wall not in removed_walls:
                    removed_walls.append(wall)
        for k, v in self.layout.items():
            if v not in removed_walls:
                room_layout[k] = v
        return room_layout

    def add_names_to_grid(self):
        for room in self.rooms:
            room.add_name_to_grid(diagram=self)
        for object in self.objects:
            object.add_name_to_grid(diagram=self)

    def add_layout_to_grid(self):
        for v in self.layout.values():
            row = self.grid[v.y]
            self.grid[v.y] = row[:v.x] + v.c + row[v.x + 1:]

    def add_ruler(self):
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

    def combine_characters_to_a_name(self, diagram):
        # This will remove this character and other name characters from
        # diagram.names
        name = ''
        for i in range(100):
            _next = diagram.name_characters.get((self.x + i, self.y), None)
            if isinstance(_next, RoomName):
                diagram.name_characters.pop((self.x + i, self.y))
                name += _next.c
            elif (_next is None and (self.x + i, self.y) not in diagram.layout
                  and name[-1] != ' '):
                name += ' '
            else:
                break
        return name.strip()

    def clean(self, diagram):
        name = self.combine_characters_to_a_name(diagram)
        diagram.rooms.append(Room(name, self.x, self.y))


class ObjectName(RoomName):
    characters = 'abcdefghijklmnopqrstuvwxyz'

    def clean(self, diagram):
        name = self.combine_characters_to_a_name(diagram)
        diagram.objects.append(Object(name, self.x, self.y))


class DoorCell(Cell):
    horizontal = '▤'
    internal = '█'
    left_intersect = '█'
    right_intersect = '█'
    top_intersect = '█'
    bottom_intersect = '█'
    vertical = '╫'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical + vertical)


class VirtualCell(Cell):
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


class WindowCell(Cell):
    horizontal = '─'
    internal = '┼'
    left_intersect = '╟'
    right_intersect = '╢'
    top_intersect = '╤'
    bottom_intersect = '╧'
    vertical = '│'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical)


class WallCell(Cell):
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


class ObjectCell(Cell):
    horizontal = '━'
    internal = '╋'
    top_left_corner = '┏'
    top_intersect = '┳'
    top_right_corner = '┓'
    bottom_left_corner = '┗'
    bottom_intersect = '┻'
    bottom_right_corner = '┛'
    left_intersect = '┣'
    vertical = '┃'
    right_intersect = '┫'
    characters = (horizontal + internal + left_intersect + right_intersect +
                  top_intersect + bottom_intersect + vertical +
                  top_left_corner + top_right_corner + bottom_left_corner +
                  bottom_right_corner)


class Room:
    horizontal_buffer = ' '
    vertical_buffer = ' '
    buffer_size = 2

    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.cells = []
        self.walls = []

    def __repr__(self):
        return 'Room<%s, %s, %s>'%(self.name, self.x, self.y)

    def __str__(self):
        return self.name

    def calc_room_dimensions(self, layout, max_x, max_y):
        self.cells = []
        self.walls = []
        self.cells.append((self.x, self.y))
        i = 0
        while i < len(self.cells):
            x, y = self.cells[i]
            for neighbor in [(x-1, y), (x+1, y), (x, y-1), (x, y + 1),
                             (x-1, y-1),(x+1, y+1), (x+1, y-1), (x-1, y+1)]:
                if not (0 <= neighbor[0] < max_x):
                    continue
                if not (0 <= neighbor[1] < max_y):
                    continue
                if neighbor in self.cells or neighbor in self.walls:
                    continue
                cell = layout.get(neighbor)
                if cell is None:
                    self.cells.append(neighbor)
                else:
                    self.walls.append(neighbor)
            i += 1

    def highlight(self, diagram, color='░'):
        if not self.cells:
            self.calc_room_dimensions(diagram.layout, diagram.width * 4,
                                      diagram.height * 2)

        for x, y in self.cells:
            if diagram.grid[y][x] == ' ':
                row = diagram.grid[y]
                diagram.grid[y] = row[:x] + color + row[x + 1:]

    def add_name_to_grid(self, diagram):
        i = len(self.name)
        l = r = 0
        for r in range(self.x + i, min(diagram.width * 4, self.x + i + 400)):
            if diagram.layout.get((r, self.y), None):
                break
        for l in range(self.x, max(-1, self.x - 400), -1):
            if l and diagram.layout.get((l, self.y), None):
                break
        name = (self.vertical_buffer * self.buffer_size + self.name.strip() +
                self.vertical_buffer * self.buffer_size)
        _ljust = (r - l - len(name)) // 2 + 1
        indexes = [self.y]
        for r in range(1, self.buffer_size + 1):
            if (self.x, self.y + r) in self.cells:
                indexes.append(self.y + r)
            if (self.x, self.y - r) in self.cells:
                indexes.append(self.y - r)
        for r in indexes:
            if 0 <= r < len(diagram.grid):
                row = diagram.grid[r]
                left_side = row[:l + _ljust]
                right_side = row[l + _ljust + len(name):]
                diagram.grid[r] = left_side + name + right_side
                name = self.horizontal_buffer * len(name)


class Object(Room):
    pass


if __name__ == '__main__':
    main()
