import classy_blocks as cb
#from classy_blocks.util import functions as f
import os
import numpy as np
import matplotlib.pyplot as plt


mesh = cb.Mesh()

cell_size = 5e-4 # Largest cell size
mesh_local = 4 # division by cellSize for chopping on cylinder surface

sphere_radius = 1e-3

tube_spacing = 4e-3 # x, y spacing between cylinder
XWidth = 1e-2 # domain width in X
YWidth = 1e-2 # domain width in Y


coordsX = np.arange(-XWidth/2, XWidth/2 + tube_spacing, tube_spacing)
coordsY = np.arange(-YWidth/2, YWidth/2 + tube_spacing, tube_spacing)
X, Y = np.meshgrid(coordsX, coordsY)
centers = np.column_stack([X.ravel(), Y.ravel()])
centers = np.column_stack([centers, np.zeros(centers.shape[0])])

fig, ax = plt.subplots()
ax.set_aspect('equal')

for x, y in centers[:, :2]:
    circle = plt.Circle((x, y), sphere_radius, color='blue', fill=False)
    ax.add_patch(circle)
plt.scatter(centers[:, 0], centers[:, 1], color="red")
plt.show()


corners= np.copy(centers)
corners[:, :2] =  corners[:, :2] + 0.5 * tube_spacing


def createTube(sphere_center, corner_point, sphere_radius=sphere_radius):
    one_core_disk = cb.WrappedDisk(sphere_center, corner_point, sphere_radius, [0, 0, 1])
    for face in one_core_disk.faces[5:]:
        face.add_edge(3, cb.Origin(sphere_center, flatness=1))
    cylinder = cb.ExtrudedShape(one_core_disk, sphere_radius)
    return cylinder


for center, corner in zip(centers, corners):
    cylinder = createTube(center, corner)
    for op in cylinder.operations[5:]:
        mesh.add(op)
        op.chop(0, start_size=cell_size/mesh_local) # Tangential chopping
        op.chop(1, start_size=cell_size/mesh_local, end_size=cell_size) # Radial chopping
        op.chop(2, count=1) # Axial chopping

   # cylinder.operations[5].chop(0, start_size=cell_size/mesh_local, end_size=cell_size) 


for op in mesh.operations:
  op.set_cell_zone("background")

mesh.set_default_patch("infinity", "patch")

grader = cb.SimpleGrader(mesh, cell_size)

mesh.write(os.path.join(r"blockMeshes", "blockMeshDict"), debug_path="debug.vtk")