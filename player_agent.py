import functools
import time

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
    def __init__(self):
        self.stats = {}

    @record
    def get_move(self, grid):
        return self.get_max(grid)
    
    def get_max(self, grid, depth=0, **kwargs):
        if depth > 2:
            return grid.get_max_tile(), None
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

class PlayerAIAlphaBeta(PlayerAI):
    def get_max(self, grid, alpha=-INF, beta=INF, depth=0):
        if depth > 3:
            return grid.get_max_tile(), None
        moves = grid.get_available_moves()
        val = -INF+1
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
        return val, move

    def get_min(self, grid, alpha=-INF, beta=INF, depth=0):
        cells = grid.get_available_cells()
        val = INF-1
        for c in cells:
            v = sum(p * self.get_max(grid.insert_tile(c, t), alpha, beta, depth+1)[0]
                    for p, t in ((.9, 2), (.1, 4)))
            if v < val:
                val = v
                if beta > v:
                    beta = v
                if v <= alpha:
                    break
        return val
