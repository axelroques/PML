
from itertools import combinations
from collections import Counter
import pandas as pd

from pml.base import Algorithm

# Check if possible to generate itemsets greater than 2 items
class Apriori(Algorithm):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data)

        self.item_col = item_col
        self.transactions = self._prepare_transactions()
        self.n_transactions = len(self.transactions)

    def run(self, min_support: float):
        """
        Run the Apriori algorithm.
        """
        
        self.frequent_patterns = {}

        # k = 1: first scan to compute support of 1-itemsets
        counter = Counter()
        for items in self.transactions:
            for item in items:
                counter[item] += 1/self.n_transactions

        for candidate in counter:
            if (counter[candidate]) >= min_support:
                self.frequent_patterns[candidate] = counter[candidate]

        # k >= 2
        k = 2
        F_k = [set([item]) for item in self.frequent_patterns]
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
                    self.frequent_patterns[frozenset(candidate)] = support

            k += 1

    def _prepare_transactions(self):
        """
        Prepare transactions as a list of sets from the DataFrame.
        """
        return [set(items) for items in self.data[self.item_col]]

    def _generate_candidates(self, candidates, k):
        """
        Generate new candidates of size k+1 from existing itemsets of size k.
        Returns an iterator. 
        """
        return (set(x) for x in combinations(set.union(*candidates), k))
    
    def _prune_candidates(self, F_k, candidates_iter, k):
        """
        Remove each candidate that contains a (k-1)-itemset that is not frequent, 
        i.e., not in F_{k-1}.
        """

        # If k=2, all itemsets are frequent
        if k == 2:
            return list(candidates_iter)
        
        # Otherwise, we have to check 
        return [
            candidate for candidate in candidates_iter 
            if all(frozenset(x) in F_k for x in combinations(candidate, k-1))
        ]
    
    def _compute_support(self, itemset):
        """
        Computes the support of an itemset.
        """
        return sum([
            1 for transaction in self.transactions 
            if all(item in transaction for item in itemset)
        ]) / self.n_transactions



if __name__ == "__main__":

    # Sample data: a DataFrame where each row is a transaction (list of items)
    data = pd.DataFrame({
        'items': [
            ['bread', 'milk'], ['bread', 'diaper', 'beer', 'egg'], ['milk', 'diaper', 'beer', 'coke'],
            ['bread', 'milk', 'diaper', 'beer'], ['bread', 'milk', 'diaper', 'coke']
        ]
    })

    alg = Apriori(data, 'items')
    alg.run(min_support=0.4)
    
    print('data =\n', data)
    print('Frequent patterns =\n', alg.frequent_patterns)
