from cadquery import *
from dataclasses import dataclass

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

@dataclass
class PlantDish(StylishPart):
    part_name = "Plant Dish"
    dish_h: float = 14
    base_r: float = 86/2
    rim_r: float = base_r + 8

    wall_thickness: float = 2
    stilt_h: float = 4
    stilt_spacing: float = 25
    
    def make(self):
        dish = (
            Workplane("XY").circle(self.base_r+self.wall_thickness)
            .workplane(self.dish_h).circle(self.rim_r+self.wall_thickness)
            .loft(ruled=1)
            .faces(">Z").shell(-self.wall_thickness, kind="intersection")
            
            .edges(selectors.AndSelector(selectors.DirectionMinMaxSelector(Vector(0,0,1)), selectors.RadiusNthSelector(3))).fillet(self.wall_thickness/1.5)
        )
        dish = (
            dish.faces("<Z[-2]").workplane()
            .rect(self.stilt_spacing, self.stilt_spacing, forConstruction=True)
            .vertices()
            .cylinder(self.stilt_h, self.wall_thickness*1.25, centered=[1,1,0])
        )
        return dish

class PlantPot(PlantDish):
    part_name = "Plant Pot"
    def make(self):
        pot = (
            Workplane("XY")
            .cylinder(75, self.base_r, centered=[1,1,0])
            .faces(">Z").shell(-6)
            .translate((0,0, self.wall_thickness + self.stilt_h))
        )
        return pot

if "show_object" in locals():
    PlantDish().display_split(show_object).export("stl/plant_dish.stl")
    PlantPot().display(show_object)
    