from cadquery import *
from dataclasses import dataclass
from math import tan, radians

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

@dataclass
class TubeAdaptor(StylishPart):
    fdm_extrude_w: float = 0.5 #Extrusion width for FDM printers. Will attempt to make thing walls a multiple of this value 
    fdm_horiz_clearance: float = 0.2 #Clearance spacing between interfacing parts for FDM printers 

    adaptor_h: float = 12
    adaptor_or: float = 8/2

    barb_angle: float = 35
    n_barbs: int = 3
    barb_spacing: float = 1

    def calc_vars(self):
        self.wall_thick = self.fdm_extrude_w * 3
        self.adaptor_ir = self.adaptor_or - self.wall_thick
        self.barb_r = self.adaptor_or + self.fdm_extrude_w * 2
    def make(self):
        part = (
            Workplane("XY").cylinder(self.adaptor_h, self.adaptor_or, centered=[1,1,0])
            .faces("|Z").shell(-self.wall_thick)
        )
        barb_h = (self.barb_r-self.adaptor_or)/tan(radians(self.barb_angle))
        barb_sketch = (
            Sketch()
            .segment((self.adaptor_or,0), (self.adaptor_or,barb_h))
            .segment((self.adaptor_or,barb_h), (self.barb_r, barb_h))
            .close()
            .assemble()
        )
        barb = Workplane("XZ").placeSketch(barb_sketch).revolve(360)
        for i in range(self.n_barbs):
            part = part.union(barb.translate((0,0,i*(barb_h+self.barb_spacing))))
        return part

@dataclass
class TubeAdaptorI(StylishPart):
    adaptor1: TubeAdaptor
    adaptor2: TubeAdaptor

    mid_h: float = 4
    def calc_vars(self):
        self.mid_r = max(self.adaptor1.adaptor_or, self.adaptor2.adaptor_or) + 2

    def make(self):
        return (
            Workplane("XY").cylinder(self.mid_h, self.mid_r)
            .cut(
                Workplane("XY")
                .workplane(self.mid_h/2).circle(self.adaptor2.adaptor_ir)
                .workplane(-self.mid_h).circle(self.adaptor1.adaptor_ir)
                .loft(ruled=True)
            )
            .union(
                self.adaptor1.part()
                .translate(Vector(0,0,-self.adaptor1.adaptor_h))
                .translate(Vector(0,0,-self.mid_h/2))
            )
            .union(
                self.adaptor2.part()
                .translate(Vector(0,0,-self.adaptor2.adaptor_h))
                .rotate(Vector(0,0,0), Vector(1,0,0), 180)
                .translate(Vector(0,0,self.mid_h/2))
            )
        )
   
@dataclass
class TubeAdaptorY(StylishPart):
    adaptor1: TubeAdaptor
    adaptor2: TubeAdaptor
    adaptor3: TubeAdaptor

    mid_r: float = 6
    y_angle: float = 80

    fdm_extrude_w: float = 0.5 #Extrusion width for FDM printers. Will attempt to make thing walls a multiple of this value 
    fdm_horiz_clearance: float = 0.2 #Clearance spacing between interfacing parts for FDM printers 

    def calc_vars(self):
        self.wall_thick = self.fdm_extrude_w * 3
        self.mid_h = 2*max(max(self.adaptor1.adaptor_or, self.adaptor2.adaptor_or), self.adaptor3.adaptor_or) - 2*self.wall_thick

    def make(self):
        return (
            Workplane("XZ").cylinder(self.mid_h, self.mid_r).shell(self.wall_thick)
            .union(
                self.adaptor1.part()
                .translate(Vector(0,0,-self.adaptor1.adaptor_h))
                .translate(Vector(0,0,-self.mid_r))
            )
            .union(
                self.adaptor2.part()
                .translate(Vector(0,0,-self.adaptor2.adaptor_h))
                .rotate(Vector(0,0,0), Vector(0,1,0), 180)
                .translate(Vector(0,0,self.mid_r))
                .rotate((0,0,0),(0,1,0), -self.y_angle/2)
            )
            .union(
                self.adaptor3.part()
                .translate(Vector(0,0,-self.adaptor3.adaptor_h))
                .rotate(Vector(0,0,0), Vector(0,1,0), 180)
                .translate(Vector(0,0,self.mid_r))
                .rotate((0,0,0),(0,1,0), self.y_angle/2)
            )
            .cut(
                Workplane("XY").workplane(invert=True)
                .cylinder(self.mid_r+self.wall_thick, self.adaptor1.adaptor_ir, centered=[1,1,0])
            )
            .cut(
                Workplane("XY")
                .cylinder(self.mid_r+self.wall_thick, self.adaptor2.adaptor_ir, centered=[1,1,0])
                .rotate((0,0,0), (0,1,0), -self.y_angle/2)
                .mirror("YZ")
            )
            .cut(
                Workplane("XY")
                .cylinder(self.mid_r+self.wall_thick, self.adaptor2.adaptor_ir, centered=[1,1,0])
                .rotate((0,0,0), (0,1,0), -self.y_angle/2)
            )
        )


if "show_object" in locals():
    #TubeAdaptor().display_split(show_object)
    TubeAdaptorI(TubeAdaptor(), TubeAdaptor()).display_split(show_object).export("stl/8to8mmAdaptor.stl")
    #TubeAdaptorY(TubeAdaptor(), TubeAdaptor(), TubeAdaptor()).display_split(show_object).export("stl/8mmYAdaptor.stl")


