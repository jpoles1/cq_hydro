import cadquery as cq
from tower_floor import Floor, PlantFloor, CrownFloor, MasonFloor, LidFloor
from collections import namedtuple
from dataclasses import dataclass

base_floor = Floor()

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
        floor_body = floor.part() if hasattr(floor, "part") else floor
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

mf = MasonFloor.from_instance(base_floor)
pf = PlantFloor.from_instance(base_floor)
cf = CrownFloor.from_instance(base_floor)
lf = LidFloor.from_instance(base_floor)

tower = assemble_tower([
    AssembleFloor(mf, color=cq.Color(1,1,0,alpha), stl="stl/mason_floor.stl"),
    AssembleFloor(pf, color=cq.Color(0,1,0,alpha), stl="stl/plant_floor.stl"),
    AssembleFloor(cf.sieve(), color=cq.Color(0,0.5,1,alpha), z_offset=0),
    AssembleFloor(pf, color=cq.Color(0,0,1,alpha), z_rot=180),
    AssembleFloor(cf.sieve(), color=cq.Color(0,0.5,1,alpha), z_offset=0, stl="stl/sieve.stl"),
    AssembleFloor(cf, color=cq.Color(0,1,1,alpha), stl="stl/crown_floor.stl"),
    AssembleFloor(lf, color=cq.Color(0.5,0,1,alpha), stl="stl/lid.stl")
], explode_h=0)

show_object(tower)
#show_object(cq.Workplane("XY").box(0.1,0.1,0.1).union(tower.toCompound()).cut(cq.Workplane("XY").box(1000,1000,1000, centered=[0,1,1])))
