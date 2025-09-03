
from collections import Counter
import pandas as pd

from pml.base import FPMiner


class PatternGrowth(FPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

    def run(self, min_support):
        """
        Run a basic pattern-growth algorithm. 
        """

        # Process starts with the complete db and the empty set
        self._pattern_growth(self.transactions, [], min_support)

    def _pattern_growth(self, db, itemset, min_support):
        """
        Main recursive function of a pattern-growth algorithm.
        db is a transaction database.
        itemset is  the current itemset.
        """

        # Scan db to find all frequent items
        frequent_items = self._find_frequent_items(db, min_support)

        # Generate k+1-itemsets that are extensions of the current itemset
        for item, support in frequent_items.items():
            
            # Combine new item with current itemset
            new_itemset = itemset + [item]

            # Save union as a frequent pattern
            self._frequent_patterns[frozenset(new_itemset)] = support

            # Project db
            db_proj = self._project_db(db, item)

            # Continue depth-first search
            self._pattern_growth(db_proj, new_itemset, min_support)

    def _find_frequent_items(self, db, min_support):
        """
        Find all frequent items in db. 
        db is a list of sets. 
        Returns a dictionary of frequent items as {item: support}.
        """
        
        counter = Counter()
        for items in db:
            for item in items:
                counter[item] += 1/self.n_transactions

        frequent_items = {}
        for candidate in sorted(counter):
            if (counter[candidate]) >= min_support:
                frequent_items[candidate] = counter[candidate]

        return frequent_items
    
    @staticmethod
    def _project_db(db, item):
        """
        Project database db according according to the item. 
        Transactions are assumed to be sorted. 
        """

        # Initialize the projected database
        db_proj = []

        # Iterate over the transactions
        for transaction in db: 

            # Check if the item appears in the transaction
            if not item in transaction:
                continue

            # Find index of the item in the transaction
            i_item = transaction.index(item)

            # Build the projected db
            db_proj.append(transaction[i_item+1:])

        return db_proj


if __name__ == "__main__":

    data = pd.DataFrame({
        'items': [
            ['bread', 'milk'], ['bread', 'diaper', 'beer', 'egg'], ['milk', 'diaper', 'beer', 'coke'],
            ['bread', 'milk', 'diaper', 'beer'], ['bread', 'milk', 'diaper', 'coke']
        ]
    })
    alg = PatternGrowth(data, 'items')
    alg.run(min_support=0.4)
    
    print(data)
    print(alg.get_results())
