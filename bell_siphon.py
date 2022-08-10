from cadquery import *
from dataclasses import dataclass
from cqstyle import StylishPart
import math

from netcup import Netcup
from typing import Any

@dataclass
class BellSiphon(StylishPart):
    vertical_pipe: bool = True #Pipe exits vertically (from bottom of basin), or horizontally (from basin wall) which does not seem to siphon well.
    round_basin: bool = True #Create a cylindrical basin if true, otherwise rectangular w/ rounded corners
    
    add_lock_nubs: bool = True #Create locking nubs to slot into receiving part w/ cutouts
    n_locks: int = 2 #Number of locks/nubs
    lock_nub_diam: float = 4 #Diameter of lock nubs

    basin_h: float = 60 #Basin height
    basin_r: float = 25 #Basin radius

    wall_thick: float = 1.6 #Wall thickness

    drain_h: float = 30 #Water level at which basin starts to draing
    
    siphon_slot_h: float = drain_h/5 #Height of slots at top of siphon to allow water in (yet support roof)
    n_siphon_slot: int = 4 #Number of slots at top of siphon to allow water in (yet support roof)

    bell_slot_h: float = drain_h/5 #Height of slots at top of siphon to allow water in (yet support roof)
    n_bell_slot: int = 8 #Number of slots at top of siphon to allow water in (yet support roof)

    siphon_h: float = drain_h + siphon_slot_h #Height of siphon tube
    siphon_r: float = 5 #Radius of siphon tube
    pipe_r: float = siphon_r #Radius of pipe outlet of siphon
    bell_r = siphon_r *2 #Radius of bell (2:1 ratio is important for bell siphon function, probably should not change this; read more here: https://www.ctahr.hawaii.edu/oc/freepubs/pdf/bio-10.pdf)
    bell_h = siphon_h - math.sqrt(bell_r**2 - siphon_r**2) #Dist between bell and top of siphon based on radius of each to prevent overlap during assembly

    siphon_offset: float = basin_r - bell_r - wall_thick if vertical_pipe else 0
    #siphon_offset: float = 0

    def lock_nubs(self, floor):
        nub = Workplane("XZ").circle(self.lock_nub_diam/2).extrude(self.lock_nub_diam/2 + 1)
        nub = nub.faces("<Y").fillet(self.lock_nub_diam/4)
        nub = nub.translate((0,-self.basin_r+1,self.basin_h-self.lock_nub_diam/2 - 1))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = i * 360 / self.n_locks 
            floor = floor.union(nub.rotate((0,0,0), (0,0,1), offset_angle))
        return floor

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
        siphon = (
            #Create siphon tube outer contour
            basin.faces(">Z[-2]").workplane()
            .cylinder(self.siphon_h, self.siphon_r, centered=[1,1,0], combine=False)
            #Create siphon tube cutouts
            .faces("XY").workplane(self.siphon_h)
            .polarArray(self.siphon_r, 0, 360, self.n_siphon_slot).circle(self.wall_thick+1).cutBlind(-self.siphon_slot_h)
            #Bore siphon tube center
        )

        basin = basin.union(siphon.translate((self.siphon_offset,0,0)))
        
        if self.vertical_pipe:
            #If vertical, cut bore all the way through siphon
            basin = basin.faces("<Z").workplane(origin=(self.siphon_offset,0)).circle(self.siphon_r - self.wall_thick).cutBlind(-self.siphon_h-self.wall_thick)
        else:
            #If swept, cut bore only at top for slots
            basin = basin.faces("<Z").workplane(-self.drain_h).circle(self.siphon_r - self.wall_thick).cutBlind(-self.siphon_h)


        #Create bell that surrounds siphon
        bell = (
            #Draw sphere half to create dome of bell
            Workplane("XY").sphere(self.bell_r).split(1,0)
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
        basin = basin.union(bell.translate((self.siphon_offset,0,self.bell_h)))

        #If swept pipe, generate path and sweep
        #Due to weird bug have to create path twice for original pipe and then cutout/bore
        if not self.vertical_pipe:
            pipe_z = self.wall_thick/2 + self.pipe_r

            pipe_path = Workplane("XZ").polyline([(0, self.drain_h), (0, pipe_z), (self.basin_r/3, pipe_z), (self.basin_r-self.wall_thick, pipe_z)])
            ipipe_path = Workplane("XZ").polyline([(0, self.drain_h), (0, pipe_z), (self.basin_r/3, pipe_z), (self.basin_r, pipe_z)])

            pipe = Workplane("XY").workplane(self.drain_h).circle(self.pipe_r).sweep(pipe_path, transition="round", isFrenet=1)
            ipipe = Workplane("XY").workplane(self.drain_h).circle(self.pipe_r-self.wall_thick).sweep(ipipe_path, transition="round", isFrenet=1)

            basin = basin.union(pipe).cut(ipipe)

        #Add lock nubs
        if self.add_lock_nubs and self.n_locks > 0:
            basin = self.lock_nubs(basin)

        snorkel_opening_h = 4
        snorkel_r = 3
        snorkel_wall_thick = 1.5
        snorkel_h = self.bell_slot_h + snorkel_opening_h
        snorkel_offset = self.bell_r + self.wall_thick + snorkel_r - 0.5

        snorkel_axis = "YZ"
        snorkel_axis_translate = (self.siphon_offset - (1 if snorkel_axis == "XZ" else 0) * snorkel_offset, (-1 if snorkel_axis == "YZ" else 0) * snorkel_offset, 0)

        snorkel_path = Workplane(snorkel_axis).polyline([(0, self.wall_thick), (0, self.drain_h), (snorkel_offset-self.bell_r, self.drain_h)])
        isnorkel_path = Workplane(snorkel_axis).polyline([(0, snorkel_h - snorkel_opening_h/2), (0, self.drain_h), (snorkel_offset-self.bell_r+self.wall_thick, self.drain_h)])

        snorkel = (
            Workplane("XY").workplane(snorkel_h)
            .circle(snorkel_r).sweep(snorkel_path, transition="round")
            .copyWorkplane(Workplane("XY")).workplane(snorkel_h)
            .polarArray(snorkel_r, 0, 360, 4)
            .circle(snorkel_wall_thick+0.1).cutBlind(-snorkel_opening_h)
            .translate(snorkel_axis_translate)
        )

        isnorkel = (
            Workplane("XY").workplane(snorkel_h)
            .circle(snorkel_r-snorkel_wall_thick).sweep(isnorkel_path, transition="round")
            .translate(snorkel_axis_translate)
        )

        basin = basin.union(snorkel)
        basin = basin.cut(isnorkel)

        return basin.rotate((0,0,0), (0,0,1), 180)

if "show_object" in locals():
    BellSiphon().display_split(show_object)
    BellSiphon().export("stl/bell_siphon.stl")
    #BellSiphon().display_split(show_object)
    #show_object(Netcup().make().translate((0,0,50)))