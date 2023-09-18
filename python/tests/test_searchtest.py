"""Test the SearchTest object."""

import unittest
from unittest.mock import patch, call

from twentysolver.grid import Grid
from twentysolver import searchtest
from twentysolver.searchtest import MoveType


class GridTester:
    """Parent class containing convenience functions for testing grid validity."""
    early_grid = [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 4, 4, 0, 0]
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
            with self.subTest(move=move):
                grid = Grid.from_list([int(t) for t in grid.strip('[]').split(',')])
                result = starting_grid.validate_move(move)
                self.assertEqual(grid, result)

    def assert_valid_opponent(self, starting_grid, possible_moves):
        """Asserts that all opponent (move,grid) pairs are valid."""
        for cell, grid in possible_moves:
            with self.subTest(cell=cell):
                grid = Grid.from_list([int(t) for t in grid.strip('[]').split(',')])
                self.assertEqual(starting_grid.get_cell_value(*cell), 0)
                self.assertEqual(grid, starting_grid)

    def assert_valid_chance(self, starting_grid, possible_moves):
        """Asserts that all chance (move,grid) pairs are valid."""
        for (cell, value), grid in possible_moves:
            with self.subTest(value=value):
                grid = Grid.from_list([int(t) for t in grid.strip('[]').split(',')])
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
            with self.subTest(move=move):
                self.assertTrue(move in possible_moves)

    def assert_complete_opponent(self, starting_grid, possible_moves):
        """Asserts that all expected opponent (move,grid) pairs are present."""
        expected_moves = starting_grid.get_available_cells()
        possible_moves = {c for c,g in possible_moves}
        for cell in expected_moves:
            with self.subTest(cell=cell):
                self.assertTrue(cell in possible_moves)

    def assert_complete_chance(self, _, possible_moves):
        """Asserts that all expected chance (move,grid) pairs are present."""
        expected_moves = [2,4]
        possible_moves = {v for (c,v),g in possible_moves}
        for value in expected_moves:
            with self.subTest(value=value):
                self.assertTrue(value in possible_moves)


class TestSearchTestSearch(unittest.TestCase, GridTester):
    """Test components of SearchTree."""
    def setUp(self):
        self.early_grid = Grid.from_list(self.early_grid)

    def test_search_max_record(self):
        """search_max(records, entry, depth) should create a record for the
        given (move, grid) pair and append it to records, before
        continuing the search with any children (until depth is exhausted)."""
        records = [None]
        entry = searchtest.Entry(None, self.early_grid)
        searchtest.search_max(records, entry, 1)
        self.assertEqual(len(records), 2)
        record = records[-1]
        self.assertIsInstance(record, dict)
        self.assertEqual(record,
                {   'key': (None, self.early_grid.as_list()),
                    'movetype': 'PLAYER',
                    'children': [(0, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 8]),
                        (2, [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 8, 0, 0, 0]),
                        (3, [2, 4, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])],
                    })

    def test_search_max_calls(self):
        """search_max(records, entry, depth) should call search_min once
        for every child, if depth is greater than 0."""
        entry = searchtest.Entry(None, self.early_grid)
        with patch.object(searchtest, 'search_min', return_value=None) as search_min:
            searchtest.search_max([], entry, 1)
            search_min.assert_not_called()
        records = []
        with patch.object(searchtest, 'search_min', return_value=None) as search_min:
            searchtest.search_max(records, entry, 2)
            search_min.assert_called()
            search_min.assert_has_calls(
                    [call(records, searchtest.Entry(move, grid), 1) for
                    move, grid in entry.grid.get_available_moves()],
                    any_order=True)

    def test_search_min_record(self):
        """search_min(records, entry, depth) should create a record for the
        given (move, grid) pair and append it to records, before
        continuing the search with any children (until depth is exhausted)."""
        grid = self.early_grid.move(0)
        records = [None]
        entry = searchtest.Entry(0, grid)
        searchtest.search_min(records, entry, 1)
        self.assertEqual(len(records), 2)
        record = records[-1]
        self.assertIsInstance(record, dict)
        self.assertEqual(record,
                {   'key': (0, grid.as_list()),
                    'movetype': 'OPPONENT',
                    'children': [(cell, grid.as_list()) for cell in grid.get_available_cells()],
                    })

    # Basic design:
    # 1. Complete DFS search, to specified depth
    # 2. Each node can be serialized individually, containing just the
    # (move, grid) tuple for its children.
    # 3. The resulting structure is a dictionary mapping (move,grid)
    # tuples to single Node objects.
    # 4. The first node in the file is the root node.

class TestSearchTestAcceptance(unittest.TestCase, GridTester):
    """SearchTest should generate a complete search tree to a specified
    depth and save the output as json."""
    def setUp(self):
        self.early_grid = Grid.from_list([0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 4, 4, 0, 0])


    def test_early_grid_depth1(self):
        """Test an early game grid to a partial depth of 1. (i.e. one
        move, not one turn.)"""
        # initialize grid
        grid = self.early_grid
        # get results of SearchTest
        json = searchtest.search(grid, depth=1)
        # convert from JSON to Python object
        records, root = searchtest.from_json(json)
        # assert that all nodes are valid
        self.assertEqual((None, str(grid.as_list())), root)
        self.assert_valid(MoveType.PLAYER, grid, records[root].children)
        # assert that no nodes are missing
        self.assert_complete(MoveType.PLAYER, grid, records[root].children)

    def test_early_grid_depth3(self):
        """Test an early game grid to a partial depth of 3. (i.e. one
        complete turn.)"""
        grid = self.early_grid
        json = searchtest.search(grid, depth=3)
        records, root = searchtest.from_json(json)
        self.assertEqual((None, str(grid.as_list())), root)
        frontier = [root]
        self.assertIsInstance(root[1], str)
        while frontier:
            record = records[frontier.pop()]
            with self.subTest(record=record):
                self.assert_valid(record.movetype, record.grid, record.children)
                self.assert_complete(record.movetype, record.grid, record.children)
                if record.movetype != MoveType.CHANCE:
                    frontier.extend(c for c in record.children)

    def test_mid_grid(self):
        """Test a mid-game grid."""

    def test_late_grid(self):
        """Test a late-game grid."""
