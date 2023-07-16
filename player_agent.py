import functools
import time
from collections import namedtuple

import heuristic
from heuristic import estimate

INF = 2**32-1

def record(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        time_in = time.process_time_ns()
        result = func(self, *args, **kwargs)
        time_out = time.process_time_ns()
        self.stats['last_move_time'] = time_out - time_in
        self.stats['last_move_value'] = result[0]
        return result[1]
    return wrapper

class PlayerAI:
    # evaluate = lambda s, x: heuristic.evaluate_max(x)
    evaluate_weights = [
            (heuristic.evaluate_max, 1),
            ]

    def __init__(self, depth_limit=2):
        self.depth_limit = depth_limit
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

class PlayerAIDownRight(PlayerAI):
    def get_max(self, grid, **kwargs):
        moves = grid.get_available_moves()
        moves.sort(key=lambda x: [1, 0, 2, 2][x[0]])
        return 0, moves[0][0]

class PlayerAIAlphaBeta(PlayerAI):
    def get_max(self, grid, alpha=-INF, beta=INF, depth=0):
        if depth == self.depth_limit:
            return heuristic.estimate(grid, self.evaluate_weights), None
        moves = grid.get_available_moves()
        val = -INF
        move = None
        for m, g in moves:
            v = self.get_min(g, alpha, beta, depth)
            if v > val:
                val = v
                move = m
                if alpha < v:
                    alpha = v
                if v >= beta:
                    break
        if move is None:
            val = 0
        return val, move

    def get_min(self, grid, alpha=-INF, beta=INF, depth=0):
        cells = grid.get_available_cells()
        val = INF
        for c in cells:
            v = sum(p * self.get_max(grid.insert_tile(c, t), alpha, beta, depth+1)[0]
                    for p, t in ((.9, 2), (.1, 4)))
            if v < val:
                val = v
                if beta > v:
                    beta = v
                if v <= alpha:
                    break
        if val == INF:
            val = 0
        return val

class PlayerAICombination(PlayerAI):
    evaluate_weights = [
            (heuristic.evaluate_combination, 1),
            (heuristic.evaluate_empty, 2),
            ]
    sort_weights = [
            (heuristic.evaluate_combination, 1),
            (heuristic.evaluate_empty, 2),
            ]

    def get_max(self, grid, alpha=-INF, beta=INF, depth=0):
        if depth == self.depth_limit:
            return heuristic.estimate(grid, self.evaluate_weights), None
        moves = grid.get_available_moves()
        moves = [(heuristic.estimate(g, self.sort_weights), m, g)
                for m, g in moves]
        moves.sort(reverse=True)
        val = -INF
        move = None
        for e, m, g in moves:
            v = self.get_min(g, alpha, beta, depth)
            if v > val:
                val = v
                move = m
                if alpha < v:
                    alpha = v
                if v >= beta:
                    break
        if move is None:
            val = 0
        return val, move

    def get_min(self, grid, alpha=-INF, beta=INF, depth=0):
        cells = grid.get_available_cells()
        val = INF
        for c in cells:
            v = sum(p * self.get_max(grid.insert_tile(c, t), alpha, beta, depth+1)[0]
                    for p, t in ((.9, 2), (.1, 4)))
            if v < val:
                val = v
                if beta > v:
                    beta = v
                if v <= alpha:
                    break
        if val == INF:
            val = 0
        return val

TURNS = [MAX, MIN, EXPECT] = range(3)

class Node:
    __slots__ = [
            'move',
            'grid',
            'value',
            'available',
            ]

    def __init__(self, move, grid, value=0):
        self.move = move
        self.grid = grid
        self.value = value
        self.available = None

    def __repr__(self):
        return f'Node({self.move!r}, {self.grid!r}, value={self.value!r})'

    def __lt__(self, other):
        return self.value < other.value

class PlayerAITree(PlayerAI):
    evaluate_weights = [
            (heuristic.evaluate_combination, 1),
            (heuristic.evaluate_empty, 2),
            ]
    sort_weights = [
            (heuristic.evaluate_combination, 1),
            (heuristic.evaluate_empty, 2),
            ]
    min_sort_weights = [
            (heuristic.evaluate_monotonic, 1),
            ]

    def __init__(self, **kwargs):
        self.root = None
        super().__init__(**kwargs)

    @record
    def get_move(self, grid):
        if self.root is None:
            self.root = Node(None, grid)
        else:
            for expecti in self.root.available:
                for maxi in expecti.available:
                    if maxi.grid == grid:
                        self.root = maxi
                        break
        max_depth = self.depth_limit
        self.depth_limit = 1
        while self.depth_limit <= max_depth:
            val, move = self.get_max(self.root)
            self.depth_limit += 1
        self.depth_limit = max_depth
        for mini in self.root.available:
            if mini.move == move:
                self.root = mini
                break
        return val, move

    def get_max(self, node, alpha=-INF, beta=INF, depth=0):
        # if depth == self.depth_limit:
        #     node.value = estimate(node.grid, self.evaluate_weights)
        #     return node.value, None
        if node.available is None:
            node.available = [Node(m, g, estimate(g, self.sort_weights))
                    for m, g in node.grid.get_available_moves()]
        node.available.sort(reverse=True)
        node.value = -INF
        move = None
        for n in node.available:
            v = self.get_min(n, alpha, beta, depth)
            if v > node.value:
                node.value = v
                move = n.move
                if alpha < v:
                    alpha = v
                if v>= beta:
                    break
        if move is None:
            node.value = -2048
        return node.value, move

    def get_min(self, node, alpha=-INF, beta=INF, depth=0):
        if depth == self.depth_limit:
            node.value = estimate(node.grid, self.evaluate_weights)
            return node.value
        if node.available is None:
            node.available = [
                    Node(c, node.grid, estimate(node.grid.insert_tile(c, 2), self.min_sort_weights))
                        for c in node.grid.get_available_cells()]
        node.available.sort()
        node.value = INF
        for n in node.available:
            v = self.get_expect(n, alpha, beta, depth)
            if v < node.value:
                node.value = v
                if beta > v:
                    beta = v
                if v <= alpha:
                    break
        if node.value == INF:
            node.value = -2048
        return node.value

    def get_expect(self, node, alpha=-INF, beta=INF, depth=0):
        if node.available is None:
            node.available = [Node(t, node.grid.insert_tile(node.move, t)) for t in [2, 4]]
        node.value = sum(p * self.get_max(n, alpha, beta, depth+1)[0]
                for p,n in zip([.9,.1], node.available))
        return node.value

class PlayerAITreeIter(PlayerAI):
    pass
