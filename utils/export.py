from config import NodeType
from config import ZONE_FIELDS, LINK_FIELDS


def export_to_h3t(world, filename="generated_template.h3t"):
    """
    Export world graph to Heroes 3 .h3t-like tab-separated format.

    Each row = zone entry (ID + 4 flags + attributes)
             + link entry (NodeA, NodeB, link parameters),
    with absolutely ZERO tabs between the last zone field and the first link field.
    """
    PRE_ZONE_TABS = 28
    ZONE_FIELD_COUNT = 93  # total zone columns (id + 4 flags + attributes)

    all_zones = list(world.nodes)
    all_links = list(world.links)
    lines = []

    def pad(values, count):
        """Pad or truncate to match column width."""
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
        f3 = "x" if node.node_type in (
            NodeType.NEUTRAL, NodeType.TREASURE, NodeType.SUPER_TREASURE) else ""
        f4 = "x" if node.node_type == NodeType.JUNCTION else ""
        return [f1, f2, f3, f4]

    total_lines = max(len(all_zones), len(all_links))

    for i in range(total_lines):
        # ---------------- ZONE SECTION ----------------
        zone_cols = [""] * PRE_ZONE_TABS  # leading 28 blank columns

        if i < len(all_zones):
            node = all_zones[i]
            node_prefix = [str(node.id)] + zone_type_flags(node)
            zone_vals = [node.attributes.get(k, "") for k in ZONE_FIELDS]
            zone_vals = pad(zone_vals, ZONE_FIELD_COUNT)
            zone_cols += node_prefix + zone_vals
        else:
            zone_cols += [""] * (1 + 4 + ZONE_FIELD_COUNT)

        # Join the zone part separately
        zone_str = "\t".join(zone_cols)

        # ---------------- LINK SECTION ----------------
        link_str = ""
        if i < len(all_links):
            link = all_links[i]
            link_prefix = [str(link.node_a.id), str(link.node_b.id)]
            link_vals = [link.attributes.get(k, "") for k in LINK_FIELDS]
            link_vals = pad(link_vals, len(LINK_FIELDS))
            # Join link part (do NOT prefix with a tab)
            link_str = "\t".join(link_prefix + link_vals)

        # ✅ Concatenate directly — no tab between zone and link parts
        line = zone_str + link_str
        lines.append(line)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[OK] Exported world to {filename}")
    print(f"Zones: {len(all_zones)} | Links: {len(all_links)} | Lines written: {len(lines)}")
