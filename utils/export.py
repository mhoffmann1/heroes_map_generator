import random
from datetime import datetime

from config import LINK_FIELDS, ZONE_FIELDS, NodeType


def generate_h3t_file(
        num_humans,
        num_ais,
        source_path="h3t_source.h3t", 
        output_path="output.h3t",
        disable_special_weeks=None,
        anarchy=None,
        ):
    """
    Generates a full .h3t template file using:
    - A static base template (h3t_source.h3t)
    - Auto-generated template attributes appended as one TAB-separated line
    """

    # --------------------------------------------------------
    # 1. Load static header from source file
    # --------------------------------------------------------
    with open(source_path, "r", encoding="utf-8") as src:
        base_content = src.read()

    # --------------------------------------------------------
    # 2. Compute dynamic values
    # --------------------------------------------------------
    # Template pack / name
    today = datetime.now().strftime("%Y%m%d")
    template_pack_name = f"{today}_balanced_H{num_humans}_C{num_ais}"
    template_pack_dsc = "template generated using automation"

    # Randomized fields
    zone_sparsness = round(random.uniform(0.8, 1.5), 3)  # float
    if disable_special_weeks is None:
        disable_special_weeks = random.choice(["", "x"])
    if anarchy is None:
        anarchy = random.choice(["", "x"])

    # --------------------------------------------------------
    # 3. Prepare attribute line (order EXACTLY as requested)
    # --------------------------------------------------------
    values = [
        11,                  # val1
        10,                  # val2
        4,                   # val3
        8,                   # val4
        10,                  # val5
        18,                  # val6
        4,                   # val7
        template_pack_name,  # template pack name
        template_pack_dsc,   # template pack description
        "",                  # available_castles
        "+144 +145 +146 +147 +148 +149 +150 +151 +152 +153 +196 +197",
        "",                  # mirror_template
        "",                  # empty
        100,                 # max_battle_rounds
        "",                  # empty
        template_pack_name,  # template_name
        32,                  # min_size
        99,                  # max_size
        "",                  # available_artifacts
        "+1 ",               # available_comb_artifacts
        "",                  # available_spells
        "",                  # available_secondary_skills
        "-88 3",             # disable_objects
        "",                  # rock_block_radius
        zone_sparsness,      # zone_sparsness
        disable_special_weeks,
        "x",                 # allow_spell_research
        anarchy
    ]

    # Convert everything to strings and join with TAB
    attribute_line = "\t".join(str(v) for v in values)

    # --------------------------------------------------------
    # 4. Write the final output file
    # --------------------------------------------------------
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(base_content.rstrip("\n"))
        out.write("\n")             # ensure separation
        out.write(attribute_line)   # append generated attributes
        out.write("\n")

    print(f"[OK] Generated {output_path}")


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

    with open(filename, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[OK] Exported world to {filename}")
    print(f"Zones: {len(all_zones)} | Links: {len(all_links)} | Lines written: {len(lines)}")
