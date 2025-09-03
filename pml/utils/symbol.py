
class Symbol:

    def __init__(self, repr, t_start, t_end) -> None:

        # Symbol properties
        self._repr = repr
        self.t_s = t_start
        self.t_e = t_end

        # Generate dictionary that converts input subrule 'op' parameter
        # into an actual operator
        self._operator = {
            '=': self.__eq__,
            '<=': self.__leq__,
            '>=': self.__geq__,
            '<': self.__lt__,
            '>': self.__gt__,
        }

    @property
    def repr(self):
        return self._repr
    @repr.setter
    def repr(self, new_repr):
        self._repr = new_repr

    def __repr__(self) -> str:
        return f'{self._repr}: ({self.t_s}, {self.t_e})'

    def __eq__(self, other) -> bool:
        """
        Equality operator.
        """

        # Check if self.repr is a nan
        if self._repr != self._repr:
            return False

        if isinstance(other, Symbol):
            return self._repr == other._repr

        if isinstance(other, str):
            return self._repr == other

        else:
            raise RuntimeError("Failure in '=' operator.")

    def __leq__(self, other) -> bool:
        """
        Less or equal operator.
        """

        # Check if self.repr is a nan
        if self._repr != self._repr:
            return False

        if isinstance(other, Symbol):
            return self._repr <= other._repr

        if isinstance(other, str):
            return self._repr <= other

        else:
            raise RuntimeError("Failure in '<=' operator.")

    def __geq__(self, other) -> bool:
        """
        Greater or equal operator.
        """

        # Check if self.repr is a nan
        if self._repr != self._repr:
            return False

        if isinstance(other, Symbol):
            return self._repr >= other._repr

        if isinstance(other, str):
            return self._repr >= other

        else:
            raise RuntimeError("Failure in '>=' operator.")

    def __lt__(self, other) -> bool:
        """
        Less than operator.
        """

        # Check if self.repr is a nan
        if self._repr != self._repr:
            return False

        if isinstance(other, Symbol):
            return self._repr < other._repr

        if isinstance(other, str):
            return self._repr < other

        else:
            raise RuntimeError("Failure in '<' operator.")

    def __gt__(self, other) -> bool:
        """
        Greater than operator.
        """

        # Check if self.repr is a nan
        if self._repr != self._repr:
            return False

        if isinstance(other, Symbol):
            return self._repr > other._repr

        if isinstance(other, str):
            return self._repr > other

        else:
            raise RuntimeError("Failure in '>' operator.")
