# Cowboy: A person on the map that can move around and interact within the saloon.

# DO NOT MODIFY THIS FILE
# Never try to directly create an instance of this class, or modify its member variables.
# Instead, you should only be reading its variables and calling its functions.

from games.saloon.game_object import GameObject



class Cowboy(GameObject):
    """The class representing the Cowboy in the Saloon game.

    A person on the map that can move around and interact within the saloon.
    """

    def __init__(self):
        """Initializes a Cowboy with basic logic as provided by the Creer code generator."""
        GameObject.__init__(self)

        # private attributes to hold the properties so they appear read only
        self._can_move = False
        self._drunk_direction = ""
        self._focus = 0
        self._health = 0
        self._is_dead = False
        self._is_drunk = False
        self._job = ""
        self._owner = None
        self._tile = None
        self._tolerance = 0
        self._turns_busy = 0

        self.preferred = None
        self.prev_assignment = []
        self.prev_tile = None
        self.same_tile = 0

    @property
    def can_move(self):
        """If the Cowboy can be moved this turn via its owner.

        :rtype: bool
        """
        return self._can_move


    @property
    def drunk_direction(self):
        """The direction this Cowboy is moving while drunk. Will be 'North', 'East', 'South', or 'West' when drunk; or '' (empty string) when not drunk.

        :rtype: str
        """
        return self._drunk_direction


    @property
    def focus(self):
        """How much focus this Cowboy has. Different Jobs do different things with their Cowboy's focus.

        :rtype: int
        """
        return self._focus


    @property
    def health(self):
        """How much health this Cowboy currently has.

        :rtype: int
        """
        return self._health


    @property
    def is_dead(self):
        """If this Cowboy is dead and has been removed from the game.

        :rtype: bool
        """
        return self._is_dead


    @property
    def is_drunk(self):
        """If this Cowboy is drunk, and will automatically walk.

        :rtype: bool
        """
        return self._is_drunk


    @property
    def job(self):
        """The job that this Cowboy does, and dictates how they fight and interact within the Saloon.

        :rtype: str
        """
        return self._job


    @property
    def owner(self):
        """The Player that owns and can control this Cowboy.

        :rtype: Player
        """
        return self._owner


    @property
    def tile(self):
        """The Tile that this Cowboy is located on.

        :rtype: Tile
        """
        return self._tile


    @property
    def tolerance(self):
        """How many times this unit has been drunk before taking their siesta and reseting this to 0.

        :rtype: int
        """
        return self._tolerance


    @property
    def turns_busy(self):
        """How many turns this unit has remaining before it is no longer busy and can `act()` or `play()` again.

        :rtype: int
        """
        return self._turns_busy



    def act(self, tile, drunkDirection=""):
        """ Does their job's action on a Tile.

        Args:
            tile (Tile): The Tile you want this Cowboy to act on.
            drunk_direction (Optional[str]): The direction the bottle will cause drunk cowboys to be in, can be 'North', 'East', 'South', or 'West'.

        Returns:
            bool: True if the act worked, False otherwise.
        """
        return self._run_on_server('act', tile=tile, drunkDirection=drunkDirection)


    def move(self, tile):
        """ Moves this Cowboy from its current Tile to an adjacent Tile.

        Args:
            tile (Tile): The Tile you want to move this Cowboy to.

        Returns:
            bool: True if the move worked, False otherwise.
        """
        return self._run_on_server('move', tile=tile)


    def play(self, piano):
        """ Sits down and plays a piano.

        Args:
            piano (Furnishing): The Furnishing that is a piano you want to play.

        Returns:
            bool: True if the play worked, False otherwise.
        """
        return self._run_on_server('play', piano=piano)

    # Custom stuff
    @property
    def near_piano(self):
        return sum(1 for t in self.tile.neighbors if t.furnishing and t.furnishing._is_piano)

    def move_pref(self, tile):
        dx = tile.x - self.tile.x
        dy = tile.y - self.tile.y
        r = self.move(tile)
        if r:
            for n in self.tile.neighbors:
                if n.x - tile.x == dx and n.y - tile.y == dy:
                    self.preferred = n
                    break


    def __str__(self):
        return "Cowboy({}, ({}, {}))\n".format(
                self._id, self.tile._x, self.tile._y) +\
                        '\n'.join("{}={}".format(k, v) for k, v in {
                    '_can_move': self._can_move,
                    '_drunk_direction': self._drunk_direction,
                    '_focus': self._focus,
                    '_health': self._health,
                    '_is_dead': self._is_dead,
                    '_is_drunk': self._is_drunk,
                    '_job': self._job,
                    '_owner': self._owner,
                    '_tile': self._tile,
                    '_tolerance': self._tolerance,
                    '_turns_busy': self._turns_busy,
                    'path': self.path,
                    'path_index': self.path_index,
                    'moving': self.moving,
                    'preferred': self.preferred
                    }.items())
