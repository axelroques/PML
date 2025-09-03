
from itertools import combinations
from collections import Counter
import pandas as pd
import numpy as np

from pml.base import FSPMiner


""" 
WIP
"""
class FreeSpan(FSPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

    def run(self, min_support):
        """
        Run the FreeSpan algorithm.
        """
        
        # Initialization
        self.frequent_patterns = {}

        # Process starts with the complete db and the empty set
        self._pattern_growth(self.sequences, [], min_support)

    def _prepare_sequences(self):
        """
        Prepare sequences from a list of sets from the DataFrame.
        Transaction data is a list of list of sets.
        Items are sorted in lexicographic order.
        """
        return [
            list(map(lambda t: tuple(sorted(t)), row)) 
            for row in self.data['items']
        ]
    
    def _pattern_growth(self, db, sequence, min_support):
        """
        Main recursive function of a pattern-growth algorithm.
        db is a transaction database.
        sequence is  the current itemset.
        """

        # Scan db to find all frequent items
        f_list = self._find_frequent_items(db, min_support)
        print('\nf_list =', f_list)

        # Build frequent item matrix
        F = self._build_F(db, list(f_list.keys()))
        # To print F:
        # for i in range(len(F)):
        #     for j in range(i, len(F)):
        #         print(f'F[{list(f_list.keys())[i]}, {list(f_list.keys())[j]}] = {F[i, j]}')

    def _find_frequent_items(self, db, min_support):
        """
        Find all frequent items in db. 
        db is a list of sequences. 
        Returns a dictionary of frequent items as {item: support}.
        """
        
        global_counter = Counter()
        for sequence in db:
            counter = Counter()
            for element in sequence:
                for item in element:
                    if item in counter:
                        continue
                    counter[item] += 1/self.n_sequences
            global_counter += counter

        # Sort elements in "support descending order" and then lexicographically
        sorted_candidates = sorted(
            global_counter.items(),
            key=lambda item: (-item[1], item[0])  # Sort by negative support, then lexicographically
        )
        frequent_items = {}
        for candidate, support in sorted_candidates:
            if support >= min_support:
                frequent_items[candidate] = support
            else:
                break
        return frequent_items

    @staticmethod
    def _build_F(db, f_items):
        """
        Build the frequent item matrix.
        f_items is a list of frequent items sorted by decreasing order
        of support.
        """

        F_global = np.zeros((len(f_items), len(f_items)), dtype=(float, 3))

        # Iterate over the sequences in the db
        for sequence in db:
            F = np.zeros((len(f_items), len(f_items)), dtype=(float, 3))

            # Keep track of the items encountered
            states = {item: None for item in f_items}

            # Iterate over the elements
            for i_element, element in enumerate(sequence):

                # Increase the count of elements that appear together
                pairwise_combinations = list(
                    combinations((e for e in element if e in f_items), 2)
                )
                for pair in pairwise_combinations:
                    i_1 = f_items.index(pair[0])
                    i_2 = f_items.index(pair[1])
                    if i_1 < i_2:
                        if F[i_1, i_2][2] != 0:
                            continue
                        else:
                            F[i_1, i_2][2] += 1
                    else:
                        if F[i_2, i_1][2] != 0:
                            continue
                        else:
                            F[i_2, i_1][2] += 1

                # Increase the count of elements that appear consecutively
                delayed_update = {item: None for item in element}
                for item in element:
                    if item not in states:
                        continue

                    # Update same item combination
                    if (states[item] is not None) and (states[item] != i_element):
                        i = f_items.index(item)
                        if F[i, i][0] == 0:
                            F[i, i][0] += 1
                    
                    # Other combinations
                    delayed_update[item] = i_element
                    for f_item in f_items:
                        if states[f_item] is None:
                            continue

                        state_1 = i_element
                        state_2 = states[f_item]                        
                        i_1 = f_items.index(item)
                        i_2 = f_items.index(f_item) 
            
                        # Skip same item or item from the same element
                        if (item == f_item) or (state_1 == state_2):
                            continue                     
                        if i_1 < i_2:
                            if state_1 < state_2:
                                i = 0
                            else:
                                i = 1
                            if F[i_1, i_2][i] != 0:
                                continue
                            else:
                                F[i_1, i_2][i] += 1
                        else:
                            if state_1 < state_2:
                                i = 1
                            else:
                                i = 0
                            if F[i_2, i_1][i] != 0:
                                continue
                            else:
                                F[i_2, i_1][i] += 1

                # Update the state of the items in the element
                for item, state in delayed_update.items():
                    states[item] = state

            # Update F
            F_global += F
                    
        return F_global

    def _generate_length_2_patterns(self, cell, item_1, item_2, min_support):
        """
        Given a cell from matrix F, generate all length-2 sequential patterns.
        """
        patterns = {}
        if cell[0] >= min_support:
            patterns[tuple((item_1,) (item_2))] = cell[0] / self.n_sequences
        if cell[1] >= min_support:
            patterns[tuple((item_2,) (item_1))]= cell[1] / self.n_sequences
        if cell[2] >= min_support:
            patterns[tuple(sorted([item_1, item_2]))] = cell[2] / self.n_sequences
        return patterns
    
    @staticmethod
    def _generate_item_annotations(F, f_items, min_support):
        """
        Generate annotations on item-repeating patterns. 
        """

        for i in range(len(F)):
            annotations = []

            for j in range(i, len(F)):
                print(f'F[{f_items[i]}, {f_items[j]}] = {F[i, j]}')

                # Diagonal elements
                if i == j:
                    if F[i, j][0] < min_support:
                        continue
                    annotations.append(tuple((f_items[i],), (f_items[j],)))
                    continue

                # i != j
                annotation = []
                if F[i, i][0] >= min_support:
                    annotation.append(f_items[i] + '+')
                else:
                    annotation.append(f_items[i])
                if F[j, j][0] >= min_support:
                    annotation.append(f_items[j] + '+')
                else:
                    annotation.append(f_items[j])
                if not sum(1 for x in F[i, j] if x >= min_support) == 1:
                    annotation = set(annotation)
                annotations.append(annotation)
            
            yield annotations
                    
    @staticmethod
    def _generate_db_annotations(F, f_items, min_support):
        """
        Generate annotations on projected databases. 
        """

        for i in range(len(F)):
            annotations = []
            row = F[i, :]

            # Check how many cells from the row are frequent
            if sum(
                sum(1 for element in cell if element >= 2) >= 1 for cell in row
            ) < 2:
                yield annotations

            # In what follows, there are at least two frequent cells
            for j in range(1, len(row)-1):

                # Check if cell has at least one frequent pattern
                if sum(1 for x in F[i, j] if x >= min_support) >= 1:
                    
                    # Get pattern
                    patterns = []
                    for i_x, x in F[i, j]:
                        if x < min_support:
                            continue
                        if i_x == 0:
                            patterns.append(
                                tuple((f_items.index(i),), (f_items.index(j),))
                            )
                        elif i_x == 1:
                            patterns.append(
                                tuple((f_items.index(j),), (f_items.index(i),))
                            )
                        else:
                            patterns.append(
                                tuple((f_items.index(i), f_items.index(j),))
                            )

                    # Iterate over the columns before j
                    for k in range(j):

                        # Check if cell has at least one frequent pattern
                        if sum(1 for x in F[i, k] if x >= min_support) >= 1:

                            # Add an annotation for each possible pattern
                            for p in patterns:
                                annotations.append(tuple(p, f_items.index(k)))

            yield annotations


    @staticmethod
    def _generate_candidates_from_annotations(annotations):
        """
        Generate a set of candidate patterns from the annotations.
        """

        for a in annotations:
            pass



if __name__ == "__main__":

    # data = pd.DataFrame({
    #     'items': [
    #         [('bread',), ('milk',)], [('bread',), ('diaper',), ('beer',), ('egg',)], [('milk',), ('diaper',), ('beer',), ('coke',)],
    #         [('bread',), ('milk',), ('diaper',), ('beer',)], [('bread',), ('milk',), ('diaper',), ('coke',)]
    #     ]
    # })
    # data = pd.DataFrame({
    #     'items': [
    #         [('a',), ('a', 'c', 'b',), ('a', 'c',), ('d',), ('c', 'f',)],
    #         [('a', 'd',), ('c',), ('b', 'c',), ('a', 'e',),],
    #         [('e', 'f',), ('a', 'b',), ('d', 'f',), ('c',), ('b',),],
    #         [('e',), ('g',), ('a', 'f',), ('c',), ('b'), ('c'),],
    #     ]
    # })
    data = pd.DataFrame({
        'items': [
            [('b', 'd',), ('c',), ('b',), ('a', 'c',),],
            [('b', 'f',), ('c', 'e',), ('b',), ('f', 'g',),],
            [('a', 'h',), ('b', 'f',), ('a',), ('b',), ('f',),],
            [('b', 'e',), ('c', 'e',), ('d',),],
            [('a',), ('b', 'd',), ('b',), ('c',), ('b',), ('a', 'd', 'e',),],
        ]
    })

    alg = FreeSpan(data, 'items')
    alg.run(min_support=0.25)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)