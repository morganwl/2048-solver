try:
    import curses
except ModuleNotFoundError:
    NoCurses = True
else:
    NoCurses = False

GRIDWIDTH = 5*4
GRIDHEIGHT = 3*4

class CursesDisplayer:
    def __init__(self):
        self.stdscr = curses.initscr()
        self.headscr = curses.newwin(1, curses.COLS, 0, 0)
        self.gridscr = curses.newwin(GRIDHEIGHT, GRIDWIDTH, 1, int(curses.COLS/2 - GRIDWIDTH/2))
        self.statscr = curses.newwin(1, curses.COLS, GRIDHEIGHT+1, 0)
        self.infoscr = curses.newwin(curses.LINES - GRIDHEIGHT - 1, curses.COLS, GRIDHEIGHT+2, 0)
        self.infoscr.scrollok(True)

    def display(self, grid):
        for i in range(4):
            for j in range(4):
                self.gridscr.addstr(3*i + 1, 5*j, f'{grid.get_cell_value(j,i): 4d}')
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

    def wait(self):
        self.infoscr.getch()

    def __del__(self):
        self.wait()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
