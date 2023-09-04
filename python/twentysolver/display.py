try:
    import curses
except ModuleNotFoundError:
    NoCurses = True
else:
    NoCurses = False
from math import log2

GRIDWIDTH = 7*4
GRIDHEIGHT = 4*4

COLORS = {
        0: curses.COLOR_BLACK,
        2: curses.COLOR_WHITE & curses.A_DIM,
        4: curses.COLOR_WHITE,
        8: curses.COLOR_WHITE & curses.A_BOLD,
        }

class CursesDisplayer:
    windows = [
            [('headscr', 1, 0),],
            [
                ('grhdscr', 1, GRIDWIDTH),
                ('gmhdscr', 0, 0),
                ('srhdscr', 0, 0),
                ],
            [
                ('gridscr', GRIDHEIGHT, GRIDWIDTH),
                ('gamescr', 0, 0),
                ('sersscr', 0, 0),
                ],
            [('statscr', 2, 0)],
            [('infoscr', 0, 0)],
            ]
    def __init__(self):
        self.stdscr = curses.initscr()
        self.stdscr.nodelay(True)
        curses.noecho()
        curses.curs_set(False)
        y,x = 0, 0
        for row in self.windows:
            height = 0
            for i, (n, h, w) in enumerate(row):
                if not h:
                    if height:
                        h = height
                    else:
                        h = curses.LINES - y
                if not height:
                    height = h
                if not w:
                    w = int((curses.COLS - x) / (len(row) - i))
                setattr(self, n, curses.newwin(h, w, y, x))
                x += w
            y += height
            x = 0
        self.infoscr.scrollok(True)
        self.gamescr.scrollok(True)
        self.sersscr.scrollok(True)
        self.init_colors()
        self.init_headers()

    def init_colors(self):
        """Initialize one color pair for each log value from 1 to 16."""
        curses.start_color()
        for p, color in enumerate([
            (curses.COLOR_BLACK, curses.COLOR_WHITE),
            (curses.COLOR_WHITE, curses.COLOR_BLACK),
            (curses.COLOR_YELLOW, curses.COLOR_WHITE),
            (curses.COLOR_MAGENTA, curses.COLOR_WHITE),
            (curses.COLOR_BLUE, curses.COLOR_WHITE),
            (curses.COLOR_CYAN, curses.COLOR_WHITE),
            (curses.COLOR_GREEN, curses.COLOR_WHITE),
            (curses.COLOR_GREEN, curses.COLOR_WHITE),
                ], 1):
            curses.init_pair(p, *color)

    def display(self, grid):
        for i in range(4):
            for j in range(4):
                val = grid.get_cell_value(j,i)
                l = int(log2(val)) if val > 0 else 0
                color = curses.color_pair((l+3) // 2) | curses.A_REVERSE | curses.A_BOLD
                if l % 2 == 1:
                    color |= curses.A_DIM
                self.gridscr.addstr(4*i, 7*j+1, f'{"":^6s}', color)
                self.gridscr.addstr(4*i+1, 7*j+1, f'{val:^ 6d}', color)
                self.gridscr.addstr(4*i+2, 7*j+1, f'{"":^6s}', color)
        self.gridscr.refresh()

    def print_player_move(self, move):
        moves = {i: m for i, m in enumerate(['Right', 'Down', 'Left', 'Up'])}
        moves[None] = 'None'
        self.statscr.addstr(0, 2, f'Player move: {moves[move]:8s}')
        self.statscr.refresh()

    def print_computer_move(self, cell):
        self.statscr.addstr(0, curses.COLS - 23, f'Computer move: {str(cell):6s}')
        self.statscr.refresh()

    def print_info(self, text):
        y,x = self.infoscr.getyx()
        self.infoscr.scroll(-(y+1))
        self.infoscr.addstr(0,0, str(text))
        self.infoscr.refresh()

    def init_headers(self):
        self.gmhdscr.addstr(0,1, f'{"n":>4s} {"time":>6s} {"val":>8s}', curses.A_UNDERLINE)
        self.srhdscr.addstr(0,1, f'{"moves":>5s} {"mtime":>6s} {"score":>5s}', curses.A_UNDERLINE)
        self.gmhdscr.refresh()
        self.srhdscr.refresh()

    def print_move_info(self, moves, mtime, val):
        y,x = self.gamescr.getyx()
        self.gamescr.scroll(-(y+1))
        self.gamescr.addstr(0,1, f'{moves:>4d} {mtime/1e9:>6.4f} {val:>8.2f}')
        self.gamescr.refresh()

    def print_game_info(self, no_moves, avg_mtime, score):
        y,x = self.sersscr.getyx()
        self.sersscr.scroll(-(y+1))
        self.sersscr.addstr(0,1, f'{no_moves: 5d} {avg_mtime/1e9: 6.4f} {score: 5d}')
        self.sersscr.refresh()

    def wait(self):
        self.infoscr.getch()

    def getch(self):
        return self.stdscr.getch()

    def __del__(self):
        self.wait()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
