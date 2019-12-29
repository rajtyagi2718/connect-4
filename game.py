# To Do:
#        mandatory moves:
#        tree inheritance
#        competition, benchmark players, round robbin, convergence

#        gui

import numpy as np, random
import time
import unittest

from board import Board, HashBoard
from player import Player, Spawn, UserInput


def pop_unstable(lst, index):
    """Remove and return item in lst at index. Replace item with last item."""
    result = lst[index]
    lst[index] = lst[-1]
    lst.pop()
    return result

def insert_unstable(lst, index, item):
    """Replace item at index with given item. Previous item goes to end."""
    if index < len(lst):
        lst.append(lst[index])
        lst[index] = item
        return
    lst.append(item)

def random_pop_unstable(lst):
    index = random.randrange(len(lst))
    result = lst[index]
    lst[index] = lst[-1]
    lst.pop()
    return result

def mean(data):
    """Return arithmetic mean of iterable data. Data need not be list."""
    n = 0
    mean = 0.0
    for x in data:
        n += 1
        mean += (x - mean)/n
    if n < 1:
        return float('nan')
    return mean

class SearchAnalysis:

    def __init__(self, name, strategy_args=(), board=None, played_keys=None,
                 search_cls=None, tree=None, ):
        self.search = Spawn.get_search(name, search_cls, tree)
        if board is None:
            board = Board()
            if played_keys:
                for key in played_keys:
                    board.play_key(key)
        self.board = board
        self.search.reset(self.board)
        self.search.explore(self.board, strategy_args)
        self.search.evaluate(self.board)

    def suggest(self):
        return random.choice(self.get_most_valuable())

    def get_most_valuable(self):
        return self.search.most_valuable

    def get_key_values(self):
        return self.search.key_values

    def get_norm_key_values(self):
        return self.search.get_norm_key_values(self.board)



##########
## Game ##
##########

class Game:

    def __init__(self, board=None, player1=None, player2=None):
        if board is None:
            board = Board()
        self.board = board
        if player1 is None:
            player1 = Spawn.get_player('random')
        self.player1 = player1
        if player2 is None:
            player2 = Spawn.get_player('random')
        self.player2 = player2
        self.player1.reset(self)
        self.player2.reset(self)

    def current_player(self):
        """Player1 plays when turn is 1. Player2 plays when turn is 2. Return
        player for current turn."""
        return [self.player1, self.player2][self.board.turn() - 1]

    def take_turn(self):
        """Query current player to make a move. Update board, notify players
        of played key."""
        key = self.current_player().move(self)
        self.board.push(key)
        self.player1.advance(self)
        self.player2.advance(self)

    def play(self):
        """Take turns until end state. Return winner: 0, 1, or 2."""
        # print(self.player1, self.player2)
        # print(self.board)
        # print()
        while not self.board.is_terminal():
            self.take_turn()
            # print(self.board)
            # print()
        # print(self.board.winner)
        return self.board.winner

class InteractiveGame(Game):

    def __init__(self, board=None):
        print('\n')
        player1 = UserInput.query_player(1)
        player2 = UserInput.query_player(2)
        if player1.name == player2.name:
            player1.name += '[1] '
            player2.name += '[2] '
        super().__init__(board, player1, player2)
        self.play()

    def play(self):
        """Take turns, print board until winner."""
        print(self, '\n')
        while not self.board.is_terminal():
            self.take_turn()
            print(self, '\n')

    def __str__(self):
        b = self.board.__str__()
        result = b[:19] + ' '*4 + 'Connect Four'
        result += b[19:59] + ' '*4 + '{} is x.'.format(self.player1)
        result += b[59:79] + ' '*4 + '{} is o.'.format(self.player2)

        last = self.board.last_key()
        if last is not None:
            last = self.board.key_to_col(last)
        result += b[79:119]
        if last is not None:
            result += ' '*4 + '{} plays {}.'.format(self.other_player(), last)

        term0 = ''
        term1 = ''
        if self.board.is_terminal():
            term0 = ['Draw!', '4-in-a-row', '4-in-a-row'][self.board.winner]
        if self.board.winner:
            term1 = '{} wins!'.format(self.other_player())
        result += b[119:159] + ' '*4 + term0
        result += b[159:179] + ' '*4 + term1
        return result

    def other_player(self):
        return [self.player1, self.player2][2 - self.board.turn()]

    def print_strategy_analysis(self, name, strategy_args, query):
        if query == 'stats':
            key_vals = self.get_player_stats(name, strategy_args)
            print(*key_vals, sep='\n')
        else:
            key = self.get_player_suggestion(name, strategy_args)
            print('How about {}.'.format(key))

    def get_player_stats(self, name, strategy_args):
        sa = SearchAnalysis(name, strategy_args, self.board)
        return sa.get_norm_key_values()

    def get_player_suggestion(self, name, strategy_args):
        sa = SearchAnalysis(name, strategy_args, self.board)
        return sa.suggest()

class TimeGame(Game):

    def __init__(self, board=None, player1=None, player2=None, t=30):
        super().__init__(board, player1, player2)
        self.time1 = self.time2 = t

    def current_time(self):
        """Return remaining play time for current player."""
        return self.time1 if self.board.turn() == 1 else self.time2

    def take_turn(self):
        """Query current player to make a move. Update board, notify players
        of played key."""
        time0 = time.time()
        key = self.current_player().move(self)
        time1 = time.time()
        self.deduct_time(time1 - time0)
        self.board.push(key)
        self.player1.advance(self)
        self.player2.advance(self)

    def deduct_time(self, t):
        attr = 'time' + str(self.board.turn())
        setattr(self, attr, self.current_time() - t)

#################
## Competition ##
#################

class Competition:

    def compete(name1, strat1, name2, strat2, n=10):
        player1=Spawn.get_player(name1, strat1)
        player2=Spawn.get_player(name2, strat2)
        result1 = [0]*3
        result2 = [0]*3
        for i in range(n):
            G = Game(player1=player1, player2=player2)
            r = G.play()
            result1[r] += 1
            r = -1 if r == 2 else r
            print(i, r)
            G = Game(player1=player2, player2=player1)
            r = G.play()
            result2[r] += 1
            r = -1 if r == 2 else r
            print(i, -r)
        result = [result1[0] + result2[0], result1[1]+result2[2], result1[2]+result2[1]]
        return result

    # def compete(name1, name2, strat1=(), strat2=(), n=100):
    #     result = [0]*3
    #     for _ in range(n):
    #         G = Game(player1=Spawn.get_player(name1, strat1),
    #                  player2=Spawn.get_player(name2, strat2))
    #         result[G.play()] += 1
    #     return result

    def check_draw(name1, name2, strat1=(), strat2=(), n=100):
        result = [0]*3
        off = []
        for _ in range(n):
            G = Game(player1=Spawn.get_player(name1, strat1),
                     player2=Spawn.get_player(name2, strat2))
            r = G.play()
            if r:
                off.append(G.board.played_keys)
            result[r] += 1
        return result[0]==n, result, off

# result = Competition.compete('confidence', (10000,), 'iterative', (8,), n=20)
# print(result)
