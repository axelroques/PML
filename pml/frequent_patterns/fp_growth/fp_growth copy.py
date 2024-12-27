
from collections import defaultdict
import pandas as pd

from pml.base import Algorithm
from fp_tree import FPTree


class FPGrowth(Algorithm):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data)

        self.item_col = item_col

    def run(self, min_support):
        """
        Executes the FP-Growth algorithm on the input data with the given minimum support.
        
        Parameters:
        min_support (float): Minimum support threshold as a fraction of the total transactions.

        Note:
        This implementation does not rely on transforming the min_support value into a min_count parameter
        like most other implementations. 
        """
        self.results = self.find_frequent_itemsets(self.data, min_support)

    def find_frequent_itemsets(self, df, min_support):
        transactions = df['items'].tolist()
        item_counts = defaultdict(int)
        n_transactions = len(transactions)

        # First pass: count item frequencies
        for transaction in transactions:
            for item in transaction:
                item_counts[item] += 1
        
        # Filter items by min_support
        min_count = min_support * n_transactions
        print('min_count =', min_count)
        frequent_items = {item: count for item, count in item_counts.items() if count >= min_count}
        
        if not frequent_items:
            return []

        # Second pass: build the FP-tree
        fp_tree = FPTree()
        for transaction in transactions:
            filtered_transaction = [item for item in transaction if item in frequent_items]
            ordered_transaction = sorted(filtered_transaction, key=lambda x: -frequent_items[x])
            fp_tree.insert_transaction(ordered_transaction)
        
        # Recursive mining
        return self.mine_tree(fp_tree, min_count)

    def mine_tree(self, tree, min_count):
        frequent_itemsets = []
        items = sorted(tree.header_table.keys(), key=lambda x: -len(tree.header_table[x]))
        for item in items:
            support = sum(node.count for node in tree.header_table[item])
            if support >= min_count:
                frequent_itemsets.append(([item], support))
                conditional_patterns = tree.get_conditional_patterns(item)
                conditional_tree = self.build_conditional_tree(conditional_patterns, min_count)
                if conditional_tree:
                    suffix_itemsets = self.mine_tree(conditional_tree, min_count)
                    for suffix_itemset, suffix_support in suffix_itemsets:
                        frequent_itemsets.append(([item] + suffix_itemset, suffix_support))
        return frequent_itemsets

    def build_conditional_tree(self, conditional_patterns, min_count):
        conditional_tree = FPTree()
        item_counts = defaultdict(int)
        for path, count in conditional_patterns:
            for item in path:
                item_counts[item] += count
        
        # Filter items by min_support
        frequent_items = {item: count for item, count in item_counts.items() if count >= min_count}
        if not frequent_items:
            return None

        # Insert filtered and ordered conditional patterns into the new FP-tree
        for path, count in conditional_patterns:
            filtered_path = [item for item in path if item in frequent_items]
            ordered_path = sorted(filtered_path, key=lambda x: -frequent_items[x])
            if ordered_path:
                conditional_tree.insert_transaction(ordered_path, count)

        return conditional_tree


if __name__ == "__main__":

    data = pd.DataFrame({
        'items': [
            ['bread', 'milk'], ['bread', 'diaper', 'beer', 'egg'], ['milk', 'diaper', 'beer', 'coke'],
            ['bread', 'milk', 'diaper', 'beer'], ['bread', 'milk', 'diaper', 'coke']
        ]
    })
    alg = FPGrowth(data, 'items')
    alg.run(min_support=0.5)
    
    print('data =\n', data)
    print('results =', alg.results)
