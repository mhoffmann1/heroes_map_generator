import random

from models.objects import NodeType
from utils.randomize import random_bool, random_choice_weighted

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

        "all_castle_same": lambda: random.choice(['', 'x']),  # 50/50
        **{f"allowed_castle_{i}": 'x' for i in range(1, 13)}
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

        "all_castle_same": lambda: random.choice(['', 'x']),
        **{f"allowed_castle_{i}": 'x' for i in range(1, 13)}
    },
    NodeType.JUNCTION: {
        "zone_type": lambda: 3,  # neutral = junction
        "zone_size": lambda: random.randint(15, 25),
        "res_parameter1": 1,
        "res_parameter2": 8,
        "res_parameter3": 2,
        "res_parameter4": 8,
        "player_control": lambda node: 0,

        "player_towns_min": 0,
        "player_castles_min": 0,
        "player_towns_density": 0,
        "player_castles_density": 0,

        "neutral_towns_min": 0,
        "neutral_castle_min": 0,
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": '',
        **{f"allowed_castle_{i}": 'x' for i in range(1, 13)}
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

        "neutral_towns_min": lambda: random_choice_weighted([(2, 0.1), (1, 0.25), (0, 0.65)]),
        "neutral_castle_min": lambda node: (
            0 if node.attributes.get("neutral_towns_min", 0) > 0
            else random_choice_weighted([(1, 0.2), (0, 0.8)])
        ),
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": lambda: random.choice(['', 'x']),
        **{f"allowed_castle_{i}": 'x' for i in range(1, 13)}
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

        "neutral_towns_min": lambda: random_choice_weighted([(2, 0.1), (1, 0.25), (0, 0.65)]),
        "neutral_castle_min": lambda node: (
            0 if node.attributes.get("neutral_towns_min", 0) > 0
            else random_choice_weighted([(2, 0.1), (1, 0.15), (0, 0.75)])
        ),
        "neutral_towns_density": 0,
        "neutral_castle_density": 0,

        "all_castle_same": lambda: random.choice(['', 'x']),
        **{f"allowed_castle_{i}": 'x' for i in range(1, 13)}
    }
}

RESOURCE_NAMES = ["wood", "mercury", "ore", "sulfur", "crystals", "gems", "gold"]

MANUAL_OVERRIDES = {}

# ──────────────────────────────────────────────
# Field order for ZONE (Node) attributes
# ──────────────────────────────────────────────
# Complete zone field order (exactly 97 items)
ZONE_FIELDS = [
    # Core zone identity / basic params
    "zone_size",
    "res_parameter1", "res_parameter2", "res_parameter3", "res_parameter4",
    "player_control",

    # Player/neutral towns & castles
    "player_towns_min", "player_castles_min", "player_towns_density", "player_castles_density",
    "neutral_towns_min", "neutral_castle_min", "neutral_towns_density", "neutral_castle_density",
    "all_castle_same",

    # Allowed castles (12)
    *[f"allowed_castle_{i}" for i in range(1, 13)],

    # Resource mins + densities
    "wood_min", "mercury_min", "ore_min", "sulfur_min", "crystals_min", "gems_min", "gold_min",
    "wood_density", "mercury_density", "ore_density", "sulfur_density", "crystals_density", "gems_density", "gold_density",

    # Terrain & monsters
    "terrain_match_town",
    *[f"allowed_terrain_{i}" for i in range(1, 11)],
    "monster_strength", "monster_match_town",
    *[f"allowed_monster_type_{i}" for i in range(1, 14)],

    # Treasure tiers
    "treasure1_low", "treasure1_high", "treasure1_density",
    "treasure2_low", "treasure2_high", "treasure2_density",
    "treasure3_low", "treasure3_high", "treasure3_density",

    # Misc layout / objects
    "zone_placement", "objects_section",

    "blank_before_ui",  # this will always export as an empty tab

    # UI position in Template generator, road, monster joining and shipyards
    "UI_position",
    "zone_faction_force_neutral",
    "allow_non_coherent_road",
    "zone_repulsion",
    "town_type_rules",
    "monster_disposition",
    "custom_monster_disposition",
    "joining_percent",
    "join_only_for_money",
    "shipyard_min",
    "shipyard_density",
    "terrain_type_rule",
    "customized_allowed_factions_bitmap",
    "zone_faction_rule",
    "max_road_block_value",

]

# Sanity check (optional)
# assert len(ZONE_FIELDS) == 97

# ──────────────────────────────────────────────
# Field order for LINK attributes
# ──────────────────────────────────────────────
LINK_FIELDS = [
    "guard_strength", "connection_type_wide", "connection_type_borderguard",
    "roads", "placement_hint", "connection_type_fictive", "monolith_repulsion",
    "human_players_min", "human_players_max", "total_players_min", "total_players_max"
]
