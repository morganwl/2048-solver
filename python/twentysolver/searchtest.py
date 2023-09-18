"""Generate complete search trees to a given depth and output as json strings."""

from collections import namedtuple
from enum import Enum, auto
import json

from twentysolver.grid import Grid

Entry = namedtuple('Entry', ('move', 'grid'))
Record = namedtuple('Record', ('grid', 'movetype', 'children'))

class MoveType(Enum):
    """Three types of moves can be made, one by the player, one by the
    opponent, and one as a result of chance."""
    PLAYER = auto()
    OPPONENT = auto()
    CHANCE = auto()

def search_max(records, entry, depth):
    """Append a record for a player move to records, and continue search
    until depth equals 0."""
    children = list(entry.grid.get_available_moves())
    record = {
            'key': (entry.move, entry.grid.as_list()),
            'movetype': 'PLAYER',
            'children': [(move, grid.as_list()) for move, grid in children],
            }
    records.append(record)
    if depth > 1:
        for e in children:
            search_min(records, Entry(*e), depth-1)

def search_min(records, entry, depth):
    """Append a record for an opponent move to records, and continue search
    until depth equals 0."""
    children = list(entry.grid.get_available_cells())
    record = {
            'key': (entry.move, entry.grid.as_list()),
            'movetype': 'OPPONENT',
            'children': [(cell, entry.grid.as_list()) for cell in children],
            }
    records.append(record)
    if depth > 1:
        for cell in children:
            search_expect(records, Entry(cell, entry.grid), depth-1)

def search_expect(records, entry, depth):
    """Append a record for a chance move to records, and continue search
    until depth equals 0."""
    children = [((entry.move, v), entry.grid.insert_tile(entry.move, v)) for v in [2,4]]
    record = {
            'key': (entry.move, entry.grid.as_list()),
            'movetype':  'CHANCE',
            'children': [((entry.move, v), entry.grid.insert_tile(entry.move, v).as_list())
                for v in [2,4]],
            }
    records.append(record)
    if depth > 1:
        for (cell, val), grid in children:
            search_max(records, Entry((cell, val), grid), depth-1)

def search(grid, depth):
    """Construct search tree from grid to a specified depth, and return
    it as a json string."""
    records = []
    search_max(records, Entry(None, grid), depth)
    return json.dumps(records)

def from_json(s):
    """Loads the json output of search and returns a mapping of (move, grid)
    tuples to search records."""
    records = json.loads(s)
    records = [parse_record(record) for record in records]
    mapping = dict(records)
    return mapping, records[0][0]

def parse_record(record):
    """Parses a single record as loaded from json and returns it as a Record object."""
    move, grid = record['key']
    movetype = MoveType[record['movetype']]
    key = deep_tuple(move), str(grid)
    grid = Grid.from_list(grid)
    children = [(deep_tuple(move), str(grid))
            for move, grid in record['children']]
    return key, Record(grid, movetype, children)

def deep_tuple(val):
    """Convert a nested list of unknown depth to nested tuples."""
    return tuple(deep_tuple(v) for v in val) if isinstance(val, list) else val
