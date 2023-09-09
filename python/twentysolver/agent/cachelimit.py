from collections import namedtuple
from enum import Enum, auto
import threading
import time

from . import PlayerAI, record, count, INF, Node

import twentysolver.heuristic as heuristic
from twentysolver.heuristic import estimate, estimate_min


frame_cache = {}


class Frame:
    __slots__ = ['grid', 'alpha', 'beta', 'i', 'queue', 'value', 'move']
    init_value = None
    def __init__(self, grid, move=None, alpha=-INF, beta=INF, i=None):
        self.value = self.init_value
        self.grid = grid
        self.move = move
        self.alpha = alpha
        self.beta = beta
        self.i = i
        self.queue = None

    def expand(self):
        """Fills the queue with possible successor frames, and sets
        index to first element."""
        raise NotImplementedError

    def alphabeta(self):
        """Update bounds ane prune branch if move is outside of
        bounds."""
        return False

    def __getitem__(self, i):
        return self.queue[i]

    def __lt__(self, other):
        try:
            return self.value < other.value
        except AttributeError:
            return self.value < other


class MaxFrame(Frame):
    sort_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    init_value = -INF
    def expand(self):
        self.queue = [MinFrame(g, move=m) for m, g in self.grid.get_available_moves()]
        self.queue.sort(reverse=True,
                key=lambda f: self.lookup(f))
        self.i = -1

    def update(self, result):
        value, move = result
        if value > self.value:
            self.value = value
            self.move = move
            if self.alpha <= self.value:
                self.alpha = self.value

    def alphabeta(self):
        """Updates alpha (lower bound) to best move seen on this branch,
        and prunes branch if a move could exceed beta (upper bound).

        Rationale: The opponent will not make a move if the player could
        respond with a move greater than or equal to beta."""
        if self.beta <= self.value:
            return True
        return False

    def lookup(self, frame):
        if cached := frame_cache.get((tuple(frame.grid.tiles), frame.move)):
            return cached
        return estimate(frame.grid, self.sort_weights)


class MinFrame(Frame):
    sort_weights = [
            (heuristic.evaluate_combination, .75),
            (heuristic.evaluate_empty, 2),
            (heuristic.evaluate_monotonic, .25),
            ]
    min_sort_weights = [
            (heuristic.evaluate_monotonic_change, .25),
            ]
    init_value = INF

    def expand(self):
        e = 1.1 * estimate(self.grid, self.sort_weights)
        self.queue = [ExpectFrame(self.grid, c)
                for c in self.grid.get_available_cells()]
        self.queue.sort(
                key = lambda f: self.lookup(f))
                # key=lambda f: e + estimate_min(self.grid, f.move, self.min_sort_weights))
        self.i = -1

    def update(self, result):
        value, _ = result
        if value < self.value:
            self.value = value
            if self.beta >= self.value:
                self.beta = self.value

    def alphabeta(self):
        if self.alpha >= self.value:
            return True
        return False

    def lookup(self, frame):
        if cached := frame_cache.get((tuple(frame.grid.tiles), frame.move)):
            return cached
        return estimate_min(frame.grid, frame.move, self.min_sort_weights)


MoveProb = namedtuple('MoveProb', ('move', 'prob'))
class ExpectFrame(Frame):
    moves = [MoveProb(2, .9), MoveProb(4, .1)]
    init_value = 0

    def expand(self):
        self.queue = [MaxFrame(self.grid.insert_tile(self.move, v))
                for v,_ in self.moves]
        self.i = -1

    def update(self, result):
        value, _ = result
        self.value += value * self.moves[self.i].prob

class CacheLimitMin(PlayerAI):
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

    def __init__(self, depth_limit=2, time_limit=2e8, **kwargs):
        self.root = None
        self.time_limit = time_limit / 1e9
        frame_cache.clear()
        super().__init__(depth_limit, **kwargs)

    def set_over(self):
        self.over = True

    def get_move(self, grid):
        self.over = False
        stime = time.process_time_ns()
        timer = threading.Timer(self.time_limit, self.set_over)
        timer.start()
        depth_limit = 1
        # resolutions = [4, 6, 8, None]
        r = 0
        val, move = -INF, None
        self.counts = {'get_max_calls': 0}
        while True:
            v, m = self.search(grid, depth_limit)
            if self.over:
                break
            val, move = v, m
            depth_limit += 1
        timer.cancel()
        self.stats = {
                'last_move_time': time.process_time_ns() - stime,
                'last_move_value': depth_limit,
                }
        if move is None:
            return grid.get_available_moves()[0][0]
        return move

    def search(self, grid, depth_limit):
        stack = [MaxFrame(grid)]
        result = None, None
        while stack and not self.over:
            frame = stack[-1]
            # check for cutoff
            if isinstance(frame, MinFrame) and len(stack) > (3 * depth_limit) - 1:
                result = estimate(frame.grid, self.evaluate_weights), frame.move
                stack.pop()
                continue
            # handle return value (in-order) or expand queue (pre-order)
            if frame.i is not None:
                frame.update(result)
            else:
                frame.expand()

            # append next child (in-order) or return value and pop frame (post-order)
            frame.i += 1
            if frame.i == len(frame.queue) or frame.alphabeta():
                if isinstance(frame, MaxFrame):
                    frame_cache[(tuple(frame.grid.tiles), None)] = frame.value
                    self.counts['get_max_calls'] += 1
                else:
                    frame_cache[(tuple(frame.grid.tiles), frame.move)] = frame.value
                result = frame.value, frame.move
                stack.pop()
                continue
            stack.append(frame[frame.i])
            stack[-1].alpha, stack[-1].beta = frame.alpha, frame.beta
        return result
