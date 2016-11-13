from functools import partial, lru_cache
from collections import OrderedDict, deque

from games.saloon.util import shortest_pairs, cowboy_bfs, transpose, opposite,\
        get_spawn_tile, is_near_enemy_piano, bfs, alignment, paths_to_all_goals,\
        safe, follow
from games.saloon.asciivis import draw_everything, general_tile_func


_dirs = ['east', 'north', 'west', 'south']

def best_drunk_direction(target_tile):
    """
    Return direction which has closest furn/wall
    If a piano is found in a direction but no wall, then return direction away from piano
    """
    best = None, 5
    for direction in _dirs:
        tile = target_tile
        for distance in range(best[1]):
            tile = tile.get_dir(direction)
            if not tile:
                break
            if tile.furnishing and tile.furnishing.is_piano:
                best = opposite(direction), distance
                break
            if tile.furnishing or tile.is_balcony:
                best = direction, distance
                break
    if best[0] is not None:
        return best[0]
    return 'east'

def best_bang_direction(sharpshooter):
    """
    Returns the direction with the most enemies, and no allies.
    Or None if no good shot.
    """
    best = None, 0
    for direction in _dirs:
        tile = sharpshooter.tile
        enemies = 0
        for _ in range(sharpshooter.focus):
            tile = tile.get_dir(direction)
            if not tile:
                break
            if tile.cowboy:
                if tile.cowboy.owner == sharpshooter.owner:
                    enemies -= 3
                else:
                    enemies += 1
            if tile.furnishing and tile.furnishing._is_piano:
                for n in tile.neighbors:
                    if n.cowboy:
                        if n.cowboy.owner != sharpshooter.owner:
                            enemies += 1
                        else:
                            enemies -= 1
        if enemies > best[1]:
            best = direction, enemies
    return best[0]

def spawn_everything(ai):
    t = get_spawn_tile(ai.player)
    # Don't spawn on pianos TODO: unless lots of enemies there
    if t.furnishing and t.furnishing._is_piano:
        return
    # Don't spawn on friendly cowboys
    if t.cowboy and t.cowboy.owner == ai.player:
        return
    for job in ai.game.jobs:
        if sum(1 for c in ai.player.cowboys if c.job == job) < ai.game.max_cowboys_per_job:
            ai.player.young_gun.call_in(job)
            break

def good_sharpshooter_spots(ai, spots):
    sharpshooter_spots = list()
    left = ai.player.id == '0'
    for spot in spots:
        if spot.piano.owner == ai.player:
            score = 0
            for piano in ai.pianos:
                if alignment(spot, piano.tile) == 0:
                    if (piano.tile.x > spot.x) == (left):
                        if piano.owner != ai.player:
                            score += 1
                        else:
                            score -= 1
            if score > 0:
                sharpshooter_spots.append((score, spot))
    # Sort sharpshooter spots
    xm = 1 if left else -1
    sharpshooter_spots.sort(key=lambda t: (t[0], t[1].x * xm), reverse=True)  # Highest first, then futhest forward
    return sharpshooter_spots

def assign_pianos(ai):
    """
    Assign each available cowboy to a piano
    Prefer staying at a piano if you are the only one
    Prefer assigning sharpshooters to spots which align with an enemy piano so they
      can shoot it later
    Prefer assigining sharpshooters to spots which don't shoot our own stuff
    Prefer assigning brawlers to enemy pianos
    """
    cowboys = [c for c in ai.player.cowboys if c.can_move and not c._is_dead]
    spots = list()
    for piano in ai.pianos:
        for n in piano.tile.neighbors:
            if (not n.cowboy or n.cowboy.owner == ai.player) and\
                    not n.furnishing and not n.is_balcony and not n.has_hazard:
                spots.append(n)

    assignments = OrderedDict()

    # Find best spots for brawlers
    left = ai.player.id == '0'
    xm = -1 if left else 1
    brawler_spots = list(sorted(((s.x * xm, s) for s in spots if s.piano.owner != ai.player),
        key=lambda p: p[0]))
    brawler_spots = [s for s in spots if s.piano.owner != ai.player]

    # Assign brawlers
    brawlers = [c for c in cowboys if c.job == 'Brawler']
    def goal_func(t):
        return t in brawler_spots
    for brawler in brawlers:  # TODO: Wait to spawn brawlers until they align with enemy pianos/spots
        if brawler_spots:
            path = cowboy_bfs(brawler, goal_func)
            if path:
                spot = path[-1]
                assignments[brawler] = spot
                brawler_spots.remove(spot)
                spots.remove(spot)

    # Find good sharpshooter spots
    sharpshooter_spots = good_sharpshooter_spots(ai, spots)
    # Assign sharpshooters
    sharpshooters = [c for c in cowboys if c.job == 'Sharpshooter']
    def wall_func(t):
        return t.is_balcony or t.has_hazard or t.furnishing or (t.cowboy and\
                t.cowboy.owner != ai.player)
    for score, spot in sharpshooter_spots:
        if not sharpshooters:
            break
        path = bfs(spot, lambda t: t.cowboy in sharpshooters, wall_func)
        if path:
            sharpshooter = path[-1].cowboy
            assignments[sharpshooter] = spot
            sharpshooter_spots.remove((score, spot))
            for n in spot.piano.tile.neighbors:
                if n in spots:
                    spots.remove(n)
                if n in sharpshooter_spots:
                    sharpshooter_spots.remove(n)

    def free(c):
        if getattr(c.tile, 'piano', None):
            count = 0
            for n in c.tile.piano.tile.neighbors:
                if n.cowboy and n.cowboy.owner == ai.player and\
                        (n.cowboy not in assignments or assignments[n.cowboy] == n):
                    count += 1
            return count != 1
        return True

    # Order cowboys Sharp, Bart, Brawler
    order = ['Sharpshooter', 'Bartender', 'Brawler']
    cowboys = sorted(ai.player.cowboys, key=lambda c: order.index(c.job))
    # Try to allocate the rest
    for cowboy in cowboys:
        if cowboy._is_dead or not cowboy.can_move or cowboy not in cowboys or not free(cowboy):
            continue
        if not spots:
            break
        def goal_func(t):
            return t in spots
        path = cowboy_bfs(cowboy, goal_func)
        if path:
            spot = path[-1]
            assignments[cowboy] = spot
            for n in spot.piano.tile.neighbors:
                if n in spots:
                    spots.remove(n)
    return assignments

"""
def free(c):
    if getattr(c.tile, 'piano', None):
        count = 0
        for n in c.tile.piano.tile.neighbors:
            if n.cowboy and n.cowboy.owner == ai.player:
                count += 1
        return count != 1
    return True
"""

def move_over(ai, cowboy, bully):
    if not cowboy.can_move:
        return False
    pianos = [n for n in cowboy.tile.neighbors if n.furnishing and n.furnishing._is_piano]
    for piano in pianos:
        # Move to another spot on the piano
        for n in piano.neighbors:
            if not n.furnishing and not n.is_balcony and not n.cowboy:
                path = cowboy_bfs(cowboy, lambda t: t == n)
                if path and len(path) == 3: # Only to close open spots
                    return cowboy.move(path[1])
    # Try to move to preferred location
    if cowboy.preferred:
        p = cowboy.preferred
        if not p.furnishing and not p.is_balcony and not p.cowboy:
            return cowboy.move(p)
    # Just move away
    for n in cowboy.tile.neighbors:
        if not n.furnishing and not n.is_balcony and not n.cowboy:
            return cowboy.move(n)
    else:
        return False


def _avoid_bottle(ai, bottle, cowboy):
    if not cowboy.can_move:
        return False
    try_directions = transpose(bottle._direction) + [bottle._direction]
    for tdir in try_directions:
        tt = cowboy.tile.get_dir(tdir)
        if not tt.is_balcony and not tt.furnishing and not tt.cowboy:
            if cowboy.move(tt):
                print(cowboy.id, 'Dodged!', tdir)
                return True
    else:  # Try to force our own cowboys out of the way
        for tdir in try_directions:
            tt = cowboy.tile.get_dir(tdir)
            if not tt.is_balcony and not tt.furnishing and tt.cowboy and tt.cowboy.owner == ai.player:
                if move_over(ai, tt.cowboy, cowboy):
                    print(cowboy.id, 'Moved to help dodge')
                    if cowboy.move(tt):
                        print(cowboy.id, 'Dodged!', tdir)
                        return True
        else:
            print(cowboy.id, 'You gonna get rekt son')
    return False


def avoid_bottles(ai):
    for bottle in ai.game.bottles:
        if not bottle._is_destroyed:
            n = bottle.tile.get_dir(bottle._direction)
            if n:
                n2 = n.get_dir(bottle._direction)  # Bottles move twice between our turns
                if n2 and n2.cowboy and n2.cowboy.owner == ai.player:
                    _avoid_bottle(ai, bottle, n2.cowboy)
                if n.cowboy and n.cowboy.owner == ai.player:
                    _avoid_bottle(ai, bottle, n.cowboy)  # TODO: Don't try opposite for this guy, because he'll get rekt anyway


def get_spawn_distance_to_enemy_piano(ai, threshold=1):
    """ Returns the best distance from my young gun to a slot on an enemy piano """
    spots = []
    for piano in ai.pianos:
        enemies = sum(1 for n in piano.tile.neighbors if n.cowboy and n.cowboy.owner != ai.player)
        if enemies >= threshold:
            for neighbor in piano.tile.neighbors:
                if not neighbor.cowboy:
                    spots.append(neighbor)
    path = bfs(get_spawn_tile(ai.player),
            goal_func=lambda t: t in spots,
            wall_func=lambda t: t.furnishing or t.cowboy or t._is_balcony)
    if path:
        return len(path)
    else:
        return 9999

def brawl_enemy_pianos(ai):
    """ Move your brawlers toward enemy pianos, play them """
    for brawler in ai.player.cowboys:
        if brawler.job == 'Brawler' and not brawler._is_dead and brawler._can_move:
            print('b2')

            def is_near_enemy_piano(tile, threshold=2):
                if tile.cowboy and tile.cowboy is not brawler:
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

            path = cowboy_bfs(brawler, is_near_enemy_piano)
            if path and len(path) > 1:
                print('b3')
                brawler.move_pref(path[1])  # TODO: Outaway

def play_pianos(ai):
    for cowboy in ai.player.cowboys:
        if cowboy._is_dead or cowboy.turns_busy:
            continue
        for neighbor in cowboy.tile.neighbors:
            if neighbor.furnishing and neighbor.furnishing.is_piano and\
                    not neighbor.furnishing.is_playing:
                cowboy.play(neighbor.furnishing)
                break

def shoot_enemy_pianos(ai):
    """ When a sharpshooter has waited long enough, tell him to move and shoot the enemy piano """
    sharpshooters = [c for c in ai.player.cowboys if not c._is_dead and
            c.job == 'Sharpshooter' and c.turns_busy == 0]
    for c in sharpshooters:
        dir = best_bang_direction(c)
        if dir:
            if c.act(c.tile.get_dir(dir)):
                print('Bang!') # TODO: Remove
            else:
                print('Failed bang')

def best_throw_direction(bartender):
    """
    Returns the direction with the most enemies, and no allies.
    Or None if no good shot.
    """
    best = None, 15, None
    for direction in _dirs:
        tile = bartender.tile
        for distance in range(best[1]):
            tile = tile.get_dir(direction)
            if not tile:
                break
            if tile.furnishing or tile.is_balcony:
                break
            if tile.cowboy:
                if tile.cowboy.owner == bartender.owner:
                    break
                else:
                    best = direction, distance, tile.cowboy
                    break
    return best[0], best[2]

def move_throw_beer(ai):
    for cowboy in ai.player.cowboys:
        if cowboy.job == 'Bartender' and not cowboy._is_dead:
            direction, enemy = best_throw_direction(cowboy)
            if direction:
                if cowboy.act(direction, best_drunk_direction(enemy.tile)):
                    print(cowboy.id, 'Throw at enemy')
                else:
                    print(cowboy.id, 'Failed to throw')
                    # TODO: Move
            else:
                path = bfs(cowboy.tile, lambda t: t.cowboy and t.cowboy.owner != ai.player, wall_func)
                cowboy.act(cowboy.tile.get_dir('north'), '')
                if path:
                    if cowboy.can_move and len(path) > 2:
                        cowboy.move(path[1])

def move_to(ai, cowboy, goal_func):
    path = cowboy_bfs(cowboy, goal_func)
    if path and len(path) > 1:
        target = path[1]
        if target.cowboy and target.cowboy.owner == cowboy.owner:
            if move_over(ai, target.cowboy, cowboy):
                cowboy.move(target)
        if not target.cowboy:
            cowboy.move(target)

def generate_starting_assignments(ai):
    """
    Grab nearest 6 pianos
    Order pianos by X
    Assign first spawn to nearest in X
    Order pianos by Y
    Assign subsequent spawns, farthest Y first

    After assigning spawns, assign roles to each spawn, based on distance
    Assign Brawlers to further pianos
    Assign sharpshooters to good sharpshooter pianos
    Assign sharpshooters and bartenders to nearest pianos
    Every unit must move down on their first turn
        This should be guaranteed by the pather, and the assignment above

    Set cowboy.assignment to that piano
    """
    left = ai.player.id == '0'
    m = 1 if left else -1

    pianos = [f for f in ai.game.furnishings if not f.is_destroyed and f.is_piano]
    # Find all pianos and their distances to spawn
    spawn = ai.player.young_gun.call_in_tile
    def goal_func(t):
        return t.furnishing and t.furnishing.is_piano
    def wall_func(t):
        return t.furnishing or t.is_balcony
    piano_paths = paths_to_all_goals(spawn, goal_func, wall_func)
    # Choose only 6 closest
    piano_paths = list(sorted(((goal, path) for goal, path in piano_paths),
        key=lambda p: len(p[1])))[:6]
    # Pick nearest X
    x_pianos = list(sorted(((goal, path) for goal, path in piano_paths),
            key=lambda p: -p[0].x*m))
    goal_pianos = [x_pianos[0]]
    # Recalculate X path to use hor movement
    new_path  = bfs(spawn, goal_func, wall_func, hor=True)
    goal_pianos = [(new_path[-1], new_path)]
    # Order rest by -Y
    y_pianos = list(sorted(((goal, path) for goal, path in piano_paths if goal != goal_pianos[0][0]),
            key=lambda p: -p[0].y*m))
    goal_pianos.extend(y_pianos)

    goal_pianos = list(sorted(((goal, path) for goal, path in piano_paths),
            key=lambda p: -p[0].y*m))

    # Assign spawns
    return list(zip(goal_pianos, ['Sharpshooter', 'Sharpshooter', 'Bartender', 'Bartender', 'Brawler', 'Brawler']))

def generate_assignments(ai):
    """
    Find all pairs paths
    Pop cowboy with the longest shortest path
    assign

    NOTE: Need to make sure to order my spawns so that brawlers get assigned the farthest pianos
    """



    
def move_starting_cowboys(ai):
    """
    Uses generate_starting_assignments 
    """
    cowboys_to_do = deque(reversed(ai.player.cowboys))
    #print(' '.join(str(c.id) for c in cowboys_to_do))
    while cowboys_to_do:
        cowboy = cowboys_to_do.pop()
        if not cowboy.can_move:
            continue
        # Move to assignment
        path = cowboy.assignment
        try:
            i = path.index(cowboy.tile)
            if i < len(path) - 2:
                target = path[i + 1]
                if not safe(target):  # Bottle gonna hit there
                    new_path = safe_bfs(ai, cowboy.tile)
                    if new_path and len(new_path) < len(path) + 3:
                        cowboy.assignment = new_path
                        cowboy.move(new_path[1])
                elif target.cowboy:
                    # Swap assignments if he has not moved yet
                    blocker = target.cowboy
                    if blocker.owner == cowboy.owner and blocker.can_move:
                        print("Swap {} {}".format(cowboy.id, blocker.id))
                        blocker.assignment, cowboy.assignment = cowboy.assignment, blocker.assignment
                        #cowboys_to_do.append(blocker)
                        #cowboys_to_do.append(cowboy)
                        try:
                            i = blocker.assignment.index(blocker.tile)
                            blocker.move(blocker.assignment[i + 1])
                        except ValueError:
                            pass
                        try:  # Use old path
                            i = blocker.assignment.index(cowboy.tile)
                            cowboy.move(blocker.assignment[i + 1])
                        except ValueError:
                            pass
                    elif cowboy.job == 'Bartender' and blocker.owner != cowboy.owner:
                        throw_dir, target = best_throw_direction(cowboy)
                        if throw_dir:
                            cowboy.act(cowboy.tile.get_dir(throw_dir), best_drunk_direction(target.tile))
                        else:
                            # Recalculate path to the same goal
                            def goal_func(t):
                                return t == path[-1]
                            def wall_func(t):
                                return t.cowboy or t.furnishing or t.is_balcony
                            path = bfs(cowboy.tile, goal_func, wall_func)
                            if path and len(path) < len(cowboy.assignment) + 2:
                                cowboy.assignment = path
                                cowboy.move(path[1])
                                print('Throw Recalc')
                    else:
                        # Recalculate path to the same goal
                        def goal_func(t):
                            return t == path[-1]
                        def wall_func(t):
                            return t.cowboy or t.furnishing or t.is_balcony
                        path = bfs(cowboy.tile, goal_func, wall_func)
                        if path and len(path) < len(cowboy.assignment) + 2:
                            cowboy.assignment = path
                            cowboy.move(path[1])
                            print('Recalc')
                elif not target.furnishing:
                    cowboy.move(path[i + 1])
                # Throw bottles if far away from target piano
                if cowboy.job == 'Bartender':
                    if len(cowboy.assignment) - i > 4:
                        throw_dir, target = best_throw_direction(cowboy)
                        if throw_dir:
                            cowboy.act(cowboy.tile.get_dir(throw_dir), best_drunk_direction(target.tile))

            elif i == len(path) - 1:  # We reached the end of our path
                # Find a new target
                path = safe_bfs(ai, cowboy.tile)
                if path:
                    cowboy.assignment = path
                    cowboy.move(path[1])
                else:  # No path found
                    pass  # TODO attack
            else: # Play the piano we are assigned to
                if not safe(cowboy.tile):  # Bottle gonna hit there
                    new_path = safe_bfs(ai, cowboy.tile)
                    if new_path and len(new_path) < len(path) + 3:
                        cowboy.assignment = new_path
                        cowboy.move(new_path[1])
                target = path[-1]
                if target.furnishing and target.furnishing.is_piano:
                    if target.furnishing.is_playing:
                        cowboy.play(path[-1])
                else:  # We broke out piano, or something wierd happened
                    # Find a new target
                    path = safe_bfs(ai, cowboy.tile)
                    if path and len(path) > 1:
                        cowboy.assignment = path
                        cowboy.move(path[1])
                    else:  # No path found
                        pass  # TODO attack
        except ValueError:  # We got drunk and moved off our path
            if not cowboy.is_drunk:
                # Find a new target
                path = safe_bfs(ai, cowboy.tile)
                if path and len(path) > 1:
                    cowboy.assignment = path
                    cowboy.move(path[1])
                else:  # No path found
                    pass  # TODO attack
    t = ai.game.current_turn // 2
    if t < 4:
        assignments = generate_starting_assignments(ai)
        if t < len(assignments):
            (goal, path), job = assignments[t]
            new = ai.player.young_gun.call_in(job)
            new.assignment = path
            new.move(path[1])
    elif t > 8: # Spawn everything else
        y = ai.player.young_gun
        for job in ['Brawler', 'Sharpshooter', 'Bartender']:
            if sum(1 for c in ai.player.cowboys if c.job == job and not c.is_dead) < 2:
                if y.can_call_in:
                    t = y.call_in_tile
                    # Stomp enemies and non-pianos
                    if (not t.furnishing or not t.furnishing.is_piano) and\
                            (not t.cowboy or t.cowboy.owner != ai.player):
                        new = y.call_in(job)
                        if new:  # Give him an assignment
                            new.assignment = []  # Don't crash
                            path = safe_bfs(ai, new.tile)
                            if path:
                                new.assignment = path
                                new.move(path[1])
                            else:  # TODO: attack
                                pass
                        break
    # Log all assignments
    if t == 0:
        for f in ai.game.furnishings:
            if not f.is_destroyed and f.is_piano:
                f.log(f.tile.id)
    for c in ai.player.cowboys:
        if c.assignment is not c.prev_assignment:
            if not c.is_dead:
                if c.assignment and len(c.assignment) > 0:
                    t = c.assignment[-1]
                    if t:
                        c.log(t.id)
                else:
                    c.log('None')
        c.prev_assignment = c.assignment


def _safe_wall_func(dist, t):
    if dist < 3:  # Check for being safe from bottles
        if not safe(t):
            return True
    return t.furnishing or t.is_balcony or\
            (t.cowboy)
def _safe_goal_func(ai, t, alive_pianos):
    # Tiles adjacent to pianos that don't have allied units at them
    #  and don't have a hazard, unless it's the only open spot
    for n in t.neighbors:
        if n.furnishing and n.furnishing.is_piano:
            allies = 0
            enemies = 0
            non_hazard_open_tiles = 0
            for nn in n.neighbors:
                if nn.cowboy:
                    if nn.cowboy.owner == ai.player and nn.cowboy.assignment[-1] == n:
                        allies += 1
                    if nn.cowboy.owner != ai.player:
                        enemies += 1
                elif not nn.furnishing and not nn.has_hazard and not nn.is_balcony:
                    non_hazard_open_tiles += 1
            if allies < ((6 // alive_pianos) + 1):  # 6 or less pianos -> double up cowboys
                if (not t.has_hazard or non_hazard_open_tiles == 0) and not t.cowboy:
                    return n
    return False
def safe_bfs(ai, start, goal_func=_safe_goal_func, wall_func=_safe_wall_func):
    alive_pianos = sum(1 for f in ai.game.furnishings if not f.is_destroyed)
    frontier = deque()
    frontier.append(start)
    parents = {start: None}
    dist = {start: 0}
    while frontier:
        top = frontier.popleft()
        if goal_func(ai, top, alive_pianos):
            path = list(reversed(list(follow(parents, top))))
            if len(path) >= 1:
                path += [goal_func(ai, top, alive_pianos)]  # Add the piano on to the end of the path
            return path
        for neighbor in top.neighbors:
            if wall_func(dist[top], neighbor) and not goal_func(ai, neighbor, alive_pianos):
                continue
            if neighbor not in parents:
                frontier.append(neighbor)
                parents[neighbor] = top
                dist[neighbor] = dist[top] + 1

