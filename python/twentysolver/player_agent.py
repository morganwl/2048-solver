import functools
import time
from collections import namedtuple
import sys
import statistics

import twentysolver.heuristic as heuristic
from twentysolver.heuristic import estimate, estimate_min

INF = 2**32-1

DEBUG=True

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
    # evaluate = lambda s, x: heuristic.evaluate_max(x)
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

    @count
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

    @count
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

class PlayerAITree(PlayerAI):
    evaluate_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    sort_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    min_sort_weights = [
            (heuristic.evaluate_monotonic_change, .25),
            ]

    def __init__(self, depth_limit=2, **kwargs):
        self.root = None
        super().__init__(depth_limit=depth_limit, **kwargs)

    @record
    def get_move(self, grid):
        stime = time.process_time_ns()
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
        while time.process_time_ns() - stime < 2e8:
        # while self.depth_limit <= max_depth:
            val, move = self.get_max(self.root)
            self.depth_limit += 1
        self.depth_limit = max_depth
        for mini in self.root.available:
            if mini.move == move:
                self.root = mini
                break
        return val, move

    @count
    def get_max(self, node, alpha=-INF, beta=INF, depth=0):
        if node.available is None:
            node.available = [Node(m, g, estimate(g, self.sort_weights))
                    for m, g in node.grid.get_available_moves()]
        node.available.sort(reverse=True)
        node.value = -INF
        move = None
        for i, n in enumerate(node.available):
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
            e = 1.1 * estimate(node.grid, self.sort_weights)
            node.available = [
                    Node(c, node.grid, e + estimate_min(node.grid, c, self.min_sort_weights))
                        for c in node.grid.get_available_cells()]
        node.available.sort()
        node.value = INF
        for i, n in enumerate(node.available):
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
        v = 0
        node.value = sum(p * self.get_max(n, alpha, beta, depth+1)[0]
                for p,n in zip([.9,.1], node.available))
        return node.value

from queue import PriorityQueue

class PriorityNode():
    __slots__ = ['node', 'parent', 'current', 'queue']
    def __init__(self, node, parent=None):
        self.node = node
        self.parent = parent
        self.current = None
        self.queue = None

    def expand(self):
        pass

    def search(self):
        pass

class PlayerAITreeIter(PlayerAI):
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
        frontier = PriorityQueue()
        self.root.search()
        frontier.put(self.root)
        while frontier:
            node = frontier.get()

MAX_GAMMA = 1.5
MIN_GAMMA = .9

class PlayerAITreeLimited(PlayerAI):
    evaluate_weights = [
            (heuristic.evaluate_combination, .5),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .5),
            ]
    sort_weights = [
            (heuristic.evaluate_combination, .5),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .5),
            ]
    min_sort_weights = [
            (heuristic.evaluate_monotonic_change, .5),
            ]

    def __init__(self, move_limit=1000, **kwargs):
        self.root = None
        self.move_limit = move_limit
        super().__init__(**kwargs)

    @record
    def get_move(self, grid):
        stime = time.process_time_ns()
        if self.root is None or self.root.available is None:
            self.root = Node(None, grid)
        else:
            for expecti in self.root.available:
                if expecti.available is None:
                    self.root = Node(None, grid)
                    break
                for maxi in expecti.available:
                    if maxi.grid == grid:
                        self.root = maxi
                        break
        max_depth = self.depth_limit
        self.depth_limit = 1
        self.over = False
        if self.root.available is None:
            self.root.available = [Node(m, g, estimate(g, self.sort_weights))
                    for m, g in self.root.grid.get_available_moves()]
        while not self.over:
            self.root.available.sort(reverse=True)
            alpha, beta = -INF, INF
            alpha_2, beta_2 = -INF, INF
            val, move = -INF, False
            # alpha_2 should contain the highest next best upstream
            # score
            # what happens when we move upstream and explore alpha_2?
            for i, node in enumerate(self.root.available):
                if i < len(self.root.available) - 1:
                    alpha_2 = (self.root.available[i+1].value 
                            / MAX_GAMMA**self.root.available[i+1].height)
                else:
                    alpha_2 = val
                v = self.get_min(node, alpha, beta, alpha_2, beta_2)
                if v > val:
                    val = v
                    move = node.move
                    # print(node.height, i, v, file=sys.stderr)
                    if alpha < v:
                        alpha = v
                # print(self.depth_limit, node.height, i, v, file=sys.stderr)
                # if time.process_time_ns() - stime > 2e8:
                #     over = True
                #     break
            self.depth_limit += 1
        # print(val, '\n', file=sys.stderr)
        self.depth_limit = max_depth
        for mini in self.root.available:
            if mini.move == move:
                self.root = mini
                break
        return val, move

    @count
    def get_max(self, node, alpha=-INF, beta=INF, alpha_2=-INF, beta_2=INF, depth=0):
        if node.available is None:
            node.available = [Node(m, g, estimate(g, self.sort_weights))
                    for m, g in node.grid.get_available_moves()]
        node.available.sort(reverse=True)
        node.value = -INF
        move = None
        next_node = -INF
        for i, n in enumerate(node.available):
            if i + 1 < len(node.available):
                next_node = node.available[i+1].value
            else:
                next_node = -INF
            v = self.get_min(n, alpha, beta, MAX_GAMMA*max(alpha_2, next_node), beta_2, depth)
            if v > node.value:
                node.value = v
                move = n.move
                node.height = n.height
                if alpha < v:
                    alpha = v
                if v>= beta:
                    break
        if move is None:
            node.value = -2048
        return node.value, move

    @count
    def get_min(self, node, alpha=-INF, beta=INF, alpha_2=-INF, beta_2=INF, depth=0):
        if node.available is None:
            e = 1.1 * estimate(node.grid, self.sort_weights)
            node.available = [
                    Node(c, node.grid, e + estimate_min(node.grid, c, self.min_sort_weights))
                        for c in node.grid.get_available_cells()]
            e = estimate(node.grid, self.evaluate_weights)
            if e < alpha_2 or e > beta_2:
                # print(depth, beta_2, e, alpha_2, file=sys.stderr)
                # print(depth, 'return', file=sys.stderr)
                node.value = e
                return node.value
        # if depth == self.depth_limit:
        #     node.value = estimate(node.grid, self.evaluate_weights)
        #     return node.value
        node.available.sort()
        node.value = INF
        next_node = INF
        for i, n in enumerate(node.available):
            if i + 1 < len(node.available):
                next_node = node.available[i+1].value
                # print(depth, next_node, e, min(next_node, beta_2), file=sys.stderr)
            else:
                next_node = INF
            v = self.get_expect(n, alpha, beta, alpha_2, MIN_GAMMA*min(beta_2, next_node), depth)
            # print(depth, i, alpha, v, beta, file=sys.stderr)
            # time.sleep(.1)
            if v < node.value:
                node.value = v
                node.height = n.height
                if beta > v:
                    beta = v
                if v <= alpha:
                    break
        if node.value == INF:
            node.value = -2048
        return node.value

    def get_expect(self, node, alpha=-INF, beta=INF, alpha_2=-INF, beta_2=INF, depth=0):
        if node.available is None:
            node.available = [Node(t, node.grid.insert_tile(node.move, t)) for t in [2, 4]]
        v = 0
        node.value = sum(p * self.get_max(n, alpha, beta, alpha_2, beta_2, depth+1)[0]
                for p,n in zip([.9,.1], node.available))
        node.height = 1 + statistics.mean([n.height for n in node.available])
        return node.value

class PlayerAITreeLimitMin(PlayerAI):
    evaluate_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    sort_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    min_sort_weights = [
            (heuristic.evaluate_monotonic_change, .25),
            ]

    def __init__(self, depth_limit=2, **kwargs):
        self.root = None
        super().__init__(depth_limit, **kwargs)

    @record
    def get_move(self, grid):
        stime = time.process_time_ns()
        if self.root is None:
            self.root = Node(None, grid)
        else:
            for expecti in self.root.available:
                for maxi in expecti.available:
                    if maxi.grid == grid:
                        self.root = maxi
                        break
                else:
                    continue
                break
            else:
                self.root = Node(None, grid)

        max_depth = self.depth_limit
        self.depth_limit = 1
        # while time.process_time_ns() - stime < 2e8:
        while self.depth_limit <= max_depth:
            val, move = self.get_max(self.root)
            self.depth_limit += 1
        self.depth_limit = max_depth
        for mini in self.root.available:
            if mini.move == move:
                self.root = mini
                break
        return val, move

    @count
    def get_max(self, node, alpha=-INF, beta=INF, depth=0):
        if node.available is None:
            node.available = [Node(m, g, estimate(g, self.sort_weights))
                    for m, g in node.grid.get_available_moves()]
        node.available.sort(reverse=True)
        node.value = -INF
        move = None
        for i, n in enumerate(node.available):
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

    @count
    def get_min(self, node, alpha=-INF, beta=INF, depth=0):
        if depth == self.depth_limit:
            node.value = estimate(node.grid, self.evaluate_weights)
            return node.value
        if node.available is None:
            e = 1.1 * estimate(node.grid, self.sort_weights)
            node.available = [
                    Node(c, node.grid, e + estimate_min(node.grid, c, self.min_sort_weights))
                        for c in node.grid.get_available_cells()]
        node.available.sort()
        node.value = INF
        for i, n in enumerate(node.available):
            if i > 5:
                node.available = node.available[:i]
                break
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
        v = 0
        node.value = sum(p * self.get_max(n, alpha, beta, depth+1)[0]
                for p,n in zip([.9,.1], node.available))
        return node.value

