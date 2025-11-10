import argparse
import random

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
