
import numpy as np


class Bitmap:

    def __init__(self, sequence) -> None:
        self.sequence = sequence
        self.sections = []
        self._bitmap = []

    def init_section(self, l):
        """
        Init section.
        """
        self.sections.append([0] * l)

    def update_section(self, s_id, pos):
        """
        Update the section with a one at the adequate position.  
        """
        self.sections[s_id][pos] = 1

    def get_sections_from_bitmap(self, ref):
        """
        Trick to retrieve section data from a complete bitmap,
        given a reference bitmap.
        """
        i = 0
        for section in ref.sections:
            l = len(section)
            self.sections.append(self.bitmap[i:i+l])
            i += l

    def I_step(self, other):
        """
        I_step process.

        Basically an AND logical operation between two bitmaps.
        """

        bitmap = [
            b1 & b2 for b1, b2 in zip(self.bitmap, other.bitmap)
        ]

        new_sequence = self.sequence[:-1] + \
            [self.sequence[-1] + other.sequence[0]]

        # Create new bitmap
        b = Bitmap(new_sequence)
        b.bitmap = bitmap
        b.get_sections_from_bitmap(self)

        return b

    def S_step(self, other):
        """
        S_step process.

        Finds k, the index of the first non zero element in the bitmap.
        Then, create a new transformed representation filled with zeros before 
        index k and filled with ones after.
        Finally, perform an AND logical operation between the transformed bitmap 
        and the input bitmap.
        """

        def first_nonzero(l):
            return next((i for i, v in enumerate(l) if v), -1)

        # Iterate over the sections
        transformed_bitmap = []
        for section in self.sections:
            # Find k
            k = first_nonzero(section)

            # Compute transformed representation
            if k != -1:
                transformed_bitmap += [0]*(k+1) + [1]*(len(section)-(k+1))
            else:
                transformed_bitmap += [0]*len(section)

        # AND logical operator
        bitmap = [
            b1 & b2 for b1, b2 in zip(transformed_bitmap, other.bitmap)
        ]

        new_sequence = self.sequence + other.sequence

        # Create new bitmap
        b = Bitmap(new_sequence)
        b.bitmap = bitmap
        b.get_sections_from_bitmap(self)

        return b
    
    def compute_support(self):
        """
        Compute relative support.
        """
        # print('\nbitmap support computation:')
        # print('\tbitmap =', self.bitmap)
        # print('\tn_occurences =', sum([any(l) for l in self.sections]))
        # print('\ttotal sections =', len(self.sections))
        # print('\t-> Support =', sum([any(l) for l in self.sections]) / len(self.sections))
        return sum([any(l) for l in self.sections]) / len(self.sections)

    @staticmethod
    def _get_seq_length(seq):
        """
        Helper function that returns an input sequence's length.
        """
        return sum([len(itemset) for itemset in seq])

    def __lt__(self, other):
        """
        Overload <= operator. 
        Implements a partial order for sequence comparison.
        """

        # If both sequences have the same length, use the lexicographic order
        if self._get_seq_length(self.sequence) == self._get_seq_length(other.sequence):
            return self.sequence < other.sequence

        # Otherwise the longest sequence is the greatest
        elif self._get_seq_length(self.sequence) < self._get_seq_length(other.sequence):
            return True
        else:
            return False
    
    @property
    def bitmap(self):
        if not self._bitmap:
            self._bitmap = [bit for section in self.sections for bit in section]
            [*self.sections]
        return self._bitmap
    
    @bitmap.setter
    def bitmap(self, bitmap):
        self._bitmap = bitmap

    def __gt__(self, other):
        """
        Overload >= operator. 
        Implements a partial order for sequence comparison.
        """

        # If both sequences have the same length, use the lexicographic order
        if self._get_seq_length(self.sequence) == self._get_seq_length(other.sequence):
            return self.sequence > other.sequence

        # Otherwise the longest sequence is the greatest
        elif self._get_seq_length(self.sequence) > self._get_seq_length(other.sequence):
            return True
        else:
            return False

    def __repr__(self) -> str:
        """
        Pretty print.
        """
        return f'Sequence: {self.sequence}'
