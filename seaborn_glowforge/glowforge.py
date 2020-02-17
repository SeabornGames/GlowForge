import os
import sys
from argparse import ArgumentParser
from seaborn_table import SeabornTable
from seaborn_glowforge.diagram import (Cell, RoomName, ObjectName, DoorCell,
                                       VirtualCell, WindowCell, WallCell, Diagram)


def main(cli_args=sys.argv[1:]):
    args = parse_args(cli_args)
    glowforge = Glowforge(wall_file=args.wall_file, floor=args.floor)

    if args.input_file:
        diagram = Diagram(**vars(args))
        diagram.remove_objects()
        glowforge.update_wall_file(args.default_wall_height, diagram)

    if args.wall_diagram_file:
        glowforge.save_wall_diagram_file(args.wall_diagram_file)
    if args.output_file:
        glowforge.save_glowforge_file(args.output_file)


def parse_args(cli_args):
    parser = ArgumentParser(description='The seaborn_glowforge.glowforge will'
                                        ' create the walls for glowforge.')
    parser.add_argument('--wall-file', default='wall_height.md',
                        help='table file from seaborn_table defining the wall'
                             ' dimensions, which will be created if it does not'
                             ' exist. Defaults to the input file plus wall.md')
    parser.add_argument('--floor', default='1',
                        help='Used to specify the floor within the'
                             ' wall-file')
    parser.add_argument('--wall-diagram-file',
                        help='outputs a diagram file from only walls for'
                             ' debugging the --wall-file')
    parser.add_argument('--default-wall-height', type=float, default=10.0,
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
    parser.add_argument('--input-file', '-i', default=None,
                        help='Path to the diagram file which if specified will'
                             ' be used to update the --wall-file.')
    parser.add_argument('--output-file', '-o', default=None,
                        help='Path to the output glowforge file, if not'
                             ' specified it will skip making the wall file'
                             ' and only update the wall height file.')
    parser.add_argument('--filter-room', '-r', nargs='+',
                        help='If specified it will only output the given rooms')
    parser.add_argument('--exclude-room', nargs='+',
                        help='If specified will exclude these rooms')
    args = parser.parse_args(cli_args)
    return args


class Glowforge:
    WALL_FILE_COLUMNS = ['floor', 'horizontal', 'status', 'height1',
                         'height2', 'room_0', 'room_1', 'room_2', 'room_3',
                         'x', 'y', 'symbols']

    def __init__(self, wall_file, floor):
        self.floor = floor
        self.wall_file = wall_file
        if os.path.exists(wall_file):
            self.wall_table = SeabornTable.file_to_obj(
                wall_file, columns=self.WALL_FILE_COLUMNS)
        else:
            self.wall_table = SeabornTable(columns=self.WALL_FILE_COLUMNS)

    def update_wall_file(self, default_wall_height, diagram):
        diagram.grid = diagram.create_grid()
        diagram.add_layout_to_grid()
        grid = '\n'.join(diagram.grid)
        for room in diagram.rooms:
            room.calc_room_dimensions(diagram.layout, diagram.width*4,
                                      diagram.height*2)
        horizontal = self.extract_horizontal_walls(grid, diagram.rooms)
        vertical = self.extract_vertical_walls(grid, diagram.rooms)

        for row in self.wall_table:
            if row['floor'] == self.floor:
                row['status'] = 'missing'

        def update_wall(wall):
            for row in self.wall_table:
                if (row['status'] == 'missing' and
                        wall['horizontal'] == row.get('horizontal') and
                        wall.get('room_0') == row.get('room_0') and
                        wall.get('room_1') == row.get('room_1') and
                        wall.get('room_2') == row.get('room_2') and
                        wall.get('room_3') == row.get('room_3')):
                    row.update(wall)
                    row['status'] = 'used'
                    return True
            return False

        for wall in horizontal + vertical:
            if not update_wall(wall):
                self.wall_table.append(dict(
                    height1=default_wall_height,
                    height2=default_wall_height,
                    floor=self.floor,
                    status='new',
                    **wall))
        self.wall_table.obj_to_file(self.wall_file, align='left',
                                    quote_numbers=False)

    def extract_horizontal_walls(self, grid, rooms):
        for v in [WallCell.vertical, WindowCell.vertical] + list(VirtualCell.characters):
            grid = grid.replace(v, ' ')
        walls = []
        grid = grid.split('\n')
        for y in range(len(grid)):
            symbols = ''
            for x in range(len(grid[y])):
                cell = grid[y][x]
                if cell != ' ':
                    symbols += cell
                if cell == ' ' or x == len(grid[y]):
                    if len(symbols) > 1:
                        wall = dict(x=x - len(symbols),
                                    y=y,
                                    symbols=symbols,
                                    horizontal=True)
                        wall_rooms = self.extract_rooms(
                            x - len(symbols), x, y, y + 1, rooms)
                        if not wall_rooms:
                            print("WARNING: failed to find room for horizontal"
                                  " wall from x: %s to %s and y: %s"%
                                  (x - len(symbols), x, y))
                            sys.exit(1)
                        for i, room in enumerate(wall_rooms):
                            wall[f'room_{i}'] = room
                        walls.append(wall)
                    symbols = ''
        return walls

    def extract_vertical_walls(self, grid, rooms):
        for h in [WallCell.horizontal,
                  WindowCell.horizontal] + list(VirtualCell.characters):
            grid = grid.replace(h, ' ')

        walls = []
        grid = grid.split('\n')
        for x in range(len(grid[0])):
            symbols = ''
            for y in range(len(grid)):
                cell = grid[y][x]
                if cell != ' ':
                    symbols += cell
                if cell == ' ' or x == len(grid[y]):
                    if symbols:
                        wall = dict(x=x,
                                    y=y - len(symbols),
                                    symbols=symbols.strip(),
                                    horizontal=False)
                        wall_rooms = self.extract_rooms(
                            x, x+1, y-len(symbols), y, rooms)
                        for i, room in enumerate(wall_rooms):
                            wall[f'room_{i}'] = room
                        walls.append(wall)
                    symbols = ''
        return walls

    @staticmethod
    def extract_rooms(x_start, x_end, y_start, y_end, rooms):
        def room_found(room):
            if not room.walls:
                return False
            for x in range(x_start, x_end):
                for y in range(y_start, y_end):
                    if (x, y) in room.walls:
                        return True
            return False
        return [room for room in rooms if room_found(room)]

    def save_glowforge_file(self, filename):
        raise NotImplemented()

    def save_wall_diagram_file(self, filename):
        walls = [wall for wall in self.wall_table if wall.status != 'missing']
        width = max([wall.x + len(wall.symbols) for wall in walls
                     if wall.horizontal])
        height = max([wall.y + len(wall.symbols) for wall in walls
                     if not wall.horizontal])
        grid = [[' ' for w in width] for h in height]
        for wall in self.wall_table:
            if wall.horizontal:
                for i, s in enumerate(wall.symbols):
                    grid[wall.y][wall.x+i] = s
            else:
                for i, s in enumerate(wall.symbols):
                    grid[wall.y+i][wall.x] = s
        with open(filename, 'w') as fn:
            fn.write('\n'.join([''.join(row) for row in grid]))


if __name__ == '__main__':
    main()
