
from collections import defaultdict


class FPNode:
    def __init__(self, item, count=1):
        self.item = item
        self.count = count
        self.parent = None
        self.children = {}
        self.link = None  # Link to the next node with the same item

    def increment(self, count=1):
        self.count += count

class FPTree:
    def __init__(self):
        self.root = FPNode(None)
        self.header_table = defaultdict(list)

    def insert_transaction(self, transaction, count=1):
        current_node = self.root
        for item in transaction:
            if item not in current_node.children:
                new_node = FPNode(item)
                new_node.parent = current_node
                current_node.children[item] = new_node
                self.header_table[item].append(new_node)
            current_node = current_node.children[item]
            current_node.increment(count)

    def get_conditional_patterns(self, item):
        conditional_patterns = []
        for node in self.header_table[item]:
            path = []
            parent = node.parent
            while parent and parent.item is not None:
                path.append(parent.item)
                parent = parent.parent
            if path:
                conditional_patterns.append((path[::-1], node.count))
        return conditional_patterns