
from abc import ABC, abstractmethod
import pandas as pd

class Algorithm(ABC):
    def __init__(self, data: pd.DataFrame):
        """
        Initializes the algorithm with a pandas DataFrame.
        
        Parameters:
        data (pd.DataFrame): A DataFrame with at least one column for items.
        """
        self.data = data
        self.results = None

    @abstractmethod
    def run(self):
        """
        Abstract method that should be implemented by all subclasses to execute the algorithm.
        """
        pass

    def get_results(self):
        """
        Returns the results of the algorithm.
        
        Returns:
        Any: The output generated by the algorithm after execution.
        """
        if self.results is None:
            raise ValueError("The algorithm has not been run yet. Call run() first.")
        return self.results

    def preprocess_data(self):
        """
        Optional method for subclasses to override if preprocessing is required.
        """
        pass
