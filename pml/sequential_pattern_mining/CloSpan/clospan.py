
from collections import Counter
import pandas as pd

from pml.base import FSPMiner
from .PSL import PSL


""" 
WIP
"""
class CloSpan(FSPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

    def run(self, min_support):
        """
        Run the CloSpan algorithm.
        """
        
        self.min_support = min_support

        # Initialization
        self.frequent_patterns = {}
        L = PSL()

        # Process starts with the complete db and the empty set
        self._pattern_growth(self.sequences, [], L, min_support)

    def _prepare_sequences(self):
        """
        Prepare sequences from a list of sets from the DataFrame.
        Transaction data is a list of list of sets.
        Items need to be sorted in lexicographic order.
        """
        return [
            list(map(lambda t: tuple(sorted(t)), row)) 
            for row in self.data['items']
        ]
    
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

        frequent_items = {}
        for candidate in sorted(global_counter):
            if (global_counter[candidate]) >= min_support:
                frequent_items[candidate] = global_counter[candidate]

        return frequent_items

    def _pattern_growth(self, db, sequence, L, min_support):
        """
        Main recursive function of the CloSpan algorithm.
        db is a transaction database.
        sequence is the current frequent sequence.
        """
        
        
    

if __name__ == "__main__":

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
            [('a', 'f'), ('d',), ('e',), ('a',),],
            [('e',), ('a',), ('b'),],
            [('e',), ('a', 'b', 'f',), ('b', 'd', 'e'),],
        ]
    })

    alg = CloSpan(data, 'items')
    alg.run(min_support=0.3)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)