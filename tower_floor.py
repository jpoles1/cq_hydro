from dataclasses import dataclass
import math
import cadquery as cq
from netcup import Netcup

@dataclass
class Floor:
    tower_od: float = 80
    wall_thick: float = 2
    floor_h: float = 74
    joint_h: float = 14
    port_angle: float= 30
    n_locks: int = 4
    lock_nub_diam: float = 3

    def __post_init__(self):
        self.tower_id = self.tower_od - 2*self.wall_thick
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

        floor = floor.faces(">Z").workplane().circle(self.tower_id/2).cutBlind(-self.floor_h)

        return floor

    def lock_nubs(self, floor):
        nub = cq.Workplane("XZ").circle()

    def lock_cutout(self):
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
        lock = lock.translate((-h_track_w+v_track_w/2,0,self.floor_h))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = i * 360 / self.n_locks 
            lock = lock.union(lock.rotate((0,0,0), (0,0,1), 90))
        return lock

    def make(self):
        #Make main body
        f = cq.Workplane("XY").circle(self.tower_od/2).circle(self.tower_od/2-self.wall_thick).extrude(self.floor_h)
        #Make inner lip for joint with section below
        inner_lip = f.faces("<Z").workplane().circle(self.tower_id/2).circle(self.tower_id/2-self.wall_thick).extrude(self.joint_h,combine=0)
        #inner_lip = inner_lip.faces(">Z").edges("<<X").chamfer(0.5)

        f = self.make_ports(f)

        f = f.union(inner_lip)

        #Create a thin wall to provide a thin outer wall to contain (and conceal) the lock nub
        lock_outer_wall_replace = f.faces(">Z").circle(self.tower_od/2).circle(self.tower_od/2-0.5).extrude(-self.joint_h, combine=0)
        f = f.cut(self.lock_cutout()).union(lock_outer_wall_replace)

        return f

floor = Floor().make()#.lock_cutout()#.make()

