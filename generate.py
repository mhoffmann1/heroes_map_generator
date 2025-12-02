import random

from utils.input_output import build_world_interactive, visualize_graph
from utils.export import export_to_h3t, generate_h3t_file

if __name__ == "__main__":
    
    random.seed()  # Set e.g. random.seed(42) for deterministic output

    #world = generate_world(num_players=3)
    template_filename, map_style, human_players, ai_players, disable_special_weeks, anarchy,world = build_world_interactive()
    world.display()

    # Create h3t file and generate template values
    generate_h3t_file(
        num_humans=human_players,
        num_ais=ai_players,
        output_path=template_filename,
        map_style=map_style,
        disable_special_weeks=disable_special_weeks,
        anarchy=anarchy
        )

    # Export map parameters to h3t file
    export_to_h3t(world, filename=template_filename)

    visualize_graph(world)
