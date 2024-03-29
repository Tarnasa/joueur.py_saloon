# YoungGun: An eager young person that wants to join your gang, and will call in the veteran Cowboys you need to win the brawl in the saloon.

# DO NOT MODIFY THIS FILE
# Never try to directly create an instance of this class, or modify its member variables.
# Instead, you should only be reading its variables and calling its functions.

from games.saloon.game_object import GameObject



class YoungGun(GameObject):
    """The class representing the YoungGun in the Saloon game.

    An eager young person that wants to join your gang, and will call in the veteran Cowboys you need to win the brawl in the saloon.
    """

    def __init__(self):
        """Initializes a YoungGun with basic logic as provided by the Creer code generator."""
        GameObject.__init__(self)

        # private attributes to hold the properties so they appear read only
        self._call_in_tile = None
        self._can_call_in = False
        self._owner = None
        self._tile = None



    @property
    def call_in_tile(self):
        """The Tile that a Cowboy will be called in on if this YoungGun calls in a Cowboy.

        :rtype: Tile
        """
        return self._call_in_tile


    @property
    def can_call_in(self):
        """True if the YoungGun can call in a Cowboy, False otherwise.

        :rtype: bool
        """
        return self._can_call_in


    @property
    def owner(self):
        """The Player that owns and can control this YoungGun.

        :rtype: Player
        """
        return self._owner


    @property
    def tile(self):
        """The Tile this YoungGun is currently on.

        :rtype: Tile
        """
        return self._tile



    def call_in(self, job):
        """ Tells the YoungGun to call in a new Cowboy of the given job to the open Tile nearest to them.

        Args:
            job (str): The job you want the Cowboy being brought to have.

        Returns:
            Cowboy: The new Cowboy that was called in if valid. They will not be added to any `cowboys` lists until the turn ends. None otherwise.
        """
        return self._run_on_server('callIn', job=job)

    # Custom stuff
    @property
    def next_call_in_tile(self):
        t = None
        if self.tile.y == 0:
            t = self.tile.get_dir('East') or self.tile.get_dir('South')
        elif self.tile.x == 21:
            t = self.tile.get_dir('South') or self.tile.get_dir('West')
        elif self.tile.y == 11:
            t = self.tile.get_dir('West') or self.tile.get_dir('North')
        elif self.tile.x == 0:
            t = self.tile.get_dir('North') or self.tile.get_dir('East')
        else:
            print('NONONONONO')
        for n in t.neighbors:
            if not n.is_balcony:
                return n
        else:
            for n in t.neighbors:
                for nn in n.neighbors:
                    if not nn.is_balcony:
                        return nn
