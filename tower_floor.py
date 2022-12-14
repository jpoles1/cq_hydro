from dataclasses import dataclass
from math import sin, cos, tan, pi, degrees, radians
import cadquery as cq
from cadquery.selectors import *

from locking_netcup import LockingNetcup
from mason_thread import MasonThread
from bell_siphon import BellSiphon
from typing import Any

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

@dataclass
class Floor(StylishPart):
    tower_od: float = 80
    wall_thick: float = 2
    lip_thick: float = 3
    floor_h: float = 85
    joint_h: float = 14
    n_locks: int = 3
    lock_nub_diam: float = 4

    def calc_vars(self):
        self.tower_id = self.tower_od - 2*self.wall_thick
        self.lip_h: float = self.joint_h
        self.lip_od = self.tower_id - 1
        self.lip_id = self.lip_od - 2*self.lip_thick

    def lock_nubs(self, floor):
        nub = cq.Workplane("XZ").circle(self.lock_nub_diam/2).extrude(self.lock_nub_diam/2)
        nub = nub.faces("<Y").fillet(self.lock_nub_diam/4)
        nub = nub.translate((0,self.tower_id/2,self.floor_h-self.lock_nub_diam/2 - 1))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = (i * 360 / self.n_locks) + (180 / self.n_locks)
            floor = floor.union(nub.rotate((0,0,0), (0,0,1), offset_angle))
        return floor

    def lock_cutout_sketch(self, lock_h, h_track_w, h_track_h, v_track_w, v_track_h, h_slanted=1, v_slant_angle = 45):
        #Sketch starts in top left corner of lock
        #Lock shape (like a sideways tetris Z)
        if h_slanted:
            h_slant_dist = 1.5
            return cq.Sketch().polygon([
                    [0,0],
                    [v_track_w+2,0],
                    [v_track_w+2+(v_track_h+0.25)/tan(radians(v_slant_angle)), -v_track_h-0.25],
                    [h_track_w,-h_slant_dist], #Adds slant
                    [h_track_w, -lock_h],
                    [h_track_w-v_track_w, -lock_h],
                    [h_track_w-v_track_w, -lock_h+v_track_h+0.25],
                    [(lock_h-h_slant_dist)/tan(radians(v_slant_angle)),-lock_h+h_slant_dist], #Adds slant
                    [0,0]
                ]).vertices().fillet(0.5)
        else:
            return cq.Sketch().polygon([
                [0,0],
                [v_track_w,0],
                [v_track_w, -v_track_h],
                [h_track_w,-v_track_h],
                [h_track_w, -lock_h],
                [h_track_w-v_track_w, -lock_h],
                [h_track_w-v_track_w, -lock_h+v_track_h],
                [0,-lock_h+v_track_h],
                [0,0]
            ])

    def lock_cutout(self, floor):
        lock_h = self.joint_h
        h_track_w = 24
        h_track_h = self.lock_nub_diam + 1
        v_track_w = self.lock_nub_diam + 1.5
        v_track_h = (lock_h - h_track_h) / 2

        #Lock shape (like a sideways tetris Z)
        lock = (
            cq.Workplane("XZ")
            .placeSketch(self.lock_cutout_sketch(lock_h, h_track_w, h_track_h, v_track_w, v_track_h))
            .extrude(-self.tower_od/2)
        )
        #Align with top of floor
        #Also align horizontally so locking nub sits aligned with the tower when seated
        lock = lock.translate((-v_track_w/2,0,-0.5))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = i * 360 / self.n_locks 
            lock = lock.union(lock.rotate((0,0,0), (0,0,1), offset_angle))
        
        #Create a thin inner wall to support the lock
        lock_outer_wall_replace = floor.faces("<Z").workplane().circle(self.lip_id/2-1.5).circle(self.lip_id/2 + 0.6).extrude(-self.joint_h, combine=0)
        floor = floor.cut(lock).union(lock_outer_wall_replace)

        return floor

    def make_base(self, add_lock_nubs=1, add_lock_cutout=1):
        #Make main body
        f = cq.Workplane("XY").circle(self.tower_od/2).circle(self.tower_od/2-self.wall_thick).extrude(self.floor_h)
        #Make inner lip for joint with section below
        lip_bridge = f.faces("<Z").workplane(offset=-2.5).circle(self.tower_od/2).circle(self.lip_id/2-1.5).extrude(3, combine=0)
        lip_bridge = lip_bridge.faces(">Z").chamfer((self.tower_od-self.lip_id-1.5)/4 - 0.4)
        inner_lip = f.faces("<Z").workplane().circle(self.lip_od/2).circle(self.lip_id/2).extrude(self.lip_h,combine=0)
        f = f.union(inner_lip).union(lip_bridge)

        if add_lock_cutout:
            f = self.lock_cutout(f)

        if add_lock_nubs:
            f = self.lock_nubs(f)

        return f

@dataclass
class PlantFloor(Floor):
    port_angle: float = 43

    def calc_vars(self):
        self.tower_id = self.tower_od - 2*self.wall_thick
        self.lip_h: float = self.joint_h
        self.lip_od = self.tower_id - 1
        self.lip_id = self.lip_od - 2*self.lip_thick
        #netcup: Any = LockingNetcup()
        #netcup_h: float = netcup.net_h
        #port_diam = netcup.net_top_diam
        #netcup_lock_top_offset = 0
        self.netcup: Any = BellSiphon(basin_angle=self.port_angle)
        self.netcup_h: float = self.netcup.basin_h
        self.port_diam: float = (self.netcup.basin_r + 0.2) * 2 #Clearance for smooth fit
        self.netcup_lock_top_offset = self.netcup.lock_top_offset


    show_netcup: bool = False
    def make_ports(self, floor, n_ports=3):
        #port_z_offset = self.floor_h / 3
        port_z_offset = 18 #Z-distance between base of tower to base of port
        port_stickout = 58
        port_wall_thick = self.wall_thick + 2
        cutout_wall_thick = 1.5
        

        #Places ports angled and positioned on the outer surface of the tower
        def position_port_part(p, angle_offset=0):
            p = p.rotate((0,0,0),(1,0,0), self.port_angle)
            p = p.translate((0,self.tower_id/2-self.port_diam/2*tan(self.port_angle*pi/180), port_z_offset))
            if angle_offset != 0:
                p = p.rotate((0,0,0), (0,0,1), angle_offset)
            return p
            
        rounded_port = 1
        #Create port pipe
        if rounded_port:
            port = cq.Workplane("XZ")\
                .circle(self.port_diam/2)\
                .circle(self.port_diam/2 + port_wall_thick)\
                .extrude(-port_stickout)

        else: 
            port = cq.Workplane("XZ")\
                .rect(self.port_diam/2, self.port_diam/2)\
                .rect(self.port_diam/2 + port_wall_thick, self.port_diam/2 + port_wall_thick)\
                .extrude(-port_stickout)

        #Create lock cutout shape for port
        lock_h= 14
        h_track_w = 12
        h_track_h = self.lock_nub_diam + 1
        v_track_w = self.lock_nub_diam + 1
        v_track_h = (lock_h - h_track_h) / 2
        lock = (
            cq.Workplane("XY")
            .placeSketch(self.lock_cutout_sketch(lock_h, h_track_w, h_track_h, v_track_w, v_track_h, v_slant_angle=90))
            .extrude(-self.tower_od/2)
            .translate((-h_track_w + v_track_w/2,port_stickout,0))
        )

        #Cut locks out of port walls
        n_locks = 2
        for i in range(n_locks):
            offset_angle = i * 360 / n_locks 
            port = port.cut(lock.rotate((0,0,0), (0,1,0), offset_angle+90))
        
        #Replace very outer port wall to prevent lock cutout from going all the way through
        port = port.faces("XZ").workplane()\
            .circle(self.port_diam/2 + port_wall_thick)\
            .circle(self.port_diam/2 + port_wall_thick-cutout_wall_thick)\
            .extrude(-port_stickout)

        port_hole = cq.Workplane("XZ")\
            .circle(self.port_diam/2)\
            .extrude(-port_stickout)

        #Clear port extrusion from inside of tower
        port_center_cutout = floor.faces(">Z").workplane().circle(self.tower_id/2).extrude(-self.floor_h)

        for i in range(n_ports):
            angle_offset = i * 360/n_ports

            floor = floor.union(position_port_part(port, angle_offset).cut(port_center_cutout))
            floor = floor.cut(position_port_part(port_hole, angle_offset))
            if (self.show_netcup):
                nc = self.netcup.make().rotate((0,0,0), (0,0,1), -90).rotate((0,0,0), (1,0,0), -90)
                nc = nc.translate((0,port_stickout-self.netcup_h+self.netcup_lock_top_offset-lock_h+self.netcup.lock_nub_diam,0))
                floor = floor.union(position_port_part(nc, angle_offset))

        return floor
    def make(self):
        f = self.make_base()
        f = self.make_ports(f)
        return f

@dataclass
class CrownFloor(Floor):
    floor_h: float = 30
    crown_angle: float = 45
    lid_h = 20
    lid_lip_h = 14

    def make(self):
        crown_id = self.tower_od - 25
        slope_apex = (self.tower_od - crown_id)/2*tan(radians(self.crown_angle))
        f = self.make_base(add_lock_nubs=0)
        crown_slope = cq.Workplane("XZ").sketch().polygon([
            [self.tower_od/2, 0],
            [crown_id/2, 0],
            #[crown_id/2, 2],
            [self.tower_od/2, slope_apex],
            [self.tower_od/2, 0],
        ]).finalize().revolve(360)
        f = f.union(crown_slope)
        return f
    def sieve(self, mini_sieve: bool = False):
        cs = CrownSieve.from_instance(self)
        cs.mini_sieve = mini_sieve
        cs.calc_vars()
        return cs

@dataclass
class CrownSieve(CrownFloor):
    #Less wide/tall version of sieve which can fit between PlantFloor to redistribute water
    mini_sieve: bool = False
    
    floor_h: float = 0
    sieve_hole_r: float = 2
    n_hole_per_row: int = 6
    sieve_thickess: float = 1.5

    tubing_od = 12
    
    def calc_vars(self):
        self.tower_id = self.tower_od - 2*self.wall_thick
        self.sieve_od = self.tower_id - (6 if self.mini_sieve else 0)
        self.sieve_id = self.tower_od - 25
        self.sieve_h = (self.sieve_od - self.sieve_id)/2*tan(radians(self.crown_angle))


    def make(self):
        s = cq.Workplane("XZ").sketch().polygon([
            [0,self.sieve_thickess],
            [0,0],
            [self.sieve_id/2,0],
            [self.sieve_od/2, self.sieve_h],
            [self.sieve_od/2, self.sieve_h+self.sieve_thickess],
            [self.sieve_od/2-self.sieve_thickess,self.sieve_h+self.sieve_thickess],
            [self.sieve_id/2-self.sieve_thickess*1.5,self.sieve_thickess],
            [0,self.sieve_thickess],
        ]).finalize().revolve(360)
        s = s.faces("<Z[-2]").workplane().cylinder(10,(self.tubing_od+6)/2,centered=[1,1,0])
        s = s.faces(">Z[-2]").circle((self.tubing_od + 0.5)/2).cutThruAll()
        s = s.edges(AndSelector(
            StringSyntaxSelector("<Z"),
            RadiusNthSelector(0)
        )).chamfer(2)

        #s = s.faces("<Z").workplane().move(self.sieve_id/2-8, 0).circle(2).cutThruAll()
        s = s.faces("<Z").workplane().polarArray(self.sieve_id/2-6, 0, 360, 2*self.n_hole_per_row).circle(self.sieve_hole_r).cutThruAll()
        s = s.faces("<Z").workplane().polarArray(self.sieve_id/2-11, 0.25*360/self.n_hole_per_row, 360, self.n_hole_per_row).circle(self.sieve_hole_r).cutThruAll()
        #s = s.faces("<Z").workplane().polarArray(self.sieve_id/2-16, 50, 360, 5).circle(2).cutThruAll()

        return s


@dataclass
class LidFloor(Floor):
    floor_h: float = 10
    lip_h: float = 8
    def make(self):
        #lid = cq.Workplane().cylinder(self.lid_h, self.tower_od/2)
        lid = cq.Workplane("XY").cylinder(self.floor_h, self.tower_od/2, centered=[1,1,0])
        lid = lid.faces("<Z").shell(-2)
        lid = lid.union(self.make_base(add_lock_cutout=0, add_lock_nubs=0))
        return lid
        
@dataclass
class MasonFloor(Floor):
    floor_h: float = 22
    lid_id: float = 82
    lid_loft_h: float = 10
    thread_pitch: float = 6.5
    cable_w: float = 6.5
    cable_h: float = 4

    def make(self):
        mason_thread = MasonThread(lid_h=18)
        self.lip_h = self.lid_loft_h+mason_thread.lid_h

        top_sketch = cq.Sketch().circle(self.tower_od).circle(self.tower_id, mode="s")
        bot_sketch = cq.Sketch().circle(mason_thread.thread_r).circle(82, mode="s")
        #Make Cone Loft Outer Contour
        m = (
            cq.Workplane("XY")
            .circle(self.tower_od/2)
            .workplane(-self.lid_loft_h)
            .circle(mason_thread.thread_r+mason_thread.wall_thick)
            .loft(ruled=1)
        )
        #Bore Cone
        m = m.cut(
            cq.Workplane("XY")
            .circle(self.tower_id/2)
            .workplane(-self.lid_loft_h)
            .circle(mason_thread.thread_r)
            .loft(ruled=1)
        )
        m = m.union(self.make_base(add_lock_cutout=0))
        m = m.union(mason_thread.make().translate((0,0,-self.lid_loft_h-mason_thread.lid_h)))
        
        cable_hole_h = self.joint_h + self.cable_h
        #Create cutout for pump power cable
        m = m.cut(
            cq.Workplane("XZ").workplane().center(0, self.floor_h-cable_hole_h)
            .rect(self.cable_w, cable_hole_h, centered=(1,0)).extrude(-self.tower_od)
            #.rotate((0,0,0), (0,0,1), 180)
        )

        cable_guard_top_cutoff = self.cable_h * 1.5

        m = m.union(
            m.faces(">Z").workplane(offset=-cable_guard_top_cutoff, origin=(0, self.tower_od/2-1))
            .rect(self.cable_w, self.cable_h+4, centered=(1,0)).extrude(-cable_hole_h+cable_guard_top_cutoff, combine=False)
            .edges("<Z and >Y").chamfer(self.cable_h+3.9)
            .faces("<Y or >Z").shell(self.wall_thick)
            #.rotate((0,0,0), (0,0,1), -45)
        )

        return m

if "show_object" in locals():
    #floor = CrownFloor().make()#.lock_cutout()#.make()
    #lid = LidFloor().make()
    #PlantFloor(show_netcup=0).display(show_object)
    MasonFloor().display(show_object)
    #CrownFloor().sieve().display_split(show_object).export("stl/sieve.stl")
    
