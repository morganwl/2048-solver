from random import random, choice

from grid import Grid
from player_agent import PlayerAI, PlayerAIAlphaBeta
from display import CursesDisplayer

class Player:
    def get_move(self, grid):
        move = input()
        while move not in ['0','1','2','3']:
            print('Move must be a value between 0 and 3.')
        return int(move)

class Computer:
    def get_move(self, grid):
        return choice(grid.get_available_cells())

class Displayer:
    def display(self, grid):
        for i in range(4):
            print()
            for j in range(4):
                print(f'{grid.get_cell_value(j,i): 4d} ', end='')
            print()
        print()

def random_tile():
    """Returns a random tile value of 2 or 4."""
    return 2 if random() < .9 else 4

def play_game(player, opponent, displayer=None):
    grid = Grid()

    for _ in range(2):
        pos = choice(grid.get_available_cells())
        tile = random_tile()
        grid = grid.insert_tile(pos, tile)

    while True:
        if displayer:
            displayer.display(grid)
        if not grid.get_available_moves():
            break
        move = player.get_move(grid)
        displayer.print_player_move(move)
        displayer.print_info((f'{player.stats["last_move_time"]/1e9:.4f}'
            f' {player.stats["last_move_value"]:.2f}'
            ))
        new_grid = grid.move(move)
        if new_grid == grid:
            displayer.print_info('Invalid move.')
            break
        grid = new_grid

        if displayer:
            displayer.display(grid)
        move = opponent.get_move(grid)
        displayer.print_computer_move(move)
        tile = random_tile()
        grid = grid.insert_tile(move, tile)


if __name__ == '__main__':
    player = PlayerAIAlphaBeta()
    # player = PlayerAI()
    displayer = CursesDisplayer()
    play_game(player, Computer(), displayer)
    displayer.wait()
