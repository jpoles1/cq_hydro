from dataclasses import dataclass
import cadquery as cq

@dataclass
class LockingNetcup:
    net_bot_diam: float = 22
    net_top_diam: float = 29
    net_top_brim_diam: float = 38
    net_h: float = 40
    wall_thick: float = 1.2
    net_bot_hole_diam = 15
    lock_h: float = 14
    n_locks: int = 2
    lock_nub_diam: float = 3

    def lock_nubs(self, net):
        nub = cq.Workplane("XZ").circle(self.lock_nub_diam/2).extrude(-self.lock_nub_diam/2)
        nub = nub.faces(">Y").fillet(self.lock_nub_diam/4)
        nub = nub.translate((0,self.net_top_diam/2,self.net_h-self.lock_h + self.lock_nub_diam/2+1))

        #Revolve around center
        for i in range(self.n_locks):
            offset_angle = i * 360 / self.n_locks 
            net = net.union(nub.rotate((0,0,0), (0,0,1), offset_angle))
        return net

    def make(self):
        #Create outer profile
        c = (
            cq.Workplane("XY").circle(self.net_bot_diam/2)
            .workplane(offset=self.net_h-self.lock_h).circle(self.net_top_diam/2)
            .workplane(offset=self.lock_h).circle(self.net_top_diam/2)
            .loft(ruled=1)
        )
        c = c.faces(">Z").circle(self.net_top_brim_diam/2).extrude(self.wall_thick)
        #Cut out inner bore
        bore = cq.Workplane("XY").workplane(offset=self.wall_thick).circle(self.net_bot_diam/2 - self.wall_thick).workplane(offset=self.wall_thick + self.net_h).circle(self.net_top_diam/2 - self.wall_thick).loft()
        c = c.cut(bore)

        #Cut bottom hole
        c = c.faces("<Z").circle(self.net_bot_hole_diam/2).cutThruAll()

        #Cut slots
        n_slots = 5
        slot_angle = 360 / 5
        slot_w = 10
        slot_h_from_top = 14
        slot = cq.Workplane("XZ").workplane(origin=(0,0,self.wall_thick))
        slot = slot.rect(10, self.net_h-self.wall_thick - slot_h_from_top, centered=[1, 0]).extrude(30)
        for i in range(n_slots):
            c = c.cut(slot.rotate((0,0,0), (0,0,1), i*slot_angle))
        c = self.lock_nubs(c)

        return c

#show_object(LockingNetcup().make())
#cq.exporters.export(LockingNetcup().make(), "stl/locking_netcup.stl")