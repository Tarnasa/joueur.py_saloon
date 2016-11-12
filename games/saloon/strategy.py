from functools import partial, lru_cache
from collections import OrderedDict

from games.saloon.util import shortest_pairs, cowboy_bfs, transpose, opposite,\
        get_spawn_tile, is_near_enemy_piano, bfs, alignment
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

def match_nearest_pianos(ai):
    """
    From each piano, fill all open spots on the piano with nearest friendlies
    """
    cowboys = [c for c in ai.player.cowboys if not c._is_dead and c.can_move]
    spots = list()
    for piano in ai.pianos:
        for n in piano.tile.neighbors:
            if n.cowboy in cowboys:
                cowboys.remove(n.cowboy)
            elif not n.cowboy and not n.furnishing and not n._is_balcony:
                spots.append(n)
    assignments = OrderedDict()

    def spot_score(cowboy, spot):
        # Prefer tiles which are further from your teams Y-side (UNTESTED)
        return spot.distance(cowboy.tile), spot.y * (int(ai.player.id)*2-1)

    try:
        for c in cowboys:
            nearest = min(spots, key=partial(spot_score, c))
            assignments[c] = nearest
            spots.remove(nearest)
    except ValueError:
        pass
    return assignments

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
                # for n in spot.piano.tile.neighbors:
                #     if n in spots:
                #         spots.remove(n)

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


def predict_brawler_death(ai):
    """ Returns the approximate number of turns it will take to kill both my brawlers """
    brawlers = [c for c in ai.player.cowboys if c.job == 'Brawler' and not c._is_dead]
    if not brawlers:
        return 0
    h = max(b.health for b in brawlers)
    if len(brawlers) == 2:
        return brawlers[0].tile.distance(brawlers[1].tile) + h
    elif len(brawlers) == 1:
        hazards = [t for t in ai.hazards if not t.furnishing and not t.cowboy]
        if hazards:
            print('hazards: ', hazards)
            return min(t.distance(brawlers[0].tile) for t in hazards) + h
        else:
            return 100
    else:
        print('wat: ', brawlers, h)


def kill_my_brawlers(ai):
    """ Tries to kill your brawlers """
    brawlers = [c for c in ai.player.cowboys if not c._is_dead]
    def hazard_goal_func(t):
        return t.has_hazard and not t.furnishing and\
                (not t.cowboy or t.cowboy in brawlers)
    hazards = [t for t in ai.hazards if hazard_goal_func(t)]
    for c in ai.player.cowboys:
        if not c._is_dead:
            if c.job == 'Brawler':
                if hazards: # Move to nearest hazard
                    path = cowboy_bfs(c, hazard_goal_func)
                    if path and 1 < len(path) < 10:
                        print('Move to nearest hazard')
                        if not path[1].cowboy:
                            c.move_pref(path[1])
                        elif path[1].cowboy not in brawlers:
                            if move_over(ai, path[1].cowboy, c):
                                c.move_pref(path[1])
                        else:
                            pass  # Wait your turn to die
                        break
                if len(brawlers) == 2: # kill the other brawler, but stay on the piano
                    target = [b for b in brawlers if b is not c]
                    path = cowboy_bfs(ai, lambda t: t.cowboy is target)
                    if path and len(path) > 2:
                        print('brawl ally brawler')
                        c.move(path[1])  # TODO: Outaway
            # TODO: Use own bartenders


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

""" TODO finish this """
def move_and_throw_bottles(ai):
    for cowboy in self.player.cowboys:
        if cowboy.job == 'Bartender' and not cowboy._is_dead and c.target is None:
            for enemy in self.player.opponent.cowboys:  # TODO: Check for stuff in the way
                if cowboy.turns_busy == 0 and alignment(enemy.tile, cowboy.tile) == 0:
                    if cowboy.act(toward(cowboy.tile, enemy.tile),
                            best_drunk_direction(enemy.tile)):
                        print(cowboy.id, 'Throw at enemy')
                        break
                    else:
                        print(cowboy.id, 'Failed to throw')
            else:
                path = bfs(cowboy.tile, lambda t: t.cowboy and t.cowboy.owner != self.player, wall_func)
                # cowboy.act(cowboy.tile.get_dir('north'), '')
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

