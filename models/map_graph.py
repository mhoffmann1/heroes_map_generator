import random
from itertools import combinations

from models.objects import Graph, Node, NodeType, Link
from models.parameters import assign_zone_attributes, assign_all_link_attributes, sanity_check_links, assign_link_attributes


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


# Helpers to build main graph by style
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

def _generate_main_graph_balanced(
    main_zone_nodes,
    current_id,
    avg_links_main,
    num_players=3,
    num_ai_players=0
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
    fragment_size = int(random.randint(*main_zone_nodes) / num_players)
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

    # Clone base fragment N times - for each human player
    clone_graphs = []
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
            new_link = g.add_link(nodes_map[l.node_a.id], nodes_map[l.node_b.id])
            if hasattr(l, "attributes"):
                new_link.attributes = dict(l.attributes)

        clone_graphs.append((g, new_nodes))

    # Connect fragments in mirrored pattern
    base_count = len(base_fragment.nodes)

    # Random number of cross-links: between 2 and number of fragment nodes (if possible)
    if base_count <= 1:
        num_cross_links = 1
    else:
        num_cross_links = random.randint(2, base_count)

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

    # Create a template START zone for AIs (used only for embedded AIs)
    AI_START_TEMPLATE = Node(-1, node_type=NodeType.START, owner=None, is_start=True)

    assign_zone_attributes(AI_START_TEMPLATE)
    AI_START_TEMPLATE_ATTRS = dict(AI_START_TEMPLATE.attributes)

    # Add AI players symmetrically
    ai_used = 0
    ai_nodes_all = []  # track all AIs for merging
    
    # --- Shared setup for symmetrical connection indices ---
    fragment_size = len(clone_graphs[0][1])
    possible_indices = list(range(fragment_size))
    # Predefine which nodes will be used for AI connections (same pattern everywhere)
    ai_connection_indices = random.sample(possible_indices, k=min(2, fragment_size))
    
    # Precompute link attributes for embedded AIs (same for all)
    EMBEDDED_AI_LINK_ATTRS = []

    for idx in ai_connection_indices:
        # dummy link uses any nodes, doesn't matter
        dummy_link = Link(Node(-1), Node(-2))
        assign_link_attributes(dummy_link)
        EMBEDDED_AI_LINK_ATTRS.append(dict(dummy_link.attributes))

    # Embedded AIs (if enough AIs for one per player)
    if num_ai_players >= num_players:
        print(f"[DEBUG] Adding embedded AIs with connection indices {ai_connection_indices}")

        for i in range(num_players):
            ai_owner = num_players + ai_used + 1

            ai_node = Node(
                current_id,
                node_type=NodeType.START,
                owner=ai_owner,
                is_start=True
            )
            current_id += 1
            ai_used += 1

            # Copy AI template START attributes
            ai_node.attributes = dict(AI_START_TEMPLATE_ATTRS)
            ai_node.attributes["player_control"] = ai_owner

            ai_nodes_all.append(ai_node)

            frag_graph, frag_nodes = clone_graphs[i]
            frag_graph.add_node(ai_node)

            # Symmetrical connections for embedded AIs with identical link attributes
            for template_attr, idx in zip(EMBEDDED_AI_LINK_ATTRS, ai_connection_indices):
                target = frag_nodes[idx % len(frag_nodes)]

                link = frag_graph.add_link(ai_node, target)

                # Copy template attributes (LOCKED)
                link.attributes = dict(template_attr)


            frag_nodes.append(ai_node)
    
    # Global AIs (remaining or all)
    remaining_ais = num_ai_players - ai_used
    
    # --- Precompute symmetrical link attributes for Global AI connections ---
    GLOBAL_AI_LINK_ATTRS = []
    for _ in ai_connection_indices:
        dummy = Link(Node(-1), Node(-2))
        assign_link_attributes(dummy)
        GLOBAL_AI_LINK_ATTRS.append(dict(dummy.attributes))

    if remaining_ais > 0:
        print(f"[DEBUG] Adding {remaining_ais} global AIs with connection indices {ai_connection_indices}")

        for _ in range(remaining_ais):
            ai_owner = num_players + ai_used + 1

            ai_node = Node(
                current_id,
                node_type=NodeType.START,
                owner=ai_owner,
                is_start=True
            )
            current_id += 1
            ai_used += 1

            # Global AI gets fresh randomized START zone attributes
            ai_node.attributes = {}
            assign_zone_attributes(ai_node)
            ai_node.attributes["player_control"] = ai_owner

            ai_nodes_all.append(ai_node)

            # Connect globally to all fragments symmetrically
            for frag_graph, frag_nodes in clone_graphs:
                for pos, idx in enumerate(ai_connection_indices):
                    target = frag_nodes[idx % len(frag_nodes)]
                    link = frag_graph.add_link(ai_node, target)

                    # Apply symmetrical template attributes
                    link.attributes = dict(GLOBAL_AI_LINK_ATTRS[pos])

            # Put it into the first fragment so it gets merged
            clone_graphs[0][0].add_node(ai_node)
    
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
        current_id
    )

# Core world generation with human + AI players + map style
def generate_world(
    num_human_players=3,
    num_ai_players=0,
    map_style="random",                 # "random" or "balanced"
    main_zone_nodes=(8, 16),
    player_zone_nodes=(3, 4),
    avg_links_main=3,
    avg_links_player=2,
    num_same_towns_in_start=1,
    num_diff_towns_in_start=0,
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
        main_graph, num_main_nodes, player_connection_indices, clone_graphs, base_fragment, current_id = _generate_main_graph_balanced(
            main_zone_nodes, current_id, avg_links_main, num_players=num_human_players, num_ai_players=num_ai_players
        )
    else:
        # Random map generation
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


    # Assign link attributes once for the template graph
    for link in template_graph.links:
        assign_link_attributes(link)

    # Keep a reference to the template START node (for AI cloning)
    if num_ai_players:
        tmpl_start = next((n for n in template_graph.nodes if n.node_type == NodeType.START), None)
        if tmpl_start is None:
            raise RuntimeError("Template graph did not produce a START node — this should not happen.")

    # Clone template for each human player
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
            new_link = g.add_link(a, b)
            if hasattr(l, "attributes"):
                new_link.attributes = dict(l.attributes)

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

    assign_all_link_attributes(world)
    sanity_check_links(world)
    return world