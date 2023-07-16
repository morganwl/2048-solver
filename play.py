from random import random, choice
import statistics

import numpy as np

from grid import Grid
from player_agent import PlayerAI, PlayerAIAlphaBeta, PlayerAICombination, PlayerAIDownRight, \
        PlayerAITree
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

    moves = []
    if displayer:
        displayer.display(grid)

    while True:
        if not grid.get_available_moves():
            break
        move = player.get_move(grid)
        grid = grid.validate_move(move)
        displayer.print_player_move(move)
        displayer.print_move_info(player.stats['last_move_time'], player.stats['last_move_value'])
        moves.append({key: val for key, val in player.stats.items()})
        displayer.display(grid)

        move = opponent.get_move(grid)
        displayer.print_computer_move(move)
        tile = random_tile()
        grid = grid.insert_tile(move, tile)
        displayer.display(grid)

    return {
            'no_moves': len(moves),
            'average_move_time': statistics.fmean(move['last_move_time'] for move in moves),
            'score': grid.get_max_tile(),
            }

def play_series(displayer, n=20):
    games = []
    generator = np.random.default_rng()
    med, confidence = 0, 0
    while confidence < .95:
        player = PlayerAITree()
        # player = PlayerAIDownRight()
        # player = PlayerAICombination()
        # player = PlayerAIAlphaBeta()
        # player = PlayerAI()
        stats = play_game(player, Computer(), displayer)
        games.append(stats)
        displayer.print_game_info(*stats.values())
        scores = np.fromiter((game['score'] for game in games), dtype=np.uint16)
        med, confidence = median_confidence(scores, generator)
        displayer.print_info(f'{med} {confidence:.3f}')
        distribution = dist_ci(scores, generator)
        displayer.print_info(
                '\t'.join(f'{per:.3f}: {interval:.3f}' for per, interval in distribution))

def interval(trials, value, confidence):
    distributions = (np.mean(trial >= value) for trial in trials)
    quantiles = np.quantile(
            np.sort(np.fromiter(distributions, np.float64)),
            [.5 - confidence/2, .5 + confidence/2])
    return quantiles[1] - quantiles[0]

def dist_ci(scores, generator=None, noise_level=8, confidence=.95):
    if generator is None:
        generator = np.default_rng()
    distribution = [np.mean(scores >= 2**i) for i in range(7, 12)]
    noise = generator.choice([2**i for i in range(4,14)], 2*noise_level)
    samples = np.concatenate([scores, noise])
    trials = list(generator.choice(samples, len(samples)) for _ in range(1000))
    confidence = [interval(trials, 2**i, confidence) for i in range(7, 12)]
    return list(zip(distribution, confidence))

def median_confidence(scores, generator=None, noise_level=8):
    if generator is None:
        generator = np.default_rng()
    noise = generator.choice([2**i for i in range(4,14)], 2*noise_level)
    med = np.median(scores)
    samples = np.concatenate([scores, noise])
    trials = (generator.choice(samples, len(samples)) for _ in range(1000))
    confidence = np.mean(np.fromiter((np.median(trial) == med for trial in trials),
        dtype=np.uint8))
    return med, confidence


if __name__ == '__main__':
    displayer = CursesDisplayer()
    play_series(displayer)
    displayer.wait()
