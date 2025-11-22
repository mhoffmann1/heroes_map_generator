import random
from itertools import combinations

from models.objects import Graph, Node, NodeType, Link
from models.parameters import assign_zone_attributes, assign_all_link_attributes, sanity_check_links, assign_link_attributes


def generate_subgraph(num_nodes, id_start, owner=None, start_zone=False, avg_links_per_node=2, double_link_chance=0.15):
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
        if random.random() < double_link_chance:
            g.add_link(a, b, allow_double=True)
            print(f"Created double link for nodes {a.id} and {b.id}")

    # Mark start node if needed
    if start_zone:
        random.choice(nodes).is_start = True

    return g


# Helpers to build main graph by style
def _generate_main_graph_random(main_zone_nodes, current_id, avg_links_main):
    num_main_nodes = main_zone_nodes
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

def _generate_main_graph_balanced(
    main_zone_nodes,
    current_id,
    avg_links_main,
    num_players=3,
):
    """
    Generate a symmetrical balanced main graph:
      - Clone one small 'core fragment' per human player
      - Interconnect fragments in mirrored fashion
      - Add AI players according to rules:
          * If A >= H → one embedded AI per fragment + remaining global AIs
          * If A <  H → all AIs are global (connect to all fragments)
    """

    # Generate base fragment
    fragment_size = main_zone_nodes
    base_fragment = generate_subgraph(
        fragment_size, id_start=current_id, avg_links_per_node=avg_links_main
    )    

    current_id += fragment_size

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

    # Generate parameters for links in the base_fragment
    for link in base_fragment.links:
        assign_link_attributes(link)

    # Chose potential connection points for AI zones
    base_nodes = list(base_fragment.nodes)

    # How many potential connection points per fragment (2–3)
    num_potential_main = random.choice([2, 3])
    base_potential_indices = random.sample(
        range(len(base_nodes)),
        k=min(num_potential_main, len(base_nodes))
    )

    # Mark them explicitly (optional, mostly for debugging / export)
    for idx in base_potential_indices:
        node = base_nodes[idx]
        node.attributes["potential_connection_main"] = True

    # Create main zone by duplicating base_gragment N times (N - number of human players)

    # Clone base fragment N times - for each human player
    clone_graphs = []
    main_conn_points = []

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

        # Recreate internal links and their attributes
        for l in base_fragment.links:
            new_link = g.add_link(nodes_map[l.node_a.id], nodes_map[l.node_b.id], allow_double=True)
            if hasattr(l, "attributes"):
                new_link.attributes = dict(l.attributes)

        # Map the potential indices to this clone's nodes
        fragment_points = [new_nodes[idx] for idx in base_potential_indices]
        main_conn_points.append(fragment_points)

        clone_graphs.append((g, new_nodes))

    # Connect fragments in mirrored pattern
    base_count = len(base_fragment.nodes)

    # Random number of cross-links: between 2 and number of fragment nodes (if possible)
    if base_count <= 1:
        num_cross_links = 1
    else:
        # Use less cross links
        #num_cross_links = random.randint(2, base_count)
        num_cross_links = random.randint(2, max(2, base_count - 2))

    base_nodes = list(base_fragment.nodes)

    # Build template: (from_idx, to_idx, attrs_dict)
    template_cross_links = []
    for _ in range(num_cross_links):
        a_idx = random.randrange(base_count)
        b_idx = random.randrange(base_count)

        # Create a dummy link on the base fragment just to compute attributes
        dummy_link = Link(base_nodes[a_idx], base_nodes[b_idx])
        assign_link_attributes(dummy_link)

        template_cross_links.append(
            (a_idx, b_idx, dict(dummy_link.attributes))
        )

    # Apply the same pattern + attributes to each fragment pair
    for i in range(num_players):
        next_i = (i + 1) % num_players

        g_i, nodes_i      = clone_graphs[i]
        g_next, nodes_next = clone_graphs[next_i]

        for a_idx, b_idx, attrs in template_cross_links:
            node_a = nodes_i[a_idx]
            node_b = nodes_next[b_idx]

            print(f"g_i {g_i} Node_a {node_a}; Node_b {node_b}")

            # Create the actual link between fragments i and next_i
            link = g_i.add_link(node_a, node_b)
            # Copy the precomputed attributes so all such links are identical
            link.attributes = dict(attrs)


    # Define indices for connecting player starting zones
    fragment_node_indices = list(range(len(base_fragment.nodes)))
    num_connections = random.choice([2, 3])
    player_connection_indices = random.sample(
        fragment_node_indices, k=min(num_connections, len(fragment_node_indices))
    )
    
    # optional central node
    if random.random() < 0.5:
        # Decide central node type: 30% Treasure, 70% Super-treasure
        roll = random.random()
        if roll < 0.30:
            central_type = NodeType.TREASURE
        else:
            central_type = NodeType.SUPER_TREASURE

        central_node = Node(
            current_id,
            node_type=central_type,
            owner=None,
            is_start=False
        )
        current_id += 1

        # Randomize zone attributes for the central node
        assign_zone_attributes(central_node)

        # Pick symmetrical indices inside each fragment (one per fragment)
        fragment_size = len(clone_graphs[0][1])
        idx = random.randrange(fragment_size)     # one index for all fragments

        # Precompute symmetrical link attributes
        dummy = Link(Node(-1, node_type=central_type), Node(-2))
        assign_link_attributes(dummy)
        CENTRAL_LINK_ATTRS = dict(dummy.attributes)

        # Connect central node to each fragment
        for frag_graph, frag_nodes in clone_graphs:
            target = frag_nodes[idx % len(frag_nodes)]

            link = frag_graph.add_link(central_node, target)

            # Symmetrical link attributes
            link.attributes = dict(CENTRAL_LINK_ATTRS)

        # Insert central node into FIRST fragment so that merge() picks it up
        clone_graphs[0][0].add_node(central_node)


    # Merge all fragments into unified main graph
    main_graph = Graph()
    for g, _ in clone_graphs:
        main_graph.merge(g)


    return (
        main_graph,
        len(main_graph.nodes),
        player_connection_indices,
        clone_graphs,
        base_fragment,
        current_id,
        main_conn_points,
    )

# Core world generation with human + AI players + map style
def generate_world(
    num_human_players=3,
    num_ai_players=0,
    map_style="random",                 # "random" or "balanced"
    main_zone_nodes=4,
    player_zone_nodes=3,
    avg_links_main=3,
    avg_links_player=2,
    num_same_towns_in_start=1,
    num_diff_towns_in_start=0,
    ai_placement_mode="main",
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
        # Balanced map generation
        main_graph, num_main_nodes, player_connection_indices, clone_graphs, base_fragment, current_id, main_conn_points = _generate_main_graph_balanced(
            main_zone_nodes, current_id, avg_links_main, num_players=num_human_players
        )
    else:
        # Random map generation
        main_graph, num_main_nodes = _generate_main_graph_random(main_zone_nodes*num_human_players, current_id, avg_links_main)
        current_id += num_main_nodes
        
    # 2) Build human template starting area
    num_nodes = player_zone_nodes
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


    # Assign link attributes once for the template graph
    for link in template_graph.links:
        assign_link_attributes(link)

    # Mark potential conneciton points for AI in player start zone
    template_nodes = list(template_graph.nodes)

    num_potential_start = random.choice([2, 3])  # or make this a setting later
    start_potential_indices = random.sample(
        range(len(template_nodes)),
        k=min(num_potential_start, len(template_nodes))
    )

    for idx in start_potential_indices:
        node = template_nodes[idx]
        node.attributes["potential_connection_start"] = True

    # Keep a reference to the template START node (for AI cloning)
    if num_ai_players:
        tmpl_start = next((n for n in template_graph.nodes if n.node_type == NodeType.START), None)
        if tmpl_start is None:
            raise RuntimeError("Template graph did not produce a START node — this should not happen.")

    # Create Player starting zones

    # Clone template for each human player
    human_graphs = []
    start_conn_points = []
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
                start_node_id = new_node.id
            nodes_map[n.id] = new_node
            copied_nodes.append(new_node)
            current_id += 1

        g = Graph()
        for n in copied_nodes:
            g.add_node(n)

        # Recreate links AND clone their attributes
        for l in template_graph.links:
            a = nodes_map[l.node_a.id]
            b = nodes_map[l.node_b.id]
            new_link = g.add_link(a, b, allow_double=True)
            if hasattr(l, "attributes"):
                new_link.attributes = dict(l.attributes)

        # map template indices to this clone
        player_start_points = [copied_nodes[idx] for idx in start_potential_indices]
        start_conn_points.append(player_start_points)

        # Find potential castle/town nodes (excluding START)
        town_candidates = []
        for node in copied_nodes:
            if node.is_start:
                continue

            attrs = node.attributes

            # Detect castle/town presence
            has_town = (
                attrs.get("neutral_towns_min", 0) > 0 or
                attrs.get("neutral_castle_min", 0) > 0
            )

            if has_town:
                town_candidates.append(node)

        # Assign SAME-town rules (nsXX_p)
        same = town_candidates[:num_same_towns_in_start]
        for node in same:
            node.attributes["town_type_rules"] = f"ns{start_node_id}_p"

        # Assign DIFF-town rules (ndXX_p) to remaining
        remaining = town_candidates[len(same):len(same) + num_diff_towns_in_start]
        for node in remaining:
            node.attributes["town_type_rules"] = f"nd{start_node_id}_p"

        human_graphs.append(g)


    # 4) Prepare world & connect human areas to main graph
    world = Graph()
    world.merge(main_graph)

    # Random map post config
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
                link = human_graph.add_link(connection_node, target, is_player_to_main=True)
                assign_link_attributes(link, is_player_to_main=True)
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

    # Balanced map post config
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
        
        # --- Precompute attributes for player->main links ---
        PLAYER_MAIN_LINK_ATTRS = []
        for _ in player_connection_indices:
            dummy = Link(Node(-1), Node(-2), is_player_to_main=True)
            assign_link_attributes(dummy, is_player_to_main=True)
            PLAYER_MAIN_LINK_ATTRS.append(dict(dummy.attributes))

        # Now connect each player's start zone <-> their corresponding main fragment clone
        for i, human_graph in enumerate(human_graphs):
            player_nodes = list(human_graph.nodes)
            player_main_nodes = clone_graphs[i][1]  # the nodes of this player’s cloned main subgraph
        
            for p_idx, m_idx in zip(player_connection_indices, main_connection_indices):
                player_node = player_nodes[p_idx]
                main_node = player_main_nodes[m_idx]
                link = human_graph.add_link(player_node, main_node, is_player_to_main=True)

                # Use template attributes for this specific link index
                template_index = player_connection_indices.index(p_idx)
                link.attributes = dict(PLAYER_MAIN_LINK_ATTRS[template_index])
                
            world.merge(human_graph)

        current_id = attach_ai_balanced(
            world=world,
            main_conn_points=main_conn_points,
            start_conn_points=start_conn_points,
            num_human_players=num_human_players,
            num_ai_players=num_ai_players,
            ai_placement_mode=ai_placement_mode,   # or "both" if you prefer
            current_id=current_id,
            assign_zone_attributes=assign_zone_attributes,
            assign_link_attributes=assign_link_attributes,
            AI_START_TEMPLATE_ATTRS=None,          # or precomputed template
        )

    assign_all_link_attributes(world)
    sanity_check_links(world)
    return world

def attach_ai_balanced(
    world,
    main_conn_points,
    start_conn_points,
    num_human_players,
    num_ai_players,
    ai_placement_mode,
    current_id,
    assign_zone_attributes,
    assign_link_attributes,
    AI_START_TEMPLATE_ATTRS=None,
):
    """
    Attach AI players in a BALANCED map using precomputed symmetric connection points.

    main_conn_points: list[list[Node]]
        main_conn_points[i] -> candidate nodes in player i's main fragment clone
    start_conn_points: list[list[Node]]
        start_conn_points[i] -> candidate nodes in player i's starting area
    num_human_players: int
    num_ai_players: int
    ai_placement_mode: str
        Currently only used to resolve 'random'; behavior matches:
        - Embedded AIs: connect to both main & start according to a shared pattern.
        - Global AIs: connect only via main_conn_points.
    current_id: next free node id
    assign_zone_attributes: function(Node) -> None
    assign_link_attributes: function(Link) -> None
    AI_START_TEMPLATE_ATTRS: optional dict with base START attributes (for AIs)
    """

    if num_ai_players <= 0:
        return current_id

    # Normalize mode
    m = ai_placement_mode.lower().strip()

    if m not in ("main", "start", "both", "random"):
        print(f"[WARN] Unknown ai_placement_mode '{m}', using 'both'.")
        m = "both"

    if m == "random":
        m = random.choice(["main", "start", "both"])
        print(f"[DEBUG] AI placement randomly selected mode = {m}")

    embedded_mode = m

    # Global AIs cannot use start-zone connections. Force main.
    global_mode = "main"
    if embedded_mode == "start":
        print("[WARN] Global AIs cannot use 'start' placement; forcing them to 'main'.")

    # Basic safety checks
    if len(main_conn_points) != num_human_players or len(start_conn_points) != num_human_players:
        print("[WARN] attach_ai_balanced: connection-point lists do not match num_human_players; skipping AI attach.")
        return current_id

    # Prepare AI START template attributes if not provided
    if AI_START_TEMPLATE_ATTRS is None:
        tmpl = Node(-1, node_type=NodeType.START, owner=None, is_start=True)
        assign_zone_attributes(tmpl)
        AI_START_TEMPLATE_ATTRS = dict(tmpl.attributes)

    # How many AIs become "embedded" (max 1 per human)
    if num_ai_players < num_human_players:
        embedded_count = 0
        remaining_ais = num_ai_players
    else:
        embedded_count = min(num_ai_players, num_human_players)
        remaining_ais = num_ai_players - embedded_count

    # ---------------------------------------------------------
    # 1️⃣ EMBEDDED AIs — symmetric, shared configuration
    # ---------------------------------------------------------
    embedded_ai_nodes = []

    if embedded_count > 0:
        # Determine base lengths (assume symmetric across players)
        main_len = min((len(lst) for lst in main_conn_points), default=0)
        start_len = min((len(lst) for lst in start_conn_points), default=0)

        if main_len == 0 and start_len == 0:
            print("[WARN] attach_ai_balanced: no connection points for embedded AIs.")
        else:
            #
            # Determine allowed total links and split based on embedded_mode
            #
            if embedded_mode == "main":
                # All links must be from MAIN
                total_links = min(2, main_len) if main_len > 0 else 0
                k_main = total_links
                k_start = 0

            elif embedded_mode == "start":
                # All links must be from START
                total_links = min(1, start_len) if start_len > 0 else 0
                k_main = 0
                k_start = total_links

            else:  # embedded_mode == "both"
                # Must include at least one of each
                # total_links is 2 or 3
                total_links = random.choice([2, 3])

                possible_splits = []
                for k_main_try in range(1, total_links):  # >=1 main, >=1 start
                    k_start_try = total_links - k_main_try
                    if 1 <= k_start_try <= start_len and k_main_try <= main_len:
                        possible_splits.append((k_main_try, k_start_try))

                if not possible_splits:
                    print("[WARN] Cannot satisfy 'both' mode; falling back to 'main' only.")
                    total_links = min(2, main_len)
                    k_main = total_links
                    k_start = 0
                else:
                    k_main, k_start = random.choice(possible_splits)

            print(f"[DEBUG] Embedded AI mode={embedded_mode}, total_links={total_links}, "
                  f"k_main={k_main}, k_start={k_start}")

            print(f"[DEBUG] Embedded AIs: total_links={total_links}, k_main={k_main}, k_start={k_start}")
            # Pick indices ONCE (symmetric) for all embedded AIs
            main_indices = random.sample(range(main_len), k=k_main) if k_main > 0 else []
            start_indices = random.sample(range(start_len), k=k_start) if k_start > 0 else []
            print(f"[DEBUG] Embedded AIs main_indices={main_indices}, start_indices={start_indices}")
            # Precompute link attributes: one template per "slot" (combined main+start)
            EMBEDDED_LINK_ATTRS = []
            for _ in range(total_links):
                dummy = Link(Node(-1), Node(-2))
                assign_link_attributes(dummy)
                EMBEDDED_LINK_ATTRS.append(dict(dummy.attributes))
            next_owner = num_human_players + 1
            # Create embedded AI players (1 per human)
            for i in range(embedded_count):
                ai_owner = next_owner
                next_owner += 1
                ai_node = Node(
                    current_id,
                    node_type=NodeType.START,
                    owner=ai_owner,
                    is_start=True
                )
                current_id += 1
                ai_node.attributes = dict(AI_START_TEMPLATE_ATTRS)
                ai_node.attributes["player_control"] = ai_owner
                ai_graph = Graph()
                ai_graph.add_node(ai_node)
                # Attach to this player's main & start according to chosen indices
                attr_idx = 0
                # MAIN side
                for idx in main_indices:
                    target_list = main_conn_points[i]
                    if idx < len(target_list):
                        target = target_list[idx]
                        link = ai_graph.add_link(ai_node, target)
                        link.attributes = dict(EMBEDDED_LINK_ATTRS[attr_idx])
                        attr_idx += 1
                # START side
                for idx in start_indices:
                    target_list = start_conn_points[i]
                    if idx < len(target_list):
                        target = target_list[idx]
                        link = ai_graph.add_link(ai_node, target)
                        link.attributes = dict(EMBEDDED_LINK_ATTRS[attr_idx])
                        attr_idx += 1
                world.merge(ai_graph)
                embedded_ai_nodes.append(ai_node)

        # Adjust remaining AIs
        remaining_ais = num_ai_players - len(embedded_ai_nodes)

    # ---------------------------------------------------------
    # 2️⃣ GLOBAL AIs — main only, exactly num_human_players links
    # ---------------------------------------------------------
    if remaining_ais > 0:
        # Determine how many positions are available in main_conn_points
        main_len = min((len(lst) for lst in main_conn_points), default=0)
        if main_len == 0:
            print("[WARN] attach_ai_balanced: no main connection points for global AIs.")
            return current_id

        print(f"[DEBUG] Attaching {remaining_ais} global AIs via main_conn_points (main_len={main_len})")

        next_owner = num_human_players + 1 + len(embedded_ai_nodes)

        for _ in range(remaining_ais):
            ai_owner = next_owner
            next_owner += 1

            ai_node = Node(
                current_id,
                node_type=NodeType.START,
                owner=ai_owner,
                is_start=True
            )
            current_id += 1

            global_ai_connection = Link(Node(-1, node_type=NodeType.START), Node(-2, node_type=NodeType.TREASURE))
            assign_link_attributes(global_ai_connection)

            # Use template as base, then customize
            ai_node.attributes = dict(AI_START_TEMPLATE_ATTRS)
            assign_zone_attributes(ai_node)
            ai_node.attributes["player_control"] = ai_owner

            ai_graph = Graph()
            ai_graph.add_node(ai_node)

            # Choose ONE shared index into main_conn_points
            # GLOBAL AIs ALWAYS USE MAIN — start zones cannot be used symmetrically
            chosen_idx = random.randrange(main_len)
            print(f"[DEBUG] Global AI {ai_owner}: chosen main index {chosen_idx}")

            # Connect to each player's main fragment at that index
            for player_idx in range(num_human_players):
                targets = main_conn_points[player_idx]
                if chosen_idx < len(targets):
                    target = targets[chosen_idx]
                    link = ai_graph.add_link(ai_node, target)
                    link.attributes = global_ai_connection.attributes

            world.merge(ai_graph)

    return current_id
