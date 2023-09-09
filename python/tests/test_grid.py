"""Test the Grid class."""

import unittest

from twentysolver.grid import Grid

DIRECTIONS = [RIGHT, DOWN, LEFT, UP] = range(4)

class TestGrid(unittest.TestCase):
    def test_move_right(self):
        grid = Grid.from_list([
            2, 2, 0, 0,
            0, 0, 0, 0,
            4, 0, 0, 0,
            8, 0, 0, 2,
            ])
        self.assertEqual([
            0, 0, 0, 4,
            0, 0, 0, 0,
            0, 0, 0, 4,
            0, 0, 8, 2,
                    ],
                    grid.move(RIGHT).as_list())

    def test_move_down(self):
        grid = Grid.from_list([
            0, 4, 8, 0,
            2, 0, 2, 2,
            0, 4, 0, 0,
            8, 2, 2, 0])
        self.assertEqual([
            0, 0, 0, 0,
            0, 0, 0, 0,
            2, 8, 8, 0,
            8, 2, 4, 2,
            ],
            grid.move(DOWN).as_list())

