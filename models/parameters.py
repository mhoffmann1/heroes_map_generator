from itertools import combinations
from config import ZONE_CONFIG, RESOURCE_NAMES
from utils.randomize import random_bool, random_choice_weighted, weighted_choice, jitter, pick_random_subset

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