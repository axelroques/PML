
from collections import Counter, defaultdict
import pandas as pd

from pml.sequential_pattern_mining.CloSPEC.closedhash import ClosedHash
from pml.base import FSPMiner


class CloSPEC(FSPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

        self.C = {
            'min_support': 1,
            'min_gap': 0,
            'max_gap': 2,
            'max_size': 5,
        }
        self._patterns = None
        self.ht = ClosedHash()
        self.infrequent_items = set()

    def run(self, C=None):
        """
        Run the CloSPEC algorithm.

        C is a set of constraints (see self.C for constraint list).
        """
        
        # Save params
        if C is not None:
            if not all(key in self.C for key in C):
                raise KeyError('Invalid constraint.')
            self.C.update(C)

        # Initialization: get all itemsets of size 1
        frequent_items,  self.infrequent_items, occ_by_item = self._get_frequent_items()
        # print('frequent_items =', frequent_items)
        # print('occ_by_item =', occ_by_item)
        # print('infrequent_items =', self.infrequent_items)

        # Pattern growth with constraints
        for item, support in frequent_items.items():
            # print('\nStarting item:', item)

            # Build projected DB
            new_P, new_occurrences = self._proj_DB(item, occ_by_item[item])
            # print('Pattern:', new_P, 'occurrences:', new_occurrences)

            # Start process
            self._pattern_growth(new_P, new_occurrences, support)

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

    def _get_frequent_items(self):
        """
        Get all frequent items that verify C.
        """

        # Get items and their occurrences 
        candidates = defaultdict(list)
        for i_seq, sequence in enumerate(self.sequences):
            for i_itemset, itemset in enumerate(sequence):
                for i_item, item in enumerate(itemset):
                    candidates[item.repr].append((
                        (i_seq, i_itemset, i_item, item.t_s),
                        (i_seq, i_itemset, i_item, item.t_e)
                    ))
        
        # Get item support
        frequent_items = {}
        for candidate in sorted(candidates):
            support = len(set([occ[0][0] for occ in candidates[candidate]]))/self.n_sequences
            if support >= self.C['min_support']:
                frequent_items[candidate] = support

        # Infrequent items
        infrequent_items = set(candidates) - set(frequent_items)

        # Item occurrences
        occ_by_item = {c: candidates[c] for c in frequent_items}

        return frequent_items, infrequent_items, occ_by_item

    def _proj_DB(self, item, item_occ):
        """
        Compute all new pattern occurrences given the addition of the item. 

        Parameters:
            P: current sequential pattern (as list of tuples)
            P_occ: list of occurrences of the pattern [(seq_id, itemset_id, item_id, t_s), ...]
            item: item to extend with (may start with '_' to indicate i-extension)
            item_occ: list of occurrences of the item [((seq_id, itemset_id, item_id, t_s), 
            (seq_id, itemset_id, item_id, t_e)), ...]
            (each occurrence captures the beginning and the end of the pattern). 

        Returns:
            new_P: extended pattern
            new_P_occ: list of new valid occurrences
        """
        return ((item,),), item_occ

    def _pattern_growth(self, P, P_occ, support):
        """
        Main recursive function of a pattern-growth algorithm.
        P is the current sequential pattern.
        P_occurences is a list of all occurrences of the pattern as (seq_id, itemset_id, item_id, t_s).
        """

        ##### Debug ######
        # if sum(len(itemset) for itemset in P) > 4:
        #     raise RuntimeError
        
        # Check anti-monotonic constraints
        ## Minimum support
        constraints = True
        if self.C['min_support'] > support:
            constraints = False
        # Max size constraint check
        if len(P) >= self.C['max_size']:
            constraints = False
        if not constraints:
            # print('\n\t--> Anti-monotonic constraints not satisfied')
            return

        # Closure computation
        prune, closed, extensions_results = self._closure_computation(P, P_occ, support)
        
        # Safe pruning 
        if prune:
            return

        # Add pattern to ClosedHash
        if closed:
            self.ht.insert(P, support)
        
        # Continue with each extension
        # The pseudo-projection was actually already done during the closure computation,
        # as we needed to build extensions and check their support
        extensions, extensions_occ = extensions_results
        for new_P, support in extensions.items():
            
            # Continue process
            new_P_occ = extensions_occ[new_P]
            # print(f'\n\nContinuing with pattern: {new_P}, support={support}, occ={new_P_occ}')
            self._pattern_growth(new_P, new_P_occ, support)
    
    def _closure_computation(self, P, P_occ, support):
        """
        Closure test.
        """

        # Compute left item extensions
        l_item_I_extensions, l_item_I_occ = self._get_item_left_I_extensions(P, P_occ)
        l_item_S_extensions, l_item_S_occ = self._get_item_left_S_extensions(P_occ)
        # print('\n\tLeft item extensions:')
        # print('\tI-extensions =', l_item_I_extensions, l_item_I_occ)
        # print('\tS-extensions =', l_item_S_extensions, l_item_S_occ)

        # Safe pruning (line 1 of Algorithm 2)
        # print('\n\tChecking early pruning')
        if self._safe_pruning(P_occ, l_item_I_occ|l_item_S_occ):
            # print('\t\t--> Safe pruning')
            return True, False, []
        # print('\t\tNo pruning')

        # Compute right item extensions
        if len(P) == 1: # Left and right I-extensions are identical for 1-patterns
            r_item_I_extensions = {i: sup for i, sup in l_item_I_extensions.items()}
            r_item_I_occ = {i: occ for i, occ in l_item_I_occ.items()}
        else:
            r_item_I_extensions, r_item_I_occ = self._get_item_right_I_extensions(P, P_occ)
        r_item_S_extensions, r_item_S_occ = self._get_item_right_S_extensions(P_occ)
        # print('\n\tRight item extensions:')
        # print('\tI-extensions =', r_item_I_extensions, r_item_I_occ)
        # print('\tS-extensions =', r_item_S_extensions, r_item_S_occ)

        # Generate pattern extensions from item extensions
        left_extensions, right_extensions, \
            left_extensions_occ, right_extensions_occ \
                = self._get_extensions(
                    P, P_occ, 
                    l_item_I_extensions, l_item_I_occ, 
                    l_item_S_extensions, l_item_S_occ,
                    r_item_I_extensions, r_item_I_occ,
                    r_item_S_extensions, r_item_S_occ
                )
        # print('\n\tleft_extensions =', left_extensions)
        # print('\tleft_extensions_occ =', left_extensions_occ)
        # print('\n\tright_extensions =', right_extensions)
        # print('\tright_extensions_occ =', right_extensions_occ)
        
        # Check closure using support
        closed = True
        if any(s >= support for s in (left_extensions | right_extensions).values()):
            closed = False
        return False, closed, [right_extensions, right_extensions_occ]

    def _get_item_left_I_extensions(self, P, P_occ):
        """
        Get all possible items for left I-extensions of the current pattern.
        """

        # Iterate over the occurrences of the pattern
        left_extensions_occ = defaultdict(list)
        for occ in P_occ:
            sequence = self.sequences[occ[0][0]]
            itemset = sequence[occ[0][1]]

            # Items at the left of the rightmost item in the pattern's first itemset
            # should not be considered
            i_first_item = [item.repr == P[0][-1] for item in itemset].index(True) + 1
            if i_first_item == len(itemset):
                continue
            
            # Get possible extensions
            for i_item, item in enumerate(itemset[i_first_item:]):
                
                # # Items already present in the pattern should not be considered 
                # if any(item.repr == i for i in P[0]):
                #     continue

                # Infrequent items should not be considered
                if item.repr in self.infrequent_items:
                    continue

                # Add extension: occ depends on the position of the items in the itemset
                if occ[0][1] == occ[1][1]: # essentially len(P) == 1
                    max_item_pos = max(occ[1][2], i_first_item+i_item)
                else: # otherwise max occ does not change
                    max_item_pos = occ[1][2]
                left_extensions_occ[f'_{item.repr}'].append((
                    (occ[0][0], occ[0][1], min(occ[0][2], i_first_item+i_item), item.t_s),
                    (occ[1][0], occ[1][1], max_item_pos, occ[1][-1])
                ))

        # Support computation
        left_extensions = {}
        for candidate in sorted(left_extensions_occ):
            support = len(set([occ[0][0] for occ in left_extensions_occ[candidate]]))/self.n_sequences
            left_extensions[candidate] = support
    
        return left_extensions, left_extensions_occ

    def _get_item_right_I_extensions(self, P, P_occ):
        """
        Get all possible items for right I-extensions of the current pattern.
        """

        # Iterate over the occurrences of the pattern
        right_extensions_occ = defaultdict(list)
        for occ in P_occ:
            sequence = self.sequences[occ[1][0]]
            itemset = sequence[occ[1][1]]

            # Items at the left of the rightmost item in the pattern's last itemset
            # should not be considered
            i_first_item = [item.repr == P[-1][-1] for item in itemset].index(True) + 1
            if i_first_item == len(itemset):
                continue
            
            # Get possible extensions
            for i_item, item in enumerate(itemset[i_first_item:]):
                
                # # Items already present in the pattern should not be considered 
                # if any(item.repr == i for i in P[-1]):
                #     continue

                # If item is infrequent it should not be considered
                if item.repr in self.infrequent_items:
                    continue

                # Add extension: occ depends on the position of the items in the itemset 
                right_extensions_occ[f'_{item.repr}'].append((
                    (occ[0][0], occ[0][1], occ[0][2], occ[0][-1]),
                    (occ[1][0], occ[1][1], max(occ[1][2], i_first_item+i_item), item.t_e)
                ))

        # Support computation
        right_extensions = {}
        for candidate in sorted(right_extensions_occ):
            support = len(set([occ[0][0] for occ in right_extensions_occ[candidate]]))/self.n_sequences
            right_extensions[candidate] = support
    
        return right_extensions, right_extensions_occ

    def _get_item_left_S_extensions(self, P_occ):
        """
        Get all possible items for left S-extensions of the current pattern.
        """

        # Iterate over the occurrences of the pattern
        left_extensions_occ = defaultdict(list)
        for occ in P_occ:
            sequence = self.sequences[occ[0][0]]

            # If occ occurs in the first itemset of the sequence, no possible left S-extensions
            i_start_itemset = occ[0][1]
            if i_start_itemset == 0:
                continue

            # Early stop condition if max_gap not respected
            early_stop = False

            # Iterate over the itemsets before
            for i_itemset, itemset in enumerate(sequence[i_start_itemset-1::-1]):
                if early_stop:
                    break
                
                # Min and max gap constraints can be applied at the itemset scale as all items in 
                # the itemset appear at the same time
                if self.C['min_gap']:
                    first_item = itemset[0]
                    gap = (occ[0][-1]-first_item.t_s).total_seconds()
                    if gap <= self.C['min_gap']:
                        continue 
                if self.C['max_gap']:
                    first_item = itemset[0]
                    gap = (occ[0][-1]-first_item.t_s).total_seconds()
                    if gap > self.C['max_gap']:
                        early_stop = True
                        break 
                
                # Iterate over the items and ensure max gap constraint
                for i_item, item in enumerate(itemset):
                    
                    # If item is infrequent it should not be considered
                    if item.repr in self.infrequent_items:
                        continue
                    
                    left_extensions_occ[item.repr].append((
                        (occ[0][0], i_start_itemset-i_itemset-1, i_item, item.t_s),
                        occ[1],
                    ))

        # Support computation
        left_extensions = {}
        for candidate in sorted(left_extensions_occ):
            support = len(set([occ[0][0] for occ in left_extensions_occ[candidate]]))/self.n_sequences
            left_extensions[candidate] = support
    
        return left_extensions, left_extensions_occ

    def _get_item_right_S_extensions(self, P_occ):
        """
        Get all possible items for right S-extensions of the current pattern.
        """

        # Iterate over the occurrences of the pattern
        right_extensions_occ = defaultdict(list)
        for occ in P_occ:
            sequence = self.sequences[occ[1][0]]

            # If occ occurs in the last itemset of the sequence, no possible right S-extensions
            i_start_itemset = occ[1][1]
            if i_start_itemset == len(sequence):
                continue

            # Early stop condition if max_gap not respected
            early_stop = False

            # Iterate over the itemsets before
            for i_itemset, itemset in enumerate(sequence[i_start_itemset+1:]):
                if early_stop:
                    break

                # Min and max gap constraints can be applied at the itemset scale as all items in 
                # the itemset appear at the same time
                if self.C['min_gap']:
                    first_item = itemset[0]
                    gap = (first_item.t_s-occ[1][-1]).total_seconds()
                    if gap < self.C['min_gap']:
                        continue 
                if self.C['max_gap']:
                    first_item = itemset[0]
                    gap = (first_item.t_s-occ[1][-1]).total_seconds()
                    if gap > self.C['max_gap']:
                        early_stop = True
                        break 
                
                # Iterate over the items and ensure max gap constraint
                for i_item, item in enumerate(itemset):
                    
                    # If item is infrequent it should not be considered
                    if item.repr in self.infrequent_items:
                        continue

                    right_extensions_occ[item.repr].append((
                        occ[0],
                        (occ[1][0], i_start_itemset+i_itemset+1, i_item, item.t_e),
                    ))

        # Support computation
        right_extensions = {}
        for candidate in sorted(right_extensions_occ):
            support = len(set([occ[0][0] for occ in right_extensions_occ[candidate]]))/self.n_sequences
            right_extensions[candidate] = support
    
        return right_extensions, right_extensions_occ
    
    def _safe_pruning(self, P_occ, l_item_occ):
        """
        Check if the pattern can be safely pruned according to line 1 of Algorithm 2.
        """

        # Get combined support of items (I + S extensions)
        item_occ = Counter()
        for item, occ in l_item_occ.items():
            item_occ[item.strip('_')] += len(occ)

        # Check "closure"
        if any(len(P_occ) == occ for occ in item_occ.values()):
            return True
        return False

    def _get_extensions(
        self, P, P_occ, 
        l_item_I_extensions, l_item_I_occ, 
        l_item_S_extensions, l_item_S_occ,
        r_item_I_extensions, r_item_I_occ,
        r_item_S_extensions, r_item_S_occ
    ):
        """
        Generate actual extensions of the pattern from item extensions.
        """

        # Merge I- and S-extensions
        if len(P) == 1: # Left and right I-extensions are identical, let's keep the right ones
            l_item_extensions = l_item_S_extensions
            l_item_occ = l_item_S_occ
        else:
            l_item_extensions = l_item_I_extensions | l_item_S_extensions
            l_item_occ = l_item_I_occ | l_item_S_occ
        r_item_extensions = r_item_I_extensions | r_item_S_extensions
        r_item_occ = r_item_I_occ | r_item_S_occ

        # Left extensions
        # print('\n\t\tLeft extensions:')
        left_extensions = defaultdict()
        left_extensions_occ = defaultdict()
        for item in l_item_extensions:

            # Combine item with the current pattern
            if item.startswith('_'):
                # I-extension
                new_P = P[:-1] + (tuple(sorted(P[-1] + (item[1:],))),)
            else:
                # S-extension
                new_P = P + ((item,),)
            # print(f'\t\t\titem={item}, new_P={new_P}')

            # Save pattern support (equal to item support)
            new_P = tuple(e for e in new_P)
            left_extensions[new_P] = l_item_extensions[item]
            left_extensions_occ[new_P] = l_item_occ[item]

        # Right extensions
        # print('\n\t\tRight extensions:')
        right_extensions = defaultdict()
        right_extensions_occ = defaultdict()
        for item in r_item_extensions:

            # Combine item with the current pattern
            if item.startswith('_'):
                # I-extension
                new_P = P[:-1] + (tuple(sorted(P[-1] + (item[1:],))),)
            else:
                # S-extension
                new_P = P + ((item,),)
            # print(f'\t\t\titem={item}, new_P={new_P}')
            
            # Save pattern support (equal to item support)
            new_P = tuple(e for e in new_P)
            right_extensions[new_P] = r_item_extensions[item]
            right_extensions_occ[new_P] = r_item_occ[item]
            
        return left_extensions, right_extensions, left_extensions_occ, right_extensions_occ

    @property
    def patterns(self):
        """
        Return patterns
        """
        if self._patterns == None:
            self._patterns = self.ht.patterns
        return self._patterns


if __name__ == "__main__":

    from pml.utils.symbol import Symbol 
    from datetime import datetime, time

    dummy_date = datetime.today().date()
    t0 = datetime.combine(dummy_date, time(second=0))
    t1 = datetime.combine(dummy_date, time(second=1))
    t2 = datetime.combine(dummy_date, time(second=2))
    t3 = datetime.combine(dummy_date, time(second=3))
    t4 = datetime.combine(dummy_date, time(second=4))
    t5 = datetime.combine(dummy_date, time(second=5))
    
    # Basic test with Table 1
    # data = pd.DataFrame({
    #     'items': [
    #         [(Symbol('a_0', t0, t1),), (Symbol('b_0', t1, t2),), (Symbol('c_0', t2, t3),), (Symbol('d_0', t3, t4),),],
    #         [(Symbol('a_0', t0, t1),), (Symbol('b_0', t1, t2),), (Symbol('c_0', t2, t3),),],
    #         [(Symbol('a_0', t0, t1), Symbol('b_0', t0, t1),), (Symbol('d_0', t1, t2),), (Symbol('b_0', t2, t3),), (Symbol('c_0', t3, t4),), (Symbol('d_0', t4, t5),),],
    #     ]
    # })
    
    # # Check left and right I-extensions to avoid generating redundant patterns
    # data = pd.DataFrame({
    #     'items': [
    #         [(Symbol('a_0', t0, t1), Symbol('b_0', t1, t2), Symbol('c_0', t2, t3),), (Symbol('d_0', t3, t4),),],
    #         [(Symbol('a_0', t0, t1), Symbol('b_0', t1, t2), Symbol('c_0', t2, t3),),],
    #         [(Symbol('a_0', t0, t1), Symbol('b_0', t0, t1), Symbol('c_0', t2, t3),), (Symbol('d_0', t1, t2),), (Symbol('b_0', t2, t3),),],
    #     ]
    # })

    # Another example from the article
    data = pd.DataFrame({
        'items': [
            [(Symbol('a', t0, t1),), (Symbol('a', t1, t2), Symbol('b', t1, t2), Symbol('c', t1, t2),), (Symbol('c', t2, t3),),],
            [(Symbol('a', t0, t1),), (Symbol('a', t1, t2), Symbol('b', t1, t2), Symbol('c', t1, t2),), (Symbol('c', t2, t3), Symbol('e', t2, t3)),],
        ]
    })
    print(data)
    alg = CloSPEC(data, 'items')
    alg.run({'max_gap': 5, 'min_gap': 0})
    print('\n\nPatterns:\n', alg.patterns)