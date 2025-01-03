
import pandas as pd

from pml.base import Algorithm


class FreeSpan(Algorithm):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data)
        
        self.item_col = item_col
        self.sequences = self._prepare_sequences()
        self.n_sequences = len(self.sequences)

    def run(self, min_support):
        """
        Run the FreeSpan algorithm.
        """
        
        # Initialization
        self.frequent_patterns = {}

        # Process starts with the complete db and the empty set
        self._pattern_growth(self.sequences, [], min_support)

    def _prepare_sequences(self):
        """
        Prepare sequences from a list of sets from the DataFrame.
        Transaction data is a list of list of sets.
        """
        return [list(map(tuple, row)) for row in self.data['items']]
    
    def _pattern_growth(self, db, sequence, min_support):
        """
        Main recursive function of a pattern-growth algorithm.
        db is a transaction database.
        sequence is  the current itemset.
        """