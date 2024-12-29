
from collections import Counter
import pandas as pd

from pml.sequential_patterns.GSP.hash_tree import HashTree
from pml.base import Algorithm


class GSP(Algorithm):
    """
    GSP from Srikant and Agrawal, Mining Sequential Patterns: Generalizations 
    and Performance Improvements (1996).
    This implementation handles time constraints only. 
    """

    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data)

        self.item_col = item_col
        self.sequences = self._prepare_sequences()
        self.n_sequences = len(self.sequences)

        # "Alternate db" representation to find item occurrences efficiently
        self.vert_temp_repr = self._create_vert_temp_repr()

        # Arbitrary time vector that should be removed later on
        self.t = [
            [i for i, _ in enumerate(s)]
            for s in self.sequences
        ]

    def run(self, min_support=0.4, min_gap=0, max_gap=100, window_size=0):
        """
        GSP algorithm.
        """

        self.frequent_patterns = {}

        # k = 1: first scan to compute support of 1-sequences (i.e., 1-itemsets)
        counter = Counter()
        for sequence in self.sequences:
            for itemset in sequence:
                for item in itemset:
                    counter[item] += 1/self.n_sequences

        for candidate in counter:
            if (counter[candidate]) >= min_support:
                self.frequent_patterns[candidate] = counter[candidate]

        # k >= 2
        k = 2
        L_k = [[tuple([item])] for item in self.frequent_patterns]
        while L_k:
            print('\nL_k =', L_k)

            # Generate k-sequences
            C_k = self._generate_candidates(L_k, k)
            print('C_k =', C_k)

            # Prune candidates
            C_k = self._prune_candidates(L_k, C_k, k)
            # print('candidates =', C_k)

            # Compute support and retain frequent candidates
            L_k, frequent_candidates = self._compute_support(C_k, min_support, min_gap, max_gap, window_size)
            self.frequent_patterns.update(frequent_candidates)

            k += 1

    def _prepare_sequences(self):
        """
        Prepare sequences from a list of sets from the DataFrame.
        Transaction data is a list of list of sets.
        """
        return [list(map(tuple, row)) for row in data['items']]
    
    def _create_vert_temp_repr(self):
        """
        For each sequence, create a map of items to their temporal occurrences.
        To be replaced with item actual time.
        """
        time_lists = []
        for sequence in self.sequences:
            time_map = {}
            for t, itemset in enumerate(sequence):
                for item in itemset:
                    if item not in time_map:
                        time_map[item] = set()
                    time_map[item].add(t)
            time_lists.append(time_map)
        return time_lists
    
    def _generate_candidates(self, L_k, k):
        """
        Generate candidate sequences of size k+1 from existing k-sequences.
        """

        C_k = []

        # When joining L1 with itself, all items should be added as part
        # of an itemset and as a separate element 
        if k == 2:
            for i in range(len(L_k)):
                for j in range(len(L_k)):
                    if i == j:
                        continue
                    # i-extension
                    C_k.append([L_k[i][-1] + L_k[j][-1]]) 
                    # s-extension
                    C_k.append(L_k[i] + [L_k[j][-1]])

        # When k > 2
        else:
            for i in range(len(L_k)):
                for j in range(len(L_k)):
                    if i == j:
                        continue
                    # Subsequence check
                    if not self._join_check(L_k[i], L_k[j]):
                        continue
                    # Create a new sequence
                    new_item, multi = self._get_element(L_k[j], pos=-1)
                    if multi:
                        new_candidate = L_k[i][:-1] + [L_k[i][-1] + (new_item,)]
                    else:
                        new_candidate = L_k[i] + [(new_item,)]
                    if new_candidate not in C_k:
                        C_k.append(new_candidate)
        
        return C_k
    
    def _join_check(self, s1, s2):
        """
        s1 joins with s2 if the subsequence obtained by dropping the first item of 
        s1 is the same as the subsequence obtained by dropping the last item of s2.
        """

        # s1
        first_element, multi = self._get_element(s1, pos=0)
        s1_cut = self._drop_item(s1, first_element, multi, 0)

        # s2
        last_element, multi = self._get_element(s2, pos=-1)
        s2_cut = self._drop_item(s2, last_element, multi, -1)

        return s1_cut == s2_cut 
    
    @staticmethod
    def _get_element(s, pos):
        """
        Get the pth element in a sequence.
        Also returns whether the element was part of an itemset of length > 1. 
        """

         # Create a flattened list along with information about tuple length
        flat_list = []
        for itemset in s:
            # Check if the tuple has more than one element
            is_multi = len(itemset) > 1  
            # Add to list
            flat_list.extend((item, is_multi) for item in itemset)
        
        # Access the element and its context at the specified position
        element, is_multi = flat_list[pos]
        return element, is_multi
    
    @staticmethod
    def _drop_item(s, item, multi, pos):
        """
        Drop item from an itemset at a given position.
        """
        if multi:
            if pos == -1:
                return s[:pos] + [tuple(i for i in s[pos] if i != item)]
            return s[:pos] + [tuple(i for i in s[pos] if i != item)] + s[pos+1:]
        else:
            if pos == -1:
                return s[:pos]
            return s[:pos] + s[pos+1:]
    
    def _prune_candidates(self, L_k, C_k, k):
        """
        Remove each candidate that contains a (k-1)-itemset that is not frequent.
        """

        # If k=2, all sequences are frequent
        if k == 2:
            return C_k
        
        pruned_candidates = []

        # Iterate over the candidates
        for candidate in C_k:
            valid = True

            # Get continuous subsequences and check if they're frequent
            for subseq in self._contiguous_subsequences(candidate):
                if subseq not in L_k:
                    valid = False
                    break
            
            if valid:
                pruned_candidates.append(candidate)

        return pruned_candidates
    
    def _contiguous_subsequences(self, s):
        """
        Create all contiguous subsequences of a given sequence.
        Given a sequence s = <s1, ..., sn> and a subsequence c, c is a contiguous
        subsequence of s if any of the following conditions hold:
            1. c is derived from s by dropping an item from either s1 or sn.
            2. c is derived from s by dropping an item from an element si which has at least 
        2 items.
            3. c is a contiguous subsequence of c', and c' is a contiguous subsequence of s.
        
        Note that condition 3 is not used during the pruning step as a subsequence of a contiguous
        subsequence is of length k-2 and cannot be compared with the frequent sequence set L_{k-1}. 
        """

        # Condition 2
        for i_itemset, itemset in enumerate(s):

            # Check itemset length
            l_itemset = len(itemset)
            if not l_itemset > 1:

                # Handle Condition 1: dropping from s1
                if i_itemset == 0:
                    first_element, multi = self._get_element(s, 0)
                    yield self._drop_item(s, first_element, multi, 0)
                
                # Handle Condition 1: dropping from sn
                elif i_itemset == len(s):
                    last_element, multi = self._get_element(s, pos=-1)
                    yield self._drop_item(s, last_element, multi, -1)
                
                # Conditions not met
                else:
                    continue
        
            # Iterate over the items
            for i_item in range(l_itemset):
                yield self._drop_item(s, itemset[i_item], True, i_itemset)

    def _compute_support(self, C_k, min_support, min_gap, max_gap, window_size):
        """
        Compute support of potential candidates.
        Find all subsequences candidates contained in each sequence in the database.
        Uses the hash-tree structure from Agrawal and Srikant, Fast algorithms for mining association 
        rules in large databases (1994).
        """

        # Build the hash tree
        hash_tree = HashTree(max_leaf_size=3)
        for candidate in C_k:
            hash_tree.insert(candidate)
        # hash_tree.display()

        # Iterate over the data sequences
        counter = Counter()
        for i_seq, (t, sequence) in enumerate(zip(self.t, self.sequences)):
            # print('\nsequence =', sequence)
            matches = self._find_subsequences(
                hash_tree, hash_tree.root, sequence, i_seq, t, window_size, max_gap
            )
            # print('\n matches =', matches)
            for match in matches:
                counter[tuple(tuple(item) for item in match)] += 1/self.n_sequences

        L_k = [
            [tuple(inner) for inner in outer] for outer in counter
        ]
        frequent_sequences = {
            s: support for s, support in counter.items()
            if support >= min_support
        }
        # print('\n NEW L_k =', L_k)
        # print('\n frequent_sequences =', frequent_sequences)
        return L_k, frequent_sequences

    def _find_subsequences(self, hash_tree, node, data_sequence, seq_id, t, window_size, max_gap, depth=0, prev_time=None):
        """
        Find all candidate sequences in the hash tree that are contained in the data sequence.
        """
        matches = []

        # Flatten the sequence for processing
        flattened_sequence = [item for transaction in data_sequence for item in transaction]

        # Handle leaf nodes
        if node.is_leaf:
            for candidate in node.sequences:
                if self._is_subsequence(candidate, seq_id, max_gap, window_size=2):
                    matches.append(candidate)
            return matches

        # Handle interior nodes
        for i_item, item in enumerate(flattened_sequence):
            if node.is_root:
                # Root node: no temporal constraints
                hash_value = hash_tree.hash_function(item)
                if hash_value in node.children:
                    matches += self._find_subsequences(
                        hash_tree,
                        node.children[hash_value],
                        data_sequence,
                        seq_id,
                        t,
                        window_size,
                        max_gap,
                        depth + 1,
                        t[i_item]
                    )

            else:
                # Non-root node: apply temporal constraints
                min_time = max(prev_time - window_size, 0)
                max_time = prev_time + max(window_size, max_gap)
                time = t[i_item]

                if min_time <= time <= max_time:
                    hash_value = hash_tree.hash_function(item)
                    if hash_value in node.children:
                        matches += self._find_subsequences(
                            hash_tree,
                            node.children[hash_value],
                            data_sequence,
                            seq_id,
                            t,
                            window_size,
                            max_gap,
                            depth + 1,
                            time
                        )

        return matches

    def _is_subsequence(self, candidate, seq_id, max_gap, window_size):
        """
        Check if a candidate sequence is contained in a data sequence.
        """
        # print('\nsequence =', self.sequences[seq_id])

        # Length
        l_candidate = len(candidate)

        # State variables
        idx_candidate = 0  # Current index in the candidate sequence
        start_time = -1  # Start time of the last matched element
        end_times = [None] * l_candidate  # To track end-times of matched elements

        while idx_candidate < l_candidate:
            # Forward phase: find successive elements of candidate in the sequence
            while idx_candidate < l_candidate:
                # print('\t candidate =', candidate[idx_candidate], start_time)
                t = self._first_occurrence(seq_id, candidate[idx_candidate], start_time + 1, window_size)
                if t:
                    start_time, end_time = t[0], t[1]
                    if idx_candidate > 0 and start_time - end_times[idx_candidate - 1] > max_gap:
                        # Max-gap violated, switch to backward phase
                        idx_candidate -= 1
                        break
                    end_times[idx_candidate] = end_time
                    start_time = end_time
                    idx_candidate += 1  # Move to the next element in the candidate
                else:
                    # Element not found in forward phase
                    return False

            # Backward phase: Pull up previous elements if necessary
            while idx_candidate > 0:
                t_prev = end_times[idx_candidate - 1]
                t_curr = end_times[idx_candidate] if idx_candidate < l_candidate else None
                # print(f'\t backward: candidate = {idx_candidate}; t_prev =', t_prev, 't_curr =', t_curr)
                if (t_curr is None) or (t_curr - t_prev <= max_gap):
                    # Constraint satisfied
                    break

                # Pull up the previous element
                # print('pulling up the previous element')
                t = self._first_occurrence(seq_id, candidate[idx_candidate - 1], t_curr - max_gap, window_size)
                if t:
                    end_times[idx_candidate - 1] = t[1]
                else:
                    # Cannot pull up element, sequence not contained
                    return False

                idx_candidate -= 1  # Move backward in the candidate sequence

            # Resume forward phase after backward adjustment
            if idx_candidate < l_candidate and end_times[idx_candidate] is not None:
                start_time = end_times[idx_candidate]

        return True
    
    def _first_occurrence(self, s_id, element, start_time, window_size):
        """
        Find the first occurrence of an element (tuple of items) in the sequence after a given start_time,
        ensuring the time gap between items in the element does not exceed the window-size.
        
        :param s_id: Sequence ID for the data sequence.
        :param element: A tuple of items to find as a group.
        :param start_time: The minimum time to begin searching from.
        :param window_size: The maximum allowable time gap between items in the element.
        :return: The start-time and end-time of the element if found, otherwise None.
        """

        s_map = self.vert_temp_repr[s_id]  # Map between items and their occurrences in the sequence
        t = start_time  # Initial time to search from

        while True:
            # Find the first transaction time for each item in the element after time t
            item_times = []
            for item in element:
                if item not in s_map:
                    return None  # Element cannot be in that sequence
                # Get the first occurrence of the current item after time t
                found_time = None
                for time in s_map[item]:
                    if time >= t:
                        found_time = time
                        break
                if found_time is None:
                    return None  # If any item is not found, the element is not present
                item_times.append(found_time)

            # Compute the start-time and end-time of the element
            start_time = min(item_times)
            end_time = max(item_times)

            # Check if the time gap satisfies the window-size constraint
            if end_time - start_time <= window_size:
                return start_time, end_time

            # If not, update t to retry
            t = end_time - window_size



if __name__ == "__main__":

    # Sample data: a DataFrame where each row is a transaction (list of items)
    data = pd.DataFrame({
        'items': [
            [('bread',), ('milk',)], [('bread',), ('diaper',), ('beer',), ('egg',)], [('milk',), ('diaper',), ('beer',), ('coke',)],
            [('bread',), ('milk',), ('diaper',), ('beer',)], [('bread',), ('milk',), ('diaper',), ('coke',)]
        ]
    })

    alg = GSP(data, 'items')
    alg.run(min_support=0.4, min_gap=0, max_gap=5, window_size=0)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)