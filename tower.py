import cadquery as cq
from tower_floor import Floor, PlantFloor, CrownFloor, MasonFloor, LidFloor
from collections import namedtuple
from dataclasses import dataclass
import cq_warehouse.extensions
from sprinkler import Sprinkler

import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

base_floor = Floor()


@dataclass
class AssembleFloor:
    floor: Floor #Floor class (or solid body)
    color: cq.Color = cq.Color(0.2,0.2,0.2)
    z_rot: float = 0 #Rotate around z axis
    z_offset: float = 0 #Offset in tower on Z-dir
    stl: str = "" #.stl File path if export desired

@dataclass
class Tower(StylishPart):
    def assemble_tower(self, floors, explode_h=0):
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
            current_h += floor.floor_h+explode_h if hasattr(floor, "floor_h") and floor.floor_h > 0 else 0
            #current_h += explode_h+f.z_offset
            
            if(f.stl != ""):
                cq.exporters.export(floor_body, f.stl)

        return a
    def make(self):
        alpha=1

        mf = MasonFloor.from_instance(base_floor)
        pf1 = PlantFloor.from_instance(base_floor)
        pf2 = PlantFloor.from_instance(base_floor)
        pf2.show_netcup = True
        cf = CrownFloor.from_instance(base_floor)
        mini_sieve = cf.sieve(mini_sieve=True)
        sieve = cf.sieve()
        sprinkler = Sprinkler()
        lf = LidFloor.from_instance(base_floor)

        tower = self.assemble_tower([
            AssembleFloor(mf, color=cq.Color(1,1,0,alpha), stl="stl/mason_floor.stl"),
            AssembleFloor(pf1, color=cq.Color(0,1,0,alpha), stl="stl/plant_floor.stl"),
            AssembleFloor(mini_sieve, color=cq.Color(1,0.5,1,alpha), z_offset=3-mini_sieve.sieve_h, stl="stl/mini_sieve.stl"),
            AssembleFloor(pf2, color=cq.Color(0,0,1,alpha), z_rot=180),
            AssembleFloor(sieve, color=cq.Color(0.2,0.2,0.6,alpha), z_offset=0, stl="stl/sieve.stl"),
            AssembleFloor(sprinkler.part(), color=cq.Color(0.6,0.2,0.6,alpha), z_offset=15, stl="stl/sprinkler.stl"),
            AssembleFloor(cf, color=cq.Color(0,1,1,alpha), stl="stl/crown_floor.stl"),
            AssembleFloor(lf, color=cq.Color(0.5,0,1,alpha), stl="stl/lid.stl")
        ], explode_h=20)
        return tower

Tower().display_split(show_object).export("stl/tower.step").export_split("stl/tower_split.step")
#show_object(Tower().part().section(cq.Plane.named("XZ")))
#show_object(cq.Workplane("XY").add(Tower().part().toCompound()).cut(cq.Workplane("XY").box(200,200,200, centered=[0,1,1])))
