
from collections import Counter
import pandas as pd

from pml.base import Algorithm


class PrefixSpan(Algorithm):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data)
        
        self.item_col = item_col
        self.sequences = self._prepare_sequences()
        self.n_sequences = len(self.sequences)

    def run(self, min_support):
        """
        Run the PrefixSpan algorithm.
        """
        
        # Initialization
        self.frequent_patterns = {}

        # Process starts with the complete db and the empty set
        self._pattern_growth(self.sequences, [], min_support)

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
    
    def _pattern_growth(self, db, sequence, min_support):
        """
        Main recursive function of a pattern-growth algorithm.
        db is a transaction database.
        sequence is  the current itemset.
        """
        
        # Scan db to find all frequent items
        f_list = self._find_frequent_items(db, min_support)
        # print('\nf_list =', f_list)

        # Divide search space
        for item, support in f_list.items():
            # print('\titem =', item)

            # Combine item with current sequence
            if item.startswith('_'):
                # i-extension
                new_sequence = sequence[:-1] + \
                    [tuple(sorted(sequence[-1] + (item[1:],)))]
            else:
                # s-extension
                # print('\ts-extension')
                new_sequence = sequence + [(item,)]

            # print('\tnew_sequence =', new_sequence)

            # Save frequent pattern
            self.frequent_patterns[
                tuple(e for e in new_sequence)
            ] = support

            # Project db
            db_proj = self._project_db(db, item.strip('_'))
            # print('\n\tprojection =', db_proj)

            # Continue depth-first search
            self._pattern_growth(db_proj, new_sequence, min_support)


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
    
    @staticmethod
    def _project_db(db, item):
        """
        Project database db according according to the item. 
        Itemsets in the sequences are assumed to be sorted. 
        """

        # Initialize the projected database
        db_proj = []

        # Iterate over the sequences
        for sequence in db: 

            # Iterate over the elements
            for raw_element in sequence:

                # Element might contain items with a trailing '_'
                element = tuple(e.strip('_') for e in raw_element)

                # Check if the item appears in the transaction
                if not item in element:
                    continue

                # Find the index of the element in the sequence
                i_element = sequence.index(raw_element)

                # Find the index of the item in the element
                i_item = element.index(item)

                # If the item appears at the last position in the element,
                # this element is not returned in the new sequence
                if i_item == len(element) - 1:
                    db_proj.append(sequence[i_element+1:])
                # Otherwise, the items before the item are removed and all
                # next items receive an '_'
                else:
                    first_element = tuple(
                        f'_{item}' for item in sequence[i_element][i_item+1:]
                    )
                    db_proj.append([first_element] + sequence[i_element+1:])

                break

        return db_proj
    

if __name__ == "__main__":

    # data = pd.DataFrame({
    #     'items': [
    #         [('bread',), ('milk',)], [('bread',), ('diaper',), ('beer',), ('egg',)], [('milk',), ('diaper',), ('beer',), ('coke',)],
    #         [('bread',), ('milk',), ('diaper',), ('beer',)], [('bread',), ('milk',), ('diaper',), ('coke',)]
    #     ]
    # })
    data = pd.DataFrame({
        'items': [
            [('a',), ('a', 'c', 'b',), ('a', 'c',), ('d',), ('c', 'f',)],
            [('a', 'd',), ('c',), ('b', 'c',), ('a', 'e',),],
            [('e', 'f',), ('a', 'b',), ('d', 'f',), ('c',), ('b',),],
            [('e',), ('g',), ('a', 'f',), ('c',), ('b'), ('c'),],
        ]
    })

    alg = PrefixSpan(data, 'items')
    alg.run(min_support=0.3)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)