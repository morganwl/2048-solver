try:
    import curses
except ModuleNotFoundError:
    NoCurses = True
else:
    NoCurses = False

GRIDWIDTH = 6*4
GRIDHEIGHT = 3*4

class CursesDisplayer:
    windows = [
            [('headscr', 1, 0),],
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
                print(n, h, w, y, x)
                setattr(self, n, curses.newwin(h, w, y, x))
                x += w
            y += height
            x = 0
        self.infoscr.scrollok(True)
        self.gamescr.scrollok(True)
        self.sersscr.scrollok(True)

    def display(self, grid):
        for i in range(4):
            for j in range(4):
                self.gridscr.addstr(3*i + 1, 6*j, f'{grid.get_cell_value(j,i): 5d}')
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

    def print_move_info(self, mtime, val):
        y,x = self.gamescr.getyx()
        self.gamescr.scroll(-(y+1))
        self.gamescr.addstr(0,0, f'{mtime/1e9: 3.4f} {val: 6.4f}')
        self.gamescr.refresh()

    def print_game_info(self, no_moves, avg_mtime, score):
        y,x = self.sersscr.getyx()
        self.sersscr.scroll(-(y+1))
        self.sersscr.addstr(0,0, f'{no_moves: 5d} {avg_mtime/1e9: 3.4f} {score: 5d}')
        self.sersscr.refresh()

    def wait(self):
        self.infoscr.getch()

    def __del__(self):
        self.wait()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
