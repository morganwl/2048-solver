# Autonomous 2048 Solver

This is a simple 2048 solver built using adversarial expectimax search.
The solver searches for a move that will lead to the best possible
outcome, assuming that the game makes the move most inconvenient for the
player AI.

![2048 solver, with grid in top left, move log in top center, game log
in top right, and distribution in bottom](images/solver_01.jpg)

## The game of 2048

The game of 2048 presents the player with numeric tiles placed on a 4x4
board.  By sliding the tiles in one of four directions (right, left, up
and down), the player can combine tiles of the same value into a new,
larger tile.

## Gameplay Interface

A session can be started from the command line by running the script
'play.py'. This will play a series of games, displaying statistics over
the course of the session. Proper display requires the _curses_ library,
which is installed on all Linux and MacOS systems, but might not be
present on a Windows system.

### Board window

The game board is shown in the top left. Tiles are color coded by value.

### Move log

The move log is shown in the top center. Each move reports the number of
game states explored, the total search time for that move, and the
estimated value of the selected move.

### Game log

The game log is shown in the top right. Each game reports the total
number of moves made, the average search time for each move, and the
final score.

### Console

Logging information is printed to the console, at the bottom of the
screen. Currently, the console prints estimated score distributions and
an estimated median score after the completion of each game. Score
distributions are reported as the percentage of games achieving a
certain score or higher, with their 95% confidence intervals. The median
is reported with the confidence that this is the exact median score.

#### Confidence Intervals

Confidence intervals are calculated by bootstrapping, i.e. repeatedly
sampling the recorded games, with repetition. Because this repeated
sampling is only meaningful with a sufficiently large number of played
games to sample from, confidence intervals calculated after only a few
games are not likely to be accurate.

One solution is warming up the bootstrap with a number of samples before
reporting any confidence intervals, to ensure a sufficiently large
sample size. Because this is a rather time-consuming process for an
interactive tool, I have chosen an alternative solution --- before
calculating confidence intervals, a number of randomly generated games
are added to the sample space, with a uniform distribution. As the
number of played games grows beyond the noise, the confidence intervals
will start to converge around the tighter distribution of those samples.

#### Why curses?

Windowed terminal applications can seem an anachronism in an era of
graphical interfaces. I chose curses for two reasons. The first was
practical: I still do a great deal of work and testing via ssh. A
curses interface will work on my laptop, my desktop, or via remote
session from my iPad to a Raspberry Pi. The second is purely nostalgia,
for a time when I ran my computer primarily in terminal mode, and played
text-based curses games such as _nethack_. I was curious to explore the
ways in which such interfaces were created.

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
