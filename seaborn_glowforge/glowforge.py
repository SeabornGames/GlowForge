import os
import sys
from argparse import ArgumentParser
from shutil import copyfile
from seaborn_table import SeabornTable
from seaborn_glowforge.diagram import (Cell, RoomName, Name, Door, Virtual,
                                       Window, Wall, Diagram)


def main(cli_args=sys.argv[1:]):
    args = parse_args(cli_args)
    if args.backup_file and args.backup_file != '-':
        if os.path.exists(args.output_file):
            copyfile(args.output_file, args.backup_file)

    diagram = Diagram(**vars(args))
    diagram.remove_objects()

    glowforge = Glowforge(diagram, args.default_height, args.floor)
    glowforge.update_wall_file(args.wall_file)
    glowforge.save(args.wall_file)


def parse_args(cli_args):
    parser = ArgumentParser(description='The seaborn_glowforge.glowforge will'
                                        ' create the walls for glowforge.')
    parser.add_argument('--wall-file', default='wall_height.csv',
                        help='table file from seaborn_table defining the wall'
                             ' dimensions, which will be created if it does not'
                             ' exist. Defaults to the input file plus wall.md')
    parser.add_argument('--floor', default='1',
                        help='Used to specify the floor within the'
                             ' wall-file')
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
                        help='Path to the diagram input file.')
    parser.add_argument('--output-file', '-o', default=None,
                        help='Path to the output glowforge file (default to the'
                             ' input file joined with ``walls``.')
    parser.add_argument('--filter-room', '-r',
                        help='If specified it will only output a given room')
    parser.add_argument('--exclude-room', nargs='+',
                        help='If specified will exclude these rooms')
    args = parser.parse_args(cli_args)
    if args.input_file and args.output_file is None:
        args.output_file = '_walls'.join(args.input_file.split('.'))
    if args.output_file and args.backup_file is None:
        args.backup_file = f"{args.output_file.rsplit('.', 1)[0]}.bck"
    return args


class Glowforge:
    def __init__(self, diagram, default_height, floor):
        self.diagram = diagram
        self.default_height = default_height
        self.floor = floor
        diagram.grid = diagram.create_grid()
        diagram.add_layout_to_grid()
        grid = '\n'.join(diagram.grid)
        self.horizontal = self.extract_horizontal_walls(grid)
        self.vertical = self.extract_vertical_walls(grid)

    def extract_horizontal_walls(self, grid):
        for v in [Wall.vertical, Window.vertical] + Virtual.characters:
            grid = grid.replace(v, ' ')
        walls = []
        grid = grid.split('\n')
        for y in range(len(grid)):
            print('row: %s'%grid[y])
            symbols = ''
            for x in range(len(grid[y])):
                cell = grid[y][x]
                if cell:
                    symbols += cell
                if cell == ' ' or x == len(grid[y]):
                    if symbols:
                        wall = dict(x=x - len(symbols),
                                    y=y,
                                    symbols=symbols,
                                    horizontal=True,
                                    height1=self.default_height,
                                    height2=self.default_height)
                        rooms = self.extract_rooms(
                            x - len(symbols), x, y, y + 1)
                        for i, room in enumerate(rooms):
                            wall[f'room_{i}'] = room
                        print('symbols: %s'%symbols)
                        walls.append(wall)
                    symbols = ''
        return walls

    def extract_vertical_walls(self, grid):
        for h in [Wall.horizontal, Window.horizontal] + Virtual.characters:
            grid = grid.replace(h, ' ')

        walls = []
        grid = grid.split('\n')
        for x in range(len(grid[0])):
            symbols = ''
            for y in range(len(grid)):
                cell = grid[y][x]
                if cell:
                    symbols += cell
                if cell == ' ' or x == len(grid[y]):
                    if symbols:
                        wall = dict(x=x,
                                    y=y - len(symbols),
                                    symbols=symbols.strip(),
                                    horizontal=False,
                                    height1=self.default_height,
                                    height2=self.default_height)
                        rooms = self.extract_rooms(
                            x, x+1, y-len(symbols), y)
                        for i, room in enumerate(rooms):
                            wall[f'room_{i}'] = room
                        walls.append(wall)
                    symbols = ''
        return walls

    def extract_rooms(self, x_start, x_end, y_start, y_end):
        def room_found(room):
            for x in range(x_start, x_end):
                for y in range(y_start, y_end):
                    if (x, y) in room.walls:
                        return True
            return False
        return [room for room in self.diagram.rooms if room_found(room)]

    def update_wall_file(self, file):
        if not os.path.exists(file):
            return
        table = SeabornTable.file_to_obj(
            file, columns=['floor', 'horizontal', 'status', 'height1',
                           'height2', 'room_0', 'room_1', 'room_2', 'room_3',
                           'x', 'y', 'symbols'])
        for row in table:
            if row['floor'] == self.floor:
                row['status'] = 'missing'

        def update_wall_from_table(wall):
            for row in table:
                if (wall['horizontal'] == row['horizontal'] and
                            wall['room_0'] == row['room_0']):
                    wall['height1'] = row['height1']
                    wall['height2'] = row['height2']
                    row['status'] = 'used'
                    return True
            return False

        for wall in self.horizontal + self.vertical:
            if not update_wall_from_table(wall):
                table.append(dict(
                    height1=self.default_height,
                    height2=self.default_height,
                    floor=self.floor,
                    status='new',
                    **wall))
        table.save()

    def save(self, file):
        SeabornTable.list_to_obj(self.horizontal+self.vertical
                                 ).obj_to_file(file)


if __name__ == '__main__':
    main()
