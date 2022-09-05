import cadquery as cq
from dataclasses import dataclass

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

@dataclass
class MasonThread(StylishPart):

    mason_thread_od: float = 82.4
    thread_pitch: float = 6.5
    thread_h: float = thread_pitch*2.5
    lid_h: float = thread_h + 2
    wall_thick: float = 2.5
    thread_contour_diam: float = 3.2
    thread_contour_h: float = 2.2
    thread_r: float = mason_thread_od/2 + thread_contour_diam 

    def make(self, export_stl=0):


        # Helix
        helix_wire = cq.Wire.makeHelix(pitch=self.thread_pitch, height=self.thread_h, radius=self.thread_r)
        helix = cq.Workplane(obj=helix_wire)
        #show_object(helix)

        # Final result. A circle sweeped along a helix.
        threads = (
            cq.Workplane('XZ')
            .center(self.thread_r, 0)
            .circle(self.thread_contour_diam/2)
            .sweep(helix_wire, isFrenet=True)
        )
        #show_object(threads)

        mason_thread = cq.Workplane("XY").circle(self.thread_r+self.wall_thick).circle(self.thread_r).extrude(self.lid_h)
        mason_thread = mason_thread.union(threads).faces("XY").workplane(origin=(0,0,0)).split(1,0)

        if export_stl:
            cq.exporters.export(mason_thread, "stl/mason_thread.stl")

        return mason_thread

if "show_object" in locals():
    MasonThread().display(show_object)
    #MasonThread().display_split(show_object)