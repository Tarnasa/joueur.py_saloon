# Tile: A Tile in the game that makes up the 2D map grid.

# DO NOT MODIFY THIS FILE
# Never try to directly create an instance of this class, or modify its member variables.
# Instead, you should only be reading its variables and calling its functions.

from games.saloon.game_object import GameObject



class Tile(GameObject):
    """The class representing the Tile in the Saloon game.

    A Tile in the game that makes up the 2D map grid.
    """

    def __init__(self):
        """Initializes a Tile with basic logic as provided by the Creer code generator."""
        GameObject.__init__(self)

        # private attributes to hold the properties so they appear read only
        self._bottle = None
        self._cowboy = None
        self._furnishing = None
        self._has_hazard = False
        self._is_balcony = False
        self._tile_east = None
        self._tile_north = None
        self._tile_south = None
        self._tile_west = None
        self._x = 0
        self._y = 0
        self._young_gun = None



    @property
    def bottle(self):
        """The beer Bottle currently flying over this Tile.

        :rtype: Bottle
        """
        return self._bottle


    @property
    def cowboy(self):
        """The Cowboy that is on this Tile, None otherwise.

        :rtype: Cowboy
        """
        return self._cowboy


    @property
    def furnishing(self):
        """The furnishing that is on this Tile, None otherwise.

        :rtype: Furnishing
        """
        return self._furnishing


    @property
    def has_hazard(self):
        """If this Tile is pathable, but has a hazard that damages Cowboys that path through it.

        :rtype: bool
        """
        return self._has_hazard


    @property
    def is_balcony(self):
        """If this Tile is a balcony of the Saloon that YoungGuns walk around on, and can never be pathed through by Cowboys.

        :rtype: bool
        """
        return self._is_balcony


    @property
    def tile_east(self):
        """The Tile to the 'East' of this one (x+1, y). None if out of bounds of the map.

        :rtype: Tile
        """
        return self._tile_east


    @property
    def tile_north(self):
        """The Tile to the 'North' of this one (x, y-1). None if out of bounds of the map.

        :rtype: Tile
        """
        return self._tile_north


    @property
    def tile_south(self):
        """The Tile to the 'South' of this one (x, y+1). None if out of bounds of the map.

        :rtype: Tile
        """
        return self._tile_south


    @property
    def tile_west(self):
        """The Tile to the 'West' of this one (x-1, y). None if out of bounds of the map.

        :rtype: Tile
        """
        return self._tile_west


    @property
    def x(self):
        """The x (horizontal) position of this Tile.

        :rtype: int
        """
        return self._x


    @property
    def y(self):
        """The y (vertical) position of this Tile.

        :rtype: int
        """
        return self._y


    @property
    def young_gun(self):
        """The YoungGun on this tile, None otherwise.

        :rtype: YoungGun
        """
        return self._young_gun

    directions = [ "North", "East", "South", "West" ]
    """int: The valid directions that tiles can be in, "North", "East", "South", or "West"
    """

    # Custom stuff
    @property
    def neighbors(self):
        return [t for t in [self._tile_north, self._tile_south, self._tile_east, self._tile_west] if t]

    @property
    def hor_neighbors(self):
        return [t for t in [self._tile_east, self._tile_west, self._tile_north, self._tile_south] if t]

    @property
    def pos(self):
        return self._x, self._y

    def distance(self, other):
        return abs(self._x - other._x) + abs(self._y - other._y)

    def get_dir(self, dir):
        return getattr(self, 'tile_' + dir.lower())

    def __str__(self):
        return "({}, {})".format(self._x, self._y)

