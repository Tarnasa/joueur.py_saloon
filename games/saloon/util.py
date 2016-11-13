from collections import deque


def follow(parent_dict, start):
    """
    Yields a path starting at start, and following parent_dict[start]
    """
    try:
        yield start
        while True:
            start = parent_dict[start]
            if start:
                yield start
    except KeyError:
        pass


def _bfs_neighbors(tile):
    yield from tile.neighbors
def bfs(start, goal_func, wall_func, hor=False):
    neighbors = _bfs_neighbors
    if hor:
        def neighbors(tile):
            yield from tile.hor_neighbors
    frontier = deque()
    frontier.append(start)
    parents = {start: None}
    while frontier:
        top = frontier.popleft()
        if goal_func(top):
            return list(reversed(list(follow(parents, top))))
        for neighbor in neighbors(top):
            if wall_func(neighbor) and not goal_func(neighbor):
                continue
            if neighbor not in parents:
                frontier.append(neighbor)
                parents[neighbor] = top


def cowboy_bfs(cowboy, goal_func):
    def wall_func(tile):
        return (tile.furnishing or tile.is_balcony\
                or (tile.cowboy and (tile.cowboy.owner != cowboy.owner\
                or not tile.cowboy.can_move)))
    return bfs(cowboy.tile, goal_func, wall_func)



def wall_func(tile):
    return tile.furnishing or tile.is_balcony or tile.cowboy


def shortest_pairs(starts, goals, stack=True):
    """
    Finds the pairing of starts with goals with the smallest total distance
    Prereq: len(goals) <= len(starts)
    If stack == True, then after every goal is filled, start filling with 2 units
    """
    #TODO: Hungarian algorithm (lol as if)
    target = {}
    starts = list(starts)
    while True:
        for goal in goals:
            if not starts:
                break
            start = min(starts, key=lambda start: start.distance(goal))
            target[start] = goal
            starts.remove(start)
        if not starts or not stack:
            break
    return target



def alignment(tile, other):
    return min(abs(tile.x - other.x), abs(tile.y - other.y))

def sign(x):
    return (x > 0) - (x < 0)

def toward(start, target):
    dx = target.x - start.x
    dy = target.y - start.y
    if dx >= abs(dy):
        return start.tile_east
    elif dy > abs(dx):
        return start.tile_south
    elif -dx >= abs(dy):
        return start.tile_west
    elif -dy > abs(dx):
        return start.tile_north
    #return None
    return start.tile_east

def flood_path(starts, wall_func):
    """ Returns a dict mapping a tile to it's next tile which is closest to a start """
    frontier = deque(starts)
    parents = {t: t for t in starts}
    while frontier:
        top = frontier.popleft()
        for neighbor in top.neighbors:
            if not wall_func(neighbor) and neighbor not in parents:
                frontier.append(neighbor)
                parents[neighbor] = top
    return parents

def flood_path_fast(starts, wall_func):
    """ Returns a dict mapping a tile to it's next tile which is closest to a start """
    frontier = deque(starts)
    parents = {t: t for t in starts}
    try:
        while True:
            top = frontier.popleft()
            for neighbor in top.neighbors:
                if not wall_func(neighbor) and neighbor not in parents:
                    frontier.append(neighbor)
                    parents[neighbor] = top
    except IndexError:
        pass
    return parents

def transpose(direction):
    if direction.lower() in ['north', 'south']:
        return ['west', 'east']
    return ['north', 'south']

_opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
def opposite(direction):
    return _opposite[direction.lower()]

_dirs = ['north', 'south', 'east', 'west']
def safe(tile):
    # TODO: Watch for bottle already on tile when it gets implemented
    if not tile._is_balcony and not tile.furnishing and not tile.cowboy:
        for dir in _dirs:
            n = tile.get_dir(dir)
            if n:
                if n.bottle and n.bottle.direction.lower() == opposite(dir):
                    return False
                n = n.get_dir(dir)
                if n:
                    if n.bottle and n.bottle.direction.lower() == opposite(dir):
                        return False
        return True
    return False

def get_spawn_tile(player):
    t = player.young_gun.tile
    if t.x == 0:
        if t.y == 0:
            return t.tile_south.tile_east
        elif t.y == 11:
            return t.tile_north.tile_east
    elif t.x == 21:
        if t.y == 0:
            return t.tile_south.tile_west
        elif t.y == 11:
            return t.tile_north.tile_west
    for n in t.neighbors:
        if not n._is_balcony:
            return n

def is_near_enemy_piano(tile, ai, threshold=2):
    if tile.cowboy:
        return False
    for neighbor in tile.neighbors:
        if neighbor.furnishing and neighbor.furnishing._is_piano:
            enemies = 0
            for n2 in neighbor.neighbors:
                if n2.cowboy and n2.cowboy.owner != ai.player:
                    enemies += 1
                    if enemies >= threshold:
                        return True
    return False

def classify_pianos(ai):
    """ Sets the piano.owner based on position """
    half = len(ai.pianos) // 2
    ordered_pianos = list(sorted(ai.pianos, key=lambda piano: piano.tile.x))
    if ai.player.id == '0':
        for piano in ordered_pianos[:half]:
            piano.owner = ai.player
        for piano in ordered_pianos[half:]:
            piano.owner = ai.player.opponent
    if ai.player.id == '1':
        for piano in ordered_pianos[:half]:
            piano.owner = ai.player.opponent
        for piano in ordered_pianos[half:]:
            piano.owner = ai.player

def set_tile_piano(ai):
    for tile in ai.game.tiles:
        tile.piano = None
    for furnishing in ai.game.furnishings:
        if furnishing.is_piano:
            for n in furnishing.tile.neighbors:
                n.piano = furnishing

def paths_to_all_goals(start, goal_func, wall_func):
    frontier = deque()
    frontier.append(start)
    goals = []
    parents = {start: None}
    while frontier:
        top = frontier.popleft()
        if goal_func(top):
            goals.append((top, list(reversed(list(follow(parents, top))))))
            continue
        for neighbor in top.neighbors:
            if wall_func(neighbor) and not goal_func(neighbor):
                continue
            if neighbor not in parents:
                frontier.append(neighbor)
                parents[neighbor] = top
    return goals

# Tests
if False:
    class MTile(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y
        tile_east = 'east'
        tile_north = 'north'
        tile_west = 'west'
        tile_south = 'south'

    assert toward(MTile(2,2), MTile(3,2)) == 'east'
    assert toward(MTile(2,2), MTile(4,1)) == 'east'
    assert toward(MTile(2,2), MTile(2,1)) == 'north'
    assert toward(MTile(2,2), MTile(1,2)) == 'west'
    assert toward(MTile(2,2), MTile(2,3)) == 'south'

    assert toward(MTile(2,2), MTile(1,1)) in ('west', 'north')
    assert toward(MTile(2,2), MTile(3,1)) in ('east', 'north')
    assert toward(MTile(2,2), MTile(1,3)) in ('west', 'south')
    assert toward(MTile(2,2), MTile(3,3)) in ('east', 'south')

    raise Exception('Yo I\'m done')

