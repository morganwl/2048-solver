"""Game grid."""

import numpy as np

DIRECTIONS = [RIGHT, DOWN, LEFT, UP] = range(4)
TILE_TYPE=np.uint16

class Grid:
    def __init__(self, tiles=None):
        if tiles is None:
            tiles = np.zeros(16, dtype=TILE_TYPE)
        self.tiles = tiles

    def get_cell_value(self, x, y):
        return self.tiles[x + 4*y]

    def get_max_tile(self):
        return max(t for t in self.tiles)

    def get_available_cells(self):
        return [(x,y) for x in range(4) for y in range(4) if self.tiles[x+4*y] == 0]

    def get_available_moves(self):
        grids = (self.move(d) for d in DIRECTIONS)
        return [(move, grid) for move, grid in zip(DIRECTIONS, grids) if grid != self]

    def validate_move(self, move):
        if move not in DIRECTIONS:
            raise Exception('Unrecognized move ' + str(move))
        grid = self.move(move)
        if grid == self:
            raise Exception('Invalid move ' + str(move))
        return grid

    def insert_tile(self, pos, tile):
        assert(self.tiles[pos[0] + pos[1]*4] == 0)
        tiles = np.array(self.tiles, dtype=TILE_TYPE)
        tiles[pos[0] + pos[1]*4] = tile
        return Grid(tiles)

    def move(self, direction):
        moved_rows = (move_row(row) for row in rol_row[direction](self.tiles))
        return type(self)(ror_rows[direction](moved_rows))

    def as_list(self):
        return self.tiles.tolist()

    def __getitem__(self, i):
        try:
            x,y = i
        except:
            return self.tiles[i]
        else:
            return self.tiles[x + 4*y]

    def __eq__(self, other):
        return (self.tiles == other.tiles).all()

    def __repr__(self):
        return f'Grid({self.tiles!r})'


    @classmethod
    def from_list(cls, tiles):
        return Grid(np.array(tiles, dtype=TILE_TYPE))


def rol_row_0(tiles):
    for i in range(0, 16, 4):
        yield np.array(tiles[i:i+4])

def rol_row_1(tiles):
    for i in reversed(range(0, 4)):
        yield tiles[[i, i+4, i+8, i+12]]

def rol_row_2(tiles):
    for i in reversed(range(0, 16, 4)):
        yield tiles[[i+3, i+2, i+1, i]]

def rol_row_3(tiles):
    for i in range(0, 4):
        yield tiles[[i+12, i+8, i+4, i]]

def ror_rows_0(rows):
    return np.concatenate([r for r in rows])

def ror_rows_1(rows):
    moved = np.concatenate([r for r in rows])
    return np.concatenate([moved[[i+12, i+8, i+4, i]] for i in range(4)])

def ror_rows_2(rows):
    moved = np.concatenate([r for r in rows])
    return np.concatenate([moved[[i+3, i+2, i+1, i]] for i in reversed(range(0, 16, 4))])

def ror_rows_3(rows):
    moved = np.concatenate([r for r in rows])
    return np.concatenate([moved[[i, i+4, i+8, i+12]] for i in reversed(range(4))])

rol_row = [rol_row_0, rol_row_1, rol_row_2, rol_row_3]
ror_rows = [ror_rows_0, ror_rows_1, ror_rows_2, ror_rows_3]

def move_row(row):
    target = 3
    source = 2
    val = row[target]
    while source >= 0:
        if row[source]:
            if val == 0:
                row[target] = row[source]
                val = row[source]
                row[source] = 0
            elif val == row[source]:
                row[target] = val << 1
                row[source] = 0
                target -= 1
                val = row[target]
            elif target - source > 1:
                source += 1
                target -= 1
                val = row[target]
            else:
                target -= 1
                val = row[target]
        source -= 1
    return row

if __name__ == '__main__':
    import csv
    import timeit

    setup = """
import csv
from __main__ import Grid

def test_grids():
    grids = []
    with open('../ai/assignments/assignment2/HW2_Q1_WajdaLevie_Morgan/results/search_player_results.csv', newline='') as fh:
        reader = csv.reader(fh)
        next(reader)
        for _ in range(500):
            row = next(reader)
            grids.append(Grid.from_list(eval(row[0])))
    while True:
        for grid in grids:
            yield grid

def test_moves():
    while True:
        for i in range(4):
            yield i

grids, moves = test_grids(), test_moves()
    """


    print(
            timeit.timeit('next(grids).move(next(moves))', setup), 'ms'
            )

