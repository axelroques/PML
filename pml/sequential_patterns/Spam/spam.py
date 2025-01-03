
import pandas as pd

from pml.sequential_patterns.Spam.bitmap import Bitmap
from pml.sequential_patterns.Spam.tree import Tree
from pml.base import Algorithm


class Spam(Algorithm):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data)
        
        self.item_col = item_col
        self.sequences = self._prepare_sequences()
        self.n_sequences = len(self.sequences)

        # Convert horizontal db input into the vertical format
        self.item_bitmaps = self._create_vertical_bitmaps()

        # Initialize tree data structure
        # Not used for now, maybe later when implementing 
        # additional pruning strategies
        self.tree = Tree()

    def run(self, min_support):
        """
        Run the Spam algorithm.
        """
        
        # Initialization
        self.frequent_patterns = {}

        # Get frequent 1-itemsets
        L_0 = [b for b in self.item_bitmaps.values()]
        # print('L_0 =', L_0)

        # Process starts with all frequent 1-itemsets
        for sequence in L_0:
            self._DFS_pruning(sequence, L_0, L_0, min_support)


    def _prepare_sequences(self):
        """
        Prepare sequences from a list of sets from the DataFrame.
        Transaction data is a list of list of sets.
        """
        return [list(map(tuple, row)) for row in self.data['items']]
    
    def _create_vertical_bitmaps(self):
        """
        Items are sorted in lexicographic order.
        """

        # Get unique items in all data sequences
        items = sorted(set(
            item for sequence in self.sequences for itemset in sequence for item in itemset
        ))

        # Initialize bitmaps
        bitmaps = {
            item: Bitmap([(item,)]) for item in items
        }

        # Iterate over the sequences
        for i_s, s in enumerate(self.sequences):
            
            # Init bitmaps for all items
            for item in items:
                bitmaps[item].init_section(len(s))

            # Add ones 
            for i_itemset, itemset in enumerate(s):
                for item in itemset:
                    bitmaps[item].update_section(i_s, i_itemset)

        return bitmaps
          

    def _DFS_pruning(self, sequence, S_n, I_n, min_support):
        """
        DFS-Pruning pseudo-algorithm from Ayres et al.
        """

        # Add frequent pattern
        self.frequent_patterns[
            tuple(tuple(itemset) for itemset in sequence.sequence)
        ] = sequence.compute_support()        

        # Initialize empty children's S_n and I_n lists
        S_temp = []
        I_temp = []

        # print('\n\tDFS sequence =', sequence)
        # print('\t --> ADDING frequent pattern')
        # print('\tS_n =', S_n)
        # print('\tI_n =', I_n)

        # Populate S_temp with the frequent items i in S_n
        # if the sequence-extension of the current sequence
        # s with i is frequent
        for item in S_n:

            # Sequence-extension
            seq_ext = sequence.S_step(item)

            # Compute support of the sequence-extension
            support = seq_ext.compute_support()
            if support >= min_support:
                S_temp.append(item)

        # With S_temp now computed, generate new children nodes
        for item in S_temp:
            I_children = [j for j in S_temp if j > item]

            # Continue tree exploration with the new updated sequence
            self._DFS_pruning(sequence.S_step(item), S_temp, I_children, min_support)

        # Populate I_temp with the frequent items i in I_n
        # if the itemset-extension of the current sequence
        # s with i is frequent
        for item in I_n:
            
            # Itemset-extension
            seq_ext = sequence.I_step(item)

            # Cannot have an itemset with two identical item
            if len(set(seq_ext.sequence[-1])) != len(seq_ext.sequence[-1]):
                continue

            # Compute support of the itemset-extension
            support = seq_ext.compute_support()
            if support >= min_support:
                I_temp.append(item)

        # With I_temp now computed, generate new children nodes
        for item in I_temp:
            I_children = [j for j in I_temp if j > item]

            # Continue tree exploration with the new updated sequence
            self._DFS_pruning(sequence.I_step(item), S_temp, I_children, min_support)


if __name__ == "__main__":
    
    data = pd.DataFrame({
        'items': [
            [('bread',), ('milk', 'beer')], [('bread',), ('diaper',), ('beer',), ('egg',)], [('milk',), ('diaper',), ('beer',), ('coke',)],
            [('bread',), ('milk',), ('diaper',), ('beer',)], [('bread',), ('milk',), ('diaper',), ('coke',)]
        ]
    })

    alg = Spam(data, 'items')
    alg.run(min_support=0.4)
    
    print('data =\n', data)
    print('Frequent_patterns =\n', alg.frequent_patterns)
