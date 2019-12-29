import random

class Search:
    """Analyze board for best positions to play."""

    def __init__(self, args=()):
        self.key_values = []
        self.most_valuable = []

    def strategy(self, game, args=()):
        """Return open key for player to play in game."""

    def evaluate(self, board):
        """Set key_values and arg_maxes. Assign value for some open keys.
        Find the most valuable among them."""

    def reset(self, board):
        """Prepare self for upcoming game."""

    def advance(self, board):
        """Prepare self for upcoming move given other player's move."""

    def get_most_valuable(self):
        """Return most valued open keys."""
        return self.most_valuable

    def get_key_values(self):
        """Return key value pairs, denoting value of each open key relative to
        current player."""
        return self.key_values

    def get_norm_key_values(self, board):
        """Return key value pairs, values normalized from 0 to 100."""
        return self.key_values

    def explore(self, *args):
        """Explore state space as necessary."""

class RandomSearch(Search):

    def strategy(self, game, args=()):
        """Return open key for player to play in game. Randomly choose from
        most valuable keys."""
        return random.choice(list(game.board.open_keys.keys()))

    def evaluate(self, board):
        """All keys valued uniformly."""
        self.most_valuable = sorted(board.open_keys.keys())
        self.key_values = [(key, 50) for key in self.most_valuable]

class TreeSearch(Search):

    def __init__(self, tree_inst):
        self.tree = tree_inst
        super().__init__()

    def explore(self, board, args):
        """Explore state space as necessary."""
        self.tree.explore(board, *args)

    def strategy(self, game, args):
        self.tree.explore(game.board, *args)
        self.evaluate(game.board)
        return random.choice(self.most_valuable)

    def reset(self, board):
        # self.tree.table = self.tree.table_cls()
        for i in range(board.moves()):
            self.tree.table.clear_moves(i)

    # def advance(self, board):
        # if board.moves():
            # self.tree.table.clear_moves(board.moves()-1)

    def evaluate(self, board):
        self.most_valuable = self.tree.most_valuable(board)

class IterativeDeepeningTreeSearch(TreeSearch):

    def explore(self, board, args):
        for depth in range(1, args[0]+1):
            self.tree.principal_explore(board, depth)

    def strategy(self, game, args):
        for depth in range(1, args[0]+1):
            self.tree.principal_explore(game.board, depth)
        self.evaluate(game.board)
        return random.choice(self.most_valuable)

class TimeIterativeDeepeningTreeSearch(IterativeDeepeningTreeSearch):

    def strategy(self, game, args):
        alarm = time.time() + game.current_time() / 2 - 1
        max_depth = args[0]+1
        for depth in range(1, max_depth):
            if time.time() > alarm:
                break
            self.tree.principal_explore(alarm, game.board, depth)
        self.evaluate(game.board)
        return random.choice(self.most_valuable)

class MonteCarloTreeSearch(TreeSearch):

    def evaluate(self, board):
        self.key_values = self.tree.children_key_values(board)
        self.most_valuable = self.tree.most_valuable(board, self.key_values)

    def get_norm_key_values(self, board):
        return [(key, self.tree.norm_value(board, value)) for key, value
                in sorted(self.children_key_values, key=lambda item: item[0])]

class TimeMonteCarloTreeSearch(MonteCarloTreeSearch):

    def strategy(self, game, args):
        alarm = time.time() + game.current_time() / 2 - 1
        if board not in self.tree.table:
            self.tree.add_child(game.board)
        iterations = args[0]
        for _ in range(iterations):
            self.tree.playout(game.board)
            if time.time() > alarm:
                break
        self.evaluate(game.board)
        return random.choice(self.most_valuable)
