import re
import sys
import os

from joueur.ansi_color_coder import ansi, text, background, style, reset

def general_tile_func(tile):
    if tile.furnishing:
        if tile.furnishing.is_piano:
            return '♬♪♬♪'
        else:
            return '┬─┬'
    elif tile.cowboy:
        b = background('red' if tile.cowboy.owner.id == '0' else 'blue')
        r = reset()
        shortname = {'Sharpshooter': 'S', 'Bartender': 'T', 'Brawler': 'B'}
        return b + shortname[tile.cowboy.job] + str(tile.cowboy.id) + r
    elif tile.young_gun:
        b = background('red' if tile.young_gun.owner.id == '0' else 'blue')
        r = reset()
        return b + 'Y-' + str(tile.young_gun.owner.id) + r
    elif tile.bottle:
        return ' [] '
    elif tile.has_hazard:
        return 'xxx'
    elif tile.is_balcony:
        return '⋅⋅⋅'
    else:
        return ''

_ansi_re = re.compile(r"\033\[[0-9;]+m")
def visible_len(s):
    return len(_ansi_re.sub('', s))

def replace_line(line, x, s):
    """ This modifies `line` in-place """
    actual = 0
    extra = 0
    for match in _ansi_re.finditer(''.join(line)):
        l = (match.end() - match.start())
        actual = match.start() - extra
        if actual > x:
            break
        extra += l
    x += extra
    line[x:x+visible_len(s)] = list(s)

def draw_everything(ai, tile_func):
    r, c = 23, 94
    if sys.stdout.isatty():
        try:
            r, c = map(int, os.popen('stty size', 'r').read().split())
        except ValueError:
            pass
    r = min(r, ai.game.map_height+2)
    lines = [['|'] + [' '] * (c-2) + ['|'] for _ in range(r-2)]
    things = {t: tile_func(t) for t in ai.game.tiles if tile_func(t)}
    for tile, s in things.items():
        y = (tile.y * (r-2)) // ai.game.map_height
        x = (tile.x * (c-2)) // ai.game.map_width + 1
        replace_line(lines[y], x, s)
    print('\033[2J\033[1;1H')  # Clear screen, move cursor to 1,1
    line = list('+' + '-'*(c-2) + '+')
    replace_line(line, 2, background('red') + ai.game.players[0].name + reset() +
            '--' + background('red') + str(ai.game.players[0].score) + reset())
    replace_line(line, c-5, background('white') + text('black') + str(ai.game.current_turn) + reset())
    print(''.join(line))
    for line in lines:
        print(''.join(line))
    line = list('+' + '-'*(c-2) + '+')
    replace_line(line, 2, background('blue') + ai.game.players[1].name + reset() +
            '--' + background('blue') + str(ai.game.players[1].score) + reset())
    print(''.join(line))

