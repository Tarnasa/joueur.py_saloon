# This is where you build your AI for the Saloon game.

from joueur.base_ai import BaseAI
from games.saloon.tile import Tile
import random

from games.saloon.strategy import _dirs, move_to
#from games.saloon.util import move_to
from games.saloon.asciivis import draw_everything, general_tile_func


class AI(BaseAI):
    """ The basic AI functions that are the same between games. """

    def get_name(self):
        return "Console Cowboy" # REPLACE THIS WITH YOUR TEAM NAME

    def start(self):
        pass

    def game_updated(self):
        """ This is called every time the game's state updates, so if you are tracking anything you can update it here.
        """
        # replace with your game updated logic

    def end(self, won, reason):
        pass

    def run_turn(self):
        p = self.player
        y = self.player.young_gun
        t = self.game.current_turn

        rot_right = {'east': 'south', 'south': 'west', 'west': 'north', 'north': 'east'}

        bartenders = [c for c in p.cowboys if c.job == 'Bartender' and not c.is_dead]
        brawlers = [c for c in p.cowboys if c.job == 'Brawler' and not c.is_dead]
        sharpshooters = [c for c in p.cowboys if c.job == 'Sharpshooter' and not c.is_dead]

        def kill(cowboy):
            def goal_func(t):
                return t.has_hazard
            move_to(self, cowboy, goal_func)

        if t in [0, 1]:
            y.call_in('Brawler')
        elif t in [2, 3]:
            if brawlers:
                b = brawlers[0]
                next = y.next_call_in_tile
                for n in b.tile.neighbors:
                    if n == next:
                        b.move(n)
                        break
            y.call_in('Bartender')
        elif t >=4:
            def next_bottle(tile):
                for n in tile.neighbors:
                    if n.bottle:
                        if n.get_dir(n.bottle.direction) == tile:
                            return True
                return False
            def open_or_same(tile, job):
                return not tile.furnishing and\
                        not tile.bottle and not next_bottle(tile) and\
                        (not tile.cowboy or (tile.cowboy and tile.cowboy.job == job))
            spawn = y.call_in_tile
            next_spawn = y.next_call_in_tile
            if brawlers:
                for b in brawlers:
                    next = y.next_call_in_tile
                    for n in b.tile.neighbors:
                        if n == next:
                            b.move(n)
                            break
                    else:
                        if spawn != next_spawn:
                            kill(b)
            if spawn == next_spawn:
                if len(brawlers) < 2 and open_or_same(spawn, 'Brawler'):
                    y.call_in('Brawler')
            else:
                if bartenders:
                    for b in bartenders:
                        for dir in _dirs:
                            if b.tile.get_dir(dir) == spawn:
                                b.move(spawn)
                                throw_dir = rot_right[dir]
                                throw_tile = b.tile.get_dir(throw_dir)
                                if not throw_tile.cowboy:
                                    b.act(throw_tile, throw_dir)
                                break
                        else:
                            kill(b)
                if len(bartenders) < 2 and open_or_same(spawn, 'Bartender'):
                    y.call_in('Bartender')
            # Stomp furnishings with sharpshooters
            if y.can_call_in and spawn.furnishing:
                y.call_in('Sharpshooter')

        for s in sharpshooters:
            def goal_func(t):
                if t.cowboy and t.cowboy != s:
                    return False
                for n in t.neighbors:
                    if n.furnishing and n.furnishing.is_piano:
                        return True
                return False
            move_to(self, s, goal_func)
            for n in s.tile.neighbors:
                if n.furnishing and n.furnishing.is_piano:
                    s.play(n.furnishing)
                    break

        draw_everything(self, general_tile_func)

        return True

