import random

class Node:
    """Represents a region on the map."""
    def __init__(self, node_id):
        self.id = node_id
        self.links = []  # list of Link objects

    def __repr__(self):
        return f"Node({self.id})"

    def add_link(self, link):
        if link not in self.links:
            self.links.append(link)

class Link:
    """Represents a road/connection between two nodes."""
    def __init__(self, node_a, node_b):
        self.node_a = node_a
        self.node_b = node_b

    def __repr__(self):
        return f"Link({self.node_a.id} <-> {self.node_b.id})"

    def connects(self, node):
        """Returns the other node in the link."""
        return self.node_b if node == self.node_a else self.node_a

class Graph:
    """Represents the full map (nodes and links)."""
    def __init__(self, min_nodes=6, max_nodes=20, avg_links_per_node=2):
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.avg_links_per_node = avg_links_per_node
        self.nodes = []
        self.links = []

    def generate(self):
        """Generates a random connected graph."""
        num_nodes = random.randint(self.min_nodes, self.max_nodes)
        self.nodes = [Node(i) for i in range(num_nodes)]
        self.links = []

        # Step 1: Ensure connectivity (build a spanning tree)
        available_nodes = self.nodes[:]
        connected = [available_nodes.pop()]
        while available_nodes:
            node_a = random.choice(connected)
            node_b = available_nodes.pop()
            self._connect_nodes(node_a, node_b)
            connected.append(node_b)

        # Step 2: Add extra random links
        total_links = int(num_nodes * self.avg_links_per_node / 2)
        while len(self.links) < total_links:
            a, b = random.sample(self.nodes, 2)
            if not self._nodes_connected(a, b):
                self._connect_nodes(a, b)

    def _connect_nodes(self, node_a, node_b):
        """Connect two nodes with a bidirectional link."""
        link = Link(node_a, node_b)
        node_a.add_link(link)
        node_b.add_link(link)
        self.links.append(link)

    def _nodes_connected(self, node_a, node_b):
        """Check if two nodes are already directly connected."""
        return any(
            (l.node_a == node_a and l.node_b == node_b) or
            (l.node_a == node_b and l.node_b == node_a)
            for l in self.links
        )

    def display(self):
        """Print the graph structure."""
        print(f"Graph with {len(self.nodes)} nodes and {len(self.links)} links:\n")
        for node in self.nodes:
            connected_ids = [l.connects(node).id for l in node.links]
            print(f"Node {node.id}: connected to {connected_ids}")

        print("\nAll links:")
        for link in self.links:
            print(f" - {link}")

if __name__ == "__main__":
    random.seed()  # For reproducibility, you can pass a number here
    g = Graph(min_nodes=6, max_nodes=20, avg_links_per_node=2)
    g.generate()
    g.display()
