from cadquery import *
from dataclasses import dataclass

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

@dataclass
class PumpAdaptor(StylishPart):
    wall_thick = 3 * 0.5
    tube_ir: float = (8+1)/2 
    pump_adaptor_or: float = 11.5/2
    
    pump_adaptor_h = 9.5
   
    def make(self):
        part = (
            #Create pump side of adaptor
            Workplane("XY")
            .cylinder(self.pump_adaptor_h, self.pump_adaptor_or, centered=[1,1,0])
            .faces("|Z").shell(-self.wall_thick)
            #Create divider between both halves
            .faces(">Z").workplane()
            .cylinder(2, 14/2, centered=[1,1,0])
            #Create tube side of adaptor
            .faces(">Z").workplane()
            .cylinder(10, self.tube_ir, centered=[1,1,0])
            #Cut hole through tube adaptor and divider
            .faces(">Z").workplane()
            .circle(self.tube_ir - self.wall_thick).cutThruAll()
        )
        #Chamfer inner contour where wider pump side meets narrower tube side
        #Intended to help reduce FDM 3d printer overhangs and turbulence
        part = (
            part.edges(selectors.RadiusNthSelector(0))
            .edges("<Z").chamfer(self.pump_adaptor_or - self.tube_ir - 0.01)
        )
        return part


if "show_object" in locals():
    #PumpAdaptor().display(show_object)
    PumpAdaptor().display_split(show_object).export("stl/pump_adaptor.stl")