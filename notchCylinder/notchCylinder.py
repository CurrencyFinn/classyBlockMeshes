### Rings around WP
import classy_blocks as cb
import os
import numpy as np

from classy_blocks.cbtyping import PointType, VectorType
from classy_blocks.construct.flat.face import Face
import classy_blocks as cb
from classy_blocks.util import functions as f
from classy_blocks.construct.operations.revolve import Revolve


mesh = cb.Mesh()

class WedgeUser(Revolve):

    def __init__(self, face: Face, angle: float, axis: VectorType, origin: PointType):

        # first, rotate this face forward, then use init this as Revolve
        # and rotate the same face
        base = face.copy().rotate(-angle / 2, axis, origin)

        super().__init__(base, angle, axis, origin)

        # assign 'wedge_left' and 'wedge_right' patches
        super().set_patch("top", "wedge_front")
        super().set_patch("bottom", "wedge_back")


class NotchedCylinder(cb.MappedSketch):
    quads = [
        [3, 0, 1, 4],
        [4, 1, 2, 5],
        [7, 4, 5, 8],
        [10, 7, 8, 11],
        [9, 6, 7, 10],
    ]

    ### Open to include chop class to do custom chopping
    
    def __init__(self, center: PointType, inner_radial: float, outer_radial : float, notch_radial: float, inner_axial : float, notch_axial: float, outer_axial: float):
        center = np.array(center, dtype=float)
        
        nPoints = max(max(row) for row in NotchedCylinder.quads) + 1
        points = np.broadcast_to(center, (nPoints, center.size)).copy()

        
        x_offset = 0
        y_offset = 0
        for i in range(4): # Go up in x
            for j in range(3): # Go down in y                
                index = i * 3 + j

                if (i == 0 or i == 1) and j == 0: # Inner notch
                    y_offset = inner_axial
                elif j == 0:
                    y_offset = 0
                elif j == 1:
                    y_offset = notch_axial
                else:
                    y_offset = outer_axial
                
                if i == 0:
                    x_offset = 0
                elif i == 1:
                    x_offset = -inner_radial
                elif i == 2:
                    x_offset = -notch_radial
                else:
                    x_offset = -outer_radial
                
                points[index] += f.vector(x_offset, y_offset, 0)
        print(points)

        super().__init__(points, NotchedCylinder.quads)


CELL_SIZE = 0.05
SWEEP_ANGLE = 0.5*np.pi
EXPORT_PATH = r"blockMeshes"

params = {
    "inner_radial": 0.3,
    "outer_radial": 2,
    "notch_radial": 0.4,
    "inner_axial": 0.3,
    "notch_axial": 0.5,
    "outer_axial": 2
}

inner_offset = -0.01 # closer to 0 for finer edge

base = NotchedCylinder([inner_offset, 0, 0], **params)

'''
Two options:
 - Create one object from sweep; difficulty chopping can be fixed with chops: ClassVar, see https://github.com/damogranlabs/classy_blocks/blob/d84424ccfeda1c79fe13abb023bea10003b8ac8b/examples/shape/custom.py#L14 
 - Create sweep from each face; possible easier for boundary assignment and grading
'''

# shape = cb.RevolvedShape(base, SWEEP_ANGLE, [0, 1, 0], [0.0, 0, 0]) # sweep shape
# shape.chop(2, count=20) # radial refinement
# mesh.add(shape)

for face in base.faces:
    shape = WedgeUser(face, SWEEP_ANGLE, [0, 1, 0], [0, 0, 0])
    shape.chop(2, count=20)
    mesh.add(shape)

mesh.assemble()

grader = cb.SimpleGrader(mesh, CELL_SIZE)
grader.grade(take="min")

mesh.set_default_patch("walls", "wall")

mesh.write(os.path.join(EXPORT_PATH, "blockMeshDict"), debug_path="debug.vtk")

