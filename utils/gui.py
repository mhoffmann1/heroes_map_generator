import tkinter as tk
from tkinter import ttk, messagebox
import random
from datetime import datetime
from utils.run_pipeline import run_generation_pipeline
from config import MANUAL_OVERRIDES
from models.map_graph import generate_world
from models.objects import NodeType


class WorldGeneratorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HoMM3 Template Generator")
        self.geometry("520x840")
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        frame = ttk.Frame(self)
        # -------------------------
        # Title / Header
        # -------------------------
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            title_frame,
            text="Heroes 3 Template Generator",
            font=("Segoe UI", 16, "bold"),
            anchor="center",
            justify="center"
        ).pack(fill="x")

        ttk.Label(
            title_frame,
            text="by Astral IT Solutions — Marcin Hoffmann",
            font=("Segoe UI", 10),
            foreground="#555555",
            anchor="center",
            justify="center"
        ).pack(fill="x")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        def label(text):
            ttk.Label(frame, text=text).pack(anchor="w", **pad)

        def row(widget):
            widget.pack(fill="x", **pad)

        # -------------------------
        # Map style
        # -------------------------
        label("Map style")
        self.map_style = tk.StringVar(value="random")
        row(ttk.Combobox(
            frame,
            textvariable=self.map_style,
            values=["random", "balanced"],
            state="readonly"
        ))

        # -------------------------
        # Players
        # -------------------------
        label("Number of human players")
        self.num_humans = tk.IntVar(value=1)
        row(ttk.Spinbox(frame, from_=1, to=8, textvariable=self.num_humans))

        label("Number of AI players")
        self.num_ai = tk.IntVar(value=1)
        row(ttk.Spinbox(frame, from_=0, to=7, textvariable=self.num_ai))

        # -------------------------
        # AI difficulty
        # -------------------------
        label("AI difficulty")
        self.ai_difficulty = tk.StringVar(value="normal")
        row(ttk.Combobox(
            frame,
            textvariable=self.ai_difficulty,
            values=["normal", "hard", "unfair", "random"],
            state="readonly"
        ))

        # -------------------------
        # Zones
        # -------------------------
        label("Start zones per player (0 = random)")
        self.start_zones = tk.IntVar(value=0)
        row(ttk.Spinbox(frame, from_=0, to=10, textvariable=self.start_zones))

        label("Main zones per player (0 = random)")
        self.main_zones = tk.IntVar(value=0)
        row(ttk.Spinbox(frame, from_=0, to=10, textvariable=self.main_zones))

        # -------------------------
        # Town rules
        # -------------------------
        label("Same-faction towns in start zone")
        self.same_towns = tk.IntVar(value=0)
        row(ttk.Spinbox(frame, from_=0, to=10, textvariable=self.same_towns))

        label("Different-faction towns in start zone")
        self.diff_towns = tk.IntVar(value=0)
        row(ttk.Spinbox(frame, from_=0, to=10, textvariable=self.diff_towns))

        # -------------------------
        # AI placement
        # -------------------------
        label("AI placement mode")
        self.ai_placement = tk.StringVar(value="main")
        row(ttk.Combobox(
            frame,
            textvariable=self.ai_placement,
            values=["main", "start", "both", "random"],
            state="readonly"
        ))

        # -------------------------
        # Game rules
        # -------------------------
        self.disable_weeks = tk.BooleanVar(value=True)
        row(ttk.Checkbutton(
            frame,
            text="Disable special weeks",
            variable=self.disable_weeks
        ))

        self.anarchy = tk.BooleanVar(value=False)
        row(ttk.Checkbutton(
            frame,
            text="Enable anarchy",
            variable=self.anarchy
        ))

        self.special_heroes = tk.BooleanVar(value=False)
        row(ttk.Checkbutton(
            frame,
            text="Enable special heroes",
            variable=self.special_heroes
        ))

        # -------------------------
        # Monster joining
        # -------------------------
        label("Monster joining percent")
        self.joining_percent = tk.StringVar(value="1 (50%)")
        row(ttk.Combobox(
            frame,
            textvariable=self.joining_percent,
            values=[
                "0 (25%)",
                "1 (50%)",
                "2 (75%)",
                "3 (100%)",
                "4 (random)"
            ],
            state="readonly"
        ))

        self.join_money = tk.BooleanVar(value=True)
        row(ttk.Checkbutton(
            frame,
            text="Monsters join only for money",
            variable=self.join_money
        ))

        # -------------------------
        # Generate button
        # -------------------------
        ttk.Separator(frame).pack(fill="x", pady=(15, 10))
        
        generate_btn = ttk.Button(
            frame,
            text="Generate Template",
            command=self._generate
        )
        generate_btn.pack(fill="x", padx=20, pady=(0, 20), ipady=6)

    # ----------------------------------------------------
    # Generation logic
    # ----------------------------------------------------
    def _generate(self):
        try:
            num_humans = self.num_humans.get()
            num_ai = self.num_ai.get()

            if num_humans + num_ai > 8:
                raise ValueError("Total players cannot exceed 8.")

            start_zones = self.start_zones.get() or random.randint(3, 5)
            main_zones = self.main_zones.get() or random.randint(4, 7)

            joining_raw = int(self.joining_percent.get()[0])
            if joining_raw == 4:
                joining_raw = random.randint(0, 3)

            MANUAL_OVERRIDES.update({
                "joining_percent": joining_raw,
                "join_only_for_money": self.join_money.get()
            })

            world = generate_world(
                num_human_players=num_humans,
                num_ai_players=num_ai,
                ai_difficulty_mode=self.ai_difficulty.get(),
                map_style=self.map_style.get(),
                main_zone_nodes=main_zones,
                player_zone_nodes=start_zones,
                avg_links_main=2,
                avg_links_player=2,
                num_same_towns_in_start=self.same_towns.get(),
                num_diff_towns_in_start=self.diff_towns.get(),
                ai_placement_mode=self.ai_placement.get(),
            )

            today = datetime.now().strftime("%Y%m%d")
            template_file = f"{today}_{self.map_style.get()}_H{num_humans}_{num_ai}CP.h3t"

            run_generation_pipeline(
                template_filename=template_file,
                map_style=self.map_style.get(),
                human_players=num_humans,
                ai_players=num_ai,
                disable_special_weeks=self.disable_weeks.get(),
                anarchy=self.anarchy.get(),
                world=world,
                heroes=self.special_heroes.get(),
            )

            messagebox.showinfo(
                "Success",
                f"Template generated:\n{template_file}"
            )


        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    WorldGeneratorGUI().mainloop()
