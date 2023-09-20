import argparse
import curses
import datetime
from random import random, choice
import statistics
import subprocess

import numpy as np

from twentysolver.grid import Grid
import twentysolver.player_agent
import twentysolver.agent
from twentysolver.agent import CacheTree
from twentysolver.display import CursesDisplayer

class Player:
    """Human-controlled agent."""
    def get_move(self, _):
        """Solicit move from standard input."""
        move = input()
        while move not in ['0','1','2','3']:
            print('Move must be a value between 0 and 3.')
        return int(move)

class Computer:
    """Computer-controlled opponent."""
    def get_move(self, grid):
        """Selects from available tiles at random."""
        return choice(grid.get_available_cells())

class Displayer:
    """Simple terminal-based displayer."""
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

def play_game(player, opponent, displayer=None, screenshot=False):
    """Play a single game and return a dictionary of statistics."""
    grid = Grid()

    for _ in range(2):
        pos = choice(grid.get_available_cells())
        tile = random_tile()
        grid = grid.insert_tile(pos, tile)

    moves = []
    if displayer:
        displayer.display(grid)
    if screenshot:
        screenshot = take_screenshot(player)

    while True:
        if screenshot:
            next(screenshot)
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

def play_series(displayer, n=20, agent=None, screenshot=False):
    """Play a series of games, calculating the confidence interval for
    median and percentiles, stopping after a sufficiently high
    confidence is reached."""
    games = []
    generator = np.random.default_rng()
    med, confidence = 0, 0
    if agent is None:
        agent = CacheTree
    while confidence < .95:
        player = agent()
        stats = play_game(player, Computer(), displayer, screenshot=screenshot)
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
    """Returns the confidence interval for the probability that a game
    will have a score greater than or equal to value."""
    distributions = (np.mean(trial >= value) for trial in trials)
    quantiles = np.quantile(
            np.sort(np.fromiter(distributions, np.float64)),
            [.5 - confidence/2, .5 + confidence/2])
    return quantiles

def dist_ci(scores, generator=None, noise_level=5, confidence=.95):
    """Returns a list of (target, distribution, confidence) pairs, where
    distribution is the estimated probability that the agent will achieve
    greater than or equal to target, and confidence is the confidence
    interval of this estimated probability. Targets are from [16, 32,
    64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]."""
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
    """Returns the percent confidence that median is the exact expected
    median score for a given agent."""
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
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
            description=('Play a series of 2048 games using an AI player '
            'in a curses environment, calculating the expected '
            'performance over the duration of the series.'))
    parser.add_argument('--agent', '-a', help='name of agent', type=select_agent)
    parser.add_argument('--screenshot', '-s', action='store_true',
            help='[DEVELOPER OPTION] store a screenshot of the console after every move')
    parser.add_argument('--list-agents', action='store_true',
            help='list available agents and exit')
    return vars(parser.parse_args())

def select_agent(agent):
    """Select agent based on class-name."""
    if agent in twentysolver.agent.__dict__:
        return twentysolver.agent.__dict__[agent]
    if agent in twentysolver.player_agent.__dict__:
        return twentysolver.player_agent.__dict__[agent]
    raise ValueError

def list_agents():
    """Print a list of known agent classes."""
    print('Available agents:', ', '.join(name for name, cls in twentysolver.agent.__dict__.items()
        if callable(getattr(cls, 'get_move', None))))
    # print(', '.join(obj.__name__
    #     for obj in twentysolver.agent.__dict__
    #     if callable(getattr(obj, 'get_move', None))))


def main(stdscr, screenshot=False, **kwargs):
    """Main program loop."""
    displayer = CursesDisplayer(stdscr)
    agent = kwargs['agent']
    play_series(displayer, agent=agent, screenshot=screenshot)
    displayer.wait()

def get_win_id():
    """Gets the X-windows id of the current window."""
    xdotool = subprocess.run(['xdotool', 'getactivewindow'], capture_output=True)
    return xdotool.stdout.decode('utf8').strip()

def take_screenshot(agent):
    """Generator taking a screenshot of the current window. Requires
    imagemagick to be installed."""
    today = datetime.datetime.today()
    game_name = f'{type(agent).__name__}_{today.strftime("%b%d-%I%M")}'
    move_no = 0
    winid = get_win_id()
    while True:
        subprocess.run(['import', '-window', winid, f'screenshots/{game_name}_{move_no:05d}.gif'])
        move_no += 1
        yield None

if __name__ == '__main__':
    parsed_args = parseargs()
    if 'list_agents' in parsed_args:
        list_agents()
    else:
        curses.wrapper(main, **parsed_args)
