
from itertools import combinations
import pandas as pd

from pml.base import FPMiner


class AprioriTID(FPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

        # Convert input into a vertical format
        self.TID_lists = self._create_vertical_db()

    def run(self, min_support: float):
        """
        Run the Apriori-TID algorithm.
        """
        
        # k = 1: find frequent 1-itemsets
        F_k = []
        for item, TID_list in self.TID_lists.items():
            support = len(TID_list) / self.n_transactions
            if support >= min_support:
                self._frequent_patterns[frozenset([item])] = support
                F_k.append(set([item]))

        # k >= 2
        k = 2
        while F_k:

            # Generate k-itemsets
            candidates_iter = self._generate_candidates(F_k, k)

            # Pruning
            candidates = self._prune_candidates(F_k, candidates_iter, k)

            # Compute support of potential candidates
            F_k = []
            for candidate in candidates:
                support = self._compute_support(candidate)
                if support >= min_support:
                    F_k.append(candidate)
                    self._frequent_patterns[frozenset(candidate)] = support

            k += 1

    def _generate_candidates(self, candidates, k):
        """
        Generate new candidates of size k+1 from existing candidates of size k.
        Returns an iterator. 
        """
        return (set(x) for x in combinations(set.union(*candidates), k))
    
    def _prune_candidates(self, F_k, candidates_iter, k):
        """
        Remove each candidate that contains a (k-1)-itemset that is not frequent, 
        i.e., not in F_{k-1}.
        """

        # If k=2, all 1-itemsets are frequent
        if k == 2:
            return list(candidates_iter)
        
        # Otherwise, we have to check 
        return [
            candidate for candidate in candidates_iter 
            if all(frozenset(x) in F_k for x in combinations(candidate, k-1))
        ]
    
    def _compute_support(self, candidate):
        """
        Computes the support for a candidate itemset.
        Support can be computed as the length of the TID-list of the intersection of 
        the consitutive items.
        """
        indexes = None
        for item in candidate:
            if item not in self.TID_lists:
                return 0
            item_indexes = self.TID_lists[item]
            indexes = item_indexes if indexes is None else indexes.intersection(item_indexes)
        return len(indexes) / self.n_transactions if indexes else 0


if __name__ == "__main__":

    # Sample data: a DataFrame where each row is a transaction (list of items)
    data = pd.DataFrame({
        'items': [
            ['bread', 'milk'], ['bread', 'diaper', 'beer', 'egg'], ['milk', 'diaper', 'beer', 'coke'],
            ['bread', 'milk', 'diaper', 'beer'], ['bread', 'milk', 'diaper', 'coke']
        ]
    })
    alg = AprioriTID(data, 'items')
    alg.run(min_support=0.4)

    print(data)
    print(alg.get_results())
