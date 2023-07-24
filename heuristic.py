def evaluate_max(grid):
    return max(grid)

def evaluate_combination(grid):
    return sum(tile_value(t) for t in grid)

def evaluate_empty(grid):
    return sum(t == 0 for t in grid) - 8

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

def evaluate_monotonic_change(grid, pos):
    left, right, up, down = 0,0,0,0
    x,y = pos
    for i in reversed(range(x)):
        if grid[i,y]:
            left = grid[i,y]
            break
    for i in range(x+1,4):
        if grid[i,y]:
            right = grid[i,y]
            break
    for j in reversed(range(y)):
        if grid[x,j]:
            up = grid[x,j]
            break
    for j in range(y+1,4):
        if grid[x,j]:
            down = grid[x,j]
            break

    h = 0
    if left > 4 and right > 4:
        h -= sum(tile_value(grid[i,y]) for i in range(4))
    if left == 2 or right == 2:
        h += .9
    if left == 4 or right == 4:
        h += .6
    if up > 4 and down > 4:
        h -= sum(tile_value(grid[x,j]) for j in range(4))
    if up == 2 or down == 2:
        h += .9
    if up == 4 or right == 4:
        h += .6
    return h

def estimate(grid, weights):
    return sum(w * f(grid) for f,w in weights)

def estimate_min(grid, tile, weights):
    return sum(w * f(grid, tile) for f,w in weights)

tile_values = {0: 0, 2: 0}

def tile_value(tile):
    if tile not in tile_values:
        tile_values[tile] = 2 * tile_values[tile >> 1] + tile
    return tile_values[tile]
