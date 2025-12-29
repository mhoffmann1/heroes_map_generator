# heroes_map_generator
Generates random templates for Heroes 3 HotA map generator for a more 'random' user experience

# To Do

- add option to modify the number od zones in main map area - DONE
- all towns/castles are the same type - change setting
- avg link per node in main - 3 seems to much -> reduce to 2 or make it dependent on number of main nodes - DONE (set to 2, no extra logic for now)
- add toggle to enable/disable special heroes in generate_h3t_file function

# Bugs

- is_player_to_main in add_link method in graph is not triggering the right monster values in parameters
- if there are less AI players than Human players they should be global AI. Now they are Embedded

# Variables description

## Template

val1 - 11
val2 - 10
val3 - 4
val4 - 8
val5 - 10
val6 - 18
val7 - 4
template_pack_name - name of template pack
template_pack_dsc - description of template pack
available_castles - None
available_heroes - "+144 +145 +146 +147 +148 +149 +150 +151 +152 +153 +196 +197"
mirror_template - None ('x' if enabled)
empty
max_battle_rounds - 100
empty
template_name - string
min_size - 32
max_size - 99
available_artifacts - None
available_comb_artifacts - "+1 "
available_spells - None
available_secondary_skills - None
disable_objects - "-88 3"
rock_block_radius - empty (x if enabled, float if custom value)
zone_sparsness - 0.8 - 1.5 (float)
disable_special_weeks - empty (or 'x')
allow_spell_research - 'x'
anarchy - empty or 'x'

## Nodes

### mines

Next batch of variables:

wood_min
mercury_min
ore_min
sulfur_min
crystals_min
gems_min
gold_min


wood_min and ore_min should be 0 by default and set to 1 for START type of zones
if any zone has neutral_towns_min > 0 then 50% chance that wood_min and ore_min is 1, otherwise 0. if a zone has neutral_castle_min > 0 then it always has wood_min and ore_min set to 1

for mercury_min, sulfur_min, crystals_min and gems_min - by default all of these are 0. 10% for one of them to be 1 for START zone. 25% for NEUTRAL zone that one of them has a value of 1. In TREASURE ZONE each one of them has 20% chance to be 1, but no more than 2 in total. In SUPER_TREASURE, each one has 25% chance to be 1 with no total limit.

gold_min - 0 by default. 5% to be 1 for NEUTRAL zone, 10%  to be 1 in TREASURE zone and 20% in SUPER_TREASURE zone

All density variables should be set to '0':
wood_density
mercury_density
ore_density
sulfur_density
crystals-density
gems_density
gold_density

### terrain and monsters

Another batch of parameters:
terrain_match_town - 1 in START zone, in any other zone, if neutral_towns_min > 0 or neutral_castle_min > 0 it has 80% chance to be 1, else 0
allowed_terrain[1-10] - ten variables for possible terrain types, placeholder for future use. All set to 1
monster_strenght - possible values are 0-3. Should be 2 for START zone. 80% to be 2 in TREASURE zone, otherwise 3. 70% to be 2 in SUPER_TREASURE zone, otherwise 3. Always 2 in JUNCTION zone
monster_match_town - 0 in START zone, in any other zone, if neutral_towns_min > 0 or neutral_castle_min > 0 it has 10% chance to be 1, else 0
allowed_monster_type[1-12] - twelve variables for possible allowed monster types. Placeholder for future use. All set to 1

### treasures

* treasure1_low - 500 for START and NEUTRAL zone, 3000 for TREASURE, 10000 for SUPER_TREASURE
* treasure1_high - 3000 for START and NEUTRAL zone, 6000 for TREASURE, 15000 for SUPER_TREASURE
* treasure1_density - 9
* treasure2_low - 3000 for START and NEUTRAL zone, 10000 for TREASURE, 15000 for SUPER_TREASURE
* treasure2_high - 6000 for START and NEUTRAL zone, 15000 for TREASURE, 20000 for SUPER_TREASURE
* treasure2_density - 6
* treasure3_low - 10000 for START and NEUTRAL zone, 15000  for TREASURE, 20000 for SUPER_TREASURE
* treasure3_high - 15000 for START and NEUTRAL zone, 20000 for TREASURE, 30000 for SUPER_TREASURE
* treasure3_density - set to 1

in case of JUNCTION type - assign values as if it was NEUTRAL or TREASURE (50/50 chance)

All low/high values above should be slightly randomized (+/- 10%, but should remain integers)

* zone_placement - set to 0
* objects_section - should be empty

### Misc

final batch of parameters for zones:

* UI_position_[1-4] - 4 values that can be negative or positive float type. Placeholder for future use. Set to empty.
* zone_faction_force_neutral - set to empty
* allow_non_coherent_road - 75% to be empty, otherwise set to 'x'
* zone_repulsion - set to empty 
* town_type_rules - set to empty
* monster_disposition - 25% to be 1, 50% to be 2, 25% to be 3
* custom_monster_disposition - set to empty
* joining_percent - set to 1
* join_only_for_money - set to 'x'
* shipyard_min - 10% to be 1 in SUPER_TREASURE zone, empty in all other cases
* shipyard_density - set to empty
* terrain_type_rule - set to empty
* customized_allowed_factions_bitmap - set to empty
* zone_faction_rule - set to empty
* max_road_block_value - 4000 for START zone, otherwise empty

monster_disposition, joining_percent and join_only_for_money variables should have an option to be provided manually during script execution - in such case the provided value should overwrite the default value provided here

## Links

Variables in order of appearance:
'-' means empty (/t) value
Starts right after Zones section, on 2nd line of Zones

* Zone A (int)
* Zone B (int)
* guard_strenght - integer. If one of the zones is START zone then: 3000 - 4000 if the other one is NEUTRAL or JUNCTION, 5000 - 7000 if TREASURE, 8000-12000 if SUPER_TREASURE. It should also be +3000 if the connection happens to be between player starting area and main part of the map if possible. 
for all other connection between zones. Rule of thumb is: the more valuable the ZONES, the higher number, and it should be especially high if one of the zone is NEUTRAL and the other is SUPER_TREASURE. Max value should be 25000 
* connection_type_wide - always empty if one of the zones is SUPER_TREASURE, otherwise, 90% to be empty, otherwise '1'
* connection_type_borderguard - always empty
* roads - '+' if one of the zones is START, otherwise 75% chance to be '+', 25% to be '-'
* placement_hint - should be set to 'random'
* connection_type_fictive - always empty
* monolith_repulsion - 20% to be 1, otherwise empty
* human_players_min - 1
* human_players_max - 8
* total_players_min - 2
* total_players_max - 8

# General template settings in h3t files

## Connections

Variables in order of appearance:
'-' means empty (/t) value
Starts right after Zones section, on 2nd line of Zones

* Zone A (int)
* Zone B (int)
* Guard strenght (int)
* Connection type wide (x)
* Connection type Border Guard (x)
* Roads (+ [yes], - [no], '-' [random] )
* Placement hint (random, teleport, underground, ground, - )
* Connection type Fictive (x)
* Monolith repulsion (x)
* Connection occurence requirements section (Human players: min (int), max (int), Total Players: min (int), max (int))

Notes:
Connection type - if all set to '-' then it will be standard. Fictive and Border Guard should be avoided.

5	15	30000				random			1	6	2	6

## Zones

Variables in order of appearance:
'-' means empty (/t) value

Start on 29th /t

* Zone ID
* Human Start (x)
* Computer Zone (x) - leave empty
* Treasue Zone (x)
* Junction Zone (x)
* Size (int) - 20 is standard size
* 1
* 6
* 2
* 6
* Player controling the zone (int, 1 - 8) 
* Player towns min (int or '-')
* Player castles min (int or '-')
* Player towns density (int or '-')
* Player castle density (int or '-')
* neutral towns min (int or '-')
* neutral castle min (int or '-')
* neutral towns density (int or '-')
* neutral castel density (int or '-')
* All castles are the same (x)
* allowed castles (x for each, x11 entries) 

* wood_min (int or '-')
* mercury_min (int or '-')
* ore_min
* sulfur_min (int or '-')
* crystals_min (int or '-')
* gems_min (int or '-')
* gold_min (int or '-')
* wood_density (int or '-')
* mercury_density (int or '-')
* ore_density (int or '-')
* sulfur_density (int or '-')
* crystals-density (int or '-')
* gems_density (int or '-')
* gold_density (int or '-')

* Terrain must match town (x)
* allowed terrain type (x for each, x10 entries)
* monster strenght (none, weak, avg, strong)
* match to to town (x)
* Monster types (x for each, starting neutral, then specific factions, x12 entries )

* treasure1 low (int or '-')    ----> if empty, all treasure# related fields need to be empty
* treasure1 high (int or '-')
* treasure1 density (int or '-')
* treasure2 low (int or '-')
* treasure2 high (int or '-')
* treasure2 density (int or '-')
* treasure3 low (int or '-')
* treasure3 high (int or '-')
* treasure3 density (int or '-')
* Placement (ground, underground, '-')
* Objects section (variable lenght, each entry looks similar to: +16 0 d d d d )
*
* UI editor positions (-/+ int, x4)
* Zone faction force neutral (x)
* Allow non coherent road (x)
* Zone repulsion (x)
* Town type rules (string)
* Monster disposition (0 - always join, 1 - Friendly [1-7], 2 - Aggresive [1-10], 3 - hostile [4-10], 4-  Savage [10], 5 - custom )
* Custom monster disposition (int 1-9)
* Joining percent of monsters (0 - 25%, 1 - 50%, 2 - 75%, 3 - 100%)
* Join only for money (x)
* Shipyard min (int or '-')
* Shipyard density (int or '-')
* Terrain type rule (string)
* bitmap size 11
* Zone Faction rule (string)
* Max road block value ('-" or int)

