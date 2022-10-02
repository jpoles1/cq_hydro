from cadquery import *
from math import atan, radians, degrees

from dataclasses import dataclass
import sys
sys.path.append("../cq_style")
from cq_style import StylishPart
from tube_adaptor import TubeAdaptor

@dataclass
class PyramidAirstone(StylishPart):
    adaptor = TubeAdaptor(flip_part=1)
    base_w: float = 35
    stone_h: float = 25
    airhole_r: float = 0.25

    def calc_vars(self):
        self.wall_thick = self.adaptor.wall_thick
        self.wall_angle = degrees(atan(self.stone_h/(self.base_w/2)))
        self.adaptor_r = self.adaptor.adaptor_or

    def make(self):
        part = (
            Workplane("XY").rect(self.base_w, self.base_w)
            .workplane(self.stone_h).circle(self.adaptor_r)
            .loft()
            .shell(-self.wall_thick)
            .faces(">Z")
            .circle(self.adaptor.adaptor_ir)
            .cutBlind("next")
        )
        base_hole = (
            Workplane("XY").cylinder(self.base_w, self.airhole_r, centered=[1,1,0])
            .translate((0,0,self.wall_thick))
            .rotate((0,0,0), (0,1,0), self.wall_angle)
        )
        n_sides = 4
        n_rows = 4
        n_cols = 3
        height_per_row = self.stone_h / n_rows
        for i in range(n_sides):
            for j in range(n_rows):
                for k in range(n_cols):
                    hole = (
                        base_hole
                        .translate((0, (k-1)*4, height_per_row * (j-1)))
                        .rotate((0,0,0), (0,0,1), i*360/n_sides)
                        .cut(Workplane("XY").box(self.base_w,self.base_w, self.wall_thick, centered=[1,1,0]))
                    )
                    #debug(hole)
                    part = part.cut(hole)

        part = part.union(self.adaptor.part().translate((0,0,self.stone_h)))
        return part

class CylinderAirstone(StylishPart):
    adaptor = TubeAdaptor(adaptor_or=4.5/2, adaptor_h=10, flip_part=1, wall_thick=1)
    stone_r: float = 6
    stone_h: float = 50
    airhole_r: float = 0.15

    def calc_vars(self):
        self.wall_thick = self.adaptor.wall_thick
        self.adaptor_r = self.adaptor.adaptor_or

    def make(self):
        loft_h = 4

        part = (
            Workplane("XY").cylinder(self.stone_h, self.stone_r, centered=[1,1,0])
            .faces(">Z").workplane().circle(self.stone_r)
            .workplane(loft_h).circle(self.adaptor.adaptor_or)
            .loft()
            .shell(-self.wall_thick)
            .faces(">Z")
            .circle(self.adaptor.adaptor_ir)
            .cutBlind("next")
        )
        
        n_rows = round(self.stone_h / 5)
        n_cols = 6
        row_h = self.stone_h * 0.8 / n_rows
        rot_angle = 360 / n_cols
        
        for i in range(n_rows):
            for j in range(n_cols):
                hole = (
                    Workplane("YZ")
                    .circle(self.airhole_r).extrude(self.stone_r)      
                    .translate((0,0,self.stone_h/2 + ((i-n_rows/2+0.5)*row_h)))      
                    .rotate((0,0,0), (0,0,1), j * rot_angle )
                )
                #debug(hole)
                part = part.cut(hole)

        part = part.union(self.adaptor.part().translate((0,0,self.stone_h+loft_h)))
        return part


if "show_object" in locals():
    #CylinderAirstone().display(show_object)
    CylinderAirstone().display_split(show_object)
    CylinderAirstone().export("stl/cylinder_airstone.stl")