from enum import Enum, auto

class NodeType(Enum):
    START = auto()
    NEUTRAL = auto()
    TREASURE = auto()
    SUPER_TREASURE = auto()
    JUNCTION = auto()

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
    def __init__(self, node_a, node_b, is_player_to_main=False):
        self.node_a = node_a
        self.node_b = node_b
        self.is_player_to_main = is_player_to_main  # <-- new flag
        self.attributes = {}  # will be filled in later

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

    #def add_link(self, node_a, node_b, is_player_to_main=False):
    #    if not self.nodes_connected(node_a, node_b):
    #        link = Link(node_a, node_b, is_player_to_main=is_player_to_main)
    #        node_a.add_link(link)
    #        node_b.add_link(link)
    #        self.links.append(link)
    #        return link

    # This fixes an issue if link already exists
    def add_link(self, node_a, node_b, is_player_to_main=False, allow_double=False):
        """
        Add a link between node_a and node_b.
        If allow_double=False, enforces only a single link.
        If allow_double=True, allows up to two links between the same nodes.
        """
        # Count existing links between the pair
        existing = [
            link for link in self.links
            if (link.node_a is node_a and link.node_b is node_b) or
               (link.node_a is node_b and link.node_b is node_a)
        ]

        # Only allow two total links max
        if not allow_double and existing:
            return existing[0]

        if allow_double and len(existing) >= 2:
            return existing[0]  # do not create a third

        # Create a new link
        link = Link(node_a, node_b, is_player_to_main=is_player_to_main)
        node_a.add_link(link)
        node_b.add_link(link)
        self.links.append(link)
        return link

    def nodes_connected(self, node_a, node_b):
        return any(
            (l.node_a == node_a and l.node_b == node_b)
            or (l.node_a == node_b and l.node_b == node_a)
            for l in self.links
        )

    def merge(self, other_graph):
        """Merge another graph into this one, preserving up to double-links."""
        existing_ids = {n.id for n in self.nodes}

        # Add nodes
        for node in other_graph.nodes:
            if node.id not in existing_ids:
                self.nodes.append(node)
                existing_ids.add(node.id)

        # Count existing links per node-pair
        pair_counts = {}
        for l in self.links:
            key = tuple(sorted([l.node_a.id, l.node_b.id]))
            pair_counts[key] = pair_counts.get(key, 0) + 1

        # Merge links (allow up to 2 links between same nodes)
        for link in other_graph.links:
            key = tuple(sorted([link.node_a.id, link.node_b.id]))

            count = pair_counts.get(key, 0)

            if count < 2:
                # Accept link
                self.links.append(link)
                pair_counts[key] = count + 1
            else:
                # already have 2 links → ignore extras
                continue
            
    def display(self):
        print(f"\nGraph with {len(self.nodes)} nodes and {len(self.links)} links:")
        for node in self.nodes:
            connected_ids = [l.connects(node).id for l in node.links]
            start_flag = " (Start)" if node.is_start else ""
            owner = f" [Player{node.owner}]" if node.owner else ""
            zone_type = f" {node.node_type}"
            print(f"Node {node.id}{owner}{start_flag}{zone_type}: connected to {connected_ids}.")
