import argparse
import math
import random
from enum import Enum, auto
from itertools import combinations

# Optional visualization libraries
try:
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_VIS = True
except ImportError:
    HAS_VIS = False


class NodeType(Enum):
    START = auto()
    NEUTRAL = auto()
    TREASURE = auto()
    SUPER_TREASURE = auto()
    JUNCTION = auto()

def random_bool(chance):
    """Return True with given probability (0.0–1.0)."""
    return random.random() < chance

def random_choice_weighted(options):
    """Random weighted choice: expects list of (value, probability)."""
    r = random.random()
    cumulative = 0
    for value, prob in options:
        cumulative += prob
        if r <= cumulative:
            return value
    return options[-1][0]  # fallback

def pick_random_subset(options, chance_per_item, max_total=None):
    """Return dict of {option: 0 or 1} with chance per item, optionally limited by max_total."""
    chosen = []
    for o in options:
        if random.random() < chance_per_item:
            chosen.append(o)
    if max_total and len(chosen) > max_total:
        chosen = random.sample(chosen, max_total)
    return {o: 1 if o in chosen else 0 for o in options}

ZONE_CONFIG = {
    NodeType.START: {
        "zone_type": lambda: 1,
        "zone_size": lambda: random.randint(15, 40),
        "res_parameter1": 1,
        "res_parameter2": 8,
        "res_parameter3": 2,
        "res_parameter4": 8,
        "player_control": lambda node: node.owner or 0,  # owner number or 0
        "player_towns_min": 0,
        "player_castles_min": 1,
        "player_towns_density": 0,
        "player_castles_density": 0,

        "neutral_towns_min": lambda: 1 if random_bool(0.2) else 0,
        "neutral_castle_min": lambda node: 0 if node.attributes.get("neutral_towns_min", 0) > 0 else 0,
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": lambda: random.choice([0, 1]),  # 50/50
        **{f"allowed_castle_{i}": 1 for i in range(1, 12)}
    },
    NodeType.NEUTRAL: {
        "zone_type": lambda: 3,  # neutral = junction
        "zone_size": lambda: random.randint(15, 40),
        "res_parameter1": 1,
        "res_parameter2": 8,
        "res_parameter3": 2,
        "res_parameter4": 8,
        "player_control": lambda node: 0,

        "player_towns_min": 0,
        "player_castles_min": 0,
        "player_towns_density": 0,
        "player_castles_density": 0,

        "neutral_towns_min": lambda: 1 if random_bool(0.2) else 0,
        "neutral_castle_min": lambda node: (
            0 if node.attributes.get("neutral_towns_min", 0) > 0
            else random_choice_weighted([(1, 0.1), (0, 0.9)])
        ),
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": lambda: random.choice([0, 1]),
        **{f"allowed_castle_{i}": 1 for i in range(1, 12)}
    },
    NodeType.TREASURE: {
        "zone_type": lambda: 2,
        "zone_size": lambda: random.randint(15, 40),
        "res_parameter1": 1,
        "res_parameter2": 8,
        "res_parameter3": 2,
        "res_parameter4": 8,
        "player_control": lambda node: 0,

        "player_towns_min": 0,
        "player_castles_min": 0,
        "player_towns_density": 0,
        "player_castles_density": 0,

        "neutral_towns_min": lambda: random_choice_weighted([(2, 0.1), (1, 0.3), (0, 0.6)]),
        "neutral_castle_min": lambda node: (
            0 if node.attributes.get("neutral_towns_min", 0) > 0
            else random_choice_weighted([(1, 0.2), (0, 0.8)])
        ),
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": lambda: random.choice([0, 1]),
        **{f"allowed_castle_{i}": 1 for i in range(1, 12)}
    },
    NodeType.SUPER_TREASURE: {
        "zone_type": lambda: 2,  # same zone_type as normal treasure
        "zone_size": lambda: random.randint(20, 40),
        "res_parameter1": 1,
        "res_parameter2": 8,
        "res_parameter3": 2,
        "res_parameter4": 8,
        "player_control": lambda node: 0,

        "player_towns_min": 0,
        "player_castles_min": 0,
        "player_towns_density": 0,
        "player_castles_density": 0,

        "neutral_towns_min": lambda: random_choice_weighted([(2, 0.1), (1, 0.3), (0, 0.6)]),
        "neutral_castle_min": lambda node: (
            0 if node.attributes.get("neutral_towns_min", 0) > 0
            else random_choice_weighted([(2, 0.1), (1, 0.2), (0, 0.7)])
        ),
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": lambda: random.choice([0, 1]),
        **{f"allowed_castle_{i}": 1 for i in range(1, 12)}
    }
}

from config import MANUAL_OVERRIDES
from utils.input_output import build_world_interactive, visualize_graph
from utils.export import export_to_h3t

# Optional visualization libraries
try:
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_VIS = True
except ImportError:
    HAS_VIS = False

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--monster_disposition", type=int, help="Override monster disposition (1–3)")
    parser.add_argument("--joining_percent", type=float, help="Override joining percent")
    parser.add_argument("--join_only_for_money", type=str, help="Override join_only_for_money (x or empty)")
    args = parser.parse_args()

    MANUAL_OVERRIDES.update({
        "monster_disposition": args.monster_disposition,
        "joining_percent": args.joining_percent,
        "join_only_for_money": args.join_only_for_money
    })

    random.seed()  # Set e.g. random.seed(42) for deterministic output

    #world = generate_world(num_players=3)
    world = build_world_interactive()
    world.display()

    visualize_graph(world)

    export_to_h3t(world)
class Node:
    def __init__(self, node_id, node_type=None, owner=None, is_start=False):
        self.id = node_id
        self.node_type = node_type
        self.owner = owner
        self.is_start = is_start
        self.links = []
        self.attributes = {}  # all generated values live here

    def add_link(self, link):
        if link not in self.links:
            self.links.append(link)

    def __repr__(self):
        type_name = self.node_type.name if self.node_type else "?"
        owner = f"[P{self.owner}]" if self.owner else ""
        return f"Node({self.id}, {type_name}{owner}{' (Start)' if self.is_start else ''})"

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
            owner = f" [Player{node.owner}]" if node.owner else ""
            zone_type = f" {node.node_type}"
            attributes = node.attributes
            print(f"Node {node.id}{owner}{start_flag}{zone_type}: connected to {connected_ids}. Attributes:\n {attributes}")

RESOURCE_NAMES = ["wood", "mercury", "ore", "sulfur", "crystals", "gems", "gold"]

def resource_logic(node):
    """Generates *_min and *_density attributes for a given node."""
    res = {}

    # Default all to 0
    for r in RESOURCE_NAMES:
        res[f"{r}_min"] = 0
        res[f"{r}_density"] = 0

    nt = node.attributes.get("neutral_towns_min", 0)
    nc = node.attributes.get("neutral_castle_min", 0)

    # --- START zones ---
    if node.node_type == NodeType.START:
        res["wood_min"] = 1
        res["ore_min"] = 1
        # 10% chance that exactly one special resource is 1
        if random_bool(0.1):
            special = random.choice(["mercury", "sulfur", "crystals", "gems"])
            res[f"{special}_min"] = 1

    # --- NEUTRAL zones ---
    elif node.node_type == NodeType.NEUTRAL:
        # Adjust wood/ore based on towns/castles
        if nc > 0:
            res["wood_min"] = res["ore_min"] = 1
        elif nt > 0:
            if random_bool(0.5):
                res["wood_min"] = res["ore_min"] = 1
        # 25% chance one of the rare resources is 1
        if random_bool(0.25):
            special = random.choice(["mercury", "sulfur", "crystals", "gems"])
            res[f"{special}_min"] = 1
        # gold 5%
        if random_bool(0.05):
            res["gold_min"] = 1

    # --- TREASURE zones ---
    elif node.node_type == NodeType.TREASURE:
        # wood/ore rules depend on towns/castles
        if nc > 0:
            res["wood_min"] = res["ore_min"] = 1
        elif nt > 0:
            if random_bool(0.5):
                res["wood_min"] = res["ore_min"] = 1
        # Each rare has 20% chance, max 2 total
        subset = pick_random_subset(["mercury", "sulfur", "crystals", "gems"], 0.2, max_total=2)
        for k, v in subset.items():
            res[f"{k}_min"] = v
        # gold 10%
        if random_bool(0.10):
            res["gold_min"] = 1

    # --- SUPER TREASURE zones ---
    elif node.node_type == NodeType.SUPER_TREASURE:
        if nc > 0:
            res["wood_min"] = res["ore_min"] = 1
        elif nt > 0:
            if random_bool(0.5):
                res["wood_min"] = res["ore_min"] = 1
        # Each rare 25%, no limit
        subset = pick_random_subset(["mercury", "sulfur", "crystals", "gems"], 0.25)
        for k, v in subset.items():
            res[f"{k}_min"] = v
        # gold 20%
        if random_bool(0.20):
            res["gold_min"] = 1

    # --- Junction / others (no resources) ---
    elif node.node_type == NodeType.JUNCTION:
        for r in ["mercury", "sulfur", "crystals", "gems", "gold"]:
            if random_bool(0.1):
                res[f"{r}_min"] = 1    
    else:
        pass

    return res

def assign_zone_attributes(node):
    config = ZONE_CONFIG.get(node.node_type, {})
    for key, value in config.items():
        if callable(value):
            try:
                node.attributes[key] = value(node)
            except TypeError:
                node.attributes[key] = value()
        else:
            node.attributes[key] = value

    node.attributes.update(resource_logic(node))

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
    
    for node in main_graph.nodes:
        # neutral world nodes
        roll = random.random()
        if roll < 0.1:
            node.node_type = NodeType.JUNCTION
        elif roll < 0.4:
            node.node_type = NodeType.NEUTRAL
        elif roll < 0.8:
            node.node_type = NodeType.TREASURE
        else:
            node.node_type = NodeType.SUPER_TREASURE
        assign_zone_attributes(node)

    current_id += num_main_nodes

    # Generate player areas (identical structure, node types, and attributes for all)
    player_graphs = []
    num_nodes = random.randint(*player_zone_nodes)

    # ──────────────────────────────
    # STEP 1: Generate template zone (first player)
    # ──────────────────────────────
    template_graph = generate_subgraph(
        num_nodes, id_start=0, owner=None, start_zone=True, avg_links_per_node=avg_links_player
    )

    # Assign node types & generate attributes for template
    for node in template_graph.nodes:
        if node.is_start:
            node.node_type = NodeType.START
        else:
            roll = random.random()
            if roll < 0.7:
                node.node_type = NodeType.NEUTRAL
            elif roll < 0.9:
                node.node_type = NodeType.TREASURE
            else:
                node.node_type = NodeType.SUPER_TREASURE
        assign_zone_attributes(node)

    # Add logic to ensure specific castle is same type as players castle

    # ──────────────────────────────
    # STEP 2: Clone template for each player
    # ──────────────────────────────
    for p in range(1, num_players + 1):
        nodes_map = {}
        copied_nodes = []

        for n in template_graph.nodes:
            new_node = Node(
                current_id,
                node_type=n.node_type,
                owner=p,
                is_start=n.is_start
            )
            # Deep copy all generated attributes
            new_node.attributes = dict(n.attributes)
            if new_node.node_type == NodeType.START:
                new_node.attributes["player_control"] = new_node.owner

            nodes_map[n.id] = new_node
            copied_nodes.append(new_node)
            current_id += 1

        g = Graph()
        for n in copied_nodes:
            g.add_node(n)

        # Recreate links using the ID map
        for l in template_graph.links:
            a = nodes_map[l.node_a.id]
            b = nodes_map[l.node_b.id]
            g.add_link(a, b)

        player_graphs.append(g)


    # Merge everything and connect player areas to main graph
    world = Graph()
    world.merge(main_graph)


#Fixup! the same node/s should be connected to main map for each player zone
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
        import matplotlib.pyplot as plt
        import networkx as nx
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

    world = generate_world(num_players=3)
    world.display()

    visualize_graph(world)
