import time

from . import PlayerAI, record, count, INF, Node

import twentysolver.heuristic as heuristic
from twentysolver.heuristic import estimate, estimate_min

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

