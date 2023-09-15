"""Generate complete search trees to a given depth and output as json strings."""

from collections import namedtuple
from enum import Enum
import json



Entry = namedtuple('Entry', ('move', 'grid'))

def search(grid, depth):
    """Construct search tree from grid to a specified depth, and return
    it as a json string."""
    nodes = []
    frontier = [Key(None, grid)]
    while frontier:
        entry = frontier.pop()

        node = handle(entry, depth)
    return json.dumps(nodes)
