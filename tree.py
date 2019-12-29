from table import SymmetryTable
from simulation import Simulation
import random
import time
from math import log, sqrt

class Tree:

    def __init__(self):
        self.table_cls = SymmetryTable
        self.table = SymmetryTable()

from board import Board

# class QLearningTable:
#
#     def __init__(self):
#         self.table = SymmetryTable()
#         self.explore(Board())
#
#     def explore(self, board):
#         if not len(self.table) % 1000:
#             print(len(self.table), end=' ', flush=True)
#         if board in self.table or board.is_terminal():
#             return
#
#         self.table[board] = [0]*4
#
#         for key in board.open_keys:
#             board.push(key)
#             self.explore(board)
#             board.pop()
#
#     def generate(self, value):
#         result = SymmetryTable()
#         for i in range(10):
#             result.table[i] = {hv: list(lst)
#                                for hv, lst in self.table.table[i].items()}
#         return result
#
# q_learning_table = QLearningTable()
# print(len(q_learning_table.table))

class IterativeDeepeningTree(Tree):

    # table: value, exact_flag, depth, best, e_val

    def principal_explore(self, board, depth, alpha=-10000, beta=10000):
        result, item, symm = self.principal_cutoff_test(board, depth, beta)
        if result:
            return item[0]

        # set starting value below alpha cutoff, best key won't remain None
        value = -10001
        best = None
        e_val = item[4] if item is not None else None

        if depth > 1:
            principal = item[3] if not symm else board.symm_col(item[3])
            board.push(principal)
            child = -self.principal_explore(board, depth-1, -beta, -alpha)
            if value < child:
                value = child
                best = principal
            board.pop()

            if value >= beta:
                self.table[board] = (value, False, depth, best, e_val)
                return value
            alpha = max(value, alpha)

            open_keys = [k for k in board.open_keys.keys() if k != principal]
        else:
            open_keys = list(board.open_keys.keys())

        open_keys.sort(key=lambda k: self.get_evaluation(board, k))

        for key in open_keys:
            board.push(key)
            child = -self.explore(board, depth-1, -beta, -alpha)
            if value < child:
                value = child
                best = key
            board.pop()

            if value >= beta:
                self.table[board] = (value, False, depth, best, e_val)
                return value
            alpha = max(value, alpha)

        self.table[board] = (value, True, depth, best, e_val)
        return value

    def principal_cutoff_test(self, board, depth, beta):
        """End explore recursion if board is terminal, depth is reached, or
        board is transposition or symmetric. Return boolean and item."""
        symmitem = self.table.get_symm_item(board)
        if symmitem is not None:
            symm, item = symmitem
        else:
            symm = item = None
        result, item = self.table_test(board, depth, beta, item)
        if result:
            return True, item, symm
        result, item = self.terminal_test(board, item)
        if result:
            return True, item, symm
        result, item = self.depth_test(board, depth, item)
        if result:
            return True, item, symm
        return False, item, symm


    def explore(self, board, depth, alpha=-10000, beta=10000):
        """Add children in depth first procedure. Bookkeep keys, board,
        hash incrementally during visit. Backtrack actions postvisit.
        Check transposition table during expansion."""
        result, item = self.cutoff_test(board, depth, beta)
        if result:
            return item[0]

        # set starting value below alpha cutoff, best key won't remain None
        value = -10001
        best = None
        e_val = item[4] if item is not None else None

        open_keys = sorted(board.open_keys.keys(),
                           key=lambda k: self.get_evaluation(board, k))
        for key in open_keys:
            board.push(key)
            child = -self.explore(board, depth-1, -beta, -alpha)
            if value < child:
                value = child
                best = key
            board.pop()

            if value >= beta:
                self.table[board] = (value, False, depth, best, e_val)
                return value
            alpha = max(value, alpha)

        self.table[board] = (value, True, depth, best, e_val)
        return value


    def cutoff_test(self, board, depth, beta):
        """End explore recursion if board is terminal, depth is reached, or
        board is transposition or symmetric. Return boolean and item."""
        item = self.table[board]
        result, item = self.table_test(board, depth, beta, item)
        if result:
            return True, item
        result, item = self.terminal_test(board, item)
        if result:
            return True, item
        result, item = self.depth_test(board, depth, item)
        if result:
            return True, item
        return False, item

    def table_test(self, board, depth, beta, item):
        if item is not None:
            value, exact_flag, prev_depth, _, _ = item
            if prev_depth >= depth and (exact_flag or value >= beta):
                return True, item
            else:
                del self.table[board]
        return False, item

    def terminal_test(self, board, item):
        if not board.is_terminal():
            return False, item
        item = (self.get_utility(board), True, 42, None, None)
        self.table[board] = item
        return True, item

    def depth_test(self, board, depth, item):
        if depth:
            return False, item
        e_val = item[4] if item is not None else board.evaluation()
        self.table[board] = item = (e_val, False, depth, None, e_val)
        return True, item


    def get_utility(self, board):
        """Return 0 for draw, -10000 for either player win. Pov of board
        turn."""
        return abs(board.utility())*-10000

    def get_evaluation(self, board, key):
        board.push(key)
        item = self.table[board]
        if item is not None:
            e_val = item[4] if item[4] is not None else item[0]
        else:
            e_val = board.evaluation()
            self.table[board] = (e_val, False, 0, None, e_val)
        board.pop()
        return e_val


    def most_valuable(self, board):
        symm, item = self.table.get_symm_item(board)
        best = item[3] if not symm else board.symm_col(item[3])
        return [best]

    def norm_value(self, board, value):
        """Return value linearly scaled from 0 to 100. From point of view of
        current player at given parent board. POV always opponents, so always
        switch."""
        return (10000 - value) / 20000

class TimeIterativeDeepeningTree(IterativeDeepeningTree):

    def principal_explore(self, alarm, board, depth, alpha=-10000, beta=10000):
        result, item, symm = self.principal_cutoff_test(alarm, board, depth, beta)
        if result:
            return item[0]

        # set starting value below alpha cutoff, best key won't remain None
        value = -10001
        best = None
        e_val = item[4] if item is not None else None

        if depth > 1:
            principal = item[3] if not symm else board.symm_col(item[3])
            board.push(principal)
            child = -self.principal_explore(alarm, board, depth-1, -beta, -alpha)
            if value < child:
                value = child
                best = principal
            board.pop()

            if value >= beta:
                self.table[board] = (value, False, depth, best, e_val)
                return value
            alpha = max(value, alpha)

            open_keys = list(board.open_keys.difference((principal,)))
        else:
            open_keys = list(board.open_keys)

        open_keys.sort(key=lambda k: self.get_evaluation(board, k))

        for key in open_keys:
            board.push(key)
            child = -self.explore(board, depth-1, -beta, -alpha)
            if value < child:
                value = child
                best = key
            board.pop()

            if value >= beta:
                self.table[board] = (value, False, depth, best, e_val)
                return value
            alpha = max(value, alpha)

        self.table[board] = (value, True, depth, best, e_val)
        return value

    def principal_cutoff_test(self, alarm, board, depth, beta):
        """End explore recursion if board is terminal, depth is reached, or
        board is transposition or symmetric. Return boolean and item."""
        symmitem = self.table.get_symm_item(board)
        if symmitem is not None:
            symm, item = symmitem
        else:
            symm = item = None
        if self.alarm_test(alarm):
            return True, item
        result, item = self.table_test(board, depth, beta, item)
        if result:
            return True, item, symm
        result, item = self.terminal_test(board, item)
        if result:
            return True, item, symm
        result, item = self.depth_test(board, depth, item)
        if result:
            return True, item, symm
        return False, item, symm

    def explore(self, alarm, board, depth, alpha=-10000, beta=10000):
        """Add children in depth first procedure. Bookkeep keys, board,
        hash incrementally during visit. Backtrack actions postvisit.
        Check transposition table during expansion."""
        result, item = self.cutoff_test(alarm, board, depth, beta)
        if result:
            return item[0]

        # set starting value below alpha cutoff, best key won't remain None
        value = -10001
        best = None
        e_val = item[4] if item is not None else None

        open_keys = sorted(board.open_keys,
                           key=lambda k: self.get_evaluation(board, k))
        for key in open_keys:
            board.push(key)
            child = -self.explore(alarm, board, depth-1, -beta, -alpha)
            if value < child:
                value = child
                best = key
            board.pop()

            if value >= beta:
                self.table[board] = (value, False, depth, best, e_val)
                return value
            alpha = max(value, alpha)

        self.table[board] = (value, True, depth, best, e_val)
        return value

    def cutoff_test(self, alarm, board, depth, beta):
        """End explore recursion if board is terminal, depth is reached, or
        board is transposition or symmetric. Return boolean and item."""
        item = self.table[board]
        if self.alarm_test(alarm):
            return True, item
        result, item = self.table_test(board, depth, beta, item)
        if result:
            return True, item
        result, item = self.terminal_test(board, item)
        if result:
            return True, item
        result, item = self.depth_test(board, depth, item)
        if result:
            return True, item
        return False, item

    def alarm_test(self, alarm):
        return time.time() > alarm

class MonteCarloTree(Tree):

    # table: value, sims, expanded, [unvisited keys]

    def explore(self, board, iterations):
        if board not in self.table:
            self.add_child(board)
        for _ in range(iterations):
            self.playout(board)

    def playout(self, board, depth=0):
        depth = self.select(board, depth)
        if board.is_terminal():
            self.back_propogate(board, depth, board.winner)
            return
        if not self.expand(board):
            return self.playout(board, depth)
        winner = Simulation(board).winner
        self.back_propogate(board, depth+1, winner)

    def select(self, board, depth=0):
        while self.table[board][2]:
            key = self.bandit(board)
            board.push(key)
            depth += 1
        return depth

    def bandit(self, board):
        return random.choice(list(board.open_keys.keys()))

    def expand(self, board):
        result = False
        symm, item = self.table.get_symm_item(board)
        unvisited_keys = item[3]

        while unvisited_keys:
            key = unvisited_keys.pop()
            if symm:
                key = board.symm_col(key)
            board.push(key)
            if board not in self.table:
                result = True
                break
            board.pop()

        if not unvisited_keys:
            item[2] = True
        if result:
            self.add_child(board)
        return result

    def add_child(self, board):
        self.table[board] = [0, 0, False, list(board.open_keys.keys())]

    def back_propogate(self, board, depth, winner):
        """Increment win share sims count for ancestors up to explore root.
        Use pov of parent, i.e. board.other()."""
        if winner:
            for _ in range(depth):
                item = self.table[board]
                if board.other() == winner:
                    item[0] += 1
                item[1] += 1
                board.pop()
            item = self.table[board]
            if board.other() == winner:
                item[0] += 1
            item[1] += 1
        else:
            for _ in range(depth):
                item = self.table[board]
                item[0] += .5
                item[1] += 1
                board.pop()
            item = self.table[board]
            item[0] += 1
            item[1] += 1

    def children_key_items(self, board):
        result = []
        for key in board.open_keys:
            board.push(key)
            item = self.table[board]
            result.append((key, item[0], item[1]))
            board.pop()
        return result

    def children_key_values(self, board):
        key_items = self.children_key_items(board)
        return [(key, wins/sims) for key, wins, sims in key_items]

    def most_valuable(self, board, children_key_values):
        max_value = max(value for _, value in children_key_values)
        return [key for key, value in children_key_values
                if value == max_value]

    def norm_value(self, board, value):
        return 100*value

class UpperConfidenceBoundTree(MonteCarloTree):

    def __init__(self, exploration_parameter=sqrt(2)):
        super().__init__()
        self.exploration_parameter = exploration_parameter

    def bandit(self, board):
        parent_sims = self.table[board][1]
        key_items = self.children_key_items(board)
        return max(key_items,
                   key=lambda keyitem:
                   self.upper_confidence_bound1(*keyitem[1:], parent_sims))[0]

    def upper_confidence_bound1(self, child_wins, child_sims, parent_sims):
        return (child_wins/child_sims + self.exploration_parameter *
                sqrt(log(parent_sims)/child_sims))

    def children_key_values(self, board):
        key_items = self.children_key_items(board)
        return [(key, sims) for key, wins, sims in key_items]

    def most_valuable(self, board, children_key_values):
        max_sims = max(sims for _, sims in children_key_values)
        return [key for key, sims in children_key_values
                if sims == max_sims]

    def norm_value(self, board, value):
        parent_sims = self.table[board][1]
        return 100*(value / parent_sims)
