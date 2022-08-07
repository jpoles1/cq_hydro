from cadquery import *
from dataclasses import dataclass

from netcup import Netcup

@dataclass
class BellSiphon:
    basin_h: float = 40
    basin_r: float = 36
    wall_thick: float = 2
    
    siphon_h: float = basin_h-16
    siphon_r: float = 8
    bell_r = siphon_r + 6

    def make(self):
        siphon = (
            Workplane("XY").cylinder(self.basin_h, self.basin_r, centered=[1,1,0])
            .faces(">Z").shell(-self.wall_thick, kind="intersection")
            .faces(">Z[-2]").workplane()
            .cylinder(self.siphon_h + self.bell_r-3, self.siphon_r, centered=[1,1,0])
            .faces("XY").workplane(self.siphon_h + self.bell_r-3)
            .polarArray(self.siphon_r, 0, 360, 6).circle(self.wall_thick+1).cutBlind(-5)
            .faces("<Z").circle(self.siphon_r - self.wall_thick).cutThruAll()
        )

        bell = (
            cq.Workplane("XY").sphere(self.bell_r).split(1,0)
            .faces("<Z").workplane().circle(self.bell_r).extrude(self.siphon_h)
            .faces("<Z").shell(-2)
            .faces("<Z").workplane()
            .polarArray(self.bell_r, 0, 360, 10)
            .circle(self.wall_thick+1).cutBlind(-self.siphon_h/4)
        )
        siphon = siphon.union(bell.translate((0,0,self.siphon_h+self.wall_thick)))
        return siphon

    def display(self):
        show_object(self.make())

    def display_split(self):
        show_object(self.make().copyWorkplane(Workplane("XZ")).split(0,1))

    def export(self, filepath: str):
        exporters.export(self.make(), filepath)

BellSiphon().display_split()
BellSiphon().export("stl/bell_siphon.stl")
#BellSiphon().display()
#show_object(Netcup().make().translate((0,0,50)))