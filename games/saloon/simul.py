from copy import deepcopy
from collections import namedtuple

Furnishings = namedtuple('Furnishing', 'tile health is_piano is_playing'.split())
Bottle = namedtuple('Bottle', 'tile direction drunk_direction'.split())
Cowboy = namedtuple('Cowboy', 'tile health is_drunk drunk_direction job owner turns_busy'.split())
Tile = namedtuple('Tile', 'x y bottle cowboy furnishing has_hazard is_balcony neighbors'.split())
Board = namedtuple('Board', 'tiles cowboys bottles furnishings'.split()))
Node = namedtuple('Node', 'score board turn player'.split())

_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
_dirs_to_offset = {'east': (1, 0), 'south': (0, 1), 'west': (-1, 0), 'north': (0, -1)}

def now_state(ai):
    """ Generate a copy of the current state """
    tiles = {}
    for tile in ai.game.tiles:
        tiles[tile.x, tile.y] = Tile(tile.x, tile.y,
                None, None, None, tile.has_hazard, tile.is_balcony, [])
    for tile in ai.game.tiles.values:
        tile.neighbors = [tiles[x+xo, y+yo] for xo, yo in _offsets if (x+xo, y+yo) in tiles]
    cowboys = []
    for c in ai.game.cowboys:
        if c.is_dead:
            continue
        cowboy = Cowboy(tiles[c.tile.x, c.tile.y], c.health, c.is_drunk,
                c.drunk_direction, c.job, int(c.owner.id), c.turns_busy)
        cowboy.tile.cowboy = cowboy
        cowboys.append(Cowboy)
    bottles = []
    for b in ai.game.bottles:
        bottle = Bottle(tiles[b.tile.x, b.tile.y], b.direction, b.drunk_direction)
        bottle.tile.bottle = bottle
        bottles.append(bottle)
    furnishings = []
    for f in ai.game.furnishings:
        if f.is_destroyed:
            continue
        furn = Furnishing(tiles[f.tile.x, f.tile.y], f.health, f.is_piano, f.is_playing)
        furn.tile.furnishing = furn
        furnishings.append(furn)
    board = Board(tiles, cowboys, bottles, furnishings)
    node = Node(score(board), board, ai.game.current_turn, int(ai.player.id)))


def score(ai, board):
    # Player score
    # Average distance from cowboy to piano
    for cowboy in board.cowboys:
        if cowboy.owner == int(ai.player.id):

            

def advance_state(state):
    board = state.board
    for bottle in state.board.bottles:
        next_pos = _dirs_to_offset[bottle.direction.lower()]
        if next_pos in board.tiles:
            next_tile = board.tiles[next_pos]
            broke = False
            if next_tile.cowboy:
                broke = True
                next_tile.cowboy.is_drunk = True
                next_tile.cowboy.drunk_direction = bottle.drunk_direction
                next_tile.cowboy.turns_busy = 5
    for cowboy in state.board.cowboys:
        t = cowboy.tile
        if 

def next_state(state):



def safe_path(ai, cowboys, wall_func, goal_func):
    


