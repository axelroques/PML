
from collections import Counter
import pandas as pd

from pml.sequential_pattern_mining.AprioriAll.hash_tree import HashTree
from pml.base import FSPMiner


class AprioriAll(FSPMiner):
    """
    AprioriAll from Agrawal and Srikant, Mining Sequential Patterns (1995).
    """

    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)
        
    def run(self, min_support=0.4):
        """
        AprioriAll algorithm.
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
                self.frequent_patterns[((candidate,),)] = counter[candidate]

        # k >= 2
        k = 2
        L_k = [[tuple(item)] for itemset in self.frequent_patterns for item in itemset]
        print('L_k =', L_k)
        while L_k:
            # print('\n L_k =', L_k)

            # Generate k-sequences
            C_k = self._generate_candidates(L_k)
            # print('C_k =', C_k)

            # Prune candidates
            C_k = self._prune_candidates(L_k, C_k, k)
            # print('candidates =', C_k)

            # Compute support and retain frequent candidates
            L_k, frequent_candidates = self._compute_support(C_k, min_support)
            self.frequent_patterns.update(frequent_candidates)

            k += 1

    def _generate_candidates(self, L_k):
        """
        Generate candidate sequences of size k+1 from existing k-sequences.
        """

        C_k = []
        
        for i in range(len(L_k)):
            for j in range(len(L_k)):
                # Compare all but the last element of sequences i and j
                if i != j and L_k[i][:-1] == L_k[j][:-1]:
                    # Create a new sequence
                    new_candidate = L_k[i] + [L_k[j][-1]]
                    if new_candidate not in C_k:
                        C_k.append(new_candidate)
        
        return C_k
    
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

            # Generate all (k-1)-subsequences
            for i in range(len(candidate)):
                subsequence = candidate[:i] + candidate[i+1:]
                # print('\t\tsubsequence =', subsequence)

                # Check if the subsequence is in L_k
                if not subsequence in L_k:
                    # print('invalid')
                    valid = False
                    break
            if valid:
                # print('valid')
                pruned_candidates.append(candidate)

        return pruned_candidates

    def _compute_support(self, C_k, min_support):
        """
        Compute support of potential candidates.
        Find all subsequences candidates contained in each sequence in the database.
        Uses the hash-tree structure from Agrawal and Srikant, Fast algorithms for mining association 
        rules in large databases (1994).
        """

        # Build the hash tree
        hash_tree = HashTree(max_leaf_size=2)
        for candidate in C_k:
            hash_tree.insert(candidate)
        # hash_tree.display()

        # Iterate over the data sequences
        counter = Counter()
        for sequence in self.sequences:
            # print('\nsequence =', sequence)
            matches = self._find_subsequences(
                hash_tree, hash_tree.root, sequence, window_size=1, max_gap=3
            )
            # print('matches =', matches)
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


    def _find_subsequences(self, hash_tree, node, data_sequence, window_size, max_gap, depth=0, prev_time=None):
        """
        Find all candidate sequences in the hash tree that are contained in the data sequence.

        :param hash_tree: The hash tree containing candidates.
        :param data_sequence: The data sequence to check against.
        :param window_size: The window size constraint.
        :param max_gap: The max-gap constraint.
        :param depth: Current depth of the tree traversal.
        :param prev_time: Transaction time of the previously hashed item.
        :return: A list of matching candidate sequences.
        """
        matches = []

        if node.is_leaf:
            # print('leaf')
            # Leaf node: Check all sequences in this node
            # print('hashtree.sequences =', hash_tree.sequences)
            for candidate in node.sequences:
                if self._is_subsequence(candidate, data_sequence):
                    matches.append(candidate)
        else:
            # Interior node
            # print('int')
            for time, item in enumerate(data_sequence):
                if prev_time is None:  # Root node: No time constraints
                    hash_value = hash_tree.hash_function(item) 
                    if hash_value in node.children:
                        matches += self._find_subsequences(
                            hash_tree,
                            node.children[hash_value],
                            data_sequence,
                            window_size,
                            max_gap,
                            depth + 1,
                            time
                        )
                else:
                    # Apply transaction time constraints
                    if time in range(prev_time - window_size, prev_time + max(window_size, max_gap) + 1):
                        hash_value = hash_tree.hash_function(item) 
                        # print('item =', item)
                        if hash_value in node.children:
                            matches += self._find_subsequences(
                                hash_tree,
                                node.children[hash_value],
                                data_sequence,
                                window_size,
                                max_gap,
                                depth + 1,
                                time
                            )

        return matches

    @staticmethod
    def _is_subsequence(candidate, data_sequence):
        """
        Check if a candidate sequence is contained in a data sequence.
        """
        it = iter(data_sequence)
        for c_item in candidate:
            if not any(d_item == c_item for d_item in it):
                # print('\t\tis subseq? -> False')
                return False
        # print('\t\tis subseq? -> True')
        return True


if __name__ == "__main__":

    # Sample data: a DataFrame where each row is a transaction (list of items)
    data = pd.DataFrame({
        'items': [
            [('bread',), ('milk',)], [('bread',), ('diaper',), ('beer',), ('egg',)], [('milk',), ('diaper',), ('beer',), ('coke',)],
            [('bread',), ('milk',), ('diaper',), ('beer',)], [('bread',), ('milk',), ('diaper',), ('coke',)]
        ]
    })

    alg = AprioriAll(data, 'items')
    alg.run(min_support=0.4)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)