from cadquery import *
from dataclasses import dataclass
import math

from netcup import Netcup
from typing import Union
from enum import Enum

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

@dataclass
class BellSiphon(StylishPart):
    round_basin: bool = True #Create a cylindrical basin if true, otherwise rectangular w/ rounded corners
   
    basin_h: float = 75 #Basin height
    basin_r: float = 22 - 0.2 #Basin radius

    add_lock_nubs: bool = True #Create locking nubs to slot into receiving part w/ cutouts
    n_locks: int = 2 #Number of locks/nubs
    lock_nub_diam: float = 4 #Diameter of lock nubs

    wall_thick: float = 1.6 #Wall thickness

    drain_h: float = 18 #Water level at which basin starts to draing
    
    basin_angle: float = 43
    
    siphon_slot_h: float = 4 #Height of slots at top of siphon to allow water in (yet support roof)
    n_siphon_slot: int = 4 #Number of slots at top of siphon to allow water in (yet support roof)

    bell_slot_h: float = 10 #Height of slots at bottom of bell to allow water in
    n_bell_slot: int = 6 #Number of slots at bottom of bell to allow water in

    siphon_r: float = 4.5 #Radius of siphon tube
    
    siphon_funnel: bool = False
    siphon_funnel_h: float = 6

    snorkel: bool = False
    snorkel_angle = 60

    drain_hole: bool = True
    drain_hole_r: float = 1

    def calc_vars(self):
        self.lock_top_offset: float = self.basin_h - 60 + 18 #Dist from top to top of lock nub
        self.siphon_slot_slanted_h: float = self.siphon_slot_h + math.tan(math.radians(90-self.basin_angle))*self.siphon_r*2 #Calculated height of siphon slots once slant is included
        self.siphon_h: float = self.drain_h + self.siphon_slot_slanted_h #Height of siphon tube
        self.siphon_funnel_top_r: float = self.siphon_r+2 if self.siphon_funnel else self.siphon_r
        self.bell_r = self.siphon_r * 2 #Radius of bell (2:1 ratio is important for bell siphon function, probably should not change this; read more here: https://www.ctahr.hawaii.edu/oc/freepubs/pdf/bio-10.pdf)
        self.bell_h = self.siphon_h - math.sqrt(self.bell_r**2 - self.siphon_funnel_top_r**2) #Dist between bell and top of siphon based on radius of each to prevent overlap during assembly
        self.siphon_offset: float = self.basin_r - self.bell_r - self.wall_thick


    def lock_nubs(self, floor):
        nub = Workplane("XZ").circle(self.lock_nub_diam/2).extrude(self.lock_nub_diam/2 + 1)
        nub = nub.faces("<Y").fillet(self.lock_nub_diam/4)
        nub = nub.translate((0,-self.basin_r+1,self.basin_h-self.lock_nub_diam/2 - self.lock_top_offset))

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
            .cylinder(self.siphon_h-self.siphon_funnel_h-self.siphon_slot_slanted_h, self.siphon_r, centered=[1,1,0], combine=False)
            .faces(">Z").workplane().circle(self.siphon_r)
            .workplane(self.siphon_funnel_h).circle(self.siphon_funnel_top_r)
            .workplane(self.siphon_slot_slanted_h).circle(self.siphon_funnel_top_r).loft(ruled=1)
            .faces("|Z").shell(-self.wall_thick)
        )

        #Create siphon cutouts
        siphon_cutouts = (
            siphon.faces("<Z[-2]").workplane()
            .polarArray(self.siphon_funnel_top_r, 0, 360, self.n_siphon_slot)
            .circle(self.siphon_funnel_top_r/2).extrude(-self.siphon_slot_slanted_h, combine=0)
        )
        if self.basin_angle != 90:
            siphon_cutouts = siphon_cutouts.cut(
                Workplane("XZ").center(self.siphon_r, self.drain_h+self.wall_thick).polyline([
                    [0,0],
                    [0,math.tan(math.radians(90-self.basin_angle))*self.siphon_r*2],
                    [-self.siphon_r*2, 0]
                ]).close().extrude(200, both=1)
            )

        siphon = siphon.cut(siphon_cutouts)
        
        basin = basin.union(siphon.translate((self.siphon_offset,0,0)))

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
            .circle(self.wall_thick+2.5).cutBlind(-self.bell_slot_h)
        )
        #Cut drain hole for siphon
        basin = basin.faces("<Z").moveTo(self.siphon_offset,0).circle(self.siphon_r-self.wall_thick).cutBlind(self.wall_thick)
        #Join siphon and bell (raising bell to sit on top of siphon)
        basin = basin.union(bell.translate((self.siphon_offset,0,self.bell_h)))

        #Add lock nubs
        if self.add_lock_nubs and self.n_locks > 0:
            basin = self.lock_nubs(basin)

        if self.snorkel:
            snorkel_opening_h = 2 #Water level at which snorkel bottom opens up = height/water level to stop siphoning
            snorkel_r = 3.5 #snorkel pipe radius
            snorkel_wall_thick = 1.5 #snorkel pipe wall thicness
            snorkel_h = self.bell_slot_h + snorkel_opening_h #Z-height at which snorkel opens to stop siphoning; derived from snorkel_opening_h
            snorkel_offset = self.bell_r + self.wall_thick + snorkel_r - 0.5 #X/Y offset of snorkel from bell wall
            snorkel_bell_entrance_h = self.siphon_h - self.bell_r  #Z-height at which snorkel enters bell
            snorkel_slot_h = 6

            

            snorkel_path = Workplane("YZ").polyline([(0, self.wall_thick), (0, snorkel_bell_entrance_h), (snorkel_offset-self.bell_r, snorkel_bell_entrance_h)])
            isnorkel_path = Workplane("YZ").polyline([(0, snorkel_h - snorkel_slot_h*0.8), (0, snorkel_bell_entrance_h), (snorkel_offset-self.bell_r+self.wall_thick, snorkel_bell_entrance_h)])

            snorkel = (
                Workplane("XY").workplane(snorkel_h)
                .circle(snorkel_r).sweep(snorkel_path, transition="round")
                .copyWorkplane(Workplane("XY")).workplane(snorkel_h)
                .polarArray(snorkel_r, 0, 360, 4)
                .circle(snorkel_wall_thick+0.2).cutBlind(-snorkel_slot_h)
                .translate((self.siphon_offset, -snorkel_offset, 0))
                .rotate((self.siphon_offset,0,0), (self.siphon_offset,0,1), -self.snorkel_angle)
            )

            isnorkel = (
                Workplane("XY").workplane(snorkel_h)
                .circle(snorkel_r-snorkel_wall_thick).sweep(isnorkel_path, transition="round")
                .translate((self.siphon_offset, -snorkel_offset, 0))
                .rotate((self.siphon_offset,0,0), (self.siphon_offset,0,1), -self.snorkel_angle)
            )

            basin = basin.union(snorkel)
            basin = basin.cut(isnorkel)

        wall_cutout = 1
        cutout_z_offset = self.wall_thick + 12
        cuthout_w = self.basin_r * 1.5
        cutout_h = 16
        cutout_angle_range = 100
        cutout_slot_n = 5
        if wall_cutout:
            #basin = basin.copyWorkplane(Workplane("YZ")).workplane(0, origin=(0,0,cutout_z_offset)).rect(cuthout_w, cutout_h, centered=[1,0]).cutBlind(-self.basin_r)
            basin = basin.copyWorkplane(Workplane("XY")).workplane(cutout_z_offset).polarArray(self.basin_r, 90 + (180-cutout_angle_range)/2, cutout_angle_range, cutout_slot_n).circle(self.wall_thick*2).cutBlind(cutout_h)

        if self.drain_hole:
            basin = basin.faces("<Z").workplane().moveTo((self.bell_r - self.siphon_r) * 1.5 + self.siphon_offset).hole(2*self.drain_hole_r, self.wall_thick)

        return basin.rotate((0,0,0), (0,0,1), 180)

    def draw_water(self, water_h):
        bs = self.make()
        water_line = Workplane("XY").workplane(water_h).circle(self.basin_r*5).extrude(1)#.intersect()
        a = Assembly()
        a = a.add(bs.translate((self.basin_r,0,0)).rotate((0,0,0), (0,1,0), self.basin_angle-90).copyWorkplane(Workplane("XZ")).split(0,1))
        a = a.add(water_line, color=Color(0, 0, 1, 0.5))
        show_object(a)
        return self

if "show_object" in locals():
    BellSiphon(basin_angle=43, siphon_funnel=0).draw_water(water_h=24).draw_water(water_h=34)
    #BellSiphon().display(show_object)
    BellSiphon().export("stl/bell_siphon.stl")
    #BellSiphon().display_split(show_object)
    #show_object(Netcup().make().translate((0,0,40)))