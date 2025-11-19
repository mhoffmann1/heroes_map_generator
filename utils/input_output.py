import math
import random
from datetime import datetime

from config import MANUAL_OVERRIDES
from models.map_graph import generate_world
from models.objects import NodeType


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


def ask_int_with_default(prompt, default=0, min=0, max=10):
    """Asks for integer or returns default if user presses ENTER."""
    
    try:
        val = -1
        while val < min or val > max:
            raw = input(prompt).strip()
            if raw == "":
                return default
            val = int(raw)
            if val < min or val > max:
                print(f"Value cannot be smaller than {min} or larger than {max}")
                continue
            else:
                return val
    except ValueError:
        print("Invalid number. Using default.")
        return default
    
def _ask_bool_default(prompt, default: bool):
    """
    Ask a yes/no question with a default used on empty input.
    default=True  -> 'Y/n' style
    default=False -> 'y/N' style
    """
    if default:
        suffix = " [Y/n] (default: Yes): "
    else:
        suffix = " [y/N] (default: No): "

    raw = input(prompt + suffix).strip().lower()
    if raw == "":
        return default
    if raw.startswith("y"):
        return True
    if raw.startswith("n"):
        return False

    print("Invalid input, using default.")
    return default


def _ask_ai_placement_mode():
    """
    Ask for AI placement mode:
      both  - use both main and start connection lists (at least 1 from each)
      main  - only main_conn_points
      start - only start_conn_points
      random- randomly choose one of the above
    Default: 'main' on empty input or invalid value.
    """
    raw = input(
        "AI placement mode [both/main/start/random] (default: main): "
    ).strip().lower()

    if raw == "":
        return "main"
    if raw in ("both", "main", "start", "random"):
        return raw

    print("Invalid AI placement mode, using 'main'.")
    return "main"


def build_world_interactive():
    # 1) MAP STYLE
    map_style = _ask_choice("Map style", ["random", "balanced"])

    # 2) Human players (balanced requires >= 2)
    min_humans = 2 if map_style == "balanced" else 1
    num_humans = _ask_int(f"Number of HUMAN players ({min_humans}-8): ", min_humans, 8)

    # 3) AI players, ensure total <= 8
    max_ai = 8 - num_humans
    if max_ai == 0:
        print("Maximum total players reached; AI players set to 0.")
        num_ai = 0
    else:
        num_ai = _ask_int(f"Number of AI players (0-{max_ai}): ", 0, max_ai)
    
    start_zones_per_player = ask_int_with_default("Number of start zones per player (default 0 -> random): ", default=0, min=1, max=6)
    if start_zones_per_player == 0:
        start_zones_per_player = random.randint(3, 5)

    main_zones_per_player = ask_int_with_default("Number of main zones per player (default 0 -> random): ", default=0, min=3, max=7)
    if main_zones_per_player == 0:
        main_zones_per_player = random.randint(4, 6)

    # 4) Town type rules in starting zones
    num_same_towns_in_start = ask_int_with_default(
        "Number of towns with SAME faction as start town in each player zone (default 0): ",
        default=0,
        min=0,
        max=10
    )

    num_diff_towns_in_start = ask_int_with_default(
        "Number of towns with DIFFERENT faction than start town in each player zone (default 0): ",
        default=0,
        min=0,
        max=10
    )

    # 5) AI placement mode
    ai_placement_mode = _ask_ai_placement_mode()

    # 6) Disable special weeks? (default: True if just ENTER)
    disable_special_weeks = _ask_bool_default(
        "Disable special weeks?",
        default=True
    )

    # 7) Anarchy? (default: False if just ENTER)
    anarchy = _ask_bool_default(
        "Enable anarchy (allows accessing some objects without fighting the guards)?",
        default=False
    )

    # 8) Joining percent (0–4, default: 2 if ENTER)
    while True:
        raw = input(
            "Monster joining percent: 0=25%, 1=50%, 2=75%, 3=100%, 4=random (default 1: 50%): "
        ).strip()
        if raw == "":
            joining_percent = 1
            break
        try:
            joining_percent = int(raw)
        except ValueError:
            print("Please enter a number between 0 and 4.")
            continue

        if 0 <= joining_percent <= 4:
            break
        print("Value must be between 0 and 4.")

    if joining_percent == 4:
        joining_percent = random.randint(0, 3)

    # 9) Monsters join only for money? (default: True on ENTER)
    join_only_for_money = _ask_bool_default(
        "Monsters join only for money?",
        default=True
    )

    # Store overrides used later by zone/link generation
    MANUAL_OVERRIDES.update({
        "joining_percent": joining_percent,
        "join_only_for_money": join_only_for_money
    })

    # 10) Generate the world
    world = generate_world(
        num_human_players=num_humans,
        num_ai_players=num_ai,
        map_style=map_style,
        main_zone_nodes=main_zones_per_player,
        player_zone_nodes=start_zones_per_player,
        avg_links_main=3,
        avg_links_player=2,
        num_same_towns_in_start=num_same_towns_in_start,
        num_diff_towns_in_start=num_diff_towns_in_start,
        ai_placement_mode=ai_placement_mode,
    )

    # Debug output for AI nodes
    ai_nodes = [n for n in world.nodes if n.node_type == NodeType.START and n.owner > num_humans]
    print(f"[DEBUG] AI nodes in final world: {len(ai_nodes)}")
    for n in ai_nodes:
        print(f"  AI#{n.owner} – ID {n.id}.h3t")

    # Template file name
    today = datetime.now().strftime("%Y%m%d")
    template_file = f"{today}_{map_style}_H{num_humans}_{num_ai}CP.h3t"

    return template_file, num_humans, num_ai, disable_special_weeks, anarchy, world

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
    palette = ["red", "blue", "tan", "green", "orange", "purple", "teal", "pink"]
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
    