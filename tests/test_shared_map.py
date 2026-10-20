import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path

from models.map_graph import generate_world
from models.objects import NodeType
from utils.export import export_to_h3t


class SharedMapTests(unittest.TestCase):
    def make_world(self, **options):
        random.seed(42)
        with contextlib.redirect_stdout(io.StringIO()):
            return generate_world(map_style="shared", **options)

    def test_humans_share_one_connected_local_area(self):
        humans = 3
        main_per_player = 4
        local_zones = 4
        world = self.make_world(
            num_human_players=humans,
            num_ai_players=2,
            main_zone_nodes=main_per_player,
            player_zone_nodes=local_zones,
            ai_placement_mode="both",
        )

        main_count = humans * main_per_player
        local = set(world.nodes[main_count:main_count + local_zones + humans - 1])
        starts = [node for node in local if node.node_type == NodeType.START]
        common = local.difference(starts)

        self.assertEqual(len(world.nodes), main_count + local_zones + humans - 1 + 2)
        self.assertEqual({node.owner for node in starts}, {1, 2, 3})
        self.assertEqual({node.attributes["player_control"] for node in starts}, {1, 2, 3})
        self.assertTrue(all(node.owner is None for node in common))
        self.assertEqual(len(common), local_zones - 1)
        self.assertEqual(len({node.id for node in world.nodes}), len(world.nodes))

        # Every human START has the same internal links to the common area.
        exit_patterns = [
            sorted((link.connects(start).id, tuple(sorted(link.attributes.items())))
                   for link in start.links if link.connects(start) in common)
            for start in starts
        ]
        self.assertTrue(exit_patterns[0])
        self.assertTrue(all(pattern == exit_patterns[0] for pattern in exit_patterns))

        reached = {starts[0]}
        pending = [starts[0]]
        while pending:
            node = pending.pop()
            for link in node.links:
                neighbor = link.connects(node)
                if neighbor in local and neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        self.assertEqual(reached, local)
        main_exits = [link for link in world.links if link.is_player_to_main]
        self.assertEqual(len(main_exits), 2)
        self.assertTrue(all(link.node_a in common or link.node_b in common for link in main_exits))
        self.assertTrue(all(link.attributes for link in world.links))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shared.h3t"
            with contextlib.redirect_stdout(io.StringIO()):
                export_to_h3t(world, filename=path)
            rows = [line.split("\t") for line in path.read_text().splitlines()]
        exported_human_owners = [row[38] for row in rows if row[29] == "x"]
        self.assertEqual(exported_human_owners, ["1", "2", "3", "4", "5"])

    def test_one_requested_local_zone_still_has_common_area(self):
        world = self.make_world(
            num_human_players=2,
            num_ai_players=0,
            main_zone_nodes=3,
            player_zone_nodes=1,
        )
        local = world.nodes[6:]
        self.assertEqual(len(local), 3)
        self.assertEqual(sum(node.node_type == NodeType.START for node in local), 2)
        self.assertEqual(sum(node.node_type != NodeType.START for node in local), 1)


if __name__ == "__main__":
    unittest.main()
