import cadquery as cq
from tower_floor import Floor, PlantFloor, CrownFloor, MasonFloor, LidFloor
from collections import namedtuple
from dataclasses import dataclass

floor = Floor()

@dataclass
class AssembleFloor:
    floor: Floor #Floor class (or solid body)
    color: cq.Color = cq.Color(0.2,0.2,0.2)
    z_rot: float = 0 #Rotate around z axis
    z_offset: float = 0 #Offset in tower on Z-dir
    stl: str = "" #.stl File path if export desired

def assemble_tower(floors, explode_h=0):
    current_h = 0
    a = cq.Assembly()
    for (i, f) in enumerate(floors):
        floor = f.floor
        floor_body = floor.make() if hasattr(floor, "make") else floor
        a = a.add(
            floor_body,
            loc=cq.Location(cq.Vector(0, 0, current_h+f.z_offset), cq.Vector(0, 0, 1), f.z_rot),
            color= f.color
        )
        current_h += floor.floor_h if hasattr(floor, "floor_h") else 0
        current_h += explode_h+f.z_offset
        
        if(f.stl != ""):
            cq.exporters.export(floor_body, f.stl)

    return a

alpha=0.7
tower = assemble_tower([
    AssembleFloor(MasonFloor.from_instance(floor), color=cq.Color(1,1,0,alpha), stl="stl/mason_floor.stl"),
    AssembleFloor(PlantFloor.from_instance(floor), color=cq.Color(0,1,0,alpha), stl="stl/plant_floor.stl"),
    AssembleFloor(PlantFloor.from_instance(floor), color=cq.Color(0,0,1,alpha), z_rot=180),
    AssembleFloor(CrownFloor.from_instance(floor), color=cq.Color(0,1,1,alpha), stl="stl/crown_floor.stl"),
    AssembleFloor(CrownFloor.from_instance(floor).sieve(), color=cq.Color(0,0.5,1,alpha), z_offset=-CrownFloor.from_instance(floor).floor_h, stl="stl/sieve.stl"),
    AssembleFloor(LidFloor.from_instance(floor), color=cq.Color(0.5,0,1,alpha), stl="stl/lid.stl")
], explode_h=21)


show_object(tower)
#show_object(cq.Workplane("XY").box(0.1,0.1,0.1).union(tower.toCompound()).cut(cq.Workplane("XY").box(1000,1000,1000, centered=[0,1,1])))

'''
mf = MasonFloor().make()
pf = PlantFloor().make()
cf = CrownFloor().make()
cfs = CrownFloor().sieve()
lf = LidFloor().make()

alpha=0.7
a = cq.Assembly()
a = a.add(mf, loc=cq.Location(cq.Vector(0, 0, 0)), color=cq.Color(1,1,0,alpha))
a = a.add(pf, loc=cq.Location(cq.Vector(0, 0, MasonFloor().floor_h)), color=cq.Color(0,1,0,alpha))
a = a.add(pf, loc=cq.Location(cq.Vector(0, 0, PlantFloor().floor_h+MasonFloor().floor_h), cq.Vector(0,0,1), 180), color=cq.Color(0,0,1,alpha))
a = a.add(cf, loc=cq.Location(cq.Vector(0, 0, 2*PlantFloor().floor_h+MasonFloor().floor_h), cq.Vector(0,0,1), 180), color=cq.Color(1,0,0,alpha))
#a = a.add(lf, loc=cq.Location(cq.Vector(0, 0, 2*PlantFloor().floor_h+MasonFloor().floor_h+CrownFloor().floor_h), cq.Vector(0,0,1), 180), color=cq.Color(1,0,1,alpha))
a = a.add(cfs, loc=cq.Location(cq.Vector(0, 0, 2*PlantFloor().floor_h+MasonFloor().floor_h-1), cq.Vector(0,0,1), 180), color=cq.Color(1,0,1,alpha))

#show_object(a)
show_object(cq.Workplane("XY").box(0.1,0.1,0.1).union(a.toCompound()).copyWorkplane(cq.Workplane("XZ")).split(0,1))
#show_object(cq.Workplane("XY").box(0.1,0.1,0.1).union(a.toCompound()).cut(cq.Workplane("XY").box(1000,1000,1000, centered=[0,1,1])))

export_stl = 1
if export_stl:
    cq.exporters.export(mf, "stl/mason_floor.stl")
    cq.exporters.export(pf, "stl/plant_floor.stl")
    cq.exporters.export(cf, "stl/crown_floor.stl")
    cq.exporters.export(cfs, "stl/sieve.stl")
'''