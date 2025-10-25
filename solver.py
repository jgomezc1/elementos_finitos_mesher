import sys
import os
source_code_path = os.path.join(os.getcwd(), "..", "solidspy")
sys.path.append(source_code_path)

import numpy as np
import sympy as sym
import assemutil as ass
import postprocesor as pos
import solutil as sol

def readin():
    nodes    = np.loadtxt('output/' + 'pilnodes.txt', ndmin=2)
    mats     = np.loadtxt('output/' + 'pilmater.txt', ndmin=2)
    elements = np.loadtxt('output/' + 'pileles.txt', ndmin=2, dtype=int)
    loads    = np.loadtxt('output/' + 'pilloads.txt', ndmin=2)

    return nodes, mats, elements, loads


nodes, mats, elements, loads = readin()                                 # Read the model
DME , IBC , neq = ass.DME(nodes, elements)                              # Creathe the assembly operator
KG = ass.assembler(elements, mats, nodes, neq, DME)                     # Assembly the global stiffness matrix
RHSG = ass.loadasem(loads, IBC, neq)                                    # Assembly the loads vector
UG = sol.static_sol(KG, RHSG)                                           # Solve the system of equations in the unknown d.o.f UG
UC = pos.complete_disp(IBC, nodes, UG)                                  # Form a completed displacements vector once the unknowns are found
E_nodes, S_nodes = pos.strain_nodes(nodes , elements, mats, UC)         # Compute strains and stresses
pos.fields_plot(elements, nodes, UC, E_nodes=E_nodes, S_nodes=S_nodes)  # Plot the main fields