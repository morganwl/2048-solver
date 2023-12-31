"""An iterative deepening agent that caches results in a search tree."""

from collections import namedtuple
import threading
import time

from twentysolver import heuristic
from twentysolver.heuristic import estimate, estimate_min

from . import PlayerAI, INF

frame_cache = {}


class Frame:
    """Stack frame for storing search state for any given move (player or opponent)."""
    __slots__ = ['_grid', 'alpha', 'beta', 'i', 'best_node']
    def __init__(self, grid, alpha=-INF, beta=INF, i=None):
        self._grid = grid
        self.alpha = alpha
        self.beta = beta
        self.i = i
        self.best_node = None

    def alphabeta(self):
        """Update bounds and prune branch if move is outside of
        bounds."""
        return False

    def result(self, value=None):
        """Store best seen child value as the value for this move.
        Optionally supply a different value instead, used when cutting
        off search at the depth limit. Otherwise, if no child node has
        been recorded, assign the minimum possible score."""
        if value is not None:
            self._grid.value = value
        elif self.best_node is not None:
            self._grid.value = self.best_node.value
        else:
            self._grid.value = -INF
        return self

    @property
    def grid(self):
        """Returns the corresponding grid for this stack frame."""
        return self._grid.grid

    @property
    def children(self):
        """Returns the list of possible moves from this stack frame."""
        return self._grid.children

    @children.setter
    def children(self, value):
        """Set the list of possible moves from this stack frame."""
        self._grid.children = value

    @property
    def value(self):
        """Returns the current estimated value of the move associated
        with this stack frame.."""
        return self._grid.value

    @property
    def move(self):
        """Returns the move associated with this stack frame."""
        return self._grid.move

    def __lt__(self, other):
        try:
            return self.value < other.value
        except AttributeError:
            return self.value < other

    def __gt__(self, other):
        try:
            return self.value > other.value
        except AttributeError:
            return self.value > other


class MaxFrame(Frame):
    """Find the subsequent move with the largest value."""
    sort_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    def expand(self):
        if self.children is None:
            self.children = [GridNode(g, m, estimate(g, self.sort_weights))
                for m, g in self.grid.get_available_moves()]
        self.children.sort(reverse=True)
        self.i = -1

    def update(self, result):
        if self.best_node is None or result._grid > self.best_node:
            self.best_node = result._grid
            if self.best_node > self.alpha:
                self.alpha = self.best_node.value

    def alphabeta(self):
        """Updates alpha (lower bound) to best move seen on this branch,
        and prunes branch if a move could exceed beta (upper bound).

        Rationale: The opponent will not make a move if the player could
        respond with a move greater than or equal to beta."""
        if self.best_node is not None and self.best_node >= self.beta:
            return True
        return False

    def __getitem__(self, index):
        return MinFrame(self.children[index],
                alpha=self.alpha, beta=self.beta)


class MinFrame(Frame):
    """Find the subsequent move with the smallest value."""
    sort_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    min_sort_weights = [
            (heuristic.evaluate_monotonic_change, .25),
            ]

    def expand(self):
        if self.children is None:
            e = 1.1 * estimate(self.grid, self.sort_weights)
            self.children = [GridNode(self.grid,
                c, e + estimate_min(self.grid, c, self.min_sort_weights))
                for c in self.grid.get_available_cells()]
        self.children.sort()
        self.i = -1

    def update(self, result):
        if self.best_node is None or result._grid < self.best_node:
            self.best_node = result._grid
            if self.best_node < self.beta:
                self.beta = self.best_node.value

    def alphabeta(self):
        if self.best_node is not None and self.best_node <= self.alpha:
            return True
        return False

    def __getitem__(self, index):
        return ExpectFrame(self.children[index],
                alpha=self.alpha, beta=self.beta)


MoveProb = namedtuple('MoveProb', ('move', 'prob'))
class ExpectFrame(Frame):
    """Calculate expected value of move based on probability of outcomes."""
    __slots__ = ['value']
    moves = [MoveProb(2, .9), MoveProb(4, .1)]
    def __init__(self, *args, **kwargs):
        self.value = 0
        super().__init__(*args, **kwargs)

    def expand(self):
        if self.children is None:
            self.children = [GridNode(self.grid.insert_tile(self.move, t), t)
                for t,_ in self.moves]
        self.i = -1

    def update(self, result):
        self.value += result.value * self.moves[self.i].prob

    def alphabeta(self):
        if self.i == 1 and self.value / self.moves[0].prob <= self.alpha:
            return True
        return False

    def result(self, value=None):
        self._grid.value = self.value
        return self

    def __getitem__(self, index):
        return MaxFrame(self.children[index],
                alpha=self.alpha*self.moves[index].prob, beta=self.beta/self.moves[index].prob)


class GridNode:
    """Store a move and corresponding grid, with links to the possible
    moves from that grid."""
    __slots__ = ['grid', 'move', 'value', 'children']

    def __init__(self, grid, move=None, value=None):
        self.grid = grid
        self.move = move
        self.value = value
        self.children = None

    def __getitem__(self, i):
        return self.children[i]

    def __lt__(self, other):
        try:
            return self.value < other.value
        except AttributeError:
            return self.value < other

    def __gt__(self, other):
        try:
            return self.value > other.value
        except AttributeError:
            return self.value > other

    def __ge__(self, other):
        try:
            return self.value >= other.value
        except AttributeError:
            return self.value >= other

    def __le__(self, other):
        try:
            return self.value <= other.value
        except AttributeError:
            return self.value <= other

class CacheTree(PlayerAI):
    evaluate_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]

    def __init__(self, depth_limit=2, time_limit=1.9e8, **kwargs):
        self.root = None
        self.time_limit = time_limit / 1e9
        frame_cache.clear()
        super().__init__(depth_limit, **kwargs)

    def set_over(self):
        self.over = True

    def get_move(self, grid):
        self.over = False
        stime = time.time_ns()
        timer = threading.Timer(self.time_limit, self.set_over)
        timer.start()
        root = self.find_root(grid)
        depth_limit = 1
        node = None
        self.counts = {'get_max_calls': 0}
        while True and not self.over:
            n = self.search(root, depth_limit)
            if self.over:
                break
            node = n
            depth_limit += 1
        self.root = node
        timer.cancel()
        self.stats = {
                'last_move_time': time.time_ns() - stime,
                'last_move_value': depth_limit -1,
                # 'last_move_value': node.value if node else 0,
                }
        if node is None:
            return grid.get_available_moves()[0][0]
        return node.move

    def find_root(self, grid):
        if self.root is not None and self.root.children is not None:
            for node in self.root.children:
                if (t := grid.get_cell_value(*node.move)) != 0:
                    if node.children is None:
                        break
                    if t == 2:
                        return node.children[0]
                    else:
                        return node.children[1]
        return GridNode(grid)

    def search(self, root, depth_limit):
        stack = [MaxFrame(root)]
        result = None
        while stack and not self.over:
            frame = stack[-1]
            # check for cutoff
            if isinstance(frame, MinFrame) and len(stack) > (3 * depth_limit) - 1:
                result = frame.result(estimate(frame.grid, self.evaluate_weights))
                stack.pop()
                continue
            # handle return value (in-order) or expand queue (pre-order)
            if frame.i is not None:
                if isinstance(frame, MaxFrame):
                    self.counts['get_max_calls'] += 1
                frame.update(result)
            else:
                frame.expand()

            # append next child (in-order) or return value and pop frame (post-order)
            frame.i += 1
            if frame.i == len(frame.children) or frame.alphabeta():
                result = frame.result()
                stack.pop()
                continue
            stack.append(frame[frame.i])
        if not self.over:
            return result.best_node
        if stack:
            return stack[0].best_node
        return None
