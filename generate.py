import math
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
                   main_zone_nodes=(8, 16),
                   player_zone_nodes=(3, 4),
                   avg_links_main=3,
                   avg_links_player=2):
    """Generate full world graph with player starting areas + main graph."""
    current_id = 1

    # Generate main graph
    num_main_nodes = random.randint(*main_zone_nodes)
    main_graph = generate_subgraph(num_main_nodes, current_id, avg_links_per_node=avg_links_main)
    current_id += num_main_nodes

    # Generate player areas (identical structure for all)
    player_graphs = []
    num_nodes = random.randint(*player_zone_nodes)

    # Create one "template" player zone
    template_graph = generate_subgraph(
        num_nodes, id_start=0, owner=None, start_zone=True, avg_links_per_node=avg_links_player
    )

    # Deep-copy the structure for each player with new node IDs
    for p in range(1, num_players + 1):
        # Create node copies with new IDs
        nodes_map = {}
        copied_nodes = []
        for n in template_graph.nodes:
            new_node = Node(current_id, is_start=n.is_start, owner=p)
            nodes_map[n.id] = new_node
            copied_nodes.append(new_node)
            current_id += 1

        # Build graph
        g = Graph()
        for n in copied_nodes:
            g.add_node(n)

        # Recreate links using mapped nodes
        for l in template_graph.links:
            a = nodes_map[l.node_a.id]
            b = nodes_map[l.node_b.id]
            g.add_link(a, b)

        player_graphs.append(g)

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
# Small geometry helpers (no extra deps)
# ───────────────────────────────────────────────
def _monotonic_chain(points):
    """Returns convex hull of points as list of (x, y) in CCW order."""
    # Andrew's monotone chain; points is a list of (x,y)
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenate lower and upper to get full hull; last point of each list is omitted because it’s repeated
    return lower[:-1] + upper[:-1]

def _inflate_polygon(poly, amount=0.05):
    """Naive polygon inflation in layout space: moves each vertex slightly away from centroid."""
    if not poly:
        return poly
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    inflated = []
    for x, y in poly:
        vx, vy = x - cx, y - cy
        # small push; if degenerate (0,0) push diagonally
        if vx == 0 and vy == 0:
            vx = vy = 1e-3
        mag = math.hypot(vx, vy)
        nx, ny = vx / mag, vy / mag
        inflated.append((x + nx * amount, y + ny * amount))
    return inflated

# ───────────────────────────────────────────────
# 🧭 Visualization with player-zone hull shading
# ───────────────────────────────────────────────
def visualize_graph(world):
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
    except ImportError:
        print("Visualization libraries (networkx/matplotlib) not installed.")
        return

    G = nx.Graph()

    # Add nodes with attributes
    for node in world.nodes:
        G.add_node(node.id, owner=node.owner, is_start=node.is_start)

    # Add edges
    for link in world.links:
        G.add_edge(link.node_a.id, link.node_b.id)

    # Consistent layout
    pos = nx.spring_layout(G, seed=42, k=0.7)

    # Color mapping for nodes
    palette = ["red", "blue", "green", "orange", "purple", "teal", "pink"]
    node_colors = []
    for node in world.nodes:
        if node.is_start:
            node_colors.append("yellow")
        elif node.owner:
            node_colors.append(palette[(node.owner - 1) % len(palette)])
        else:
            node_colors.append("gray")

    # Draw edges first
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_edges(G, pos, alpha=0.5)

    # ── Draw shaded convex hulls for each player's zone
    # group node ids by owner
    owner_to_nodes = {}
    for node in world.nodes:
        if node.owner:
            owner_to_nodes.setdefault(node.owner, []).append(node.id)

    for owner, ids in owner_to_nodes.items():
        pts = [(pos[n][0], pos[n][1]) for n in ids]

        # Handle tiny groups gracefully
        hull_pts = []
        if len(pts) >= 3:
            hull_pts = _monotonic_chain(pts)
            hull_pts = _inflate_polygon(hull_pts, amount=0.06)  # small padding
        elif len(pts) == 2:
            # make a skinny capsule-like quad around the segment
            (x1, y1), (x2, y2) = pts
            dx, dy = x2 - x1, y2 - y1
            mag = math.hypot(dx, dy) or 1.0
            nxp, nyp = -dy / mag, dx / mag  # perpendicular
            pad = 0.05
            hull_pts = [(x1 + nxp*pad, y1 + nyp*pad),
                        (x2 + nxp*pad, y2 + nyp*pad),
                        (x2 - nxp*pad, y2 - nyp*pad),
                        (x1 - nxp*pad, y1 - nyp*pad)]
        else:
            # single point: small diamond
            x, y = pts[0]
            pad = 0.06
            hull_pts = [(x, y + pad), (x + pad, y), (x, y - pad), (x - pad, y)]

        # Fill polygon with player color, low alpha
        face = palette[(owner - 1) % len(palette)]
        xs, ys = zip(*hull_pts)
        plt.fill(xs, ys, alpha=0.15, color=face, zorder=0, linewidth=0)

    # Draw nodes on top
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=520, edgecolors="black")
    nx.draw_networkx_labels(G, pos, font_size=9, font_color="white")

    plt.title("Heroes 3 Map Graph — Player Zones Highlighted")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

# ───────────────────────────────────────────────
if __name__ == "__main__":
    random.seed()  # Set e.g. random.seed(42) for deterministic output

    world = generate_world(num_players=6)
    world.display()

    visualize_graph(world)
