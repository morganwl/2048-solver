"""Test the SearchTest object."""

from enum import Enum, auto
import json

import unittest

class MoveType(Enum):
    """Three types of moves can be made, one by the player, one by the
    opponent, and one as a result of chance."""
    PLAYER = auto()
    OPPONENT = auto()
    CHANCE = auto()

class TestSearchTest(unittest.testcase):
    """SearchTest should generate a complete search tree to a specified
    depth and save the output as json."""
    def assert_valid(self, move_type, starting_grid, possible_moves):
        """Asserts that all (move,grid) pairs are valid, meaning that
        the move is possible from starting_grid, and the resulting grid
        is the correct outcome."""
        match move_type:
            case MoveType.PLAYER:
                return self.assert_valid_player(starting_grid, possible_moves)
            case MoveType.OPPONENT:
                return self.assert_valid_opponent(starting_grid, possible_moves)
            case MoveType.CHANCE:
                return self.assert_valid_chance(starting_grid, possible_moves)

    def assert_valid_player(self, starting_grid, possible_moves):
        """Asserts that all player (move,grid) pairs are valid."""
        for move, grid in possible_moves:
            with self.subtest(move=move):
                result = starting_grid.validate_move(move)
                self.assertEqual(grid, result)

    def assert_valid_opponent(self, starting_grid, possible_moves):
        """Asserts that all opponent (move,grid) pairs are valid."""
        for cell, grid in possible_moves:
            with self.subtest(cell=cell):
                self.assertEqual(starting_grid.get_cell_value(*cell), 0)
                self.assertEqual(grid, starting_grid)

    def assert_valid_chance(self, starting_grid, possible_moves):
        """Asserts that all chance (move,grid) pairs are valid."""
        for (cell, value), grid in possible_moves:
            with self.subtest(value=value):
                self.assertTrue(value in {2,4})
                self.assertEqual(grid, starting_grid.insert_tile(cell, value))

    def assert_complete(self, move_type, starting_grid, possible_moves):
        """Asserts that a list of (move,grid) pairs contains all
        possible moves from a given grid."""
        match move_type:
            case MoveType.PLAYER:
                return self.assert_complete_player(starting_grid, possible_moves)
            case MoveType.OPPONENT:
                return self.assert_complete_opponent(starting_grid, possible_moves)
            case MoveType.CHANCE:
                return self.assert_complete_chance(starting_grid, possible_moves)

    def assert_complete_player(self, starting_grid, possible_moves):
        """Asserts that all expected player (move,grid) pairs are present."""
        expected_moves = [m for m,g in starting_grid.get_available_moves()]
        possible_moves = {m for m,g in possible_moves}
        for move in expected_moves:
            with self.subtest(move=move):
                self.assertTrue(move in possible_moves)

    def assert_complete_opponent(self, starting_grid, possible_moves):
        """Asserts that all expected opponent (move,grid) pairs are present."""
        expected_moves = starting_grid.get_available_cells()
        possible_moves = {c for c,g in possible_moves}
        for cell in expected_moves:
            with self.subtest(cell=cell):
                self.assertTrue(cell in possible_moves)

    def assert_complete_chance(self, _, possible_moves):
        """Asserts that all expected chance (move,grid) pairs are present."""
        expected_moves = [2,4]
        possible_moves = {v for (c,v),g in possible_moves}
        for value in expected_moves:
            with self.subtest(value=value):
                self.assertTrue(value in possible_moves)

    def test_early_grid_depth1(self):
        """Test an early game grid to a partial depth of 1. (i.e. one
        move, not one turn.)"""
        # initialize grid
        grid = self.early_grid
        # get results of SearchTest
        tree = SearchTest.search(grid, depth=1)
        # convert from JSON to Python object
        tree = json.loads(tree)
        # assert that all nodes are valid
        self.assertEqual(grid, tree['grid'])
        self.assert_valid(MoveType.PLAYER, grid, tree['children'])
        # assert that no nodes are missing
        self.assert_complete(MoveType.PLAYER, grid, tree['children'])

    def test_early_grid_depth3(self):
        """Test an early game grid to a partial depth of 3. (i.e. one
        complete turn.)"""
        grid = self.early_grid
        tree = SearchTest.search(grid, depth=3)
        tree = json.loads(tree)
        self.assertEqual(grid, tree['grid'])
        frontier = [tree]
        self.assert_valid(MoveType.PLAYER, grid, tree['children'])
        # assert that no nodes are missing
        self.assert_complete(MoveType.PLAYER, grid, tree['children'])

    def test_mid_grid(self):
        """Test a mid-game grid."""

    def test_late_grid(self):
        """Test a late-game grid."""
