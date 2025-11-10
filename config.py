import random
from utils.randomize import random_choice_weighted, random_bool


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

RESOURCE_NAMES = ["wood", "mercury", "ore", "sulfur", "crystals", "gems", "gold"]