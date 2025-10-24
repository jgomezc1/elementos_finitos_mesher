import sys
import os


import numpy as np
import preprocesor as msh
import meshio

mesh       = meshio.read("template.msh")
points     = mesh.points
cells      = mesh.cells
point_data = mesh.point_data
cell_data  = mesh.cell_data
nodes_array     = msh.node_writer(points , point_data)
nf , els1_array = msh.ele_writer(cells , cell_data , "triangle" , 100 , 3 , 0 , 0)
nini = nf
nf , els2_array = msh.ele_writer(cells , cell_data , "triangle" , 200 , 3 , 1 , nini)
els_array =np.append(els1_array , els2_array , axis = 0)
#
nodes_array = msh.boundary_conditions(cells , cell_data , 300 , nodes_array , -1 , 0)
nodes_array = msh.boundary_conditions(cells , cell_data , 400 , nodes_array , 0 , -1)
cargas      = msh.loading(cells , cell_data , 500 , 0.0 , -2.0)
np.savetxt("Meles.txt" , els_array   , fmt="%d")
np.savetxt("Mloads.txt", cargas, fmt=("%d", "%.6f", "%.6f"))
np.savetxt("Mnodes.txt", nodes_array , fmt=("%d", "%.4f", "%.4f", "%d", "%d"))