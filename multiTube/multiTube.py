import classy_blocks as cb
from classy_blocks.util import functions as f
import os
import numpy as np
import matplotlib.pyplot as plt


mesh = cb.Mesh()

cell_size = 5e-4 # Largest cell size
mesh_local = 4 # division by cellSize for chopping on cylinder surface

sphere_radius = 1e-3


tube_spacing = 4e-3 # x, y spacing between cylinder
ROutside = 1e-2

sphere_outer_center = (0, 0, 0)
sphere_outer_rim = (ROutside, ROutside, 0)

XWidth = np.sqrt(2) * ROutside # domain width in X
YWidth = XWidth # domain width in Y

n_max = int(np.floor(ROutside / tube_spacing))

coordsX = np.arange(0, (n_max+1)*tube_spacing, tube_spacing)
coordsY = np.arange(0, (n_max+1)*tube_spacing, tube_spacing)
coordsX = np.concatenate([-coordsX[1:][::-1], coordsX])  
coordsY = np.concatenate([-coordsY[1:][::-1], coordsY])
X, Y = np.meshgrid(coordsX, coordsY)

centers = np.column_stack([X.ravel(), Y.ravel()])
distances = np.sqrt(centers[:, 0]**2 + centers[:, 1]**2)
mask = distances + np.sqrt(2) * 0.5 * tube_spacing < ROutside # 0.5 here is the additional spacing so mesh optimization can work with it
centers = centers[mask]
centers = np.column_stack([centers, np.zeros(centers.shape[0])])

distances = np.linalg.norm(centers, axis=1)
max_distance = np.max(distances)
tol = tube_spacing / 2
outer_indices = np.where(distances >= max_distance - tol)[0]
outer_centers = centers[outer_indices]

fig, ax = plt.subplots()
ax.set_aspect('equal')

for x, y in centers[:, :2]:
    circle = plt.Circle((x, y), sphere_radius, color='blue', fill=False)
    ax.add_patch(circle)

circle = plt.Circle((0, 0), ROutside, color='green', fill=False)
ax.add_patch(circle)
plt.scatter(centers[:, 0], centers[:, 1], color="red")
plt.scatter(outer_centers[:, 0], outer_centers[:, 1], color="orange")
plt.show()


corners= np.copy(centers)
corners[:, :2] =  corners[:, :2] + 0.5 * tube_spacing


def createTube(sphere_center, corner_point, sphere_radius=sphere_radius, is_outer=False):
    one_core_disk = cb.WrappedDisk(sphere_center, corner_point, sphere_radius, [0, 0, 1])
    for i, face in enumerate(one_core_disk.faces[5:]):
        face.add_edge(3, cb.Origin(sphere_center, flatness=1))
        
        if is_outer: # only select outer faces
            outerFacePoints = face.points.copy()  # Nx3
            
            for point in outerFacePoints:
                polarPoint = f.to_polar(point.position, axis="z")
                if polarPoint[0] >= n_max/2 * np.sqrt(2) * tube_spacing:  #  little extra - 1 * tube_spacing
                    polarPoint[0] = ROutside
                    movedOutPoint = f.to_cartesian(polarPoint, axis="z", direction=1)
                    point.move_to(movedOutPoint)
                    

    cylinder = cb.ExtrudedShape(one_core_disk, sphere_radius)
    return cylinder


for i, (center, corner) in enumerate(zip(centers, corners)):
    is_outer = i in outer_indices
    cylinder = createTube(center, corner, is_outer=is_outer)
    for op in cylinder.operations[5:]:
        mesh.add(op)
        op.chop(0, start_size=cell_size/mesh_local) # Tangential chopping
        op.chop(1, start_size=cell_size/mesh_local, end_size=cell_size) # Radial chopping
        op.chop(2, count=1) # Axial chopping

   # cylinder.operations[5].chop(0, start_size=cell_size/mesh_local, end_size=cell_size) 

grader = cb.SimpleGrader(mesh, cell_size)
grader.grade()


for op in mesh.operations:
  op.set_cell_zone("background")

mesh.set_default_patch("infinity", "patch")

mesh.write(os.path.join(r"blockMeshes", "blockMeshDict"), debug_path="debug.vtk")