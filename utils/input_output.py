import math

from models.map_graph import generate_world
from models.objects import NodeType


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
    # balanced should require at least 2 Human players

    world = generate_world(
        num_human_players=num_humans,
        num_ai_players=num_ai,
        map_style=map_style,
        main_zone_nodes=(8, 16),
        player_zone_nodes=(3, 4),
        avg_links_main=3,
        avg_links_player=2
    )

    ai_nodes = [n for n in world.nodes if n.node_type == NodeType.START and n.owner > num_humans]
    print(f"[DEBUG] AI nodes in final world: {len(ai_nodes)}")
    for n in ai_nodes:
        print(f"  AI#{n.owner} – ID {n.id}")

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