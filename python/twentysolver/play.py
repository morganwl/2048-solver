import argparse
import curses
from random import random, choice
import statistics

import numpy as np

from twentysolver.grid import Grid
from twentysolver.player_agent import PlayerAI, PlayerAIAlphaBeta, PlayerAICombination, PlayerAIDownRight, \
        PlayerAITree, PlayerAITreeLimited, PlayerAITreeLimitMin
from twentysolver.display import CursesDisplayer

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
        displayer.init_headers()
        input = displayer.getch()
        if input == ord('q'):
            return None
        if not grid.get_available_moves():
            break
        move = player.get_move(grid)
        grid = grid.validate_move(move)
        displayer.print_player_move(move)
        displayer.print_move_info(
                player.counts.get('get_max_calls', 0),
                player.stats['last_move_time'],
                player.stats['last_move_value'])
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

def play_series(displayer, n=20, player=None):
    games = []
    generator = np.random.default_rng()
    med, confidence = 0, 0
    while confidence < .95:
        if player is None:
            player = PlayerAITreeLimitMin()
        stats = play_game(player, Computer(), displayer)
        if stats is None:
            break
        games.append(stats)
        displayer.print_game_info(*stats.values())
        scores = np.fromiter((game['score'] for game in games), dtype=np.uint16)
        med, confidence = median_confidence(scores, generator)
        displayer.print_info(f'{med} {confidence:.3f}')
        distribution = dist_ci(scores, generator)
        displayer.print_info(
                '\t'.join(f'{int(target)}: {100*per:.1f} in [{100*low:.0f}, {100*high:.0f}]'
                    for target, per, (low, high) in distribution))

def interval(trials, value, confidence):
    distributions = (np.mean(trial >= value) for trial in trials)
    quantiles = np.quantile(
            np.sort(np.fromiter(distributions, np.float64)),
            [.5 - confidence/2, .5 + confidence/2])
    return quantiles
    return quantiles[1] - quantiles[0]

def dist_ci(scores, generator=None, noise_level=5, confidence=.95):
    if generator is None:
        generator = np.default_rng()
    targets = [2** i for i in range(9,13)]
    distribution = [np.mean(scores >= target) for target in targets]
    noise = generator.choice([2**i for i in range(4,14)], 2*noise_level)
    samples = np.concatenate([scores, noise])
    trials = list(generator.choice(samples, len(samples)) for _ in range(1000))
    confidence = [interval(trials, target, confidence) for target in targets]
    return list(zip(targets, distribution, confidence))

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

def parseargs():
    parser = argparse.ArgumentParser(
            description='run a series of 2048 games for an AI agent')
    parser.add_argument('--agent', '-a', help='name of agent')
    return vars(parser.parse_args())

def main(stdscr):
    kwargs = parseargs()
    displayer = CursesDisplayer(stdscr)
    agent = kwargs['agent']
    if agent == 'PlayerAI':
        agent = PlayerAI()
    elif agent == 'PlayerAIAlphaBeta':
        agent = PlayerAIAlphaBeta()
    elif agent == 'PlayerAICombination':
        agent = PlayerAICombination()
    elif agent == 'PlayerAITree':
        agent = PlayerAITree()
    elif agent == 'PlayerAITreeLimited':
        agent = PlayerAITreeLimited()
    elif agent == 'PlayerAITreeLimitMin':
        agent = PlayerAITreeLimitMin()
    else:
        agent = None
    play_series(displayer, player=agent)
    displayer.wait()

if __name__ == '__main__':
    curses.wrapper(main)
