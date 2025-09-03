
import pandas as pd

from pml.base import FPMiner


class Eclat(FPMiner):
    def __init__(self, data: pd.DataFrame, item_col: str):
        super().__init__(data, item_col)

        # Convert input into a vertical format
        self.TID_lists = self._create_vertical_db()

    def run(self, min_support: float):
        """
        Run the Eclat algorithm.
        """

        # Get frequent 1-itemsets
        R = {
            frozenset([item]): tid_list 
            for item, tid_list in self.TID_lists.items()
            if len(tid_list) / self.n_transactions >= min_support
        }

        # Process starts with all frequent 1-itemsets
        self._eclat(R, min_support)

    def _eclat(self, R, min_support):
        """
        Main recursive function of the Eclat algorithm.
        R is a dictionary of frequent itemsets with their TID-lists.
        """
        # print('\nR =', R)
        for itemset, TID_list in R.items():
            # print(f'\t itemset={itemset}, tid={TID_list}')

            # Add frequent patterns
            self._frequent_patterns[itemset] = len(TID_list) / self.n_transactions
            
            # Generate k+1-itemsets that are extensions of the current itemset
            E = {}
            for candidate, other in self._generate_candidates(itemset, R):
                # print('\t\t candidate =', candidate, 'other =', other)
                
                # Compute TID-list of the candidate and its support
                tid = set.intersection(
                    R[itemset], R[other]
                )
                # print('\t\t tid =', tid)
                support = len(tid) / self.n_transactions
                if support < min_support:
                    continue 

                # Add to E
                E[candidate] = tid

                # Continue depth-first search
                self._eclat(E, min_support)
    
    def _generate_candidates(self, itemset, itemsets):
        """
        Create k+1 extensions.
        """
        for other in itemsets:

            # Sort input and candidate
            itemset = sorted(itemset)
            other = sorted(other)

            # Check if all but the last item of the input set matches with the other set
            if not (itemset[:-1] == other[:-1]):
                continue
                
            # Get extension
            extension = other[-1]

            # If extension is not already in the input set, create a new extended set
            if extension not in itemset:
                yield frozenset(itemset + [extension]), frozenset(other)


if __name__ == "__main__":
    data = pd.DataFrame({
        'items': [
            ['bread', 'milk'], ['bread', 'diaper', 'beer', 'egg'], ['milk', 'diaper', 'beer', 'coke'],
            ['bread', 'milk', 'diaper', 'beer'], ['bread', 'milk', 'diaper', 'coke']
        ]
    })
    alg = Eclat(data, 'items')
    alg.run(min_support=0.4)
    
    print(data)
    print(alg.get_results())
