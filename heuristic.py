def evaluate_max(grid):
    return max(grid)

def evaluate_combination(grid):
    return sum(tile_value(t) for t in grid)

def evaluate_empty(grid):
    return sum(t == 0 for t in grid) - 16

def evaluate_monotonic(grid):
    h = 0
    for y in range(4):
        increasing = True
        decreasing = True
        row = 0
        for x in range(1, 4):
            t = grid[x,y]
            if t == 0:
                continue
            increasing = increasing and t >= grid[x-1,y]
            decreasing = decreasing and t <= grid[x-1,y]
            row += tile_value(t)
        if increasing or decreasing:
            h += row
    for x in range(4):
        increasing = True
        decreasing = True
        col = 0
        for y in range(1,4):
            t = grid[x,y]
            if grid[x,y] == 0:
                continue
            increasing = increasing and t >= grid[x,y-1]
            decreasing = decreasing and t <= grid[x,y-1]
            col += tile_value(t)
        if increasing or decreasing:
            h += col
    return h

def estimate(grid, weights):
    return sum(w * f(grid) for f,w in weights)

tile_values = {0: 0, 2: 0}

def tile_value(tile):
    if tile not in tile_values:
        tile_values[tile] = 2 * tile_values[tile >> 1] + tile
    return tile_values[tile]
