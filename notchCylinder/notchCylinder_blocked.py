import classy_blocks as cb
import os
import numpy as np

from classy_blocks.util import functions as f
from classy_blocks.construct.flat.sketches.disk import QuarterDisk


def extrudeRingFace(Face, thickness, direction=0):

    outerFacePoints = Face.point_array   
    movedOutFacePoints = np.empty_like(outerFacePoints)
    for i, point in enumerate(outerFacePoints):
        polarPoint = f.to_polar(point, axis="z")
        polarPoint[direction] = thickness 
        movedOutFacePoints[i] = f.to_cartesian(polarPoint, axis="z", direction=1)
    
    movedOutFace = cb.Face(movedOutFacePoints)

    movedOutFace.add_edge(1, cb.Origin((0, 0, params["notch_axial"]), flatness=1))
    movedOutFace.add_edge(3, cb.Origin((0, 0, params["outer_axial"]), flatness=1))

    extrudedQuarter = cb.Loft(Face, movedOutFace)
    

    return extrudedQuarter, movedOutFace

def extrudeAxialFace(Face, thickness, direction=0):

    outerFacePoints = Face.point_array   
    movedOutFacePoints = np.empty_like(outerFacePoints)

    for i, point in enumerate(outerFacePoints):
        point[direction] = thickness 
        movedOutFacePoints[i] = point
    
    movedOutFace = cb.Face(movedOutFacePoints)

    movedOutFace.add_edge(1, cb.Origin((0, 0, 0), flatness=1))
    movedOutFace.add_edge(3, cb.Origin((0, 0, 0), flatness=1))

    extrudedAxial = cb.Loft(Face, movedOutFace)
    
    return extrudedAxial, movedOutFace



def extrudeQuarter(Quarter, thickness):
    extrudedQuarters = []
    extrudedFaces = []

    for op in Quarter.shell:
        front_face = op.get_face("right")

        extrudedQuarter, extrudedFace = extrudeRingFace(front_face, thickness)

        extrudedQuarters.append(extrudedQuarter)
        extrudedFaces.append(extrudedFace)
    
    return extrudedQuarters, extrudedFaces

mesh = cb.Mesh()
CELL_SIZE = 0.05
SWEEP_ANGLE = 0.5*np.pi
EXPORT_PATH = r"\\wsl.localhost\Ubuntu\home\finn\foam\finn-5.0\run\test_coils\system"

params = {
    "inner_radial": 0.3,
    "outer_radial": 2,
    "notch_radial": 0.5,
    "inner_axial": 0.3,
    "notch_axial": 0.5,
    "outer_axial": 2
}

# inner two stacked cylinder

QuarterDisk.core_ratio = 0.4


outerQuarter = cb.QuarterCylinder([0, 0, params["inner_axial"]], [0, 0, params["notch_axial"]], [params["inner_radial"], params["inner_radial"], params["inner_axial"]]) 

mesh.add(outerQuarter)

innerQuarter = cb.QuarterCylinder([0, 0, params["notch_axial"]], [0, 0, params["outer_axial"]], [params["inner_radial"], params["inner_radial"], params["notch_axial"]]) 

mesh.add(innerQuarter)

outerQuarter.chop_tangential(start_size=CELL_SIZE/2)
innerQuarter.chop_tangential(start_size=CELL_SIZE/2)

outerQuarter.chop_radial(start_size=CELL_SIZE/1.5)
innerQuarter.chop_radial(start_size=CELL_SIZE/1.5)

extrudedQuartersNotch, extrudedFacesNotch = extrudeQuarter(innerQuarter, params["notch_radial"])

for extrudedQuarterNotch, extrudedFaceNotch in zip(extrudedQuartersNotch, extrudedFacesNotch):
    
    mesh.add(extrudedQuarterNotch)
    extrudedQuarterNotch.chop(2, start_size=CELL_SIZE/2)

    extrudedQuartersOuter, _ = extrudeRingFace(extrudedFaceNotch, params["outer_radial"])
    mesh.add(extrudedQuartersOuter)

    outerRing, _ = extrudeAxialFace(extrudedQuartersOuter.get_face("right"), 0, direction=2)
    mesh.add(outerRing)
    outerRing.chop(0, start_size=CELL_SIZE, end_size=CELL_SIZE/2)





mesh.assemble()

grader = cb.SimpleGrader(mesh, CELL_SIZE)
grader.grade(take="min")

mesh.set_default_patch("walls", "wall")

mesh.write(os.path.join(EXPORT_PATH, "blockMeshDict"), debug_path="debug.vtk")

