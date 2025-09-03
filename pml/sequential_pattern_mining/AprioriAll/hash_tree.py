
class Node:
    def __init__(self, is_leaf=True):
        """
        A node in the hash tree.
        :param is_leaf: True if this is a leaf node, False for an interior node.
        """
        self.is_leaf = is_leaf
        self.children = {}  # For interior nodes: a hash table (dictionary) of children
        self.sequences = []  # For leaf nodes: a list of sequences


class HashTree:
    def __init__(self, max_leaf_size=2, n_branches=3):
        """
        Initialize the hash tree.
        :param max_leaf_size: Maximum number of sequences a leaf can hold before splitting.
        """
        self.root = Node()
        self.max_leaf_size = max_leaf_size
        self.n_branches = n_branches

    def hash_function(self, element):
        """
        A simple hash function.
        :param element: The element to hash.
        :return: The hash bucket (e.g., the element itself for simplicity).
        """
        return sum(ord(c) for c in element[0])

    def _insert_into_leaf(self, leaf, sequence):
        """
        Insert a sequence into a leaf node.
        :param leaf: The leaf node.
        :param sequence: The sequence to insert.
        """
        leaf.sequences.append(sequence)

    def _split_leaf(self, leaf, depth):
        """
        Split a leaf node into an interior node and redistribute sequences.
        :param leaf: The leaf node to split.
        :param depth: The current depth in the tree.
        """

        # Ensure the node transitions from a leaf to an interior node
        leaf.is_leaf = False

        # Initialize children for the new interior node
        leaf.children = {}

        # Redistribute sequences into child nodes
        for sequence in leaf.sequences:
            if depth < len(sequence):  # Ensure there is a hashable element
                key = self.hash_function(sequence[depth])
                if key not in leaf.children:
                    leaf.children[key] = Node() 
                leaf.children[key].sequences.append(sequence)
            else:
                # If no more depth to hash, keep in the same node as a "terminal leaf"
                if None not in leaf.children:
                    leaf.children[None] = Node()
                leaf.children[None].sequences.append(sequence)

        # Clear the sequences in the current node since it is no longer a leaf
        leaf.sequences = []

    def _insert(self, node, sequence, depth):
        """
        Recursively insert a sequence into the hash tree.
        :param node: The current node.
        :param sequence: The sequence to insert.
        :param depth: The current depth in the tree.
        """
        if node.is_leaf:
            # If it's a leaf, insert the sequence
            self._insert_into_leaf(node, sequence)

            # Split the leaf if it exceeds the max size
            if len(node.sequences) > self.max_leaf_size:
                self._split_leaf(leaf=node, depth=depth)
        else:
            # Determine the bucket key for the current depth
            key = self.hash_function(sequence[depth]) if depth < len(sequence) else None
            
            # If no child exists for the key, create a new leaf node
            if key not in node.children:
                node.children[key] = Node()

            # Recursively insert into the appropriate child node
            self._insert(node.children[key], sequence, depth + 1)

    def insert(self, sequence):
        """
        Public method to insert a sequence into the hash tree.
        :param sequence: The sequence to insert.
        """
        self._insert(self.root, sequence, depth=0)

    def display(self, node=None, depth=0):
        """
        Display the structure of the hash tree for debugging purposes.
        :param node: The current node to display.
        :param depth: The current depth in the tree.
        """
        if node is None:
            node = self.root

        if node.is_leaf:
            print("  " * depth + f"Leaf: {node.sequences}")
        else:
            print("  " * depth + "Interior Node:")
            for key, child in node.children.items():
                print("  " * depth + f"  Key: {key}")
                self.display(child, depth + 1)


if __name__ == '__main__':

    hash_tree = HashTree(max_leaf_size=3)
    sequences = [
        ['1', '7', '8'],
        ['1', '4', '5'],
        ['1', '2', '7'],
        ['4', '5', '7'],
        ['1', '2', '5'],
        ['1', '5', '8'],
        ['4', '5', '8'],
        ['4', '5', '9'],
        ['4', '5', '6'],
        ['7', '8', '9'],
        ['1', '6', '8'],
        ['2', '4', '6'],
        ['2', '7', '8'],
        ['2', '5', '8'],
        ['2', '8', '9'],
        ['5', '6', '8'],
        ['1', '2', '8'],
        ['3', '4', '6'],
        ['3', '7', '9'],
        ['6', '7', '8'],
        ['3', '5', '6'],
        ['6', '8', '9'],
        ['3', '6', '7'],
    ]
    # sequences = [
    #     [('bread',), ('milk',)],
    #     [('bread',), ('diaper',)],
    #     [('bread',), ('beer',)],
    #     [('milk',), ('bread',)],
    #     [('milk',), ('diaper',)],
    #     [('milk',), ('beer',)],
    #     [('diaper',), ('bread',)],
    #     [('diaper',), ('milk',)],
    #     [('diaper',), ('beer',)],
    #     [('beer',), ('bread',)],
    #     [('beer',), ('milk',)],
    #     [('beer',), ('diaper',)],
    # ]

    for seq in sequences:
        hash_tree.insert(seq)

    hash_tree.display()
