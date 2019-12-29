from board import Board
import random

class Simulation:

    winner_slices_last_key = Board.winner_slices_last_key

    def __init__(self, board):
        self.values = list(board.values)
        moves = board.moves()
        open_keys = list(list(v) for v in board.open_keys.values())
        self.winner = None
        self.play(moves, open_keys)

    def get_random_open_key(self, open_keys):
        i = random.randrange(len(open_keys))
        try:
            return open_keys[i].pop()
        except IndexError:
            del open_keys[i]
            return self.get_random_open_key(open_keys)

    def play(self, moves, open_keys):
        turn = 1 + moves % 2
        for _ in range(6-moves):
            key = self.get_random_open_key(open_keys)
            self.values[key] = turn
            turn = 3 - turn
        moves = max(moves, 6)
        for _ in range(42-moves):
            key = self.get_random_open_key(open_keys)
            self.values[key] = turn
            if self.calc_winner(key, turn):
                return
            turn = 3 - turn
        self.winner = 0

    def calc_winner(self, key, turn):
        for s in self.winner_slices_last_key[key]:
            count = 0
            for x in s:
                for i in x:
                    if self.values[i] == turn:
                        count += 1
                    else:
                        break
            if count > 2:
                self.winner = turn
                return True
        return False
