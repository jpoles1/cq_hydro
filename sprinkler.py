from cadquery import *
from dataclasses import dataclass
from math import tan, radians

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart
from tube_adaptor import TubeAdaptor

@dataclass
class Sprinkler(StylishPart):
    fdm_extrude_w: float = 0.5 #Extrusion width for FDM printers. Will attempt to make thing walls a multiple of this value 
    fdm_horiz_clearance: float = 0.2 #Clearance spacing between interfacing parts for FDM printers 

    sprinkler_bot_r: float = 40/2
    sprinkler_h: float = 10
    
    slot_h: float = 3
    slot_spacer_angle: float = 25

    n_slots: int = 5
    n_rows: int = 1

    def calc_vars(self):
        self.wall_thick = self.fdm_extrude_w * 4
        self.sprinkler_top_r = self.sprinkler_bot_r * 0.65

    def make(self):
        adaptor = TubeAdaptor()

        sprinkler = (
            Workplane("XZ").sketch()
            .segment((0,0), (self.sprinkler_bot_r,0))
            .segment((self.sprinkler_top_r,self.sprinkler_h))
            .segment((0,self.sprinkler_h))
            .close().assemble().finalize()
            .revolve().shell(-self.wall_thick)
            .union(
                adaptor.part()
                .translate((0,0,-adaptor.adaptor_h))
            )
            .copyWorkplane(Workplane("XY")).circle(adaptor.adaptor_ir).cutBlind(self.wall_thick)
        )
        slot_angle = (360 - self.slot_spacer_angle*self.n_slots) / self.n_slots
        row_offset = self.sprinkler_h / (self.n_rows + 1)
        for i in range(self.n_rows):
            for j in range(self.n_slots):
                sprinkler = sprinkler.cut(
                    sprinkler.copyWorkplane(Workplane("XZ")).moveTo(0, (i+1)*row_offset)
                    .rect(2*self.sprinkler_bot_r, self.slot_h, centered=[0,1]).revolve(slot_angle, combine=False)
                    .rotate((0,0,0), (0,0,1),j*(slot_angle+self.slot_spacer_angle)+i*((slot_angle+self.slot_spacer_angle)/2))
                )

        sprinkler = (
            sprinkler.copyWorkplane(Workplane("XY"))
            .rect(adaptor.adaptor_or+2*self.wall_thick, adaptor.adaptor_or+2*self.wall_thick, forConstruction=True)
            .vertices().cylinder(self.sprinkler_h, 1, centered=[1,1,0])
        )
        sprinkler = sprinkler.union(
            Workplane("XY")
            .rect(self.sprinkler_bot_r/2, self.sprinkler_bot_r/2, forConstruction=True)
            .vertices().cylinder(self.sprinkler_h, 1, centered=[1,1,0])
            .rotate((0,0,0),(0,0,1), 45)
        )
        return sprinkler

if "show_object" in locals():
    Sprinkler().display(show_object).export("stl/sprinkler.stl")

