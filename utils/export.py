from config import NodeType
from config import ZONE_FIELDS, LINK_FIELDS

def export_to_h3t(world, filename="generated_template.h3t"):
    """
    Export world graph to Heroes 3 .h3t-like tab-separated format.
    Each row = zone entry (with leading padding + node ID + zone flags + parameters)
             + link entry (NodeA, NodeB, link parameters).
    """
    PRE_ZONE_TABS = 28
    ZONE_FIELD_COUNT = 97

    lines = []

    all_zones = list(world.nodes)
    all_links = list(world.links)

    def pad(values, count):
        vals = ["" if (v is None or v == 0) else str(v) for v in values]
        if len(vals) < count:
            vals += [""] * (count - len(vals))
        elif len(vals) > count:
            vals = vals[:count]
        return vals

    def zone_type_flags(node):
        """Return the 4 'x' flags for START / NEUTRAL+TREASURE / JUNCTION."""
        f1 = "x" if node.node_type == NodeType.START else ""
        f2 = ""
        f3 = "x" if node.node_type in (NodeType.NEUTRAL, NodeType.TREASURE, NodeType.SUPER_TREASURE) else ""
        f4 = "x" if node.node_type == NodeType.JUNCTION else ""
        return [f1, f2, f3, f4]

    # --------------------------
    # MAIN LOOP
    # --------------------------
    for node in all_zones:
        # Collect zone info
        zone_vals = [node.attributes.get(k, "") for k in ZONE_FIELDS]
        zone_vals = pad(zone_vals, ZONE_FIELD_COUNT)

        # Node base info (ID + 4 flags)
        node_prefix = [str(node.id)] + zone_type_flags(node)

        # Find connected links (only one direction to avoid duplicates)
        connected_links = [l for l in node.links if l.node_a.id < l.node_b.id]

        if connected_links:
            for link in connected_links:
                link_prefix = [str(link.node_a.id), str(link.node_b.id)]
                link_vals = [link.attributes.get(k, "") for k in LINK_FIELDS]
                link_vals = pad(link_vals, len(LINK_FIELDS))

                # combine all sections
                line = (
                    "\t" * PRE_ZONE_TABS
                    + "\t".join(node_prefix)
                    + "\t"
                    + "\t".join(zone_vals)
                    + "\t"
                    + "\t".join(link_prefix + link_vals)
                )
                lines.append(line)
        else:
            # zone with no outgoing links
            line = (
                "\t" * PRE_ZONE_TABS
                + "\t".join(node_prefix)
                + "\t"
                + "\t".join(zone_vals)
            )
            lines.append(line)

    # --------------------------
    # HANDLE EXTRA LINKS (if more links than zones)
    # --------------------------
    if len(all_links) > len(all_zones):
        extra_links = all_links[len(all_zones):]
        for link in extra_links:
            link_prefix = [str(link.node_a.id), str(link.node_b.id)]
            link_vals = [link.attributes.get(k, "") for k in LINK_FIELDS]
            link_vals = pad(link_vals, len(LINK_FIELDS))

            line = (
                "\t" * (PRE_ZONE_TABS + 1 + 4 + ZONE_FIELD_COUNT)
                + "\t".join(link_prefix + link_vals)
            )
            lines.append(line)

    # --------------------------
    # WRITE TO FILE
    # --------------------------
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"[OK] Exported world to {filename}")
    print(f"Zones: {len(all_zones)} | Links: {len(all_links)} | Lines written: {len(lines)}")
