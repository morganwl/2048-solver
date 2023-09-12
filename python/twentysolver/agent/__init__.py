import functools
import time
from collections import namedtuple
import sys
import statistics

import twentysolver.heuristic as heuristic
from twentysolver.heuristic import estimate, estimate_min

INF = 2**31 - 1

def record(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        time_in = time.process_time_ns()
        self.counts = {}
        result = func(self, *args, **kwargs)
        time_out = time.process_time_ns()
        self.stats['last_move_time'] = time_out - time_in
        self.stats['last_move_value'] = result[0]
        # print(result, file=sys.stderr)
        return result[1]
    return wrapper

def count(func):
    # if not DEBUG:
    #     return func
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        key = func.__name__ + '_calls'
        self.counts[key] = self.counts.get(key, 0) + 1
        if func.__name__ == 'get_min' and self.counts.get('get_max_calls', 0) > self.move_limit:
            self.over = True
            args[0].value = estimate(args[0].grid, self.evaluate_weights)
            return args[0].value
        return func(self, *args, **kwargs)
    return wrapper

class PlayerAI:
    evaluate_weights = [
            (heuristic.evaluate_max, 1),
            ]

    def __init__(self, depth_limit=3, move_limit=INF):
        self.depth_limit = depth_limit
        self.move_limit = move_limit
        self.stats = {}

    @record
    def get_move(self, grid):
        return self.get_max(grid)
    
    def get_max(self, grid, depth=0, **kwargs):
        if depth == self.depth_limit:
            return heuristic.estimate(grid, self.evaluate_weights), None
        moves = grid.get_available_moves()
        val = -INF
        move = None
        for m, g in moves:
            v = self.get_min(g, depth)
            if v > val:
                val = v
                move = m
        return val, move

    def get_min(self, grid, depth=0, **kwargs):
        cells = grid.get_available_cells()
        val = INF
        for c in cells:
            v = (.9 * self.get_max(grid.insert_tile(c, 2), depth+1)[0] +
                    .1 * self.get_max(grid.insert_tile(c, 4), depth+1)[0])
            if v < val:
                val = v
        return val

class Node:
    __slots__ = [
            'move',
            'grid',
            'value',
            'available',
            'height',
            ]

    def __init__(self, move, grid, value=0):
        self.move = move
        self.grid = grid
        self.value = value
        self.available = None
        self.height = 0

    def __repr__(self):
        return f'Node({self.move!r}, {self.grid!r}, value={self.value!r})'

    def __lt__(self, other):
        return self.value < other.value

from .treelimit import PlayerAITreeLimitMin
from .newlimit import NewLimitMin
from .cachelimit import CacheLimitMin
from .cachetree import CacheTree
