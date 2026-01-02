import random

from config import MANUAL_OVERRIDES, RESOURCE_NAMES, ZONE_CONFIG
from models.objects import NodeType
from utils.randomize import (
    jitter,
    pick_random_subset,
    random_bool,
    weighted_choice,
)

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
        attrs["terrain_match_town"] = 'x'
    elif nt > 0 or nc > 0:
        attrs["terrain_match_town"] = 'x' if random_bool(0.8) else 0
    else:
        attrs["terrain_match_town"] = 0

    # ─── allowed_terrain_1–10 (placeholders) ───
    for i in range(1, 11):
        attrs[f"allowed_terrain_{i}"] = 'x'

    # ─── monster_strength ───
    if node.node_type == NodeType.START or node.node_type == NodeType.NEUTRAL or node.node_type == NodeType.JUNCTION:
        attrs["monster_strength"] = 'avg'
    elif node.node_type == NodeType.TREASURE:
        attrs["monster_strength"] = 'avg' if random_bool(0.8) else 'strong'
    elif node.node_type == NodeType.SUPER_TREASURE:
        attrs["monster_strength"] = 'avg' if random_bool(0.7) else 'strong'
    else:
        attrs["monster_strength"] = 'none'  # fallback

    # ─── monster_match_town ───
    if node.node_type == NodeType.START:
        attrs["monster_match_town"] = 0
    elif nt > 0 or nc > 0:
        attrs["monster_match_town"] = 'x' if random_bool(0.1) else 0
    else:
        attrs["monster_match_town"] = 0

    # ─── allowed_monster_type_1–12 (placeholders) ───
    for i in range(1, 14):
        attrs[f"allowed_monster_type_{i}"] = 'x'

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
    #for i in range(1, 5):
    attrs["UI_position"] = "0 0 0 0"

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

def apply_ai_difficulty(node, difficulty):
    """
    Modify the AI START node (and/or the zone around it)
    according to difficulty.
    """

    # Normal: do nothing
    if difficulty == 'normal':
        return

    # Hard difficulty: give extra resources
    if difficulty == 'hard':
        attrs = node.attributes
        attrs["treasure1_density"] = 15
        attrs["treasure2_density"] = 9
        attrs["treasure3_density"] = 3

    # Unfair difficulty: everything from Hard + monster joining buff
    if difficulty == 'unfair':
        # Include HARD buffs
        apply_ai_difficulty(node, 'hard')

        # Add unfair behavior
        attrs = node.attributes
        attrs["join_only_for_money"] = ''
        attrs["monster_disposition"] = 0
        attrs["monster_match_town"] = 1


def assign_all_link_attributes(graph):
    """
    Assign attributes for every link in a graph.
    Honors pre-marked player→main links.
    """
    for link in graph.links:
        # skip links that already have attributes - they are either player zones or set manualy. Should not be overwritten
        if link.attributes:
            continue
        assign_link_attributes(link, is_player_to_main=link.is_player_to_main)

def assign_link_attributes(link, is_player_to_main=False):
    """
    Assign parameters to a link based on connected zone types and game rules.
    If `is_player_to_main` is True, this link connects player start area to the main map.
    """

    a, b = link.node_a, link.node_b
    a_type = a.node_type
    b_type = b.node_type
    types = {a_type, b_type}

    attrs = {}

    # ───────────────────────────────
    # GUARD STRENGTH
    # ───────────────────────────────
    guard_strength = 0

    # START zone logic
    if NodeType.START in types:
        # Determine the "other" node type
        other_type = b_type if a_type == NodeType.START else a_type
        if other_type in (NodeType.NEUTRAL, NodeType.JUNCTION):
            guard_strength = random.randint(3000, 4000)
        elif other_type == NodeType.TREASURE:
            guard_strength = random.randint(5000, 7000)
        elif other_type == NodeType.SUPER_TREASURE:
            guard_strength = random.randint(8000, 12000)
        else:
            guard_strength = random.randint(2500, 3500)

    # All other (non-start) combinations
    else:
        # Simple heuristic matrix
        def strength_range(a_t, b_t):
            combo = {a_t, b_t}
            if combo == {NodeType.NEUTRAL}:
                return (3000, 5000)
            if combo == {NodeType.NEUTRAL, NodeType.TREASURE} or combo == {NodeType.TREASURE, None}:
                return (6000, 9000)
            if combo == {NodeType.TREASURE}:
                return (10000, 15000)
            if combo == {NodeType.TREASURE, NodeType.SUPER_TREASURE}:
                return (14000, 22000)
            if combo == {NodeType.NEUTRAL, NodeType.SUPER_TREASURE} or combo == {NodeType.SUPER_TREASURE, None}:
                return (15000, 25000)
            if combo == {NodeType.SUPER_TREASURE, NodeType.SUPER_TREASURE}:
                return (20000, 30000)
            if NodeType.JUNCTION in combo:
                return (10000, 20000)
            if is_player_to_main:
                return (6000, 9000)
            # fallback
            print(f"[DEBUG] Unable to determine Link type based on node type: {a_t} {b_t}")
            return (2000, 4000)

        low, high = strength_range(a_type, b_type)
        guard_strength = random.randint(low, high)

    # Add bonus for connection to main world
    if is_player_to_main:
        guard_strength += random.randint(3000, 6000)

    # Cap at 25 000
    attrs["guard_strength"] = min(guard_strength, 25000)

    

    # ───────────────────────────────
    # CONNECTION TYPE: WIDE
    # ───────────────────────────────
    if NodeType.SUPER_TREASURE in types:
        attrs["connection_type_wide"] = ""
    else:
        attrs["connection_type_wide"] = "" if random.random() < 0.9 else "1"

    # ───────────────────────────────
    # CONNECTION TYPE: BORDERGUARD
    # ───────────────────────────────
    attrs["connection_type_borderguard"] = ""

    # ───────────────────────────────
    # ROADS
    # ───────────────────────────────
    if NodeType.START in types:
        attrs["roads"] = "+"
    else:
        attrs["roads"] = "+" if random.random() < 0.75 else "-"

    # ───────────────────────────────
    # PLACEMENT HINT
    # ───────────────────────────────
    attrs["placement_hint"] = ""

    # ───────────────────────────────
    # CONNECTION TYPE: FICTIVE
    # ───────────────────────────────
    attrs["connection_type_fictive"] = ""

    # ───────────────────────────────
    # MONOLITH REPULSION
    # ───────────────────────────────
    attrs["monolith_repulsion"] = 1 if random.random() < 0.2 else ""

    # ───────────────────────────────
    # PLAYER LIMITS
    # ───────────────────────────────
    attrs["human_players_min"] = 1
    attrs["human_players_max"] = 8
    attrs["total_players_min"] = 2
    attrs["total_players_max"] = 8

    # Attach attributes
    link.attributes = attrs

def sanity_check_links(graph):
    """
    Verify that all links in the graph have attributes assigned.
    Prints a summary and highlights missing or incomplete links.
    """
    total_links = len(graph.links)
    missing_attrs = []
    attr_summary = {}

    for link in graph.links:
        attrs = getattr(link, "attributes", None)
        if not attrs or not isinstance(attrs, dict) or not attrs:
            missing_attrs.append(link)
            continue

        # Count how many links have each guard strength range
        gs = attrs.get("guard_strength", None)
        if gs is not None:
            bucket = (gs // 5000) * 5000
            attr_summary[bucket] = attr_summary.get(bucket, 0) + 1

    print("\n──── Link Attribute Sanity Check ────")
    print(f"Total links: {total_links}")
    print(f"Links with assigned attributes: {total_links - len(missing_attrs)}")
    print(f"Links missing attributes: {len(missing_attrs)}")

    if missing_attrs:
        print("\n⚠️  Missing attribute data for:")
        for link in missing_attrs[:10]:  # avoid spamming
            print(f"  {link}")
        if len(missing_attrs) > 10:
            print("  ... (more omitted)")

    print("\nGuard strength distribution (approximate):")
    for bucket in sorted(attr_summary.keys()):
        print(f"  {bucket:5d}–{bucket+4999:5d} : {attr_summary[bucket]} links")

    print("─────────────────────────────────────\n")
