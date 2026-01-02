from utils.export import export_to_h3t, generate_h3t_file
from utils.input_output import visualize_graph


def run_generation_pipeline(
    template_filename,
    map_style,
    human_players,
    ai_players,
    disable_special_weeks,
    anarchy,
    world,
    heroes,
):
    # Optional debug
    world.display()

    # Create h3t file and generate template values
    generate_h3t_file(
        num_humans=human_players,
        num_ais=ai_players,
        output_path=template_filename,
        map_style=map_style,
        disable_special_weeks=disable_special_weeks,
        anarchy=anarchy,
        special_heroes=heroes
    )

    # Export map parameters to h3t file
    export_to_h3t(world, filename=template_filename)

    # Optional visualization
    visualize_graph(world)
