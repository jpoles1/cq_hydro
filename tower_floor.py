from dataclasses import dataclass
import math
import cadquery as cq
from netcup import Netcup
from mason_thread import MasonThread

@dataclass
class Floor:
    tower_od: float = 80
    wall_thick: float = 2
    lip_thick: float = 3
    floor_h: float = 74
    joint_h: float = 14
    lip_h: float = joint_h
    port_angle: float= 30
    n_locks: int = 4
    lock_nub_diam: float = 3

    def __post_init__(self):
        self.tower_id = self.tower_od - 2*self.wall_thick
        self.lip_od = self.tower_id - 1
        self.lip_id = self.lip_od - 2*self.lip_thick
        self.netcup = Netcup()
        self.netcup_top_diam = self.netcup.net_top_diam

    def make_ports(self, floor, n_ports=3):
        port_h_offset = self.floor_h / 2 - 6
        port_stickout = 30
        def position_port_part(p, angle_offset=0):
            p = p.rotate((0,0,0),(1,0,0), 30)
            p = p.translate((0,self.tower_id/2-self.netcup_top_diam/2*math.tan(self.port_angle*math.pi/180), port_h_offset))
            if angle_offset != 0:
                p = p.rotate((0,0,0), (0,0,1), angle_offset)
            return p
            
        port = cq.Workplane("XZ")\
            .circle(self.netcup_top_diam/2)\
            .circle(self.netcup_top_diam/2 + self.wall_thick)\
            .extrude(-port_stickout)

        
        port_hole = cq.Workplane("XZ")\
            .circle(self.netcup_top_diam/2)\
            .extrude(-port_stickout)

        for i in range(n_ports):
            angle_offset = i * 360/n_ports

            floor = floor.union(position_port_part(port, angle_offset))
            floor = floor.cut(position_port_part(port_hole, angle_offset))

        #Offset to prevent cutting out lock nubs
        floor = floor.faces(">Z").workplane(offset=-10).circle(self.tower_id/2).cutBlind(-(self.floor_h-10))

        return floor

    def lock_nubs(self, floor):
        nub = cq.Workplane("XZ").circle(self.lock_nub_diam/2).extrude(self.lock_nub_diam/2)
        nub = nub.faces("<Y").fillet(self.lock_nub_diam/4)
        nub = nub.translate((0,self.tower_id/2,self.floor_h-self.lock_nub_diam/2 - 1))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = i * 360 / self.n_locks 
            floor = floor.union(nub.rotate((0,0,0), (0,0,1), offset_angle))
        return floor

    def lock_cutout(self, floor):
        lock_h = self.joint_h
        h_track_w = 14
        h_track_h = self.lock_nub_diam + 1
        v_track_w = self.lock_nub_diam + 1
        v_track_h = (lock_h - h_track_h) / 2

        #Lock shape (like a sideways tetris Z)
        lock = cq.Workplane("XZ").sketch().polygon([
            [0,0],
            [v_track_w,0],
            [v_track_w, -v_track_h],
            [h_track_w,-v_track_h],
            [h_track_w, -lock_h],
            [h_track_w-v_track_w, -lock_h],
            [h_track_w-v_track_w, -lock_h+v_track_h],
            [0,-lock_h+v_track_h],
            [0,0]
        ]).finalize().extrude(-self.tower_od/2)
        #Align with top of floor
        #Also align horizontally so locking nub sits aligned with the tower when seated
        lock = lock.translate((-v_track_w/2,0))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = i * 360 / self.n_locks 
            lock = lock.union(lock.rotate((0,0,0), (0,0,1), offset_angle))
        
        #Create a thin inner wall to support the lock
        lock_outer_wall_replace = floor.faces("<Z").workplane().circle(self.lip_id/2).circle(self.lip_id/2 + self.wall_thick/3).extrude(-self.joint_h, combine=0)
        floor = floor.cut(lock).union(lock_outer_wall_replace)

        return floor

    def make_base(self, add_lock_nubs=1, add_lock_cutout=1):
        #Make main body
        f = cq.Workplane("XY").circle(self.tower_od/2).circle(self.tower_od/2-self.wall_thick).extrude(self.floor_h)
        #Make inner lip for joint with section below
        lip_bridge = f.faces("<Z").workplane(offset=-2.5).circle(self.tower_od/2).circle(self.lip_id/2).extrude(3, combine=0)
        lip_bridge = lip_bridge.faces(">Z").chamfer((self.tower_od-self.lip_id)/4 - 0.4)
        inner_lip = f.faces("<Z").workplane().circle(self.lip_od/2).circle(self.lip_id/2).extrude(self.lip_h,combine=0)
        f = f.union(inner_lip).union(lip_bridge)

        if add_lock_cutout:
            f = self.lock_cutout(f)

        if add_lock_nubs:
            f = self.lock_nubs(f)

        return f

class PlantFloor(Floor):
    def make(self):
        f = self.make_base()
        f = self.make_ports(f)
        return f

@dataclass
class CrownFloor(Floor):
    floor_h: float = 30
    crown_angle: float = 45
    def make(self):
        crown_id = self.tower_od - 25
        slope_apex = (self.tower_od - crown_id)/2*math.tan(self.crown_angle*math.pi/180)
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

    def make_sieve(self):
        crown_id = self.tower_od - 25
        sieve_thickess = 2
        slope_apex = (self.tower_od - crown_id)/2*math.tan(self.crown_angle*math.pi/180)
        s = cq.Workplane("XZ").sketch().polygon([
            [0,sieve_thickess],
            [0,0],
            [crown_id/2-sieve_thickess,0],
            [self.tower_id/2, slope_apex],
            [self.tower_id/2, slope_apex+sieve_thickess],
            [self.tower_id/2-sieve_thickess,slope_apex+sieve_thickess],
            [crown_id/2-2,sieve_thickess],
            [0,sieve_thickess],
        ]).finalize().revolve(360)
        s = s.faces("<Z[-2]").workplane().cylinder(10,16/2,centered=[1,1,0])
        s = s.faces(">Z[-2]").circle(12.5/2).cutThruAll()

        #s = s.faces("<Z").workplane().move(crown_id/2-8, 0).circle(2).cutThruAll()
        s = s.faces("<Z").workplane().polarArray(crown_id/2-8, 0, 360, 5).circle(2).cutThruAll()
        s = s.faces("<Z").workplane().polarArray(crown_id/2-12, 25, 360, 5).circle(2).cutThruAll()
        s = s.faces("<Z").workplane().polarArray(crown_id/2-16, 50, 360, 5).circle(2).cutThruAll()

        return s

@dataclass
class MasonFloor(Floor):
    floor_h: float = 18
    lid_id: float = 82
    lid_loft_h: float = 10
    thread_pitch: float = 6.5

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
        return m
        
#floor = PlantFloor().make()#.lock_cutout()#.make()
#floor = CrownFloor().make()#.lock_cutout()#.make()
#floor = CrownFloor().make_sieve()#.lock_cutout()#.make()
#floor = MasonFloor().make().copyWorkplane(cq.Workplane("XZ")).workplane(origin=(0,0,0)).split(0,1)
