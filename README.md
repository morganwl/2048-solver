# Autonomous 2048 Solver

This is a simple 2048 solver built using adversarial expectimax search.
The solver searches for a move that will lead to the best possible
outcome, assuming that the game makes the move most inconvenient for the
player AI.

## The game of 2048

The game of 2048 presents the player with numeric tiles placed on a 4x4
board.  By sliding the tiles in one of four directions (right, left, up
and down), the player can combine tiles of the same value into a new,
larger tile.

## Results

### July 16

1.000: 0.133    1.000: 0.133    0.977: 0.183    0.886: 0.217    0.705:
0.250
2048.0 0.961

## Issues

### Game runner

- Need a command line switch for agent selection
- Curses implementation is kludgy
- Status windows need labels
- Needs improved error logging

### Agent

- Try implementing time limit as an interrupt instead of polling
- Try loop-based iteration instead of recursive iteration

### Documentation

- Readme needs more detailed description of game, with references
- Readme needs more detailed description of player interface, with
  screenshots
- Readme needs more detailed description of agent implementations, with
  evaluation
