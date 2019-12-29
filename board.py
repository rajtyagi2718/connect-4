
class Board:

    # 5  11 17 23 29 35 41
    # 4  10 16 22 28 34 40
    # 3  9  15 21 27 33 39
    # 2  8  14 20 26 32 38
    # 1  7  13 19 25 31 37
    # 0  6  12 18 24 30 36

    # all 4-in-a-row slices
    slices = []
    # map key index to all 4-in-a-row slices containing that position
    winner_slices = [[] for _ in range(42)]
    # map key index to radial slices with center at position
    winner_slices_last_key = [[] for _ in range(42)]

    def __init__(self, values=None, played_keys=None, open_keys=None,
                 winner=None, hash_value=0, symm_value=0):
        """
        Board flattened to values list. Positions are keys or indices of
        values. Values items can be 0, 1, or 2, if open, played by player 1,
        or played by player 2. All keys decompose to played and open. Winner
        is None during play; 0, 1, or 2 at end of play. Hash value is unique
        to current state of board. Symm value is hash value for symmetric board
        i.e. reflected left right.
        """
        if values is None:
            values = [0]*42
            played_keys = []
            open_keys = {i:[j for j in range(6*(i+1)-1, 6*i-1, -1)]
                         for i in range(7)}
            winner = None
        self.values = values
        self.played_keys = played_keys
        self.open_keys = open_keys
        self.winner = winner
        self.hash_value = hash_value
        self.symm_value = symm_value

    ## State methods ##

    def moves(self):
        """Return number of keys already played."""
        return len(self.played_keys)

    def turn(self):
        """Return number of current player, i.e. first to act on current
        board. Player 1 is first to act on empty board. Player 2 follows.
        Turns alternated."""
        return 1 + self.moves() % 2

    def other(self):
        """Return opponents player number i.e. the player that last played."""
        return 2 - self.moves() % 2

    def last_key(self):
        """Return last played key or None if empty board."""
        try:
            return self.played_keys[-1]
        except IndexError:
            return None

    def is_terminal(self):
        """Return True if winner exists."""
        return self.winner is not None

    ## Play methods ###

    def push(self, col):
        """Assert col is open, play bottom most key in col, i.e. set values
        item to current player number at key index. Update attributes."""
        key = self.open_keys[col].pop()
        if not self.open_keys[col]:
            del self.open_keys[col]
        assert self.values[key] == 0
        self.values[key] = self.turn()
        # turn is function of number of moves i.e. len of played_keys
        self.hash_value += HashBoard.hash_item(key, self.turn())
        symm_key = 6 * (6 - col) + key % 6
        self.symm_value += HashBoard.hash_item(symm_key, self.turn())
        self.played_keys.append(key)
        self.set_winner()

    def pop(self):
        """Undo play of last key. Update attributes."""
        last_key = self.played_keys.pop()
        self.values[last_key] = 0
        self.winner = None
        self.hash_value -= HashBoard.hash_item(last_key, self.turn())
        last_col, last_row = divmod(last_key, 6)
        symm_key = 6 * (6 - last_col) + last_row
        self.symm_value -= HashBoard.hash_item(symm_key, self.turn())
        try:
            self.open_keys[last_col].append(last_key)
        except KeyError:
            self.open_keys[last_col] = [last_key]

    def set_winner(self):
        """Check if board at end state: a player wins with 4 positions in a
        single row, column, or diagonal slice; draw when no more open
        positions. Set winner to winning player or 0 if draw. Return winner if
        end state, else return None. Winning slices checked efficiently by
        class attribute list by last key played."""
        # slices of length 4, no winner can exist until move 7
        if self.moves() < 7:
            return

        # other player last played, potentially won
        for s in Board.winner_slices_last_key[self.last_key()]:
            count = 0
            for x in s:
                for i in x:
                    if self.values[i] == self.other():
                        count += 1
                    else:
                        break
            if count > 2:
                self.winner = self.other()
                return

        # 42th move fills the board, end state
        if self.moves() == 42:
            self.winner = 0

    ## Tree methods ##

    def utility(self):
        """Return value of board. 1 if player one won, 2 if player two won,
        0 otherwise."""
        return [0, -1, 1][self.winner] if self.winner else 0

    def evaluation(self):
        """
        Return linear combination of slices of 0 and or num of one player.
             1000 * diff of num of 4-in-a-rows
            + 100 * diff of num of 3 of 4-in-a-rows
            +  10 * diff of num of 2 of 4-in-a-rows
            +   1 * diff of num of 1 of 4-in-a-rows.
        """
        diff = [0]*4
        for s in self.slices:
            counter = [0]*3
            for i in s:
                counter[self.values[i]] += 1
            if counter[1] and not counter[2]:
                diff[counter[1]-1] += 1
            elif counter[2] and not counter[1]:
                diff[counter[2]-1] -= 1
        result = diff[0] + diff[1]*10 + diff[2]*100 + diff[3]*1000
        if self.turn() == 2:
            result *= -1
        return result

    def force_block(self):
        """Return an open key that results in a loss if not played, and
        opponent plays. i.e. 3 of 4-in-a-row for opponent. Only check last
        played key."""
        if self.moves() < 4:
            return None
        for s in self.winner_slices[self.last_key()]:
            counter = [0]*3
            for i in s:
                counter[self.values[i]] += 1
            if counter[self.other()] == 3 and counter[0] == 1:
                for i in s:
                    if not self.values[i]:
                        col = i // 6
                        if self.open_keys[col] == i:
                            return col
                        break
        return None

    def force_win(self):
        """Return an open key that results in win if played i.e. 3 of 4-in-a-
        row for current player. Only check last played key by current player.
        """
        if self.moves() < 4:
            return
        second_to_last_key = self.played_keys[-2]
        for s in self.winner_slices[second_to_last_key]:
            counter = [0]*3
            for i in s:
                counter[self.values[i]] += 1
            if counter[self.turn()] == 3 and counter[0] == 1:
                for i in s:
                    if not self.values[i]:
                        col = i // 6
                        if self.open_keys[col] == i:
                            return col
                        break
        return None

    ## Other methods ##

    def __repr__(self):
        """
        Display board as matrix. Possible representations:
        start:       middle:      end:
        [0, 0, 0]    [0, 1, 0]    [1, 1, 2]
        [0, 0, 0]    [2, 2, 0]    [2, 2, 1]
        [0, 0, 0]    [1, 2, 1]    [1, 2, 1]
        """
        return '\n'.join([self.values[i: 42: 6].__str__()
                          for i in range(5, -1, -1)])

    def __str__(self):
        """
        Display board as grid with border. Possible strings:
        ///////////////////
        // 0 1 2   4 5 6 //
        // . . . x . . . //
        // . . . x . . . //
        // . . . o . . . //
        // . . . x . . . //
        // . . . o . . . //
        // . . o x . . . //
        ///////////////////
        """
        result = '/'*19 + '\n'
        result += '// '
        result += ' '.join(str(i) if i in self.open_keys else ' '
                           for i in range(7))
        result += ' //' + '\n'
        for i in range(5, -1, -1):
            row = '// '
            for key in range(i, 42, 6):
                value = self.values[key]
                row += self.value_to_piece(value)
                row += ' '
            row += '//'
            result += row + '\n'
        result += '/'*19
        return result

    def value_to_piece(self, value):
        return ['.', 'x', 'o'][value]

    def symm_col(self, col):
        """Return reflection of given col over vertical axis."""
        return 6 - col

    def key_to_col(self, key):
        return key // 6

# flattened indices of each row, column, diagonal slice of board
slices = []
# rows
slices.extend(tuple(range(i, 42, 6)) for i in range(6))
# cols
slices.extend(tuple(range(i, i+6)) for i in range(0, 42, 6))
# diags
slices.extend(tuple(range(i, j+1, 5))
                     for i, j in zip((3, 4, 5, 11, 17, 23),
                                     (18, 24, 30, 36, 37, 38)))
slices.extend(tuple(range(i, j+1, 7))
                     for i, j in zip((2, 1, 0, 6, 12, 18),
                                     (23, 29, 35, 41, 40, 39)))

Board.winner_slices_last_key = [[] for _ in range(42)]
for s in slices:
    for i in range(len(s)):
        t = s[i-1::-1] if i else()
        Board.winner_slices_last_key[s[i]].append((t, s[i+1:i+4]))

Board.slices = [s[i:i+4] for s in slices for i in range(len(s)-3)]

Board.winner_slices = [[] for _ in range(42)]
for s in slices:
    for i in range(len(s)-3):
        t = s[i:i+4]
        for x in t:
            Board.winner_slices[x].append(t)

class HashBoard:

    # map k to [3**k, 3**k+1, 3**k+2] for 0 <= k < len(values)
    table = [[0]*3 for _ in range(42)]

    m = 1
    for i in range(42):
        c = m
        for j in range(1, 3):
            table[i][j] = c
            c += m
        m = c

    @classmethod
    def hash(cls, board):
        """Return hash value of board."""
        return cls.hash_values(board.values)

    @classmethod
    def hash_values(cls, values):
        """Hash values as base 3 integer. Return hash value."""
        return sum(cls.hash_item(key, values[key]) for key in range(42))

    @classmethod
    def hash_item(cls, key, turn):
        """Use table to hash key value pair. Total hash is linear
        combination."""
        return cls.table[key][turn]
