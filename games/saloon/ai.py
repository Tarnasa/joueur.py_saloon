# This is where you build your AI for the Saloon game.

from joueur.base_ai import BaseAI
from games.saloon.tile import Tile
import random
import time

from games.saloon.util import bfs, shortest_pairs, wall_func,\
        alignment, toward, flood_path, flood_path_fast,\
        cowboy_bfs, safe, classify_pianos, set_tile_piano
from games.saloon.strategy import best_drunk_direction, best_bang_direction,\
        spawn_everything, move_over, avoid_bottles,\
        brawl_enemy_pianos, play_pianos,\
        get_spawn_distance_to_enemy_piano, shoot_enemy_pianos, assign_pianos,\
        move_to, move_starting_cowboys
from games.saloon.asciivis import draw_everything, general_tile_func
from games.saloon.train import train_strat


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

    i = 0
    def run_turn(self):
        genesis = time.time()

        if False:
            if self.player.time_remaining > 2e9:
                if self.i == 0:
                    t = self.game.current_turn
                    if t < 20:
                        self.i = 21 - t
                    elif (t // 2) % 10 == 0:
                        self.i = t
                    else:
                        train_strat(self)
                        draw_everything(self, general_tile_func)
                        return True
                    return False
                elif self.i == 1:
                    self.i = 0
                    train_strat(self)
                    draw_everything(self, general_tile_func)
                    return True
                else:
                    self.i -= 1
                    return False
            train_strat(self)
            draw_everything(self, general_tile_func)
            return True

        if True:
            if self.player.score > self.player.opponent.score + 40:
                train_strat(self)
            else:
                move_starting_cowboys(self)
                play_pianos(self)
                draw_everything(self, general_tile_func)
            return True

        # Init stuff
        self.tiles_pos = {(tile.x, tile.y): tile for tile in self.game.tiles}
        self.pianos = [f for f in self.game.furnishings if f._is_piano and not f._is_destroyed]
        self.hazards = [t for t in self.game.tiles if t._has_hazard]
        classify_pianos(self)
        set_tile_piano(self)
        for c in self.player.cowboys:
            c.moving = False
            c.target = None

        spawn_everything(self)

        avoid_bottles(self)

        if False and self.player.id == '0':
            distance = get_spawn_distance_to_enemy_piano(self)
            death = predict_brawler_death(self)
            print('distance: ', distance, death)
            if self.player.young_gun.tile.x > 11:
                print('do it')
                kill_my_brawlers(self)
                brawl_enemy_pianos(self)

        assignments = assign_pianos(self)

        for c, target in assignments.items():
            c.target = target
            path = cowboy_bfs(c, lambda t: t == target)
            if path and len(path) > 1:
                target = path[1]
                if target.cowboy and target.cowboy.owner == self.player:
                    if move_over(self, target.cowboy, c):
                        c.move_pref(target)
                    else:  # Try to find another path of equal distance
                        print(c.id, 'halp')
                else:
                    if safe(target):
                        c.move_pref(target)
                    else:
                        print(c.id, "It's dangerous out there!")

        play_pianos(self)  # Teehee

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
                    cowboy.act(cowboy.tile.get_dir('north'), '')
                    if path:
                        if cowboy.can_move and len(path) > 2:
                            cowboy.move(path[1])

        shoot_enemy_pianos(self)

        play_pianos(self)

        draw_everything(self, general_tile_func)

        print("Took {} seconds".format(time.time() - genesis))
        return True

