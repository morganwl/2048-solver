"""Test the CacheTree agent."""

import unittest

from twentysolver.agent.cachetree import CacheTree, MaxFrame,\
        MinFrame, ExpectFrame, GridNode

class TestMaxFrame(unittest.TestCase):
    def test_gt(self):
        frame = MaxFrame(GridNode(None, value=3))
        assert frame._grid is not None
        self.assertTrue(frame > 2)
        self.assertFalse(frame > 4)

    def test_update(self):
        frame = MaxFrame(None)
        child1, child2, child3 = (MinFrame(GridNode(None, value=2)),
            MinFrame(GridNode(None, value=3)), 
            MinFrame(GridNode(None, value=1)))
        frame.update(child1)
        self.assertEqual(frame.best_node, child1._grid)
        frame.update(child2)
        self.assertEqual(frame.best_node, child2._grid)
        frame.update(child3)
        self.assertEqual(frame.best_node, child2._grid)
