"""Test the NewLimitMin class."""

import unittest

from twentysolver.agent.newlimit import NewLimitMin, MaxFrame
from twentysolver.grid import Grid
from twentysolver.heuristic import estimate

class TestMaxFrame(unittest.TestCase):
    def test_init(self):
        grid = Grid.from_list([
            2, 2, 0, 0,
            0, 0, 0, 0,
            4, 0, 0, 0,
            8, 0, 0, 2,
            ])
        frame = MaxFrame(grid)
        self.assertEqual(frame.grid, grid)

    def test_expand(self):
        grid = Grid.from_list([
            2, 2, 0, 0,
            0, 0, 0, 0,
            4, 0, 0, 0,
            8, 0, 0, 2,
            ])
        frame = MaxFrame(grid)
        frame.expand()
        self.assertEqual(len(frame.queue), 4)
        self.assertGreaterEqual(estimate(frame[0].grid, frame.sort_weights),
                estimate(frame[-1].grid, frame.sort_weights))

    def test_alphabeta(self):
        frame = MaxFrame(None, alpha=1, beta=2)
        frame.update((1.5, None))
        self.assertFalse(frame.alphabeta())
        self.assertEqual(frame.alpha, 1.5)
        frame.update((2.5, None))
        self.assertTrue(frame.alphabeta())


class TestNewLimitMin(unittest.TestCase):
    pass
