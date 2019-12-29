class TranspositionTable:
    """
    Use board hash value as unique key. Along with board number moves,
    table efficiently maps boards to items of interest. Transpositions collide
    in table. This saves computation and memory. Trees may store essential
    node data, while children relationships are computed during search.
    """

    def __init__(self):
        """Store list of dicts by number of moves. Default is callable."""
        self.table = [{} for _ in range(43)]

    def __len__(self):
        """Return number of entries in table. O(moves) time complexity."""
        return sum(len(t) for t in self.table)

    def __getitem__(self, board):
        return self.table[board.moves()][board.hash_value]

    def __setitem__(self, board, item):
        self.table[board.moves()][board.hash_value] = item

    def __delitem__(self, board):
        del self.table[board.moves()][board.hash_value]

    def __contains__(self, board):
        return board.hash_value in self.table[board.moves()]

    def clear_moves(self, moves):
        """Remove table entries with given number of moves."""
        self.table[moves] = {}

class SymmetryTable(TranspositionTable):
    """
    Use board hash value as unique key. Along with board number moves,
    table efficiently maps boards to items of interest. Transpositions and
    symmetries collide in table. This saves computation and memory. Trees may
    store essential node data, while children relationships, symmetric moves
    are computed during search.
    """

    def __getitem__(self, board):
        for value in (board.hash_value, board.symm_value):
            if value in self.table[board.moves()]:
                return self.table[board.moves()][value]
        return None

    def __delitem__(self, board):
        for value in (board.hash_value, board.symm_value):
            if value in self.table[board.moves()]:
                del self.table[board.moves()][value]
                return

    def __contains__(self, board):
        return any(value in self.table[board.moves()]
                   for value in (board.hash_value, board.symm_value))

    def get_symm_item(self, board):
        """Return value of stored board and permutation mapping stored board
        to given board."""
        if board.hash_value in self.table[board.moves()]:
            return (False, self.table[board.moves()][board.hash_value])
        if board.symm_value in self.table[board.moves()]:
            return (True, self.table[board.moves()][board.symm_value])
        return None
