from cadquery import *
from dataclasses import dataclass
import math

from netcup import Netcup

@dataclass
class BellSiphon:
    vertical_pipe: bool = True #Pipe exits vertically (from bottom of basin), or horizontally (from basin wall)
    round_basin: bool = False #Create a cylindrical basin if true, otherwise rectangular w/ rounded corners

    basin_h: float = 50 #Basin height
    basin_r: float = 26 #Basin radius

    wall_thick: float = 2 #Wall thickness

    drain_h: float = 30 #Water level at which basin starts to draing
    
    siphon_slot_h: float = drain_h/4 #Height of slots at top of siphon to allow water in (yet support roof)
    n_siphon_slot: int = 4 #Number of slots at top of siphon to allow water in (yet support roof)

    bell_slot_h: float = drain_h/4 #Height of slots at top of siphon to allow water in (yet support roof)
    n_bell_slot: int = 8 #Number of slots at top of siphon to allow water in (yet support roof)

    siphon_h: float = drain_h + siphon_slot_h #Height of siphon tube
    siphon_r: float = 7 #Radius of siphon tube
    pipe_r: float = siphon_r #Radius of pipe outlet of siphon
    bell_r = siphon_r *2 #Radius of bell (2:1 ratio is important for bell siphon function, probably should not change this; read more here: https://www.ctahr.hawaii.edu/oc/freepubs/pdf/bio-10.pdf)
    bell_h = siphon_h - math.sqrt(bell_r**2 - siphon_r**2) #Dist between bell and top of siphon based on radius of each to prevent overlap during assembly

    def make(self):
        #Create basin
        if self.round_basin:
            #Cylindrical basin
            basin = (
                Workplane("XY").cylinder(self.basin_h, self.basin_r, centered=[1,1,0])
                .faces(">Z").shell(-self.wall_thick, kind="intersection")
            )
        else:
            #Rectangular basin
            basin = (
                Workplane("XY").box(2*self.basin_r, 2*self.basin_r,self.basin_h, centered=[1,1,0])
                .faces(">Z").shell(-self.wall_thick, kind="intersection")
                .edges("|Z").fillet(self.wall_thick)
            )
        #Create siphon (+basin)
        basin = (
            #Create siphon tube outer contour
            basin.faces(">Z[-2]").workplane()
            .cylinder(self.siphon_h, self.siphon_r, centered=[1,1,0])
            #Create siphon tube cutouts
            .faces("XY").workplane(self.siphon_h)
            .polarArray(self.siphon_r, 0, 360, self.n_siphon_slot).circle(self.wall_thick+1).cutBlind(-self.siphon_slot_h)
            #Bore siphon tube center
        )
        
        if self.vertical_pipe:
            #If vertical, cut bore all the way through siphon
            basin = basin.faces("<Z").workplane().circle(self.siphon_r - self.wall_thick).cutBlind(-self.siphon_h-self.wall_thick)
        else:
            #If swept, cut bore only at top for slots
            basin = basin.faces("<Z").workplane(-self.drain_h).circle(self.siphon_r - self.wall_thick).cutBlind(-self.siphon_h)


        #Create bell that surrounds siphon
        bell = (
            #Draw sphere half to create dome of bell
            cq.Workplane("XY").sphere(self.bell_r).split(1,0)
            #Create walls down from dome
            .faces("<Z").workplane().circle(self.bell_r).extrude(self.bell_h)
            #Bore out bell
            .faces("<Z").shell(self.wall_thick)
            #Cut slots at bottom of bell to allow water to flow in
            .faces("<Z").workplane()
            .polarArray(self.bell_r, 0, 360, self.n_bell_slot)
            .circle(self.wall_thick+1).cutBlind(-self.bell_slot_h)
        )
        #Join siphon and bell (raising bell to sit on top of siphon)
        basin = basin.union(bell.translate((0,0,self.bell_h)))

        #If swept pipe, generate path and sweep
        #Due to weird bug have to create path twice for original pipe and then cutout/bore
        if not self.vertical_pipe:
            pipe_z = self.wall_thick/2 + self.pipe_r

            pipe_path = Workplane("XZ").polyline([(0, self.drain_h), (0, pipe_z), (self.basin_r/3, pipe_z), (self.basin_r-self.wall_thick, pipe_z)])
            ipipe_path = Workplane("XZ").polyline([(0, self.drain_h), (0, pipe_z), (self.basin_r/3, pipe_z), (self.basin_r, pipe_z)])

            pipe = Workplane("XY").workplane(self.drain_h).circle(self.pipe_r).sweep(pipe_path, transition="round", isFrenet=1)
            ipipe = Workplane("XY").workplane(self.drain_h).circle(self.pipe_r-self.wall_thick).sweep(ipipe_path, transition="round", isFrenet=1)

            basin = basin.union(pipe).cut(ipipe)

        return basin

    def display(self):
        show_object(self.make())

    def display_split(self):
        show_object(self.make().copyWorkplane(Workplane("XZ")).split(0,1))

    def export(self, filepath: str):
        exporters.export(self.make(), filepath)

BellSiphon().display_split()
BellSiphon().export("stl/bell_siphon.stl")
#BellSiphon().display()
show_object(Netcup().make().translate((0,0,50)))