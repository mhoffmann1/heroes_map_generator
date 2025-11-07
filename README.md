# heroes_map_generator
Generates random templates for Heroes 3 HotA map generator for a more 'random' user experience

# To Do
- Generate initial values
- Generate starting areas for players or players + AI
- Generate fair main grid
- Print template to file
- generate template values

# Variables description

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