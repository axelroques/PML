
from abc import ABC, abstractmethod
import pandas as pd

class FPMiner(ABC):
    def __init__(self, data: pd.DataFrame, item_col: str):
        """
        Abstract class for a frequent pattern miner. 
        
        Parameters:
        data (pd.DataFrame): A DataFrame with at least one column for items.
        """
        self.data = data
        self.item_col = item_col
        self.transactions = self._prepare_transactions()
        self.n_transactions = len(self.transactions)
        self._frequent_patterns = {}
        self.frequent_patterns = {}

    def get_results(self):
        """ 
        Return mining results.
        """
        if not self._frequent_patterns:
            raise RuntimeError('Run algorithm first.') 
        if self.frequent_patterns:
            return self.frequent_patterns
        self.frequent_patterns = {
            frozenset(self.int_to_item[i] for i in pattern): support
            for pattern, support in self._frequent_patterns.items()
        }
        return self.frequent_patterns
        
    def _prepare_transactions(self):
        """
        Prepare transactions as a list of sorted integer-mapped items from the DataFrame.
        """
        raw_transactions = [sorted(itemset) for itemset in self.data[self.item_col]]

        # Build the set of unique items
        unique_items = sorted({item for transaction in raw_transactions for item in transaction})
        
        # Create mapping dictionaries
        self.item_to_int = {item: idx for idx, item in enumerate(unique_items)}
        self.int_to_item = {idx: item for item, idx in self.item_to_int.items()}
        
        # Map transactions to integers
        transactions = [
            [self.item_to_int[item] for item in transaction]
            for transaction in raw_transactions
        ]
        
        return transactions
    
    def _create_vertical_db(self):
        """
        Create a map of items to the indices of transactions containing them.
        """
        TID_lists = {}
        for tid, transaction in enumerate(self.transactions):
            for item in transaction:
                if item not in TID_lists:
                    TID_lists[item] = set()
                TID_lists[item].add(tid)
        return dict(sorted(TID_lists.items()))
    
    @abstractmethod
    def run(self):
        """
        Abstract method that should be implemented by all subclasses to execute the algorithm.
        """
        pass


class FSPMiner(ABC):
    def __init__(self, data: pd.DataFrame, item_col: str):
        """
        Abstract class for a frequent sequential pattern miner. 
        
        Parameters:
        data (pd.DataFrame): A DataFrame with at least one column for items.
        """
        self.data = data
        self.item_col = item_col
        self.sequences = self._prepare_sequences()
        self.n_sequences = len(self.sequences)

    def _prepare_sequences(self):
        """
        Prepare sequences from a list of sets from the DataFrame column.
        Transaction data is a list of list of sets.
        In each itemset, items are sorted in lexicographic order.
        """
        return [
            list(map(lambda t: tuple(sorted(t)), row)) 
            for row in self.data['items']
        ]

    def _create_vertical_db(self):
        """
        Create a map of items to the indices of transactions containing them.
        """
        TID_lists = {}
        for tid, transaction in enumerate(self.transactions):
            for item in transaction:
                if item not in TID_lists:
                    TID_lists[item] = set()
                TID_lists[item].add(tid)
        return dict(sorted(TID_lists.items()))
    
    @abstractmethod
    def run(self):
        """
        Abstract method that should be implemented by all subclasses to execute the algorithm.
        """
        pass
