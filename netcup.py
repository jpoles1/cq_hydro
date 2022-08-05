from dataclasses import dataclass
import cadquery as cq

@dataclass
class Netcup:
    net_bot_diam: float = 22
    net_top_diam: float = 29
    net_top_brim_diam: float = 38
    net_h: float = 40
    wall_thick: float = 1.2
    net_bot_hole_diam = 15

    def __post_init__(self):
        #Post-init processing
        self.net_h
    def make(self):
        #Create outer profile
        c = cq.Workplane("XY").circle(self.net_bot_diam/2).workplane(offset=self.net_h).circle(self.net_top_diam/2).loft()
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
        slot_h_from_top = 12
        slot = cq.Workplane("XZ").workplane(origin=(0,0,self.wall_thick))
        slot = slot.rect(10, self.net_h-self.wall_thick - slot_h_from_top, centered=[1, 0]).extrude(30)
        for i in range(n_slots):
            c = c.cut(slot.rotate((0,0,0), (0,0,1), i*slot_angle))

        return c

#show_object(Netcup().make())
