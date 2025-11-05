import random
from itertools import combinations

# Optional visualization libraries
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_VIS = True
except ImportError:
    HAS_VIS = False


class Node:
    def __init__(self, node_id, is_start=False, owner=None):
        self.id = node_id
        self.links = []  # list of Link objects
        self.is_start = is_start
        self.owner = owner  # player ID or None for neutral

    def add_link(self, link):
        if link not in self.links:
            self.links.append(link)

    def __repr__(self):
        tag = " (Start)" if self.is_start else ""
        owner = f" [P{self.owner}]" if self.owner else ""
        return f"Node({self.id}{owner}{tag})"


class Link:
    def __init__(self, node_a, node_b):
        self.node_a = node_a
        self.node_b = node_b

    def connects(self, node):
        return self.node_b if node == self.node_a else self.node_a

    def __repr__(self):
        return f"Link({self.node_a.id} <-> {self.node_b.id})"


class Graph:
    def __init__(self):
        self.nodes = []
        self.links = []

    def add_node(self, node):
        self.nodes.append(node)

    def add_link(self, node_a, node_b):
        if not self.nodes_connected(node_a, node_b):
            link = Link(node_a, node_b)
            node_a.add_link(link)
            node_b.add_link(link)
            self.links.append(link)

    def nodes_connected(self, node_a, node_b):
        return any(
            (l.node_a == node_a and l.node_b == node_b)
            or (l.node_a == node_b and l.node_b == node_a)
            for l in self.links
        )

    def merge(self, other_graph):
        """Merge another graph into this one."""
        self.nodes.extend(other_graph.nodes)
        self.links.extend(other_graph.links)

    def display(self):
        print(f"\nGraph with {len(self.nodes)} nodes and {len(self.links)} links:")
        for node in self.nodes:
            connected_ids = [l.connects(node).id for l in node.links]
            start_flag = " (Start)" if node.is_start else ""
            owner = f" [P{node.owner}]" if node.owner else ""
            print(f"Node {node.id}{owner}{start_flag}: connected to {connected_ids}")


def generate_subgraph(num_nodes, id_start, owner=None, start_zone=False, avg_links_per_node=2):
    """Generate a connected subgraph with controlled link randomness."""
    g = Graph()
    nodes = [Node(id_start + i, owner=owner) for i in range(num_nodes)]
    for n in nodes:
        g.add_node(n)

    # Step 1: Spanning tree for guaranteed connectivity
    available_nodes = nodes[:]
    connected = [available_nodes.pop()]
    while available_nodes:
        node_a = random.choice(connected)
        node_b = available_nodes.pop()
        g.add_link(node_a, node_b)
        connected.append(node_b)

    # Step 2: Add random extra links (safe bounded version)
    max_possible_links = num_nodes * (num_nodes - 1) // 2
    target_links = min(int(num_nodes * avg_links_per_node / 2), max_possible_links)
    all_pairs = list(combinations(nodes, 2))
    random.shuffle(all_pairs)

    for (a, b) in all_pairs:
        if len(g.links) >= target_links:
            break
        g.add_link(a, b)

    # Mark start node if needed
    if start_zone:
        random.choice(nodes).is_start = True

    return g


def generate_world(num_players=3,
                   main_zone_nodes=(8, 15),
                   player_zone_nodes=(2, 4),
                   avg_links_main=2,
                   avg_links_player=2):
    """Generate full world graph with player starting areas + main graph."""
    current_id = 1

    # Generate main graph
    num_main_nodes = random.randint(*main_zone_nodes)
    main_graph = generate_subgraph(num_main_nodes, current_id, avg_links_per_node=avg_links_main)
    current_id += num_main_nodes

    # Generate player areas
    player_graphs = []
    num_nodes = random.randint(*player_zone_nodes)
    for p in range(1, num_players + 1):
        player_graph = generate_subgraph(
            num_nodes, current_id, owner=p, start_zone=True, avg_links_per_node=avg_links_player
        )
        current_id += num_nodes
        player_graphs.append(player_graph)

    # Merge everything and connect player areas to main graph
    world = Graph()
    world.merge(main_graph)

    for player_graph in player_graphs:
        # Choose one node in player's area as connection node
        connection_node = random.choice(player_graph.nodes)
        # Connect to 2 random nodes in the main graph
        main_targets = random.sample(main_graph.nodes, 2)
        for target in main_targets:
            player_graph.add_link(connection_node, target)
        # Merge into world
        world.merge(player_graph)

    return world


# ───────────────────────────────────────────────
# 🧭 Optional Visualization
# ───────────────────────────────────────────────
def visualize_graph(world):
    if not HAS_VIS:
        print("Visualization libraries (networkx/matplotlib) not installed.")
        return

    G = nx.Graph()

    # Add nodes with attributes
    for node in world.nodes:
        G.add_node(node.id, owner=node.owner, is_start=node.is_start)

    # Add edges
    for link in world.links:
        G.add_edge(link.node_a.id, link.node_b.id)

    # Color mapping
    color_map = []
    for node in world.nodes:
        if node.is_start:
            color_map.append("yellow")  # highlight start nodes
        elif node.owner:
            # Assign a color per player (basic palette)
            palette = ["red", "blue", "green", "orange", "purple", "teal", "pink"]
            color_map.append(palette[(node.owner - 1) % len(palette)])
        else:
            color_map.append("gray")  # main world

    # Layout & plot
    plt.figure(figsize=(9, 7))
    pos = nx.spring_layout(G, seed=42, k=0.7)

    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=500, edgecolors="black")
    nx.draw_networkx_edges(G, pos, alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_size=9, font_color="white")

    plt.title("Heroes 3 Map Graph (Players & Main World)")
    plt.axis("off")
    plt.show()


# ───────────────────────────────────────────────
if __name__ == "__main__":
    random.seed()  # Set e.g. random.seed(42) for deterministic output

    world = generate_world(num_players=4)
    world.display()

    visualize_graph(world)
