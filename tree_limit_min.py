from collections import deque
from heapq import heappush, heappop
import time
import sys

from player_agent import PlayerAI, record, count, INF
import heuristic
from heuristic import estimate, estimate_min

class Node:
    __slots__ = [
            'move',
            'grid',
            'value',
            'available',
            'queue',
            'cut',
            ]

    def __init__(self, move, grid, value=0):
        self.move = move
        self.grid = grid
        self.value = value
        self.cut = False
        self.available = None
        self.queue = []

    def __repr__(self):
        return f'Node({self.move!r}, {self.grid!r}, value={self.value!r})'

    def __lt__(self, other):
        return self.value < other.value

class MaxNode(Node):
    def __lt__(self, other):
        return self.value > other.value

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
            for expecti in self.root.queue:
                for maxi in expecti.queue:
                    if maxi.grid == grid:
                        self.root = maxi
                        break
                else:
                    continue
                break
            else:
                self.root = Node(None, grid)

        self.available_breadth = True
        while self.available_breadth:# and time.process_time_ns() - stime < 4e8:
            self.available_breadth = False
            val, move = self.get_max(self.root)
            print(val, move, file=sys.stderr)

        for mini in self.root.queue:
            if mini.move == move:
                self.root = mini
                break
        return val, move

    @count
    def get_max(self, node, alpha=-INF, beta=INF, depth=0):
        if node.available is None:
            node.available = deque(sorted(MaxNode(m, g, estimate(g, self.sort_weights))
                    for m, g in node.grid.get_available_moves()))

        node.value = -INF
        move = None
        new_queue = []
        if node.available:
            n = node.available.pop()
            n.value = node.value
            heappush(node.queue, n)
        if node.available:
            self.available_breadth = True
        while node.queue:
            n = heappop(node.queue)
            if n.cut:
                continue
            v = self.get_min(n, alpha, beta, depth)
            heappush(new_queue, n)
            if v > node.value:
                node.value = v
                move = n.move
                if alpha < v:
                    alpha = v
                if v>= beta:
                    node.cut = True
                    break
        node.queue = new_queue
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
            node.available = deque(sorted(
                    Node(c, node.grid, e + estimate_min(node.grid, c, self.min_sort_weights))
                        for c in node.grid.get_available_cells()))
        node.value = INF
        if node.available:
            n = node.available.pop()
            n.value = node.value
            heappush(node.queue, n)
        if node.available:
            self.available_breadth = True
        new_queue = []
        while node.queue:
            n = heappop(node.queue)
            if n.cut:
                continue
            v = self.get_expect(n, alpha, beta, depth)
            heappush(new_queue, n)
            if v < node.value:
                node.value = v
                if beta > v:
                    beta = v
                if v <= alpha:
                    node.cut = True
                    break
        node.queue = new_queue
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
