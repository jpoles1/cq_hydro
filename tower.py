import cadquery as cq
from tower_floor import Floor, PlantFloor, CrownFloor, MasonFloor

mf = MasonFloor().make()
pf = PlantFloor().make()
cf = CrownFloor().make()
cfs = CrownFloor().make_sieve()

alpha=0.7
a = cq.Assembly()
a = a.add(mf, loc=cq.Location(cq.Vector(0, 0, 0)), color=cq.Color(1,1,0,alpha))
a = a.add(pf, loc=cq.Location(cq.Vector(0, 0, MasonFloor().floor_h)), color=cq.Color(0,1,0,alpha))
a = a.add(pf, loc=cq.Location(cq.Vector(0, 0, PlantFloor().floor_h+MasonFloor().floor_h), cq.Vector(0,0,1), 180), color=cq.Color(0,0,1,alpha))
a = a.add(cf, loc=cq.Location(cq.Vector(0, 0, 2*PlantFloor().floor_h+MasonFloor().floor_h), cq.Vector(0,0,1), 180), color=cq.Color(1,0,0,alpha))
a = a.add(cfs, loc=cq.Location(cq.Vector(0, 0, 2*PlantFloor().floor_h+MasonFloor().floor_h-1), cq.Vector(0,0,1), 180), color=cq.Color(1,0,1,alpha))
show_object(a)

export_stl = 1
if export_stl:
    cq.exporters.export(mf, "stl/mason_floor.stl")
    cq.exporters.export(pf, "stl/plant_floor.stl")
    cq.exporters.export(cf, "stl/crown_floor.stl")
    cq.exporters.export(cfs, "stl/sieve.stl")
