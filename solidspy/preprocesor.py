# -*- coding: utf-8 -*-
"""
Postprocessor subroutines
-------------------------

This module contains functions to preprocess the input files to compute
a Finite Element Analysis.

"""
from __future__ import absolute_import, division, print_function
import sys
import numpy as np


def readin(folder=""):
    """Read the input files"""
    nodes = np.loadtxt(folder + 'nodes.txt', ndmin=2)
    mats = np.loadtxt(folder + 'mater.txt', ndmin=2)
    elements = np.loadtxt(folder + 'eles.txt', ndmin=2, dtype=np.int)
    loads = np.loadtxt(folder + 'loads.txt', ndmin=2)

    return nodes, mats, elements, loads


def echomod(nodes, mats, elements, loads, folder=""):
    """Create echoes of the model input files"""
    np.savetxt(folder + "KNODES.txt", nodes, fmt='%5.2f', delimiter=' ')
    np.savetxt(folder + "KMATES.txt", mats, fmt='%5.2f', delimiter=' ')
    np.savetxt(folder + "KELEMS.txt", elements, fmt='%d', delimiter=' ')
    np.savetxt(folder + "KLOADS.txt", loads, fmt='%5.2f', delimiter=' ')


def initial_params():
    """Read initial parameters for the simulation

    The parameters to be read are:

    - folder: location of the input files.
    - name: name for the output files (if echo is True).
    - echo: echo output files.
    """
    # Check Python version
    version = sys.version_info.major
    if version == 3:
        global raw_input
        raw_input = input
    elif version == 2:
        pass
    else:
        raise ValueError("You should use Python 2.x at least!")

    # Try to run with easygui
    try:
        import easygui
        folder = easygui.diropenbox(title="Folder for the job") + "/"
    except:
        folder = raw_input('Enter folder (empty for the current one): ')

    return folder


def ele_writer(cells, cell_data, ele_tag, phy_sur,  ele_type, mat_tag, nini):
    """
    Extracts a subset of elements from a complete mesh according to the
    physical surface  phy_sur and writes down the proper fields into an
    elements array.

    Parameters
    ----------
        cell : dictionary or list
            Dictionary created by meshio with cells information (old API)
            or list of CellBlock objects (new API v4.0+).
        cell_data: dictionary
            Dictionary created by meshio with cells data information.
        ele_tag : string
            Element type according to meshio convention,
            e.g., quad9 or line3.
        phy_sur : int
            Physical surface for the subset.
        ele_type: int
            Element type.
        mat_tag : int
            Material profile for the subset.
        ndof : int
            Number of degrees of freedom for the elements.
        nnode : int
            Number of nodes for the element.
        nini : int
            Element id for the first element in the set.

    Returns
    -------
        nf : int
            Element id for the last element in the set
        els_array : int
            Elemental data.

    """
    dict_nnode = {'triangle': 3,
                  'triangle6': 6,
                  'quad': 4}
    nnode = dict_nnode[ele_tag]

    # Handle cell_data format (new meshio returns {data_name: [arrays]} format)
    if isinstance(cells, list):
        # New meshio format - search through ALL blocks of this element type
        all_elements = []
        for idx, cell_block in enumerate(cells):
            if cell_block.type == ele_tag:
                phy_surface = cell_data['gmsh:physical'][idx]
                eles = cell_block.data
                # Find elements in this block that match the physical surface
                ele_id = [cont for cont in range(len(phy_surface))
                          if phy_surface[cont] == phy_sur]
                if ele_id:  # If we found matching elements in this block
                    all_elements.append(eles[ele_id, :])

        if not all_elements:
            raise ValueError(f"Physical surface {phy_sur} not found in mesh for element type '{ele_tag}'")

        # Concatenate all matching elements from different blocks
        eles_matched = np.vstack(all_elements) if len(all_elements) > 1 else all_elements[0]

    else:
        # Old meshio format
        phy_surface = cell_data[ele_tag]['gmsh:physical']
        eles = cells[ele_tag]
        ele_id = [cont for cont, _ in enumerate(phy_surface[:])
                  if phy_surface[cont] == phy_sur]
        eles_matched = eles[ele_id, :]

    n_matched = len(eles_matched)
    els_array = np.zeros([n_matched , 3 + nnode], dtype=int)
    els_array[: , 0] = range(nini , n_matched + nini )
    els_array[: , 1] = ele_type
    els_array[: , 2] = mat_tag
    els_array[: , 3::] = eles_matched
    nf = nini + n_matched
    return nf , els_array


def node_writer(points , point_data):
    """Write nodal data as required by SolidsPy

    Parameters
    ----------
    points : dictionary
        Nodal points
    point_data : dictionary
        Physical data associatted to the nodes.

    Returns
    -------
    nodes_array : ndarray (int)
        Array with the nodal data according to SolidsPy.

    """
    nodes_array = np.zeros([points.shape[0], 5])
    nodes_array[:, 0] = range(points.shape[0])
    nodes_array[:, 1:3] = points[:, :2]
    return nodes_array


def boundary_conditions(cells, cell_data, phy_lin, nodes_array, bc_x, bc_y):
    """Impose nodal point boundary conditions as required by SolidsPy

    Parameters
    ----------
        cell : dictionary or list
            Dictionary created by meshio with cells information (old API)
            or list of CellBlock objects (new API v4.0+).
        cell_data: dictionary
            Dictionary created by meshio with cells data information.
        phy_lin : int
            Physical line where BCs are to be imposed.
        nodes_array : int
            Array with the nodal data and to be modified by BCs.
        bc_x, bc_y : int
            Boundary condition flag along the x and y direction:
                * -1: restrained
                * 0: free

    Returns
    -------
        nodes_array : int
            Array with the nodal data after imposing BCs according
            to SolidsPy.

    """
    # Handle cell_data format
    if isinstance(cells, list):
        # New meshio format - search through ALL line blocks
        nodes_frontera = []
        for idx, cell_block in enumerate(cells):
            if cell_block.type == "line":
                phy_line = cell_data['gmsh:physical'][idx]
                lines = cell_block.data
                # Find elements in this block that match the physical line
                id_frontera = [cont for cont in range(len(phy_line))
                              if phy_line[cont] == phy_lin]
                if id_frontera:  # If we found matching elements in this block
                    nodes_in_block = lines[id_frontera]
                    nodes_frontera.extend(nodes_in_block.flatten())

        if not nodes_frontera:
            raise ValueError(f"Physical line {phy_lin} not found in mesh")

        nodes_frontera = list(set(nodes_frontera))
    else:
        # Old meshio format
        lines = cells["line"]
        phy_line = cell_data["line"]["gmsh:physical"]
        id_frontera = [cont for cont in range(len(phy_line))
                       if phy_line[cont] == phy_lin]
        nodes_frontera = lines[id_frontera]
        nodes_frontera = nodes_frontera.flatten()
        nodes_frontera = list(set(nodes_frontera))

    nodes_array[nodes_frontera, 3] = bc_x
    nodes_array[nodes_frontera, 4] = bc_y
    return nodes_array


def loading(cells, cell_data, phy_lin, P_x, P_y, distribution='uniform', direction=None, nodes_array=None, variation_start='min'):
    """Impose nodal loads as required by SolidsPy

    Parameters
    ----------
        cell : dictionary or list
            Dictionary created by meshio with cells information (old API)
            or list of CellBlock objects (new API v4.0+).
        cell_data: dictionary
            Dictionary created by meshio with cells data information.
        phy_lin : int
            Physical line where loads are to be applied.
        P_x, P_y : float
            Load components in x and y directions (total for uniform, max for linear).
        distribution : str, optional
            Load distribution type: 'uniform' or 'linear'. Default: 'uniform'.
        direction : str, optional
            Direction of variation for linear loads: 'horizontal' (varies with x)
            or 'vertical' (varies with y). Required for linear distribution.
        nodes_array : ndarray, optional
            Array with nodal coordinates. Required for linear distribution.
        variation_start : str, optional
            Where the MAXIMUM load occurs: 'min' (at minimum coordinate) or 'max' (at maximum coordinate).
            Default: 'min'.
            For hydrostatic pressure on dam (Y=0 at bottom): use 'min' (max pressure at min Y = bottom).

    Returns
    -------
        cargas : ndarray
            Array with nodal loads in SolidsPy format [node_id, fx, fy].

    Notes
    -----
    For linear distribution:
    - Load varies linearly from 0 at one end to P_max at the other
    - Total resultant force = 0.5 * P_max * length (triangular distribution)
    - variation_start controls which end has the maximum load

    Examples
    --------
    >>> # Uniform load
    >>> loads = loading(cells, cell_data, phy_lin=100, P_x=0, P_y=-1000)

    >>> # Hydrostatic pressure (max at bottom = min Y)
    >>> loads = loading(cells, cell_data, phy_lin=100, P_x=-98100, P_y=0,
    ...                 distribution='linear', direction='vertical',
    ...                 variation_start='min', nodes_array=nodes)

    """
    # Validate inputs for linear distribution
    if distribution == 'linear':
        if direction is None:
            raise ValueError("direction must be specified for linear load distribution")
        if nodes_array is None:
            raise ValueError("nodes_array must be provided for linear load distribution")

    # Handle cell_data format to get nodes on the physical line
    if isinstance(cells, list):
        # New meshio format - search through ALL line blocks
        nodes_carga = []
        for idx, cell_block in enumerate(cells):
            if cell_block.type == "line":
                phy_line = cell_data['gmsh:physical'][idx]
                lines = cell_block.data
                # Find elements in this block that match the physical line
                id_carga = [cont for cont in range(len(phy_line))
                            if phy_line[cont] == phy_lin]
                if id_carga:  # If we found matching elements in this block
                    nodes_in_block = lines[id_carga]
                    nodes_carga.extend(nodes_in_block.flatten())

        if not nodes_carga:
            raise ValueError(f"Physical line {phy_lin} not found in mesh")

        nodes_carga = list(set(nodes_carga))
    else:
        # Old meshio format
        phy_line = cell_data["line"]["gmsh:physical"]
        lines = cells["line"]
        # Bounds contains data corresponding to the physical line.
        id_carga = [cont for cont in range(len(phy_line))
                    if phy_line[cont] == phy_lin]
        nodes_carga = lines[id_carga]
        nodes_carga = nodes_carga.flatten()
        nodes_carga = list(set(nodes_carga))

    ncargas = len(nodes_carga)
    cargas = np.zeros((ncargas, 3))
    cargas[:, 0] = nodes_carga

    if distribution == 'uniform':
        # Uniform distribution: divide total load equally
        cargas[:, 1] = P_x/ncargas
        cargas[:, 2] = P_y/ncargas

    elif distribution == 'linear':
        # Linear distribution: load varies from 0 to P_max
        # The loads (P_x and P_y) can vary with either X or Y coordinate position
        # Get node coordinates
        node_coords = nodes_array[nodes_carga, 1:3]  # [x, y] coordinates

        if direction == 'vertical':
            # Load magnitude varies with y-coordinate (e.g., hydrostatic pressure on vertical wall)
            # The load can be in X direction (pushing into wall) or Y direction (friction)
            y_coords = node_coords[:, 1]
            y_min = y_coords.min()
            y_max = y_coords.max()
            y_range = y_max - y_min

            if y_range < 1e-10:
                # Check if there's variation in X instead
                x_coords = node_coords[:, 0]
                x_range = x_coords.max() - x_coords.min()
                if x_range > 1e-10:
                    st_warning = (f"Warning: Line is nearly horizontal (y-range={y_range:.2e}m). "
                                 f"Consider using direction='horizontal' for better results.")
                    print(st_warning)
                    # Still allow it to proceed with small y variation
                    y_range = max(y_range, 1e-10)
                else:
                    raise ValueError(f"Cannot apply varying load on point (both x-range and y-range are zero)")

            # Normalize coordinates: normalized_coord = (Y - Y_min) / (Y_max - Y_min)
            # This gives: 0 at Y_min, 1 at Y_max
            normalized_coord = (y_coords - y_min) / y_range

            # variation_start controls where MAXIMUM load occurs:
            # - 'min': max load at minimum Y coordinate → reverse (1 at Y_min, 0 at Y_max)
            # - 'max': max load at maximum Y coordinate → don't reverse (0 at Y_min, 1 at Y_max)
            # For hydrostatic (Y=0 at bottom, Y=H at top): want max at bottom (Y_min), so use 'min'
            if variation_start == 'min':
                normalized_coord = 1.0 - normalized_coord

        elif direction == 'horizontal':
            # Load magnitude varies with x-coordinate (e.g., varying wind load)
            # The load can be in X direction or Y direction
            x_coords = node_coords[:, 0]
            x_min = x_coords.min()
            x_max = x_coords.max()
            x_range = x_max - x_min

            if x_range < 1e-10:
                # Check if there's variation in Y instead
                y_coords = node_coords[:, 1]
                y_range = y_coords.max() - y_coords.min()
                if y_range > 1e-10:
                    st_warning = (f"Warning: Line is nearly vertical (x-range={x_range:.2e}m). "
                                 f"Consider using direction='vertical' for better results.")
                    print(st_warning)
                    # Still allow it to proceed with small x variation
                    x_range = max(x_range, 1e-10)
                else:
                    raise ValueError(f"Cannot apply varying load on point (both x-range and y-range are zero)")

            # Normalize coordinates: normalized_coord = (X - X_min) / (X_max - X_min)
            # This gives: 0 at X_min, 1 at X_max
            normalized_coord = (x_coords - x_min) / x_range

            # variation_start controls where MAXIMUM load occurs:
            # - 'min': max load at minimum X coordinate → reverse (1 at X_min, 0 at X_max)
            # - 'max': max load at maximum X coordinate → don't reverse (0 at X_min, 1 at X_max)
            if variation_start == 'min':
                normalized_coord = 1.0 - normalized_coord

        else:
            raise ValueError(f"Invalid direction: {direction}. Must be 'horizontal' or 'vertical'")

        # Calculate load at each node (linearly varying)
        # Both P_x and P_y vary with the same pattern (normalized_coord)
        # normalized_coord ranges from 0 to 1 based on position and variation_start setting
        #
        # For triangular load distribution:
        # - If variation_start='min': load = P_max at min coord, 0 at max coord (e.g., hydrostatic on dam)
        # - If variation_start='max': load = 0 at min coord, P_max at max coord
        #
        # Total resultant = 0.5 * P_max * length
        cargas[:, 1] = P_x * normalized_coord / ncargas
        cargas[:, 2] = P_y * normalized_coord / ncargas

    else:
        raise ValueError(f"Invalid distribution type: {distribution}. Must be 'uniform' or 'linear'")

    return cargas


def rect_grid(length, height, nx, ny, eletype=None):
    """Generate a structured mesh for a rectangle

    The coordinates of the nodes will be defined in the
    domain [-length/2, length/2] x [-height/2, height/2].

    Parameters
    ----------
        length : float
            Length of the domain.
        height : gloat
            Height of the domain.
        nx : int
            Number of elements in the x direction.
        ny : int
            Number of elements in the y direction.
        eletype : None
            It does nothing right now.

    Returns
    -------
        x : ndarray (float)
            x-coordinates for the nodes.
        y : ndarray (float)
            y-coordinates for the nodes.
        els : ndarray
            Array with element data.

    Examples
    --------

    >>> x, y, els = rect_grid(2, 2, 2, 2)
    >>> x
    array([-1.,  0.,  1., -1.,  0.,  1., -1.,  0.,  1.])
    >>> y
    array([-1., -1., -1.,  0.,  0.,  0.,  1.,  1.,  1.])
    >>> els
    array([[0, 1, 0, 0, 1, 4, 3],
           [1, 1, 0, 1, 2, 5, 4],
           [2, 1, 0, 3, 4, 7, 6],
           [3, 1, 0, 4, 5, 8, 7]])

    """
    y, x = np.mgrid[-height/2:height/2:(ny + 1)*1j,
                    -length/2:length/2:(nx + 1)*1j]
    els = np.zeros((nx*ny, 7), dtype=int)
    els[:, 1] = 1
    for row in range(ny):
        for col in range(nx):
            cont = row*nx + col
            els[cont, 0] = cont
            els[cont, 3:7] = [cont + row, cont + row + 1,
                              cont + row + nx + 2, cont + row + nx + 1]
    return x.flatten(), y.flatten(), els


if __name__ == "__main__":
    import doctest
    doctest.testmod()
