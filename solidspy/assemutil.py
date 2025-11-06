# -*- coding: utf-8 -*-
"""
Assembly routines
-----------------

Functions to assemble the system of equations for the Finite Element
Analysis.

"""
from __future__ import absolute_import, division, print_function
import numpy as np
from scipy.sparse import coo_matrix
import uelutil as ue
import femutil as fem


def eqcounter(nodes):
    """Counts active equations and creates BCs array IBC

    Parameters
    ----------
    nodes : ndarray
      Array with nodes coordinates and boundary conditions.

    Returns
    -------
    neq : int
      Number of equations in the system after removing the nodes
      with imposed displacements.
    IBC : ndarray (int)
      Array that maps the nodes with number of equations.

    """
    nnodes = nodes.shape[0]
    IBC = np.zeros([nnodes, 2], dtype=np.integer)
    for i in range(nnodes):
        for k in range(2):
            IBC[i , k] = int(nodes[i , k+3])
    neq = 0
    for i in range(nnodes):
        for j in range(2):
            if IBC[i, j] == 0:
                IBC[i, j] = neq
                neq = neq + 1

    return neq, IBC


def DME(nodes, elements):
    """Counts active equations, creates BCs array IBC[]
    and the assembly operator DME[]

    Parameters
    ----------
    nodes    : ndarray.
      Array with the nodal numbers and coordinates.
    elements : ndarray
      Array with the number for the nodes in each element.

    Returns
    -------
    DME : ndarray (int)
      Assembly operator.
    IBC : ndarray (int)
      Boundary conditions array.
    neq : int
      Number of active equations in the system.

    """
    nels = elements.shape[0]
    IELCON = np.zeros([nels, 9], dtype=np.integer)
    DME = np.zeros([nels, 18], dtype=np.integer)

    neq, IBC = eqcounter(nodes)

    for i in range(nels):
        iet = elements[i, 1]
        ndof, nnodes, ngpts = fem.eletype(iet)
        for j in range(nnodes):
            IELCON[i, j] = elements[i, j+3]
            kk = IELCON[i, j]
            for l in range(2):
                DME[i, 2*j+l] = IBC[kk, l]

    return DME , IBC , neq


def retriever(elements , mats , nodes , i, uel=None):
    """Computes the elemental stiffness matrix of element i

    Parameters
    ----------
    elements : ndarray
      Array with the number for the nodes in each element.
    mats    : ndarray.
      Array with the material profiles.
    nodes    : ndarray.
      Array with the nodal numbers and coordinates.
    i    : int.
      Identifier of the element to be assembled.

    Returns
    -------
    kloc : ndarray (float)
      Array with the local stiffness matrix.
    ndof : int.
      Number of degrees of fredom of the current element.
    """
    IELCON = np.zeros([9], dtype=np.integer)
    iet = elements[i, 1]
    ndof, nnodes, ngpts = fem.eletype(iet)
    elcoor = np.zeros([nnodes, 2])
    im = int(elements[i, 2])
    par0, par1 = mats[im, 0], mats[im, 1]  # Extract only E and nu (ignore density if present)
    for j in range(nnodes):
        IELCON[j] = elements[i, j+3]
        elcoor[j, 0] = nodes[IELCON[j], 1]
        elcoor[j, 1] = nodes[IELCON[j], 2]
    if uel is None:
        if iet == 1:
            kloc = ue.uel4nquad(elcoor, par1, par0)
        elif iet == 2:
            kloc = ue.uel6ntrian(elcoor, par1, par0)
        elif iet == 3:
            kloc = ue.uel3ntrian(elcoor, par1, par0)
        elif iet == 5:
            kloc = ue.uelspring(elcoor, par1, par0)
        elif iet == 6:
            kloc = ue.ueltruss2D(elcoor, par1, par0)
        elif iet == 7:
            kloc = ue.uelbeam2DU(elcoor, par1, par0)
        elif iet == 8:
        	kloc = ue.uel8nquad(elcoor, par1, par0)
    else:
        kloc, ndof, iet = uel(elcoor, par1, par0)

    return kloc, ndof, iet


def assembler(elements, mats, nodes, neq, DME, sparse=True, uel=None):
    """Assembles the global stiffness matrix

    Parameters
    ----------
    elements : ndarray (int)
      Array with the number for the nodes in each element.
    mats    : ndarray (float)
      Array with the material profiles.
    nodes    : ndarray (float)
      Array with the nodal numbers and coordinates.
    DME  : ndarray (int)
      Assembly operator.
    neq : int
      Number of active equations in the system.
    sparse : boolean (optional)
      Boolean variable to pick sparse assembler. It is True
      by default.
    uel : callable function (optional)
      Python function that returns the local stiffness matrix.

    Returns
    -------
    KG : ndarray (float)
      Array with the global stiffness matrix. It might be
      dense or sparse, depending on the value of _sparse_

    """
    if sparse:
        KG = sparse_assem(elements, mats, nodes, neq, DME, uel=uel)
    else:
        KG = dense_assem(elements, mats, nodes, neq, DME, uel=uel)

    return KG


def dense_assem(elements, mats, nodes, neq, DME, uel=None):
    """
    Assembles the global stiffness matrix _KG_
    using a dense storing scheme

    Parameters
    ----------
    elements : ndarray (int)
      Array with the number for the nodes in each element.
    mats    : ndarray (float)
      Array with the material profiles.
    nodes    : ndarray (float)
      Array with the nodal numbers and coordinates.
    DME  : ndarray (int)
      Assembly operator.
    neq : int
      Number of active equations in the system.
    uel : callable function (optional)
      Python function that returns the local stiffness matrix.

    Returns
    -------
    KG : ndarray (float)
      Array with the global stiffness matrix in a dense numpy
      array.

    """
    KG = np.zeros((neq, neq))
    nels = elements.shape[0]
    for el in range(nels):
        kloc, ndof, iet  = retriever(elements, mats, nodes, el, uel=uel)
        dme = DME[el, :ndof]
        for row in range(ndof):
            glob_row = dme[row]
            if glob_row != -1:
                for col in range(ndof):
                    glob_col = dme[col]
                    if glob_col != -1:
                        KG[glob_row, glob_col] = KG[glob_row, glob_col] +\
                                                 kloc[row, col]

    return KG


def sparse_assem(elements, mats, nodes, neq, DME, uel=None):
    """
    Assembles the global stiffness matrix _KG_
    using a sparse storing scheme

    The scheme used to assemble is COOrdinate list (COO), and
    it converted to Compressed Sparse Row (CSR) afterward
    for the solution phase [1]_.

    Parameters
    ----------
    elements : ndarray (int)
      Array with the number for the nodes in each element.
    mats    : ndarray (float)
      Array with the material profiles.
    nodes    : ndarray (float)
      Array with the nodal numbers and coordinates.
    DME  : ndarray (int)
      Assembly operator.
    neq : int
      Number of active equations in the system.
    uel : callable function (optional)
      Python function that returns the local stiffness matrix.

    Returns
    -------
    KG : ndarray (float)
      Array with the global stiffness matrix in a sparse
      Compressed Sparse Row (CSR) format.

    References
    ----------
    .. [1] Sparse matrix. (2017, March 8). In Wikipedia,
        The Free Encyclopedia.
        https://en.wikipedia.org/wiki/Sparse_matrix

    """
    rows = []
    cols = []
    vals = []
    nels = elements.shape[0]
    for el in range(nels):
        kloc, ndof, iet  = retriever(elements , mats  , nodes , el, uel=uel)
        dme = DME[el, :ndof]

        for row in range(ndof):
            glob_row = dme[row]
            if glob_row != -1:
                for col in range(ndof):
                    glob_col = dme[col]
                    if glob_col != -1:
                        rows.append(glob_row)
                        cols.append(glob_col)
                        vals.append(kloc[row, col])

    return coo_matrix((vals, (rows, cols)), shape=(neq, neq)).tocsr()


def loadasem(loads, IBC, neq):
    """Assembles the global Right Hand Side Vector RHSG

    Parameters
    ----------
    loads : ndarray
      Array with the loads imposed in the system.
    IBC : ndarray (int)
      Array that maps the nodes with number of equations.
    neq : int
      Number of equations in the system after removing the nodes
      with imposed displacements.

    Returns
    -------
    RHSG : ndarray
      Array with the right hand side vector.

    """
    nloads = loads.shape[0]
    RHSG = np.zeros([neq])
    for i in range(nloads):
        il = int(loads[i, 0])
        ilx = IBC[il, 0]
        ily = IBC[il, 1]
        if ilx != -1:
            RHSG[ilx] = loads[i, 1]
        if ily != -1:
            RHSG[ily] = loads[i, 2]

    return RHSG


def body_force_assembler(elements, mats, nodes, neq, DME, grav_x=0.0, grav_y=-9.81):
    """
    Assembles the body force vector due to gravity or acceleration.

    This function computes equivalent nodal forces from body forces
    (gravity, acceleration) applied to the elements. It assumes triangular
    elements and distributes the force based on element area and material density.

    Parameters
    ----------
    elements : ndarray (int)
        Array with the number for the nodes in each element.
        Format: [ele_id, ele_type, mat_id, node1, node2, node3, ...]
    mats : ndarray (float)
        Array with the material profiles.
        Format: [E, nu, density] where density is mass per unit volume.
        If density column is missing, assumes zero density (no body forces).
    nodes : ndarray (float)
        Array with the nodal coordinates.
        Format: [node_id, x, y, bc_x, bc_y]
    neq : int
        Number of active equations in the system.
    DME : ndarray (int)
        Assembly operator (Degrees of freedom mapping for elements).
    grav_x : float, optional
        Gravity/acceleration in x-direction (m/s²). Default: 0.0
    grav_y : float, optional
        Gravity/acceleration in y-direction (m/s²). Default: -9.81

    Returns
    -------
    RHSG_body : ndarray
        Body force vector (right-hand side contribution).

    Notes
    -----
    - For 2D plane stress/strain, body force per unit volume is: f = ρ * g
    - The force is distributed to element nodes using consistent formulation
    - For triangular elements, centroid-based distribution is used
    - Element area is computed from nodal coordinates

    Examples
    --------
    >>> # Apply gravity in y-direction with density in materials array
    >>> body_forces = body_force_assembler(elements, mats, nodes, neq, DME,
    ...                                     grav_x=0.0, grav_y=-9.81)
    >>> # Add to total load vector
    >>> RHSG_total = RHSG_applied + body_forces

    """
    RHSG_body = np.zeros(neq)
    nels = elements.shape[0]

    # Check if density information is available
    if mats.shape[1] < 3:
        # No density information, return zero vector
        return RHSG_body

    for el in range(nels):
        # Get material ID for this element
        mat_id = int(elements[el, 2])

        # Get material density (third column in mats array)
        if mat_id < len(mats):
            density = mats[mat_id, 2]
        else:
            density = 0.0

        # Skip if no density
        if density == 0.0:
            continue

        # Get element type
        ele_type = int(elements[el, 1])

        # Get node indices for this element (columns 3 onwards)
        if ele_type == 1:  # Linear triangle (3 nodes)
            node_indices = elements[el, 3:6].astype(int)
            nnodes = 3
        elif ele_type == 2:  # Linear quadrilateral (4 nodes)
            node_indices = elements[el, 3:7].astype(int)
            nnodes = 4
        elif ele_type == 3:  # Quadratic triangle (6 nodes)
            node_indices = elements[el, 3:9].astype(int)
            nnodes = 6
        else:
            continue  # Unsupported element type

        # Get nodal coordinates
        verts = nodes[node_indices, 1:3]

        # Calculate element area
        if nnodes == 3:  # Triangle
            # Area = 0.5 * |det([[x1, y1, 1], [x2, y2, 1], [x3, y3, 1]])|
            area = 0.5 * abs(np.linalg.det(np.column_stack((verts, np.ones(3)))))
        elif nnodes == 4:  # Quadrilateral (approximate)
            # Split into two triangles and sum
            area1 = 0.5 * abs(np.linalg.det(np.column_stack((verts[[0,1,2], :], np.ones(3)))))
            area2 = 0.5 * abs(np.linalg.det(np.column_stack((verts[[0,2,3], :], np.ones(3)))))
            area = area1 + area2
        elif nnodes == 6:  # Quadratic triangle (use corner nodes)
            area = 0.5 * abs(np.linalg.det(np.column_stack((verts[[0,1,2], :], np.ones(3)))))
        else:
            continue

        # Body force per unit volume
        force_x_vol = density * grav_x
        force_y_vol = density * grav_y

        # Total force on element
        total_force_x = force_x_vol * area
        total_force_y = force_y_vol * area

        # Distribute equally to nodes (simplified consistent approach)
        force_per_node_x = total_force_x / nnodes
        force_per_node_y = total_force_y / nnodes

        # Assemble into global force vector
        dme = DME[el, :nnodes*2]
        for i in range(nnodes):
            # x-direction DOF
            glob_dof_x = dme[2*i]
            if glob_dof_x != -1:
                RHSG_body[glob_dof_x] += force_per_node_x

            # y-direction DOF
            glob_dof_y = dme[2*i + 1]
            if glob_dof_y != -1:
                RHSG_body[glob_dof_y] += force_per_node_y

    return RHSG_body


if __name__ == "__main__":
    import doctest
    doctest.testmod()
