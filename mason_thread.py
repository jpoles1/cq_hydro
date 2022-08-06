import cadquery as cq

mason_thread_od = 82.4
thread_pitch = 6.5
thread_h = thread_pitch*2.5
lid_h = thread_h + 2
wall_thick = 2.5
thread_contour_diam=3
thread_contour_h=2.2

thread_r = mason_thread_od/2 + thread_contour_diam 

# Helix
helix_wire = cq.Wire.makeHelix(pitch=thread_pitch, height=thread_h, radius=thread_r)
helix = cq.Workplane(obj=helix_wire)
#show_object(helix)

# Final result. A circle sweeped along a helix.
threads = (
    cq.Workplane('XZ')
    .center(thread_r, 0)
    .circle(thread_contour_diam/2)
    .sweep(helix_wire, isFrenet=True)
)
#show_object(threads)

mason_thread = cq.Workplane("XY").circle(thread_r+wall_thick).circle(thread_r).extrude(lid_h)
mason_thread = mason_thread.union(threads).faces("XY").workplane(origin=(0,0,0)).split(1,0)

show_object(mason_thread)
cq.exporters.export(mason_thread, "stl/mason_thread.stl")