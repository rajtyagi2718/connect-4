from search import Search, RandomSearch, TreeSearch, IterativeDeepeningTreeSearch, TimeIterativeDeepeningTreeSearch, MonteCarloTreeSearch, TimeMonteCarloTreeSearch
from tree import IterativeDeepeningTree, TimeIterativeDeepeningTree, MonteCarloTree, UpperConfidenceBoundTree

class Player:
    """
    Creates object with name and search. Connects game board with player
    search. Abstraction diagram: x --> y i.e. y references x
        search --> player --> game --> board
    """

    def __init__(self, name, search, strategy_args=()):
        """Note search strategy defined by variable args."""
        self.name = name
        self.search = search
        self.strategy_args = strategy_args

    def reset(self, game):
        self.search.reset(game.board)

    def advance(self, game):
        self.search.advance(game.board)

    def move(self, game):
        return self.search.strategy(game, self.strategy_args)

    def __repr__(self):
        return self.name

class Spawn:
    """Creates player instances. AI players referenced by same name, variable
    strategy args. All other players are considered human."""

    # map player name (str) to tuple of search (cls), tree of some form
    players = {}

    # map player name (str) to tuple of args (str) for strategy
    strategy_args = {}

    @classmethod
    def get_player(cls, name, strategy_args=(), search_cls=None, tree=None):
        """Return instance of player."""
        search = cls.get_search(name, search_cls, tree)
        return Player(name, search, strategy_args)

    @classmethod
    def get_search(cls, name, search_cls, tree):
        """Return search instance from tree instance."""
        if not search_cls:
            if name in cls.players:
                search_cls, tree = cls.players[name]
            else:
                search_cls, tree = cls.players['user']
        if callable(tree):
            tree = tree()
        return search_cls(tree)

class UserInput:

    @classmethod
    def query_player(cls, i):
        """Query user to name playeri."""
        print("Player{}'s name?".format(i))
        name = str(input('--> '))
        strategy_args = ()
        if name in Spawn.players:
            strategy_args = cls.query_strategy_args(name)
        return Spawn.get_player(name, strategy_args)

    @classmethod
    def query_strategy_analysis(cls, query, game):
        while True:
            print('Which computer?')
            name = input('--> ')
            if (name not in Spawn.players or name == 'user' or
                query == 'stats' and name == 'alphabeta'):
                print('Unavailable. Try "negamax".')
            else:
                strategy_args = cls.query_strategy_args(name)
                break
        game.print_strategy_analysis(name, strategy_args, query)

    @classmethod
    def query_strategy_args(cls, name):
        return tuple(cls.query_arg(name, arg) for arg in
                     Spawn.strategy_args[name])

    @classmethod
    def query_arg(cls, name, arg):
        if arg == 'iterations':
            while True:
                print(' '*4 + 'How many iterations?')
                try:
                    iterations = int(input('    --> '))
                    if iterations > 0:
                        return iterations
                    print(' '*4 + 'Enter a positive integer.')
                except ValueError:
                    print(' '*4 + 'Enter an integer i.e. 100.')
        if arg == 'depth':
            while True:
                print('    How many moves deep?')
                try:
                    iterations = int(input(' '*4 + '--> '))
                    if iterations > 0:
                        if iterations > 9:
                            msg = "This game has max depth 9. We'll use 9."
                            print(' '*4 + msg)
                            iterations = 9
                        return iterations
                    print(' '*4 + 'Enter a positive integer.')
                except ValueError:
                    print(' '*4 + 'Enter an integer i.e. 3.')

class UserSearch(Search):

    def strategy(self, game, args=()):
        """Return open key queried from user input."""
        print('{} plays'.format(game.current_player()))
        entry = input('--> ')
        if len(entry) != 1:
            return self.strategy_not_key(entry, game)
        # check key is int
        try:
            key = int(entry)
        except ValueError:
            print('Enter a column number.')
            return self.strategy(game)
        # check key fits board
        if not (0 <= key < 7):
            print('Enter a column number.')
            print('Columns are numbered from 0 to 6.')
            return self.strategy(game)
        # check column is open
        if key not in game.board.open_keys:
            print('Column is full.')
            print('Open columns: ', str(game.board.open_keys.values())[13:-2])
            return self.strategy(game)
        return key

    def strategy_not_key(self, entry, game):
        if entry in ('stats', 'suggest'):
            UserInput.query_strategy_analysis(entry, game)
        else:
            print('Enter a column number.')
        return self.strategy(game)

Spawn.players['random'] = (RandomSearch, ())
Spawn.strategy_args['random'] = ()


Spawn.players['user'] = (UserSearch, ())
Spawn.strategy_args['user'] = ()


Spawn.players['iterative'] = (IterativeDeepeningTreeSearch,
                              IterativeDeepeningTree)
Spawn.strategy_args['iterative'] = ('depth',)

Spawn.players['idtime'] = (TimeIterativeDeepeningTreeSearch,
                           TimeIterativeDeepeningTree)
Spawn.strategy_args['idtime'] = ('depth',)


Spawn.players['montecarlo'] = (MonteCarloTreeSearch, MonteCarloTree)
Spawn.strategy_args['montecarlo'] = ('iterations',)

Spawn.players['confidence'] = (MonteCarloTreeSearch, UpperConfidenceBoundTree)
Spawn.strategy_args['confidence'] = ('iterations',)

Spawn.players['ucttime'] = (TimeMonteCarloTreeSearch,
                            UpperConfidenceBoundTree)
Spawn.strategy_args['ucttime'] = ('iterations',)
