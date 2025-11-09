import math
import random
import argparse
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

def weighted_choice(weights):
    """Return index (1-based) according to weight distribution list."""
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for i, w in enumerate(weights, start=1):
        if upto + w >= r:
            return i
        upto += w
    return len(weights)

def jitter(value, pct=0.1):
    """Return value randomly adjusted by ±pct, keeping it integer."""
    low = int(value * (1 - pct))
    high = int(value * (1 + pct))
    return random.randint(low, high)

def pick_random_subset(options, chance_per_item, max_total=None):
    """Return dict of {option: 0 or 1} with chance per item, optionally limited by max_total."""
    chosen = []
    for o in options:
        if random.random() < chance_per_item:
            chosen.append(o)
    if max_total and len(chosen) > max_total:
        chosen = random.sample(chosen, max_total)
    return {o: 1 if o in chosen else 0 for o in options}

# Optional manual overrides (these replace generated defaults if set)
#MANUAL_OVERRIDES = {
#    "monster_disposition": None,     # (0 - always join, 1 - Friendly [1-7], 2 - Aggresive [1-10], 3 - hostile [4-10], 4-  Savage [10]
#    "joining_percent": None,         # (0 - 25%, 1 - 50%, 2 - 75%, 3 - 100%)
#    "join_only_for_money": None      # usually "x" or ""
#}

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

def terrain_and_monster_attributes(node):
    """Generate terrain- and monster-related attributes."""
    attrs = {}

    nt = node.attributes.get("neutral_towns_min", 0)
    nc = node.attributes.get("neutral_castle_min", 0)

    # ─── terrain_match_town ───
    if node.node_type == NodeType.START:
        attrs["terrain_match_town"] = 1
    elif nt > 0 or nc > 0:
        attrs["terrain_match_town"] = 1 if random_bool(0.8) else 0
    else:
        attrs["terrain_match_town"] = 0

    # ─── allowed_terrain_1–10 (placeholders) ───
    for i in range(1, 11):
        attrs[f"allowed_terrain_{i}"] = 1

    # ─── monster_strength ───
    if node.node_type == NodeType.START or node.node_type == NodeType.NEUTRAL or node.node_type == NodeType.JUNCTION:
        attrs["monster_strength"] = 2
    elif node.node_type == NodeType.TREASURE:
        attrs["monster_strength"] = 2 if random_bool(0.8) else 3
    elif node.node_type == NodeType.SUPER_TREASURE:
        attrs["monster_strength"] = 2 if random_bool(0.7) else 3
    else:
        attrs["monster_strength"] = 0  # fallback / neutral

    # ─── monster_match_town ───
    if node.node_type == NodeType.START:
        attrs["monster_match_town"] = 0
    elif nt > 0 or nc > 0:
        attrs["monster_match_town"] = 1 if random_bool(0.1) else 0
    else:
        attrs["monster_match_town"] = 0

    # ─── allowed_monster_type_1–12 (placeholders) ───
    for i in range(1, 13):
        attrs[f"allowed_monster_type_{i}"] = 1

    return attrs

def treasure_attributes(node):
    """Generate treasure-related attributes for the zone."""
    attrs = {}

    # Determine effective type (JUNCTION uses NEUTRAL or TREASURE randomly)
    ntype = node.node_type
    if node.node_type == NodeType.JUNCTION:
        ntype = NodeType.NEUTRAL if random_bool(0.5) else NodeType.TREASURE

    # Base definitions per type
    if ntype == NodeType.START or ntype == NodeType.NEUTRAL:
        t1_low, t1_high = 500, 3000
        t2_low, t2_high = 3000, 6000
        t3_low, t3_high = 10000, 15000
    elif ntype == NodeType.TREASURE:
        t1_low, t1_high = 3000, 6000
        t2_low, t2_high = 10000, 15000
        t3_low, t3_high = 15000, 20000
    elif ntype == NodeType.SUPER_TREASURE:
        t1_low, t1_high = 10000, 15000
        t2_low, t2_high = 15000, 20000
        t3_low, t3_high = 20000, 30000
    else:
        # fallback — treat as neutral
        t1_low, t1_high = 500, 3000
        t2_low, t2_high = 3000, 6000
        t3_low, t3_high = 10000, 15000

    # Apply jitter ±10%
    attrs["treasure1_low"] = jitter(t1_low)
    attrs["treasure1_high"] = jitter(t1_high)
    attrs["treasure1_density"] = 9

    attrs["treasure2_low"] = jitter(t2_low)
    attrs["treasure2_high"] = jitter(t2_high)
    attrs["treasure2_density"] = 6

    attrs["treasure3_low"] = jitter(t3_low)
    attrs["treasure3_high"] = jitter(t3_high)
    attrs["treasure3_density"] = 1

    # Fixed attributes
    attrs["zone_placement"] = ""     # other posible values: ground, underground
    attrs["objects_section"] = ""  # empty placeholder

    return attrs

def meta_zone_attributes(node):
    """Generate final batch of meta/control attributes for the zone."""
    attrs = {}

    # ─── UI positions (4 placeholders, can be ±float, set to empty now)
    for i in range(1, 5):
        attrs[f"UI_position_{i}"] = ""

    # ─── Various placeholders
    attrs["zone_faction_force_neutral"] = ""
    attrs["zone_repulsion"] = ""
    attrs["town_type_rules"] = ""
    attrs["shipyard_density"] = ""
    attrs["terrain_type_rule"] = ""
    attrs["customized_allowed_factions_bitmap"] = ""
    attrs["zone_faction_rule"] = ""

    # ─── allow_non_coherent_road ───
    attrs["allow_non_coherent_road"] = "" if random_bool(0.75) else "x"

    # ─── monster_disposition ───
    if MANUAL_OVERRIDES.get("monster_disposition") is not None:
        attrs["monster_disposition"] = MANUAL_OVERRIDES["monster_disposition"]
    else:
        # 25% → 1, 50% → 2, 25% → 3
        attrs["monster_disposition"] = weighted_choice([0.25, 0.5, 0.25])

    # ─── custom_monster_disposition ───
    attrs["custom_monster_disposition"] = ""

    # ─── joining_percent ───
    if MANUAL_OVERRIDES.get("joining_percent") is not None:
        attrs["joining_percent"] = MANUAL_OVERRIDES["joining_percent"]
    else:
        attrs["joining_percent"] = 1

    # ─── join_only_for_money ───
    if MANUAL_OVERRIDES.get("join_only_for_money") is not None:
        attrs["join_only_for_money"] = MANUAL_OVERRIDES["join_only_for_money"]
    else:
        attrs["join_only_for_money"] = "x"

    # ─── shipyard_min ───
    if node.node_type == NodeType.SUPER_TREASURE:
        attrs["shipyard_min"] = 1 if random_bool(0.1) else ""
    else:
        attrs["shipyard_min"] = ""

    # ─── max_road_block_value ───
    attrs["max_road_block_value"] = 4000 if node.node_type == NodeType.START else ""

    return attrs


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

    # generate mines
    node.attributes.update(resource_logic(node))
    # generate terrain and monsters
    node.attributes.update(terrain_and_monster_attributes(node))
    # generate treasure
    node.attributes.update(treasure_attributes(node))
    # misc parameters
    node.attributes.update(meta_zone_attributes(node))


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

# ───────────────────────────────────────────────
# Helpers to build main graph by style
# ───────────────────────────────────────────────
def _generate_main_graph_random(main_zone_nodes, current_id, avg_links_main):
    num_main_nodes = random.randint(*main_zone_nodes)
    main_graph = generate_subgraph(num_main_nodes, current_id, avg_links_per_node=avg_links_main)

    # Type assignment (current "random" method)
    for node in main_graph.nodes:
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

    return main_graph, num_main_nodes

def _generate_main_graph_balanced(main_zone_nodes, current_id, avg_links_main, num_players=4):
    """
    Generate a symmetrical balanced main graph:
      - Create one small random 'core fragment'
      - Clone it for each player
      - Interconnect clones in mirrored fashion
      - Connect player zones symmetrically via 2–3 links
    """
    # Generate small base fragment
    fragment_size = int(random.randint(*main_zone_nodes)/num_players)
    base_fragment = generate_subgraph(fragment_size, id_start=0, avg_links_per_node=avg_links_main)

    for node in base_fragment.nodes:
        roll = random.random()
        if roll < 0.1:
            node.node_type = NodeType.JUNCTION
        elif roll < 0.4:
            node.node_type = NodeType.NEUTRAL
        elif roll < 0.7:
            node.node_type = NodeType.TREASURE
        else:
            node.node_type = NodeType.SUPER_TREASURE
        assign_zone_attributes(node)

    # Clone fragment for each player
    clone_graphs = []  # list of (Graph, [nodes]) tuples
    for _ in range(num_players):
        nodes_map = {}
        new_nodes = []
        g = Graph()

        for n in base_fragment.nodes:
            new_n = Node(current_id, node_type=n.node_type)
            new_n.attributes = dict(n.attributes)
            nodes_map[n.id] = new_n
            g.add_node(new_n)
            new_nodes.append(new_n)
            current_id += 1

        # Recreate internal links
        for l in base_fragment.links:
            g.add_link(nodes_map[l.node_a.id], nodes_map[l.node_b.id])

        clone_graphs.append((g, new_nodes))

    # Create mirrored connections between fragments
    base_nodes = list(base_fragment.nodes)
    connection_indices = random.sample(range(len(base_nodes)), k=min(2, len(base_nodes)))

    for i in range(num_players):
        next_i = (i + 1) % num_players  # wrap around for symmetry
        for idx in connection_indices:
            node_a = clone_graphs[i][1][idx]
            node_b = clone_graphs[next_i][1][idx]
            clone_graphs[i][0].add_link(node_a, node_b)

    # Define indices for player-to-fragment links (symmetrical)
    fragment_node_indices = list(range(len(base_fragment.nodes)))
    num_connections = random.choice([2, 3])
    player_connection_indices = random.sample(fragment_node_indices, k=min(num_connections, len(fragment_node_indices)))

    # Merge all clones into unified main graph
    main_graph = Graph()
    for g, _ in clone_graphs:
        main_graph.merge(g)

    # ⬇️ Return everything the caller needs
    return main_graph, len(main_graph.nodes), player_connection_indices, clone_graphs, base_fragment


# ───────────────────────────────────────────────
# Core world generation with human + AI players + map style
# ───────────────────────────────────────────────
def generate_world(
    num_human_players=3,
    num_ai_players=0,
    map_style="random",                 # "random" or "balanced"
    main_zone_nodes=(8, 16),
    player_zone_nodes=(3, 4),
    avg_links_main=3,
    avg_links_player=2
):
    """
    Generate full world:
    - Main graph by 'map_style'
    - Human players: identical starting areas (cloned from one template)
    - AI players: single START node cloned from the template's START node
    """
    assert 1 <= num_human_players <= 8, "Human players must be in [1, 8]"
    total_players = num_human_players + num_ai_players
    assert total_players <= 8, "Total players (human + AI) must be <= 8"

    current_id = 1

    # 1) Generate main graph by style
    if map_style.lower() == "balanced":
        # ───────────────────────────────────────────────
        # BALANCED MAP GENERATION
        # ───────────────────────────────────────────────
        main_graph, num_main_nodes, player_connection_indices, clone_graphs, base_fragment = _generate_main_graph_balanced(
    main_zone_nodes, current_id, avg_links_main, num_players=num_human_players
)

    else:
        main_graph, num_main_nodes = _generate_main_graph_random(main_zone_nodes, current_id, avg_links_main)
    
    current_id += num_main_nodes
        
    # 2) Build human template starting area
    num_nodes = random.randint(*player_zone_nodes)
    template_graph = generate_subgraph(
        num_nodes, id_start=0, owner=None, start_zone=True, avg_links_per_node=avg_links_player
    )
    # Assign node types & attributes for template (identical across all humans)
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
    # Keep a reference to the template START node (for AI cloning)
    if num_ai_players:
        tmpl_start = next((n for n in template_graph.nodes if n.node_type == NodeType.START), None)
        if tmpl_start is None:
            raise RuntimeError("Template graph did not produce a START node — this should not happen.")
    
    # 3) Clone template for each human player
    human_graphs = []
    for p in range(1, num_human_players + 1):
        nodes_map = {}
        copied_nodes = []
        for n in template_graph.nodes:
            new_node = Node(
                current_id,
                node_type=n.node_type,
                owner=p,
                is_start=n.is_start
            )
            new_node.attributes = dict(n.attributes)
            if new_node.node_type == NodeType.START:
                new_node.attributes["player_control"] = new_node.owner
            nodes_map[n.id] = new_node
            copied_nodes.append(new_node)
            current_id += 1
        g = Graph()
        for n in copied_nodes:
            g.add_node(n)
        for l in template_graph.links:
            a = nodes_map[l.node_a.id]
            b = nodes_map[l.node_b.id]
            g.add_link(a, b)
        human_graphs.append(g)

    # 4) Prepare world & connect human areas to main graph
    world = Graph()
    world.merge(main_graph)

    if map_style.lower() == "random":
        # Choose connection indices ONCE from the template (can be same index twice)
        template_nodes = list(template_graph.nodes)
        if len(template_nodes) == 1:
            connection_indices = [0, 0]
        else:
            connection_indices = [
                random.randrange(len(template_nodes)),
                random.randrange(len(template_nodes)),
            ]
        for human_graph in human_graphs:
            player_nodes = list(human_graph.nodes)
            main_targets = random.sample(list(main_graph.nodes), 2)
            for conn_idx, target in zip(connection_indices, main_targets):
                connection_node = player_nodes[conn_idx]
                human_graph.add_link(connection_node, target)
            world.merge(human_graph)
        # 5) Create AI players: each gets a single START node cloned from the template START
        #    and connects to main graph with 2 links
        next_owner = num_human_players + 1
        for _ in range(num_ai_players):
            ai_start = Node(current_id, node_type=NodeType.START, owner=next_owner, is_start=True)
            ai_start.attributes = dict(tmpl_start.attributes)
            ai_start.attributes["player_control"] = next_owner
            ai_graph = Graph()
            ai_graph.add_node(ai_start)
            # connect to 2 random main graph nodes (from the same AI start node)
            main_targets = random.sample(list(main_graph.nodes), 2)
            for target in main_targets:
                ai_graph.add_link(ai_start, target)
            world.merge(ai_graph)
            current_id += 1
            next_owner += 1
    else:    
        # All players share the same pattern of start/main connections
        num_links = random.choice([2, 3])
        
        # Pick which player-zone nodes will connect
        player_nodes_example = list(template_graph.nodes)
        player_connection_indices = random.sample(
            range(len(player_nodes_example)),
            k=min(num_links, len(player_nodes_example))
        )
        
        # Pick which main-fragment nodes (by index within fragment) will connect
        base_fragment_nodes = list(base_fragment.nodes)
        main_connection_indices = random.sample(
            range(len(base_fragment_nodes)),
            k=min(num_links, len(base_fragment_nodes))
        )
        
        # Now connect each player's start zone <-> their corresponding main fragment clone
        for i, human_graph in enumerate(human_graphs):
            player_nodes = list(human_graph.nodes)
            player_main_nodes = clone_graphs[i][1]  # the nodes of this player’s cloned main subgraph
        
            for p_idx, m_idx in zip(player_connection_indices, main_connection_indices):
                player_node = player_nodes[p_idx]
                main_node = player_main_nodes[m_idx]
                human_graph.add_link(player_node, main_node)
        
            world.merge(human_graph)

    return world

# ───────────────────────────────────────────────
# Simple interactive entrypoint
# ───────────────────────────────────────────────
def _ask_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            v = int(input(prompt).strip())
            if min_val is not None and v < min_val:
                print(f"Value must be >= {min_val}.")
                continue
            if max_val is not None and v > max_val:
                print(f"Value must be <= {max_val}.")
                continue
            return v
        except ValueError:
            print("Please enter an integer.")

def _ask_choice(prompt, choices):
    choices_lower = [c.lower() for c in choices]
    while True:
        v = input(f"{prompt} ({'/'.join(choices)}): ").strip().lower()
        if v in choices_lower:
            return v
        print(f"Please choose one of: {', '.join(choices)}")


def build_world_interactive():
    # 1) Human players
    num_humans = _ask_int("Number of HUMAN players (1-8): ", 1, 8)

    # 2) AI players, keep total <= 8
    max_ai = 8 - num_humans
    if max_ai == 0:
        print("Maximum total players reached; AI players set to 0.")
        num_ai = 0
    else:
        num_ai = _ask_int(f"Number of AI players (0-{max_ai}): ", 0, max_ai)

    # 3) Map style
    map_style = _ask_choice("Map style", ["random", "balanced"])

    # Ask about zone numbers and number of links

    world = generate_world(
        num_human_players=num_humans,
        num_ai_players=num_ai,
        map_style=map_style,
        main_zone_nodes=(8, 16),
        player_zone_nodes=(3, 4),
        avg_links_main=3,
        avg_links_player=2
    )
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

    ids = [n.id for n in world.nodes]
    print(f"Total nodes: {len(world.nodes)}, Unique IDs: {len(set(ids))}")
    loops = [l for l in world.links if l.node_a.id == l.node_b.id]
    print(f"Self-loops: {len(loops)}")

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
    for node_id in G.nodes:
        data = G.nodes[node_id]
        owner = data.get("owner")
        is_start = data.get("is_start")
        if is_start:
            node_colors.append("yellow")
        elif owner:
            node_colors.append(palette[(owner - 1) % len(palette)])
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
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--monster_disposition", type=int, help="Override monster disposition (1–3)")
    parser.add_argument("--joining_percent", type=float, help="Override joining percent")
    parser.add_argument("--join_only_for_money", type=str, help="Override join_only_for_money (x or empty)")
    args = parser.parse_args()

    MANUAL_OVERRIDES = {
        "monster_disposition": args.monster_disposition,
        "joining_percent": args.joining_percent,
        "join_only_for_money": args.join_only_for_money
    }

    random.seed()  # Set e.g. random.seed(42) for deterministic output

    #world = generate_world(num_players=3)
    world = build_world_interactive()
    world.display()

    visualize_graph(world)
