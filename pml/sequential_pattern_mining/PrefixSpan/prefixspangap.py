
from collections import defaultdict
import pandas as pd

from pml.base import FSPMiner

"""
WIP, requires using a Symbol class to handle temporal constraints.
"""
class PrefixSpan(FSPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

    def run(self, min_support, max_gap=None, max_size=None):
        """
        Run the PrefixSpan algorithm.
        """
        
        # Save params
        self.min_support = min_support
        self.max_gap = max_gap
        self.max_size = max_size

        # Initialization
        self.frequent_patterns = {}

        # Process starts with the complete db and the empty set
        self._pattern_growth([], [])

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
    
    def _pattern_growth(self, sequence, occurrences):
        """
        Main recursive function of a pattern-growth algorithm.
        db is a list of occurrences (seq_id, itemset_id, item_id, t_s).
        sequence is the current frequent sequence.
        """
        # print('\nseq =', sequence)
        # print('occurrences =', occurrences)

        # Max size constraint check
        if len(sequence) >= self.max_size:
            # print('reached max_size constraint')
            return
        
        # Scan db to find all frequent items and their occurrence
        f_list, occ_by_item = self._find_frequent_items(occurrences)
        # print('\nf_list =', f_list)
        # print('occ_by_item =', occ_by_item)

        # Divide search space
        for item, support in f_list.items():
            # print('\titem =', item)
            # print('\tocc =', occ_by_item[item])

            # Get valid projections from all current occurrences
            new_sequence, new_occurrences = self._multi_proj(
                sequence, occurrences, item, occ_by_item[item]
            )
            # print('\n\tnew_sequence =', new_sequence)
            # print('\tnew_occurrences =', new_occurrences)

            # Save frequent pattern
            self.frequent_patterns[tuple(e for e in new_sequence)] = support

            # Continue depth-first search
            self._pattern_growth(new_sequence, new_occurrences)


    def _find_frequent_items(self, occurrences):
        """
        Find all frequent items in db. 
        db is a list of sequences. 
        Returns a dictionary of frequent items as {item: support}.
        """
        # print('finding frequent items')

        f_list = defaultdict(list)
        # When db is empty, a full scan is necessary
        if not occurrences:
            for i_seq, sequence in enumerate(self.sequences):
                for i_itemset, itemset in enumerate(sequence):
                    for i_item, item in enumerate(itemset):
                        f_list[item].append((i_seq, i_itemset, i_item, item.t_s))

        # Otherwise, just check for the symbols within max_gap
        else:
            for occ in occurrences:
                sequence = self.sequences[occ[0]]
                # print('\tseq =', sequence)
                # print('\tocc =', occ)
                # Early stop condition if max_gap not respected
                early_stop = False
                for i_itemset, itemset in enumerate(sequence[occ[1]:]):
                    # print('\t\titemset =', i_itemset+occ[1], itemset)
                    if early_stop:
                        break
                    # i-extensions
                    if i_itemset == 0:
                        # print('\t\t\ti-ext')
                        for i_item, item in enumerate(itemset[occ[2]+1:]):
                            # print('\t\t\titem =', i_item+occ[2]+1, item)
                            f_list[f'_{item}'].append((
                                occ[0], i_itemset+occ[1], i_item+occ[2]+1, item.t_s
                            ))
                    # s-extensions
                    else:
                        # print('\t\t\ts-ext')
                        for i_item, item in enumerate(itemset):
                            # print('\t\t\titem =', i_item, item)
                            # Ensure max_gap constraint
                            if self.max_gap:
                                gap = (item.t_s - occ[-1]).total_seconds()
                                if gap > self.max_gap:
                                    early_stop = True
                                    break 
                            f_list[item.repr].append((
                                occ[0], i_itemset+occ[1], i_item, item.t_s
                            ))

        frequent_items = {}
        for candidate in sorted(f_list):
            # print('candidate =', candidate, f_list[candidate])
            support = len(set([occ[0] for occ in f_list[candidate]]))/self.n_sequences
            if support >= self.min_support:
                frequent_items[candidate] = support
    
        return frequent_items, {c: f_list[c] for c in frequent_items}
    
    def _multi_proj(self, sequence, seq_occ, item, item_occ):
        """
        Compute all new sequence occurrences given the addition of the item. 

        Parameters:
            sequence: current frequent sequence (as list of tuples)
            seq_occ: list of occurrences of the sequence [(seq_id, itemset_id, item_id, t_s), ...]
            item: item to extend with (may start with '_' to signal i-extension)
            item_occ: list of occurrences of the item [(seq_id, itemset_id, item_id, t_s), ...]
            max_gap: max allowed gap in seconds between two items

        Returns:
            new_sequence: extended pattern
            new_occurrences: list of new valid occurrences
        """
        # print('\nmulti proj')

        # Combine item with current sequence
        extension_type = None
        if item.startswith('_'):
            # i-extension
            new_sequence = sequence[:-1] + \
                [tuple(sorted(sequence[-1] + (item[1:],)))]
            extension_type = 'i-extension'
        else:
            # s-extension
            # print('\ts-extension')
            new_sequence = sequence + [(item,)]
            extension_type = 's-extension'
        # print('\tnew_sequence =', new_sequence, extension_type)

        # Return item occurrences if it's the first pass
        if not seq_occ:
            # print('\t--> first pass')
            return new_sequence, item_occ

        # Index item_occ by sequence ID for fast lookup
        item_occ_index = defaultdict(list)
        for occ in item_occ:
            item_occ_index[occ[0]].append(occ)
        # print('\titem_occ_index =', item_occ_index)

        # Generate new possible occurrences
        new_occurrences = []
        for s_occ in seq_occ:
            # print('\t\ts_occ =', s_occ)
            seq_id, itemset_id, item_id, t_s = s_occ

            # Early stop if item not in sequence
            if seq_id not in item_occ_index:
                # print('\t\tearly stop')
                continue
            
            # Check occurrence per sequence
            for i_occ in item_occ_index[seq_id]:
                # print('\t\t\ti_occ =', i_occ)
                i_seq_id, i_itemset_id, i_item_id, i_t_s = i_occ
                if extension_type == 'i-extension':
                    # Same itemset, later item
                    if i_itemset_id == itemset_id and i_item_id > item_id:
                        # print('\t\t\t--> apended')
                        new_occurrences.append((seq_id, i_itemset_id, i_item_id, i_t_s))
                else:  # s-extension
                    if i_itemset_id > itemset_id:
                        if self.max_gap is not None:
                            gap = (i_t_s - t_s).total_seconds()
                            if gap > self.max_gap:
                                continue
                        # print('\t\t\t--> apended')
                        new_occurrences.append((seq_id, i_itemset_id, i_item_id, i_t_s))

        return new_sequence, new_occurrences
    

if __name__ == "__main__":

    data = pd.DataFrame({
        'items': [
            [('a',), ('a', 'c', 'b',), ('a', 'c',), ('d',), ('c', 'f',)],
            [('a', 'd',), ('c',), ('b', 'c',), ('a', 'e',),],
            [('e', 'f',), ('a', 'b',), ('d', 'f',), ('c',), ('b',),],
            [('e',), ('g',), ('a', 'f',), ('c',), ('b'), ('c'),],
        ]
    })

    alg = PrefixSpan(data, 'items')
    alg.run(min_support=0.3, max_gap=2, max_size=3)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)