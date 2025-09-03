
class ClosedHash():

    def __init__(self):
        self._hash_table = {}

    def insert(self, P, support):
        """
        Insert pattern P in a tree.
        """
        # print(f'\nInserting {P} in tree (support={support})')

        # If support not in hash table, init tree
        if not support in self._hash_table:
            self._hash_table[support] = Tree()

        # Insert into tree
        tree = self._hash_table[support]
        tree.insert(P)
    
    @property
    def patterns(self):
        patterns = [tree.patterns for tree in self._hash_table.values()]
        return {s: p for s, p in zip(self._hash_table, patterns)}


class Tree():

    def __init__(self):
        self.root = Node('∅', level=-1, root=True)
        self.nodes = [self.root]
        self.patterns = []

    def insert(self, P):
        """
        Insert a pattern P in the tree.
        """ 
        # print('\tcurrent patterns =', self.patterns)
        
        # Check inclusion
        P_is_subseq, P_is_superseq, i_p = self._inclusion_checks(P)
        # print(f'\tInclusion checks: P_is_subseq={P_is_subseq}; P_is_superseq={P_is_superseq}; i_p={i_p}')
        
        # If P is a subsequence of an existing pattern
        if P_is_subseq:
            # print('\t--> pattern already in tree')
            return

        # If an existing pattern is included in P
        if P_is_superseq:
            # print('\t--> reorganizing tree')
            self._reorganize(P, self.patterns[i_p])
            
        # If P not in the tree, add it
        if (not P_is_subseq) and (not P_is_superseq):
            # print('\t--> adding pattern in tree')
            self._add(P)

        # Save pattern
        self.patterns.append(P) 

    def _add(self, P):
        """
        Add a pattern P to the tree.
        """

        # Start from the root
        current_node = self.root 
        level = 0

        # Iterate over the itemsets
        for itemset in P:
            # Check if a child with the same itemset already exists
            matching_child = None
            for child in current_node.children:
                if set(child.symb) == set(itemset):
                    matching_child = child
                    break

            # If no matching child, create a new node
            if not matching_child:
                new_node = Node(itemset, level=level)
                new_node.add_parent(current_node)
                current_node.add_child(new_node)
                self.nodes.append(new_node)
                current_node = new_node
            else:
                current_node = matching_child

            level += 1

    def _reorganize(self, P, P_old):
        """ 
        Add a pattern to the tree, potentially restructuring it.
        """

        # Step 1: Find the longest prefix match
        match_path = self._find_longest_prefix_path(P)

        # Step 2: From the last matched node, add the rest of the pattern
        current_node = match_path[-1] if match_path else self.root
        level = current_node.level + 1
        for i in range(len(match_path), len(P)):
            itemset = P[i]
            new_node = Node(itemset, level=level)
            new_node.add_parent(current_node)
            current_node.add_child(new_node)
            self.nodes.append(new_node)
            current_node = new_node
            level += 1

        # Step 3: Clean old pattern
        self._clean(P_old, len(match_path))

    def _inclusion_checks(self, P):
        """
        Check if P is included in an existing pattern, or if an existing pattern
        is included in P.
        
        Returns a tuple of bools, and the index of the eventual included pattern. 
        First bool indicates whether P is included in the existing patterns.
        Second bool indicates whether an existing pattern is included in P.
        """
        
        # Iterate over the existing patterns
        for i_p, p in enumerate(self.patterns):

            # Check lengths
            l1 = len(P)
            l2 = len(p)

            # P is (strictly) longer than p
            if l1 > l2:
                if self._is_subseq(p, P):
                    return False, True, i_p
            
            # p is (strictly) longer than P
            if l2 > l1:
                if self._is_subseq(P, p):
                    return True, False, i_p

            # Equal lengths
            if l1 == l2:
                # Compare number of items
                l1 = sum(len(itemset) for itemset in P)
                l2 = sum(len(itemset) for itemset in p)
                if l1 > l2:
                    if self._is_subseq(p, P):
                        return False, True, i_p
                if l2 > l1:
                    if self._is_subseq(P, p):
                        return True, False, i_p

        # No match
        return False, False, -1

    def _clean(self, P, offset):
        """
        Remove the path corresponding to P after reorganization.
        offset corresponds to the number of nodes matched to add the new pattern
        in the tree: the first 'offset' nodes should not be considered.
        """

        # Nothing to clean if offset = to pattern length
        if offset == len(P):
            return

        # Get node path to P
        node_path = self._find_longest_prefix_path(P)

        # Start cleaning proces
        for node in reversed(node_path[offset:]):
            if not node.children:
                node.parent.children.remove(node)
                self.nodes.remove(node)
            else:
                return

    def _find_longest_prefix_path(self, P):
        """
        Return the path of nodes that match the longest prefix of the pattern.
        """

        path = []
        current = self.root
        for itemset in P:
            match = None

            for child in current.children:
                if set(child.symb) == set(itemset):
                    match = child
                    break

            if match:
                path.append(match)
                current = match
            else:
                break

        return path

    @staticmethod
    def _is_subseq(P1, P2):
        """
        Check of P1 is a subsequence of P2.
        """

        n1, n2 = len(P1), len(P2)
        i1, i2 = 0, 0

        while i1 < n1 and i2 < n2:
            if set(P1[i1]).issubset(set(P2[i2])):
                i1 += 1
            i2 += 1

        return i1 == n1


class Node():

    def __init__(self, symb, level, root=False):
        self.symb = symb
        self.level = level
        self.is_root = root
        self.parent = None
        self.children = []
        
    def add_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)