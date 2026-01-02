import random

from utils.input_output import build_world_interactive
from utils.gui import WorldGeneratorGUI
from utils.run_pipeline import run_generation_pipeline

USE_GUI = True  # ← toggle here

if __name__ == "__main__":
    random.seed()  # or random.seed(42)

    if USE_GUI:
        # GUI mode
        WorldGeneratorGUI().mainloop()

    else:
        # CLI mode (unchanged behavior)
        (
            template_filename,
            map_style,
            human_players,
            ai_players,
            disable_special_weeks,
            anarchy,
            world,
            heroes,
        ) = build_world_interactive()

        run_generation_pipeline(
            template_filename=template_filename,
            map_style=map_style,
            human_players=human_players,
            ai_players=ai_players,
            disable_special_weeks=disable_special_weeks,
            anarchy=anarchy,
            world=world,
            heroes=heroes
        )
