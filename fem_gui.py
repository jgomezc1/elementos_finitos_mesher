#!/usr/bin/env python3
"""
SolidsPy based FEM Builder - Streamlit GUI
-------------------------------------------

Interactive web interface for creating finite element models.

Usage:
    streamlit run fem_gui.py
"""
import streamlit as st
import yaml
import numpy as np
from pathlib import Path
import tempfile
import os
import subprocess
import sys

# Add SolidsPy to path
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
solidspy_path = os.path.join(script_dir, "solidspy")
if os.path.exists(solidspy_path):
    sys.path.insert(0, solidspy_path)
else:
    # Fallback: try using current working directory
    solidspy_path_cwd = os.path.join(os.getcwd(), "solidspy")
    if os.path.exists(solidspy_path_cwd):
        sys.path.insert(0, solidspy_path_cwd)

from fem_config import FEMConfig
from fem_converter import FEMConverter
from fem_templates import RectangularPlate, LayeredPlate, LShapeBeam, PlateWithHole

# SolidsPy imports (will be used for solver)
SOLIDSPY_AVAILABLE = False
SOLIDSPY_ERROR = None
try:
    import assemutil as ass
    import postprocesor as pos
    import solutil as sol
    SOLIDSPY_AVAILABLE = True
except ImportError as e:
    SOLIDSPY_AVAILABLE = False
    SOLIDSPY_ERROR = str(e)
except Exception as e:
    SOLIDSPY_AVAILABLE = False
    SOLIDSPY_ERROR = f"Unexpected error: {str(e)}"


# Page configuration
st.set_page_config(
    page_title="SolidsPy based FEM Builder",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 4rem !important;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'model_created' not in st.session_state:
        st.session_state.model_created = False
    if 'yaml_content' not in st.session_state:
        st.session_state.yaml_content = None
    if 'conversion_complete' not in st.session_state:
        st.session_state.conversion_complete = False


def geometry_preview(geometry_type):
    """Show ASCII art preview of geometry"""
    previews = {
        "rectangle": """
        ┌─────────────────┐
        │                 │
        │   Rectangle     │
        │                 │
        └─────────────────┘
        """,
        "layered_plate": """
        ┌─────────────────┐
        │   Material 2    │  ← Upper Layer
        ├─────────────────┤
        │   Material 1    │  ← Lower Layer
        └─────────────────┘
        """,
        "lshape": """
        ┌───────┐
        │       │
        │       │  ← Vertical Flange
        ├───┐   │
        │   │   │
        │   └───┘
        │       │  ← Horizontal Flange
        └───────┘
        """,
        "plate_with_hole": """
        ┌─────────────────┐
        │                 │
        │       ●         │  ← Circular Hole
        │                 │
        └─────────────────┘
        """
    }
    st.code(previews.get(geometry_type, ""), language="")


def create_geometry_params(geometry_type):
    """Create parameter inputs based on geometry type"""
    st.markdown('<p class="section-header">📐 Geometry Parameters</p>', unsafe_allow_html=True)

    params = {}

    if geometry_type == "rectangle":
        col1, col2 = st.columns(2)
        with col1:
            params['length'] = st.number_input("Length (m)", min_value=0.1, value=2.0, step=0.1)
        with col2:
            params['height'] = st.number_input("Height (m)", min_value=0.1, value=1.0, step=0.1)

    elif geometry_type == "layered_plate":
        col1, col2 = st.columns(2)
        with col1:
            params['length'] = st.number_input("Length (m)", min_value=0.1, value=2.0, step=0.1)
        with col2:
            params['height'] = st.number_input("Height (m)", min_value=0.1, value=1.0, step=0.1)

    elif geometry_type == "lshape":
        col1, col2 = st.columns(2)
        with col1:
            params['width'] = st.number_input("Total Width (m)", min_value=0.1, value=3.0, step=0.1)
            params['flange_width'] = st.number_input("Horizontal Flange Width (m)", min_value=0.1, value=1.0, step=0.1)
        with col2:
            params['height'] = st.number_input("Total Height (m)", min_value=0.1, value=3.0, step=0.1)
            params['flange_height'] = st.number_input("Vertical Flange Height (m)", min_value=0.1, value=1.0, step=0.1)

    elif geometry_type == "plate_with_hole":
        col1, col2 = st.columns(2)
        with col1:
            params['length'] = st.number_input("Plate Length (m)", min_value=0.1, value=4.0, step=0.1)
            params['height'] = st.number_input("Plate Height (m)", min_value=0.1, value=2.0, step=0.1)
        with col2:
            params['hole_x'] = st.number_input("Hole Center X (m)", min_value=0.0, value=2.0, step=0.1)
            params['hole_y'] = st.number_input("Hole Center Y (m)", min_value=0.0, value=1.0, step=0.1)
            params['hole_radius'] = st.number_input("Hole Radius (m)", min_value=0.01, value=0.3, step=0.05)

    return params


def create_material_inputs(geometry_type):
    """Create material property inputs"""
    st.markdown('<p class="section-header">🔧 Material Properties</p>', unsafe_allow_html=True)

    materials = []

    if geometry_type == "layered_plate":
        st.info("📚 Multi-layer configuration")
        num_layers = st.number_input("Number of Layers", min_value=1, max_value=10, value=2, step=1)

        for i in range(num_layers):
            st.markdown(f"**Layer {i+1}**")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                name = st.text_input(f"Name", value=f"layer_{i+1}", key=f"layer_name_{i}")
            with col2:
                y_min = st.number_input(f"Y min (m)", value=float(i/num_layers), step=0.1, key=f"y_min_{i}", format="%.3f")
            with col3:
                y_max = st.number_input(f"Y max (m)", value=float((i+1)/num_layers), step=0.1, key=f"y_max_{i}", format="%.3f")
            with col4:
                physical_id = st.number_input(f"Physical ID", value=i+1, step=1, key=f"phys_id_{i}")

            col1, col2 = st.columns(2)
            with col1:
                E = st.number_input(f"Young's Modulus (Pa)", value=1.0e6*(i+1), format="%.2e", key=f"E_{i}")
            with col2:
                nu = st.number_input(f"Poisson's Ratio", min_value=0.0, max_value=0.49, value=0.3, step=0.01, key=f"nu_{i}", format="%.3f")

            materials.append({
                'name': name,
                'region': [y_min, y_max],
                'physical_id': physical_id,
                'E': E,
                'nu': nu
            })
            st.divider()

    else:
        # Single material
        col1, col2 = st.columns(2)
        with col1:
            E = st.number_input("Young's Modulus (Pa)", value=2.1e11, format="%.2e")
        with col2:
            nu = st.number_input("Poisson's Ratio", min_value=0.0, max_value=0.49, value=0.3, step=0.01, format="%.3f")

        materials = {'E': E, 'nu': nu}

    return materials


def create_bc_inputs():
    """Create boundary condition inputs"""
    st.markdown('<p class="section-header">🔒 Boundary Conditions</p>', unsafe_allow_html=True)

    num_bcs = st.number_input("Number of Boundary Conditions", min_value=0, max_value=10, value=2, step=1)

    bcs = []
    for i in range(num_bcs):
        st.markdown(f"**BC {i+1}**")
        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input("Name", value=f"bc_{i+1}", key=f"bc_name_{i}")
            location = st.selectbox(
                "Location",
                ["left", "right", "top", "bottom"],
                key=f"bc_location_{i}"
            )

        with col2:
            physical_id = st.number_input("Physical ID", value=100+i, step=1, key=f"bc_phys_id_{i}")
            x_constraint = st.selectbox("X Constraint", ["free", "fixed"], key=f"bc_x_{i}")

        with col3:
            st.write("")  # Spacer
            st.write("")  # Spacer
            y_constraint = st.selectbox("Y Constraint", ["free", "fixed"], key=f"bc_y_{i}")

        bcs.append({
            'name': name,
            'location': location,
            'physical_id': physical_id,
            'constraints': {'x': x_constraint, 'y': y_constraint}
        })
        st.divider()

    return bcs


def create_load_inputs():
    """Create load inputs"""
    st.markdown('<p class="section-header">⚡ Loads</p>', unsafe_allow_html=True)

    num_loads = st.number_input("Number of Loads", min_value=0, max_value=10, value=1, step=1)

    loads = []
    for i in range(num_loads):
        st.markdown(f"**Load {i+1}**")
        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input("Name", value=f"load_{i+1}", key=f"load_name_{i}")
            location = st.selectbox(
                "Location",
                ["left", "right", "top", "bottom"],
                key=f"load_location_{i}"
            )

        with col2:
            physical_id = st.number_input("Physical ID", value=200+i, step=1, key=f"load_phys_id_{i}")
            fx = st.number_input("Force X (N)", value=0.0, format="%.2f", key=f"load_fx_{i}")

        with col3:
            st.write("")  # Spacer
            fy = st.number_input("Force Y (N)", value=-1000.0, format="%.2f", key=f"load_fy_{i}")

        loads.append({
            'name': name,
            'location': location,
            'physical_id': physical_id,
            'force': {'x': fx, 'y': fy},
            'distribution': 'uniform'
        })
        st.divider()

    return loads


def create_mesh_inputs():
    """Create mesh parameter inputs"""
    st.markdown('<p class="section-header">🔲 Mesh Settings</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        mesh_size = st.number_input("Mesh Size (m)", min_value=0.001, value=0.1, step=0.01, format="%.3f")
        element_type = st.selectbox("Element Type", ["triangle", "triangle6", "quad"], index=0)

    with col2:
        use_algorithm = st.checkbox("Specify Mesh Algorithm", value=False)
        algorithm = None
        if use_algorithm:
            algorithm = st.number_input("Algorithm (1-9)", min_value=1, max_value=9, value=6, step=1)

    return {
        'size': mesh_size,
        'element_type': element_type,
        'algorithm': algorithm
    }


def build_yaml_config(model_name, description, geometry_type, geom_params, materials, bcs, loads, mesh_params):
    """Build YAML configuration dictionary"""
    config = {
        'model_name': model_name,
        'description': description,
        'geometry': {
            'type': geometry_type,
            **geom_params
        },
        'mesh': mesh_params
    }

    # Add materials or layers
    if geometry_type == "layered_plate":
        config['layers'] = [
            {
                'name': mat['name'],
                'region': mat['region'],
                'physical_id': mat['physical_id'],
                'material': {'E': mat['E'], 'nu': mat['nu']}
            }
            for mat in materials
        ]
    else:
        config['material'] = materials

    # Add boundary conditions
    if bcs:
        config['boundary_conditions'] = bcs

    # Add loads
    if loads:
        config['loads'] = loads

    return config


def calculate_reaction_forces(nodes_array, elements_array, materials_array,
                             UC, loads_array, DME, IBC, neq):
    """
    Calculate reaction forces at constrained nodes.

    Parameters
    ----------
    nodes_array : ndarray
        Nodes array with boundary conditions
    elements_array : ndarray
        Elements array
    materials_array : ndarray
        Materials array
    UC : ndarray
        Complete displacement vector
    loads_array : ndarray
        Applied loads array
    DME : ndarray
        Assembly operator
    IBC : ndarray
        Boundary conditions indicator
    neq : int
        Number of equations

    Returns
    -------
    reactions : ndarray
        Reaction forces array (N x 3): [node_id, Rx, Ry]
    """
    # Total number of DOFs
    n_nodes = len(nodes_array)
    n_dof = 2 * n_nodes

    # Assemble full stiffness matrix (including constrained DOFs)
    # We need the full matrix to compute reactions
    KG_full = ass.assembler(elements_array, materials_array, nodes_array, n_dof, DME)

    # Flatten displacement vector
    U_full = UC.flatten()

    # Calculate internal forces: F_internal = K * U
    F_internal = KG_full @ U_full

    # Create applied loads vector
    F_applied = np.zeros(n_dof)
    if loads_array is not None and len(loads_array) > 0:
        for load in loads_array:
            node_id = int(load[0])
            F_applied[2*node_id] = load[1]      # Fx
            F_applied[2*node_id + 1] = load[2]  # Fy

    # Reaction forces = Internal forces - Applied forces
    F_reaction = F_internal - F_applied

    # Extract reactions at constrained nodes only
    reaction_list = []
    for i, node in enumerate(nodes_array):
        node_id = int(node[0])
        bc_x = int(node[3])
        bc_y = int(node[4])

        # If either DOF is constrained, this node has reactions
        if bc_x == -1 or bc_y == -1:
            Rx = F_reaction[2*i] if bc_x == -1 else 0.0
            Ry = F_reaction[2*i + 1] if bc_y == -1 else 0.0
            reaction_list.append([node_id, Rx, Ry])

    if reaction_list:
        return np.array(reaction_list)
    else:
        return np.array([[0, 0, 0]])  # No reactions


def run_solidspy_solver(nodes_array, elements_array, materials_array, loads_array):
    """
    Run SolidsPy FEA solver on the generated mesh.

    Parameters
    ----------
    nodes_array : ndarray
        Nodes array (N x 5): [node_id, x, y, bc_x, bc_y]
    elements_array : ndarray
        Elements array (M x 7+): [ele_id, ele_type, mat_id, node1, node2, ...]
    materials_array : ndarray
        Materials array (K x 3): [E, nu, density]
    loads_array : ndarray or None
        Loads array (L x 3): [node_id, fx, fy]

    Returns
    -------
    dict
        Results dictionary containing:
        - 'success': bool
        - 'displacements': ndarray (completed displacements UC)
        - 'strains': ndarray (strains at nodes)
        - 'stresses': ndarray (stresses at nodes)
        - 'nodes': ndarray (nodes for plotting)
        - 'elements': ndarray (elements for plotting)
        - 'max_displacement': float
        - 'max_stress': float
        - 'error': str (if failed)
    """
    if not SOLIDSPY_AVAILABLE:
        return {
            'success': False,
            'error': 'SolidsPy modules not available. Check solidspy folder.'
        }

    try:
        # Step 1: Create assembly operator
        DME, IBC, neq = ass.DME(nodes_array, elements_array)

        # Step 2: Assemble global stiffness matrix
        KG = ass.assembler(elements_array, materials_array, nodes_array, neq, DME)

        # Step 3: Assemble loads vector
        if loads_array is None or len(loads_array) == 0:
            loads_array = np.zeros((1, 3))
        RHSG = ass.loadasem(loads_array, IBC, neq)

        # Step 4: Solve system of equations
        UG = sol.static_sol(KG, RHSG)

        # Step 5: Complete displacements vector
        UC = pos.complete_disp(IBC, nodes_array, UG)

        # Step 6: Compute strains and stresses at nodes
        E_nodes, S_nodes = pos.strain_nodes(nodes_array, elements_array, materials_array, UC)

        # Step 7: Calculate reaction forces at constrained nodes
        # Reaction forces = K * U - F_applied at constrained DOFs
        reactions = calculate_reaction_forces(nodes_array, elements_array, materials_array,
                                             UC, loads_array, DME, IBC, neq)

        # Calculate summary statistics
        max_disp = np.max(np.abs(UC))
        max_stress = np.max(np.abs(S_nodes))

        return {
            'success': True,
            'displacements': UC,
            'strains': E_nodes,
            'stresses': S_nodes,
            'nodes': nodes_array,
            'elements': elements_array,
            'reactions': reactions,
            'loads_array': loads_array,
            'max_displacement': max_disp,
            'max_stress': max_stress,
            'neq': neq
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def create_interactive_contour_plot(nodes, elements, field_values, title, colorbar_title, height=700):
    """
    Create an interactive Plotly contour plot for FEM results.

    Parameters
    ----------
    nodes : ndarray
        Nodes array with coordinates
    elements : ndarray
        Elements array with connectivity
    field_values : ndarray
        Field values at nodes (1D array)
    title : str
        Plot title
    colorbar_title : str
        Label for colorbar
    height : int
        Plot height in pixels

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure
    """
    import plotly.graph_objects as go

    # Extract coordinates
    x = nodes[:, 1]
    y = nodes[:, 2]

    # Get element connectivity (triangles)
    # Elements format: [id, type, mat_id, node1, node2, node3, ...]
    # For triangles: columns 3, 4, 5 are the node indices
    triangles = elements[:, 3:6].astype(int)

    # Create triangulation-based contour plot
    fig = go.Figure(data=go.Mesh3d(
        x=x,
        y=y,
        z=np.zeros_like(x),  # 2D mesh
        i=triangles[:, 0],
        j=triangles[:, 1],
        k=triangles[:, 2],
        intensity=field_values,
        colorscale='RdYlBu_r',
        colorbar=dict(
            title=dict(text=colorbar_title, side='right'),
            tickformat='.2e',
            thickness=20,
            len=0.7
        ),
        hovertemplate='<b>Value</b>: %{intensity:.3e}<br>' +
                      '<b>X</b>: %{x:.3f}<br>' +
                      '<b>Y</b>: %{y:.3f}<br>' +
                      '<extra></extra>',
        showscale=True
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        scene=dict(
            xaxis=dict(title='X', showgrid=False),
            yaxis=dict(title='Y', showgrid=False),
            zaxis=dict(showticklabels=False, showgrid=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=0, z=2.5),
                up=dict(x=0, y=1, z=0),  # Y-axis points up
                center=dict(x=0, y=0, z=0),
                projection=dict(type='orthographic')
            )
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='closest'
    )

    return fig


def create_filtered_contour_plot(nodes, elements, field_values, title, colorbar_title, threshold=None, threshold_type='above', height=700):
    """
    Create an interactive Plotly contour plot with binary threshold filtering.
    Regions exceeding threshold shown in red, safe regions in gray.

    Parameters
    ----------
    nodes : ndarray
        Nodes array with coordinates
    elements : ndarray
        Elements array with connectivity
    field_values : ndarray
        Field values at nodes (1D array)
    title : str
        Plot title
    colorbar_title : str
        Label for colorbar
    threshold : float, optional
        Threshold value for filtering
    threshold_type : str
        'above' to highlight values above threshold, 'below' for below threshold
    height : int
        Plot height in pixels

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure
    stats : dict
        Statistics about threshold exceedance
    """
    import plotly.graph_objects as go

    # Extract coordinates
    x = nodes[:, 1]
    y = nodes[:, 2]

    # Get element connectivity (triangles)
    triangles = elements[:, 3:6].astype(int)

    # Apply binary threshold filtering
    stats = {}

    if threshold is not None:
        if threshold_type == 'above':
            mask = field_values >= threshold

            stats['exceeding_nodes'] = np.sum(mask)
            stats['total_nodes'] = len(field_values)
            stats['percentage'] = (stats['exceeding_nodes'] / stats['total_nodes']) * 100
            stats['threshold'] = threshold
            stats['type'] = 'above'
        else:  # 'below'
            mask = field_values <= threshold

            stats['exceeding_nodes'] = np.sum(mask)
            stats['total_nodes'] = len(field_values)
            stats['percentage'] = (stats['exceeding_nodes'] / stats['total_nodes']) * 100
            stats['threshold'] = threshold
            stats['type'] = 'below'

        # Compute per-triangle status (if ANY vertex exceeds, mark the triangle as exceeding)
        triangle_exceeds = []
        for tri in triangles:
            # Check if any vertex of this triangle exceeds the threshold
            if np.any(mask[tri]):
                triangle_exceeds.append('red')
            else:
                triangle_exceeds.append('lightgray')

        # Create mesh with per-face coloring
        fig = go.Figure(data=go.Mesh3d(
            x=x,
            y=y,
            z=np.zeros_like(x),
            i=triangles[:, 0],
            j=triangles[:, 1],
            k=triangles[:, 2],
            facecolor=triangle_exceeds,  # Use facecolor for per-triangle coloring
            hovertemplate='<b>X</b>: %{x:.3f}<br><b>Y</b>: %{y:.3f}<br><extra></extra>',
            showscale=False,  # No colorbar needed for categorical colors
            flatshading=True  # No interpolation between vertices
        ))

        # Add a custom legend
        # Add dummy traces for legend
        fig.add_trace(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode='markers',
            marker=dict(size=10, color='red'),
            name=f'Exceeds {threshold/1e6:.1f} MPa',
            showlegend=True
        ))
        fig.add_trace(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode='markers',
            marker=dict(size=10, color='lightgray'),
            name='Within Limit',
            showlegend=True
        ))

        # Add title with threshold info
        plot_title = f"{title} - Limit: {threshold/1e6:.2f} MPa"
    else:
        # No threshold - use regular continuous color scale
        fig = go.Figure(data=go.Mesh3d(
            x=x,
            y=y,
            z=np.zeros_like(x),
            i=triangles[:, 0],
            j=triangles[:, 1],
            k=triangles[:, 2],
            intensity=field_values,
            colorscale='RdYlBu_r',
            colorbar=dict(
                title=dict(text=colorbar_title, side='right'),
                tickformat='.2e',
                thickness=20,
                len=0.7
            ),
            hovertemplate='<b>Value</b>: %{intensity:.3e}<br>' +
                          '<b>X</b>: %{x:.3f}<br>' +
                          '<b>Y</b>: %{y:.3f}<br>' +
                          '<extra></extra>',
            showscale=True
        ))
        plot_title = title

    fig.update_layout(
        title=dict(text=plot_title, x=0.5, xanchor='center'),
        scene=dict(
            xaxis=dict(title='X', showgrid=False),
            yaxis=dict(title='Y', showgrid=False),
            zaxis=dict(showticklabels=False, showgrid=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=0, z=2.5),
                up=dict(x=0, y=1, z=0),  # Y-axis points up
                center=dict(x=0, y=0, z=0),
                projection=dict(type='orthographic')
            )
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='closest'
    )

    return fig, stats


def create_deformed_configuration_plot(nodes, elements, displacements, scale_factor=1.0, height=700):
    """
    Create an interactive plot showing deformed and undeformed configurations.

    Parameters
    ----------
    nodes : ndarray
        Nodes array with original coordinates (N x 5): [node_id, x, y, bc_x, bc_y]
    elements : ndarray
        Elements array with connectivity (M x 7+): [ele_id, ele_type, mat_id, node1, node2, ...]
    displacements : ndarray
        Displacement array (N x 2): [ux, uy] for each node
    scale_factor : float
        Scale factor to amplify displacements for visualization (default: 1.0)
    height : int
        Plot height in pixels

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure with original and deformed meshes
    """
    import plotly.graph_objects as go

    # Extract original coordinates
    x_orig = nodes[:, 1]
    y_orig = nodes[:, 2]

    # Compute deformed coordinates
    x_def = x_orig + scale_factor * displacements[:, 0]
    y_def = y_orig + scale_factor * displacements[:, 1]

    # Compute displacement magnitude
    disp_mag = np.sqrt(displacements[:, 0]**2 + displacements[:, 1]**2)

    # Get element connectivity (triangles)
    triangles = elements[:, 3:6].astype(int)

    # Create figure with two meshes
    fig = go.Figure()

    # Add original mesh (gray, semi-transparent)
    fig.add_trace(go.Mesh3d(
        x=x_orig,
        y=y_orig,
        z=np.zeros_like(x_orig),
        i=triangles[:, 0],
        j=triangles[:, 1],
        k=triangles[:, 2],
        color='lightgray',
        opacity=0.3,
        name='Original',
        showlegend=True,
        hoverinfo='skip',
        flatshading=True
    ))

    # Add deformed mesh (colored by displacement magnitude)
    fig.add_trace(go.Mesh3d(
        x=x_def,
        y=y_def,
        z=np.zeros_like(x_def),
        i=triangles[:, 0],
        j=triangles[:, 1],
        k=triangles[:, 2],
        intensity=disp_mag,
        colorscale='Plasma',
        colorbar=dict(
            title=dict(text='Displacement<br>Magnitude (m)', side='right'),
            tickformat='.2e',
            thickness=20,
            len=0.7
        ),
        name='Deformed',
        showlegend=True,
        hovertemplate='<b>Displacement</b>: %{intensity:.3e} m<br>' +
                      '<b>X</b>: %{x:.3f}<br>' +
                      '<b>Y</b>: %{y:.3f}<br>' +
                      '<extra></extra>',
        showscale=True
    ))

    fig.update_layout(
        title=dict(
            text=f'Deformed Configuration (Scale Factor: {scale_factor}x)',
            x=0.5,
            xanchor='center'
        ),
        scene=dict(
            xaxis=dict(title='X', showgrid=True, gridcolor='lightgray'),
            yaxis=dict(title='Y', showgrid=True, gridcolor='lightgray'),
            zaxis=dict(showticklabels=False, showgrid=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=0, z=2.5),
                up=dict(x=0, y=1, z=0),
                center=dict(x=0, y=0, z=0),
                projection=dict(type='orthographic')
            )
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='closest',
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='gray',
            borderwidth=1
        )
    )

    return fig


def create_reaction_forces_plot(nodes, elements, reactions, loads_array=None, height=700):
    """
    Create a plot showing reaction forces as vector arrows on the mesh.

    Parameters
    ----------
    nodes : ndarray
        Nodes array with coordinates
    elements : ndarray
        Elements array with connectivity
    reactions : ndarray
        Reactions array (N x 3): [node_id, Rx, Ry]
    loads_array : ndarray or None
        Applied loads array (M x 3): [node_id, Fx, Fy]
    height : int
        Plot height in pixels

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure showing reactions
    """
    import plotly.graph_objects as go

    # Extract coordinates
    x = nodes[:, 1]
    y = nodes[:, 2]

    # Get element connectivity
    triangles = elements[:, 3:6].astype(int)

    # Create figure with mesh
    fig = go.Figure()

    # Add mesh (semi-transparent)
    fig.add_trace(go.Mesh3d(
        x=x,
        y=y,
        z=np.zeros_like(x),
        i=triangles[:, 0],
        j=triangles[:, 1],
        k=triangles[:, 2],
        color='lightblue',
        opacity=0.3,
        name='Mesh',
        showlegend=True,
        hoverinfo='skip',
        flatshading=True
    ))

    # Calculate arrow scaling
    max_reaction = np.max(np.abs(reactions[:, 1:])) if len(reactions) > 0 else 1.0
    coords = nodes[:, 1:3]
    char_length = max(np.max(coords[:, 0]) - np.min(coords[:, 0]),
                     np.max(coords[:, 1]) - np.min(coords[:, 1]))
    arrow_scale = 0.1 * char_length / max_reaction if max_reaction > 0 else 0.1 * char_length

    # Add reaction force arrows
    for reaction in reactions:
        node_id = int(reaction[0])
        Rx = reaction[1]
        Ry = reaction[2]

        # Get node coordinates
        node_x = nodes[node_id, 1]
        node_y = nodes[node_id, 2]

        # Draw arrow if reaction is non-zero
        if abs(Rx) > 1e-10 or abs(Ry) > 1e-10:
            # Arrow endpoint
            end_x = node_x + Rx * arrow_scale
            end_y = node_y + Ry * arrow_scale

            # Arrow line
            fig.add_trace(go.Scatter3d(
                x=[node_x, end_x],
                y=[node_y, end_y],
                z=[0, 0],
                mode='lines+markers',
                line=dict(color='red', width=6),
                marker=dict(size=[4, 8], color='red', symbol=['circle', 'diamond']),
                name=f'Reaction {node_id}',
                showlegend=False,
                hovertemplate=f'<b>Node {node_id}</b><br>' +
                             f'Rx: {Rx:.3e} N<br>' +
                             f'Ry: {Ry:.3e} N<br>' +
                             '<extra></extra>'
            ))

    # Add applied load arrows if provided
    if loads_array is not None and len(loads_array) > 0:
        max_load = np.max(np.abs(loads_array[:, 1:]))
        load_arrow_scale = 0.1 * char_length / max_load if max_load > 0 else 0.1 * char_length

        for load in loads_array:
            node_id = int(load[0])
            Fx = load[1]
            Fy = load[2]

            if abs(Fx) > 1e-10 or abs(Fy) > 1e-10:
                node_x = nodes[node_id, 1]
                node_y = nodes[node_id, 2]

                # Arrow starts away from node (load is applied TO the node)
                start_x = node_x - Fx * load_arrow_scale
                start_y = node_y - Fy * load_arrow_scale

                fig.add_trace(go.Scatter3d(
                    x=[start_x, node_x],
                    y=[start_y, node_y],
                    z=[0, 0],
                    mode='lines+markers',
                    line=dict(color='green', width=6),
                    marker=dict(size=[8, 4], color='green', symbol=['diamond', 'circle']),
                    name=f'Load {node_id}',
                    showlegend=False,
                    hovertemplate=f'<b>Node {node_id}</b><br>' +
                                 f'Fx: {Fx:.3e} N<br>' +
                                 f'Fy: {Fy:.3e} N<br>' +
                                 '<extra></extra>'
                ))

    fig.update_layout(
        title=dict(
            text='Reaction Forces and Applied Loads',
            x=0.5,
            xanchor='center'
        ),
        scene=dict(
            xaxis=dict(title='X', showgrid=True, gridcolor='lightgray'),
            yaxis=dict(title='Y', showgrid=True, gridcolor='lightgray'),
            zaxis=dict(showticklabels=False, showgrid=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=0, z=2.5),
                up=dict(x=0, y=1, z=0),
                center=dict(x=0, y=0, z=0),
                projection=dict(type='orthographic')
            )
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='closest'
    )

    return fig


def calculate_principal_stress_directions(stresses):
    """
    Calculate principal stress directions at each node.

    Parameters
    ----------
    stresses : ndarray
        Stress array (N x 3): [σxx, σyy, τxy]

    Returns
    -------
    dict
        Dictionary containing:
        - 'sigma_1': Maximum principal stress
        - 'sigma_2': Minimum principal stress
        - 'theta_1': Angle of σ₁ direction (radians)
        - 'theta_2': Angle of σ₂ direction (radians)
        - 'dir_1_x': X-component of σ₁ direction unit vector
        - 'dir_1_y': Y-component of σ₁ direction unit vector
        - 'dir_2_x': X-component of σ₂ direction unit vector
        - 'dir_2_y': Y-component of σ₂ direction unit vector
    """
    sigma_xx = stresses[:, 0]
    sigma_yy = stresses[:, 1]
    tau_xy = stresses[:, 2]

    # Calculate principal stresses
    sigma_avg = (sigma_xx + sigma_yy) / 2
    R = np.sqrt(((sigma_xx - sigma_yy) / 2)**2 + tau_xy**2)

    sigma_1 = sigma_avg + R  # Maximum principal stress
    sigma_2 = sigma_avg - R  # Minimum principal stress

    # Calculate principal directions
    # θ = 0.5 * atan2(2*τxy, σxx - σyy)
    theta_1 = 0.5 * np.arctan2(2 * tau_xy, sigma_xx - sigma_yy)
    theta_2 = theta_1 + np.pi / 2  # Perpendicular to σ₁

    # Direction unit vectors
    dir_1_x = np.cos(theta_1)
    dir_1_y = np.sin(theta_1)
    dir_2_x = np.cos(theta_2)
    dir_2_y = np.sin(theta_2)

    return {
        'sigma_1': sigma_1,
        'sigma_2': sigma_2,
        'theta_1': theta_1,
        'theta_2': theta_2,
        'dir_1_x': dir_1_x,
        'dir_1_y': dir_1_y,
        'dir_2_x': dir_2_x,
        'dir_2_y': dir_2_y
    }


def create_principal_stress_trajectories_plot(nodes, elements, stresses, height=700, show_mode='both'):
    """
    Create a plot showing principal stress trajectories as arrows.

    Parameters
    ----------
    nodes : ndarray
        Nodes array with coordinates
    elements : ndarray
        Elements array with connectivity
    stresses : ndarray
        Stress array (N x 3): [σxx, σyy, τxy]
    height : int
        Plot height in pixels
    show_mode : str
        'sigma_1', 'sigma_2', or 'both' to show which trajectories

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure showing stress trajectories
    """
    import plotly.graph_objects as go

    # Extract coordinates
    x = nodes[:, 1]
    y = nodes[:, 2]

    # Get element connectivity
    triangles = elements[:, 3:6].astype(int)

    # Calculate principal stress directions
    principal = calculate_principal_stress_directions(stresses)

    # For coloring the mesh, use Von Mises or max principal when showing both
    if show_mode == 'both':
        # Color by Von Mises stress for neutral background
        sigma_xx = stresses[:, 0]
        sigma_yy = stresses[:, 1]
        tau_xy = stresses[:, 2]
        mesh_intensity = np.sqrt(sigma_xx**2 - sigma_xx*sigma_yy + sigma_yy**2 + 3*tau_xy**2)
        title_text = "Principal Stress Trajectories (σ₁ and σ₂ - Perpendicular)"
        color_title = "Von Mises (Pa)"
    elif show_mode == 'sigma_1':
        mesh_intensity = principal['sigma_1']
        title_text = "Principal Stress Trajectories (σ₁ - Maximum)"
        color_title = "σ₁ (Pa)"
    else:  # sigma_2
        mesh_intensity = principal['sigma_2']
        title_text = "Principal Stress Trajectories (σ₂ - Minimum)"
        color_title = "σ₂ (Pa)"

    # Create figure with mesh
    fig = go.Figure()

    # Add mesh colored by stress
    fig.add_trace(go.Mesh3d(
        x=x,
        y=y,
        z=np.zeros_like(x),
        i=triangles[:, 0],
        j=triangles[:, 1],
        k=triangles[:, 2],
        intensity=mesh_intensity,
        colorscale='RdYlBu_r',
        colorbar=dict(
            title=dict(text=color_title, side='right'),
            tickformat='.2e',
            thickness=20,
            len=0.7
        ),
        hoverinfo='skip',
        showscale=True,
        opacity=0.6 if show_mode == 'both' else 0.7
    ))

    # Calculate arrow scaling
    coords = nodes[:, 1:3]
    char_length = max(np.max(coords[:, 0]) - np.min(coords[:, 0]),
                     np.max(coords[:, 1]) - np.min(coords[:, 1]))
    arrow_length = char_length * 0.03  # Fixed arrow length for direction

    # Downsample nodes for clearer visualization
    n_nodes = len(nodes)
    skip = max(1, n_nodes // 300)  # Show ~300 arrows max

    # Add direction arrows at sampled nodes
    if show_mode in ['sigma_1', 'both']:
        # Add σ₁ trajectories (orange/red)
        for i in range(0, n_nodes, skip):
            start_x = x[i] - principal['dir_1_x'][i] * arrow_length / 2
            start_y = y[i] - principal['dir_1_y'][i] * arrow_length / 2
            end_x = x[i] + principal['dir_1_x'][i] * arrow_length / 2
            end_y = y[i] + principal['dir_1_y'][i] * arrow_length / 2

            fig.add_trace(go.Scatter3d(
                x=[start_x, end_x],
                y=[start_y, end_y],
                z=[0, 0],
                mode='lines',
                line=dict(color='orangered', width=3),
                showlegend=(i == 0 and show_mode == 'both'),
                name='σ₁ direction',
                legendgroup='sigma1',
                hoverinfo='skip'
            ))

    if show_mode in ['sigma_2', 'both']:
        # Add σ₂ trajectories (cyan/blue)
        for i in range(0, n_nodes, skip):
            start_x = x[i] - principal['dir_2_x'][i] * arrow_length / 2
            start_y = y[i] - principal['dir_2_y'][i] * arrow_length / 2
            end_x = x[i] + principal['dir_2_x'][i] * arrow_length / 2
            end_y = y[i] + principal['dir_2_y'][i] * arrow_length / 2

            fig.add_trace(go.Scatter3d(
                x=[start_x, end_x],
                y=[start_y, end_y],
                z=[0, 0],
                mode='lines',
                line=dict(color='cyan', width=3),
                showlegend=(i == 0 and show_mode == 'both'),
                name='σ₂ direction',
                legendgroup='sigma2',
                hoverinfo='skip'
            ))

    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center'
        ),
        scene=dict(
            xaxis=dict(title='X', showgrid=True, gridcolor='lightgray'),
            yaxis=dict(title='Y', showgrid=True, gridcolor='lightgray'),
            zaxis=dict(showticklabels=False, showgrid=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=0, z=2.5),
                up=dict(x=0, y=1, z=0),
                center=dict(x=0, y=0, z=0),
                projection=dict(type='orthographic')
            )
        ),
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='closest',
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='gray',
            borderwidth=1
        ) if show_mode == 'both' else None
    )

    return fig


def verify_equilibrium(reactions, loads_array, nodes):
    """
    Verify global equilibrium: ΣFx = 0, ΣFy = 0, ΣM = 0

    Parameters
    ----------
    reactions : ndarray
        Reactions array (N x 3): [node_id, Rx, Ry]
    loads_array : ndarray or None
        Applied loads array (M x 3): [node_id, Fx, Fy]
    nodes : ndarray
        Nodes array with coordinates

    Returns
    -------
    dict
        Dictionary with equilibrium check results
    """
    # Sum of reaction forces
    sum_Rx = np.sum(reactions[:, 1])
    sum_Ry = np.sum(reactions[:, 2])

    # Sum of applied loads
    sum_Fx = 0.0
    sum_Fy = 0.0
    if loads_array is not None and len(loads_array) > 0:
        sum_Fx = np.sum(loads_array[:, 1])
        sum_Fy = np.sum(loads_array[:, 2])

    # Total force balance
    total_Fx = sum_Rx + sum_Fx
    total_Fy = sum_Ry + sum_Fy

    # Moment balance about origin (ΣM = Σ(x*Fy - y*Fx))
    sum_M_reactions = 0.0
    for reaction in reactions:
        node_id = int(reaction[0])
        x = nodes[node_id, 1]
        y = nodes[node_id, 2]
        Rx = reaction[1]
        Ry = reaction[2]
        sum_M_reactions += (x * Ry - y * Rx)

    sum_M_loads = 0.0
    if loads_array is not None and len(loads_array) > 0:
        for load in loads_array:
            node_id = int(load[0])
            x = nodes[node_id, 1]
            y = nodes[node_id, 2]
            Fx = load[1]
            Fy = load[2]
            sum_M_loads += (x * Fy - y * Fx)

    total_M = sum_M_reactions + sum_M_loads

    return {
        'sum_Fx': total_Fx,
        'sum_Fy': total_Fy,
        'sum_M': total_M,
        'reaction_Fx': sum_Rx,
        'reaction_Fy': sum_Ry,
        'applied_Fx': sum_Fx,
        'applied_Fy': sum_Fy,
        'balanced': (abs(total_Fx) < 1e-6 and abs(total_Fy) < 1e-6 and abs(total_M) < 1e-6)
    }


def display_solver_results(results):
    """
    Display SolidsPy solver results in Streamlit with interactive Plotly visualizations.

    Parameters
    ----------
    results : dict
        Results dictionary from run_solidspy_solver
    """
    if not results['success']:
        st.error(f"❌ Solver Error: {results['error']}")
        return

    st.success("✅ Analysis Complete!")

    # Results summary
    st.markdown("---")
    st.markdown('<p class="section-header">📊 Results Summary</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Nodes", len(results['nodes']))
        st.metric("Total Elements", len(results['elements']))
    with col2:
        st.metric("Total DOFs", results['neq'])
        st.metric("Max Displacement", f"{results['max_displacement']:.3e} m")
    with col3:
        st.metric("Max Stress", f"{results['max_stress']:.3e} Pa")
        st.metric("Max Stress (MPa)", f"{results['max_stress']/1e6:.2f}")

    # Visualization
    st.markdown("---")
    st.markdown('<p class="section-header">📈 Interactive Visualization</p>', unsafe_allow_html=True)

    st.info("💡 Hover over plots to see values | Drag to rotate | Scroll to zoom")

    try:
        # Extract data
        nodes = results['nodes']
        elements = results['elements']
        disp = results['displacements']
        strains = results['strains']
        stresses = results['stresses']

        # Compute displacement magnitude
        disp_mag = np.sqrt(disp[:, 0]**2 + disp[:, 1]**2)

        # Create tabs for different result types
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔵 Displacements", "🟢 Strains", "🔴 Stresses", "🟣 Principal Stresses", "⚖️ Reactions"])

        with tab1:
            st.markdown("### Displacement Fields")

            # Sub-tabs for displacement components
            subtab1, subtab2, subtab3, subtab4 = st.tabs(["Magnitude", "X-Component", "Y-Component", "Deformed Shape"])

            with subtab1:
                fig = create_interactive_contour_plot(
                    nodes, elements, disp_mag,
                    "Displacement Magnitude",
                    "Displacement (m)",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab2:
                fig = create_interactive_contour_plot(
                    nodes, elements, disp[:, 0],
                    "Horizontal Displacement (ux)",
                    "ux (m)",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab3:
                fig = create_interactive_contour_plot(
                    nodes, elements, disp[:, 1],
                    "Vertical Displacement (uy)",
                    "uy (m)",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab4:
                st.markdown("#### Deformed Configuration")
                st.info("💡 Adjust the scale factor to amplify the deformation for better visualization")

                # Get max displacement for intelligent default scaling
                max_disp = results['max_displacement']

                # Compute characteristic dimension (to suggest reasonable scale factors)
                coords = nodes[:, 1:3]
                x_range = np.max(coords[:, 0]) - np.min(coords[:, 0])
                y_range = np.max(coords[:, 1]) - np.min(coords[:, 1])
                characteristic_length = max(x_range, y_range)

                # Suggest scale factor: make max displacement ~5-10% of characteristic length
                if max_disp > 0:
                    suggested_scale = (0.05 * characteristic_length) / max_disp
                    # Round to nice values
                    magnitude = 10 ** np.floor(np.log10(suggested_scale))
                    suggested_scale = np.round(suggested_scale / magnitude) * magnitude
                else:
                    suggested_scale = 1.0

                # Display max displacement info
                st.metric("Maximum Displacement", f"{max_disp:.3e} m")
                st.metric("Suggested Scale Factor", f"{suggested_scale:.1f}x")

                # Scale factor slider
                scale_factor = st.slider(
                    "Deformation Scale Factor",
                    min_value=0.0,
                    max_value=float(suggested_scale * 5),
                    value=float(suggested_scale),
                    step=float(suggested_scale / 20) if suggested_scale > 0 else 1.0,
                    format="%.1f",
                    key="deformation_scale_slider",
                    help="Multiplier to amplify displacements for visualization. Does not affect computed values."
                )

                # Create deformed configuration plot
                fig = create_deformed_configuration_plot(
                    nodes, elements, disp,
                    scale_factor=scale_factor,
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

                st.caption(f"🔍 Gray mesh: Original configuration | Colored mesh: Deformed configuration (scale: {scale_factor}x)")

        with tab2:
            st.markdown("### Strain Fields")

            # Sub-tabs for strain components
            subtab1, subtab2, subtab3 = st.tabs(["ε-xx", "ε-yy", "γ-xy"])

            with subtab1:
                fig = create_interactive_contour_plot(
                    nodes, elements, strains[:, 0],
                    "Normal Strain (ε-xx)",
                    "ε-xx",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab2:
                fig = create_interactive_contour_plot(
                    nodes, elements, strains[:, 1],
                    "Normal Strain (ε-yy)",
                    "ε-yy",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab3:
                fig = create_interactive_contour_plot(
                    nodes, elements, strains[:, 2],
                    "Shear Strain (γ-xy)",
                    "γ-xy",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.markdown("### Stress Fields")

            # Compute von Mises stress
            sigma_xx = stresses[:, 0]
            sigma_yy = stresses[:, 1]
            tau_xy = stresses[:, 2]
            von_mises = np.sqrt(sigma_xx**2 - sigma_xx*sigma_yy + sigma_yy**2 + 3*tau_xy**2)

            # Sub-tabs for stress components
            subtab1, subtab2, subtab3, subtab4 = st.tabs(["Von Mises", "σ-xx", "σ-yy", "τ-xy"])

            with subtab1:
                max_vm_stress_pa = float(np.max(np.abs(von_mises)))
                max_vm_stress_mpa = max_vm_stress_pa / 1e6

                # Format MPa display based on magnitude
                if max_vm_stress_mpa >= 0.1:
                    mpa_display = f"{max_vm_stress_mpa:.2f} MPa"
                else:
                    mpa_display = f"{max_vm_stress_mpa:.6f} MPa ({max_vm_stress_mpa:.3e} MPa)"

                st.info(f"💡 Max Von Mises Stress: {max_vm_stress_pa:.3e} Pa = {mpa_display}")

                # Filter controls
                st.markdown("---")
                st.markdown("##### 🎯 Failure Analysis Filter")

                # Always use slider with intelligent range and step size
                if max_vm_stress_mpa < 0.001:
                    # Very small stresses - use micro range
                    slider_max = max(0.001, max_vm_stress_mpa * 1.5)
                    slider_step = slider_max / 1000
                    default_value = max_vm_stress_mpa * 0.7 if max_vm_stress_mpa > 0 else slider_max * 0.5
                elif max_vm_stress_mpa < 0.1:
                    # Small stresses - use fine resolution
                    slider_max = max(0.1, max_vm_stress_mpa * 1.2)
                    slider_step = slider_max / 1000
                    default_value = max_vm_stress_mpa * 0.7
                else:
                    # Normal stresses
                    slider_max = max_vm_stress_mpa
                    slider_step = slider_max / 100
                    default_value = max_vm_stress_mpa * 0.7

                threshold_mpa = st.slider(
                    "Set Stress Limit (MPa)",
                    min_value=0.0,
                    max_value=float(slider_max),
                    value=float(default_value),
                    step=float(slider_step),
                    format="%.6f",
                    key="vm_threshold_slider",
                    help="Drag to set the stress limit. Regions in RED exceed this limit."
                )

                enable_filter = st.toggle("Show Filtered View (Red = Exceeds Limit, Gray = Safe)", value=False, key="vm_filter_toggle")
                st.markdown("---")

                # Create plot based on filter state
                if enable_filter:
                    st.success(f"✅ FILTERED VIEW ACTIVE - Limit: {threshold_mpa:.1f} MPa")
                    threshold_pa = threshold_mpa * 1e6

                    # Create binary mask
                    mask = von_mises >= threshold_pa
                    exceeding_count = np.sum(mask)
                    percentage = (exceeding_count / len(von_mises)) * 100

                    # Color each triangle
                    triangle_colors = []
                    for tri in elements[:, 3:6].astype(int):
                        if np.any(mask[tri]):
                            triangle_colors.append('red')
                        else:
                            triangle_colors.append('lightgray')

                    # Create figure
                    import plotly.graph_objects as go
                    x = nodes[:, 1]
                    y = nodes[:, 2]
                    triangles = elements[:, 3:6].astype(int)

                    fig = go.Figure(data=go.Mesh3d(
                        x=x, y=y, z=np.zeros_like(x),
                        i=triangles[:, 0],
                        j=triangles[:, 1],
                        k=triangles[:, 2],
                        facecolor=triangle_colors,
                        flatshading=True,
                        showscale=False
                    ))

                    fig.update_layout(
                        title=f"Von Mises Stress - Filtered (Limit: {threshold_mpa:.1f} MPa)",
                        scene=dict(
                            xaxis=dict(title='X', showgrid=False),
                            yaxis=dict(title='Y', showgrid=False),
                            zaxis=dict(showticklabels=False, showgrid=False),
                            aspectmode='data',
                            camera=dict(
                                eye=dict(x=0, y=0, z=2.5),
                                up=dict(x=0, y=1, z=0),
                                center=dict(x=0, y=0, z=0),
                                projection=dict(type='orthographic')
                            )
                        ),
                        height=700,
                        margin=dict(l=0, r=0, t=40, b=0),
                        hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    if percentage > 0:
                        st.error(f"🚨 **{exceeding_count} nodes ({percentage:.1f}%)** exceed the stress limit!")
                    else:
                        st.success(f"✅ All regions are within the stress limit")
                else:
                    st.info("ℹ️ CONTINUOUS VIEW - Enable filter above to identify overstressed regions")
                    fig = create_interactive_contour_plot(
                        nodes, elements, von_mises,
                        "Von Mises Stress",
                        "σ (Pa)",
                        height=700
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with subtab2:
                fig = create_interactive_contour_plot(
                    nodes, elements, sigma_xx,
                    "Normal Stress (σ-xx)",
                    "σ-xx (Pa)",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab3:
                fig = create_interactive_contour_plot(
                    nodes, elements, sigma_yy,
                    "Normal Stress (σ-yy)",
                    "σ-yy (Pa)",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

            with subtab4:
                fig = create_interactive_contour_plot(
                    nodes, elements, tau_xy,
                    "Shear Stress (τ-xy)",
                    "τ-xy (Pa)",
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.markdown("### Principal Stresses")

            # Calculate principal stresses
            # For 2D plane stress: σ1, σ2 = (σxx + σyy)/2 ± sqrt(((σxx - σyy)/2)^2 + τxy^2)
            sigma_xx = stresses[:, 0]
            sigma_yy = stresses[:, 1]
            tau_xy = stresses[:, 2]

            sigma_avg = (sigma_xx + sigma_yy) / 2
            R = np.sqrt(((sigma_xx - sigma_yy) / 2)**2 + tau_xy**2)

            sigma_1 = sigma_avg + R  # Maximum principal stress
            sigma_2 = sigma_avg - R  # Minimum principal stress
            tau_max = R              # Maximum shear stress = (σ1 - σ2)/2

            # Sub-tabs for principal stress components
            subtab1, subtab2, subtab3, subtab4 = st.tabs(["σ₁ (Max Principal)", "σ₂ (Min Principal)", "τmax (Max Shear)", "📐 Stress Trajectories"])

            with subtab1:
                max_s1_stress_pa = float(np.max(np.abs(sigma_1)))
                max_s1_stress_mpa = max_s1_stress_pa / 1e6
                min_s1_stress_pa = float(np.min(sigma_1))
                min_s1_stress_mpa = min_s1_stress_pa / 1e6

                # Format MPa display based on magnitude
                if max_s1_stress_mpa >= 0.1:
                    max_mpa_display = f"{max_s1_stress_mpa:.2f} MPa"
                else:
                    max_mpa_display = f"{max_s1_stress_mpa:.6f} MPa ({max_s1_stress_mpa:.3e} MPa)"

                if abs(min_s1_stress_mpa) >= 0.1:
                    min_mpa_display = f"{min_s1_stress_mpa:.2f} MPa"
                else:
                    min_mpa_display = f"{min_s1_stress_mpa:.6f} MPa ({min_s1_stress_mpa:.3e} MPa)"

                st.info(f"💡 Max σ₁: {max_s1_stress_pa:.3e} Pa = {max_mpa_display} | Min σ₁: {min_s1_stress_pa:.3e} Pa = {min_mpa_display}")

                # Filter controls
                st.markdown("---")
                st.markdown("##### 🎯 Failure Analysis Filter")

                # Always use slider with intelligent range and step size
                if max_s1_stress_mpa < 0.001:
                    # Very small stresses - use micro range
                    slider_max = max(0.001, max_s1_stress_mpa * 1.5)
                    slider_step = slider_max / 1000
                    default_value = max_s1_stress_mpa * 0.7 if max_s1_stress_mpa > 0 else slider_max * 0.5
                elif max_s1_stress_mpa < 0.1:
                    # Small stresses - use fine resolution
                    slider_max = max(0.1, max_s1_stress_mpa * 1.2)
                    slider_step = slider_max / 1000
                    default_value = max_s1_stress_mpa * 0.7
                else:
                    # Normal stresses
                    slider_max = max_s1_stress_mpa
                    slider_step = slider_max / 100
                    default_value = max_s1_stress_mpa * 0.7

                threshold_mpa_s1 = st.slider(
                    "Set Stress Limit (MPa)",
                    min_value=0.0,
                    max_value=float(slider_max),
                    value=float(default_value),
                    step=float(slider_step),
                    format="%.6f",
                    key="s1_threshold_slider",
                    help="Drag to set the stress limit. Regions in RED exceed this limit."
                )

                enable_filter_s1 = st.toggle("Show Filtered View (Red = Exceeds Limit, Gray = Safe)", value=False, key="s1_filter_toggle")
                st.markdown("---")

                # Create plot based on filter state
                if enable_filter_s1:
                    st.success(f"✅ FILTERED VIEW ACTIVE - Limit: {threshold_mpa_s1:.1f} MPa")
                    threshold_pa_s1 = threshold_mpa_s1 * 1e6

                    # Create binary mask
                    mask = sigma_1 >= threshold_pa_s1
                    exceeding_count = np.sum(mask)
                    percentage = (exceeding_count / len(sigma_1)) * 100

                    # Color each triangle
                    triangle_colors = []
                    for tri in elements[:, 3:6].astype(int):
                        if np.any(mask[tri]):
                            triangle_colors.append('red')
                        else:
                            triangle_colors.append('lightgray')

                    # Create figure
                    import plotly.graph_objects as go
                    x = nodes[:, 1]
                    y = nodes[:, 2]
                    triangles = elements[:, 3:6].astype(int)

                    fig = go.Figure(data=go.Mesh3d(
                        x=x, y=y, z=np.zeros_like(x),
                        i=triangles[:, 0],
                        j=triangles[:, 1],
                        k=triangles[:, 2],
                        facecolor=triangle_colors,
                        flatshading=True,
                        showscale=False
                    ))

                    fig.update_layout(
                        title=f"Maximum Principal Stress (σ₁) - Filtered (Limit: {threshold_mpa_s1:.1f} MPa)",
                        scene=dict(
                            xaxis=dict(title='X', showgrid=False),
                            yaxis=dict(title='Y', showgrid=False),
                            zaxis=dict(showticklabels=False, showgrid=False),
                            aspectmode='data',
                            camera=dict(
                                eye=dict(x=0, y=0, z=2.5),
                                up=dict(x=0, y=1, z=0),
                                center=dict(x=0, y=0, z=0),
                                projection=dict(type='orthographic')
                            )
                        ),
                        height=700,
                        margin=dict(l=0, r=0, t=40, b=0),
                        hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    if percentage > 0:
                        st.error(f"🚨 **{exceeding_count} nodes ({percentage:.1f}%)** exceed the stress limit!")
                    else:
                        st.success(f"✅ All regions are within the stress limit")
                else:
                    st.info("ℹ️ CONTINUOUS VIEW - Enable filter above to identify overstressed regions")
                    fig = create_interactive_contour_plot(
                        nodes, elements, sigma_1,
                        "Maximum Principal Stress (σ₁)",
                        "σ₁ (Pa)",
                        height=700
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with subtab2:
                max_s2_stress_pa = float(np.max(np.abs(sigma_2)))
                max_s2_stress_mpa = max_s2_stress_pa / 1e6
                min_s2_stress_pa = float(np.min(sigma_2))
                min_s2_stress_mpa = min_s2_stress_pa / 1e6

                # Format MPa display based on magnitude
                if max_s2_stress_mpa >= 0.1:
                    max_mpa_display = f"{max_s2_stress_mpa:.2f} MPa"
                else:
                    max_mpa_display = f"{max_s2_stress_mpa:.6f} MPa ({max_s2_stress_mpa:.3e} MPa)"

                if abs(min_s2_stress_mpa) >= 0.1:
                    min_mpa_display = f"{min_s2_stress_mpa:.2f} MPa"
                else:
                    min_mpa_display = f"{min_s2_stress_mpa:.6f} MPa ({min_s2_stress_mpa:.3e} MPa)"

                st.info(f"💡 Max σ₂: {max_s2_stress_pa:.3e} Pa = {max_mpa_display} | Min σ₂: {min_s2_stress_pa:.3e} Pa = {min_mpa_display}")

                # Filter controls
                st.markdown("---")
                st.markdown("##### 🎯 Failure Analysis Filter")

                # Always use slider with intelligent range and step size
                if max_s2_stress_mpa < 0.001:
                    # Very small stresses - use micro range
                    slider_max = max(0.001, max_s2_stress_mpa * 1.5)
                    slider_step = slider_max / 1000
                    default_value = max_s2_stress_mpa * 0.7 if max_s2_stress_mpa > 0 else slider_max * 0.5
                elif max_s2_stress_mpa < 0.1:
                    # Small stresses - use fine resolution
                    slider_max = max(0.1, max_s2_stress_mpa * 1.2)
                    slider_step = slider_max / 1000
                    default_value = max_s2_stress_mpa * 0.7
                else:
                    # Normal stresses
                    slider_max = max_s2_stress_mpa
                    slider_step = slider_max / 100
                    default_value = max_s2_stress_mpa * 0.7

                threshold_mpa_s2 = st.slider(
                    "Set Stress Limit (MPa)",
                    min_value=0.0,
                    max_value=float(slider_max),
                    value=float(default_value),
                    step=float(slider_step),
                    format="%.6f",
                    key="s2_threshold_slider",
                    help="Drag to set the stress limit. Regions in RED exceed this limit."
                )

                enable_filter_s2 = st.toggle("Show Filtered View (Red = Exceeds Limit, Gray = Safe)", value=False, key="s2_filter_toggle")
                st.markdown("---")

                # Create plot based on filter state
                if enable_filter_s2:
                    st.success(f"✅ FILTERED VIEW ACTIVE - Limit: {threshold_mpa_s2:.1f} MPa")
                    threshold_pa_s2 = threshold_mpa_s2 * 1e6

                    # Create binary mask
                    mask = np.abs(sigma_2) >= threshold_pa_s2  # Use absolute value for σ₂
                    exceeding_count = np.sum(mask)
                    percentage = (exceeding_count / len(sigma_2)) * 100

                    # Color each triangle
                    triangle_colors = []
                    for tri in elements[:, 3:6].astype(int):
                        if np.any(mask[tri]):
                            triangle_colors.append('red')
                        else:
                            triangle_colors.append('lightgray')

                    # Create figure
                    import plotly.graph_objects as go
                    x = nodes[:, 1]
                    y = nodes[:, 2]
                    triangles = elements[:, 3:6].astype(int)

                    fig = go.Figure(data=go.Mesh3d(
                        x=x, y=y, z=np.zeros_like(x),
                        i=triangles[:, 0],
                        j=triangles[:, 1],
                        k=triangles[:, 2],
                        facecolor=triangle_colors,
                        flatshading=True,
                        showscale=False
                    ))

                    fig.update_layout(
                        title=f"Minimum Principal Stress (σ₂) - Filtered (Limit: {threshold_mpa_s2:.1f} MPa)",
                        scene=dict(
                            xaxis=dict(title='X', showgrid=False),
                            yaxis=dict(title='Y', showgrid=False),
                            zaxis=dict(showticklabels=False, showgrid=False),
                            aspectmode='data',
                            camera=dict(
                                eye=dict(x=0, y=0, z=2.5),
                                up=dict(x=0, y=1, z=0),
                                center=dict(x=0, y=0, z=0),
                                projection=dict(type='orthographic')
                            )
                        ),
                        height=700,
                        margin=dict(l=0, r=0, t=40, b=0),
                        hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    if percentage > 0:
                        st.error(f"🚨 **{exceeding_count} nodes ({percentage:.1f}%)** exceed the stress limit!")
                    else:
                        st.success(f"✅ All regions are within the stress limit")
                else:
                    st.info("ℹ️ CONTINUOUS VIEW - Enable filter above to identify overstressed regions")
                    fig = create_interactive_contour_plot(
                        nodes, elements, sigma_2,
                        "Minimum Principal Stress (σ₂)",
                        "σ₂ (Pa)",
                        height=700
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with subtab3:
                max_tmax_stress_pa = float(np.max(np.abs(tau_max)))
                max_tmax_stress_mpa = max_tmax_stress_pa / 1e6

                # Format MPa display based on magnitude
                if max_tmax_stress_mpa >= 0.1:
                    mpa_display = f"{max_tmax_stress_mpa:.2f} MPa"
                else:
                    mpa_display = f"{max_tmax_stress_mpa:.6f} MPa ({max_tmax_stress_mpa:.3e} MPa)"

                st.info(f"💡 Max τmax: {max_tmax_stress_pa:.3e} Pa = {mpa_display}")

                # Filter controls
                st.markdown("---")
                st.markdown("##### 🎯 Shear Failure Analysis Filter")

                # Always use slider with intelligent range and step size
                if max_tmax_stress_mpa < 0.001:
                    # Very small stresses - use micro range
                    slider_max = max(0.001, max_tmax_stress_mpa * 1.5)
                    slider_step = slider_max / 1000
                    default_value = max_tmax_stress_mpa * 0.7 if max_tmax_stress_mpa > 0 else slider_max * 0.5
                elif max_tmax_stress_mpa < 0.1:
                    # Small stresses - use fine resolution
                    slider_max = max(0.1, max_tmax_stress_mpa * 1.2)
                    slider_step = slider_max / 1000
                    default_value = max_tmax_stress_mpa * 0.7
                else:
                    # Normal stresses
                    slider_max = max_tmax_stress_mpa
                    slider_step = slider_max / 100
                    default_value = max_tmax_stress_mpa * 0.7

                threshold_mpa_tmax = st.slider(
                    "Set Shear Strength Limit (MPa)",
                    min_value=0.0,
                    max_value=float(slider_max),
                    value=float(default_value),
                    step=float(slider_step),
                    format="%.6f",
                    key="tmax_threshold_slider",
                    help="Drag to set the shear strength limit. Regions in RED exceed this limit."
                )

                enable_filter_tmax = st.toggle("Show Filtered View (Red = Exceeds Limit, Gray = Safe)", value=False, key="tmax_filter_toggle")
                st.markdown("---")

                # Create plot based on filter state
                if enable_filter_tmax:
                    st.success(f"✅ FILTERED VIEW ACTIVE - Shear Limit: {threshold_mpa_tmax:.1f} MPa")
                    threshold_pa_tmax = threshold_mpa_tmax * 1e6

                    # Create binary mask
                    mask = tau_max >= threshold_pa_tmax
                    exceeding_count = np.sum(mask)
                    percentage = (exceeding_count / len(tau_max)) * 100

                    # Color each triangle
                    triangle_colors = []
                    for tri in elements[:, 3:6].astype(int):
                        if np.any(mask[tri]):
                            triangle_colors.append('red')
                        else:
                            triangle_colors.append('lightgray')

                    # Create figure
                    import plotly.graph_objects as go
                    x = nodes[:, 1]
                    y = nodes[:, 2]
                    triangles = elements[:, 3:6].astype(int)

                    fig = go.Figure(data=go.Mesh3d(
                        x=x, y=y, z=np.zeros_like(x),
                        i=triangles[:, 0],
                        j=triangles[:, 1],
                        k=triangles[:, 2],
                        facecolor=triangle_colors,
                        flatshading=True,
                        showscale=False
                    ))

                    fig.update_layout(
                        title=f"Maximum Shear Stress (τmax) - Filtered (Limit: {threshold_mpa_tmax:.1f} MPa)",
                        scene=dict(
                            xaxis=dict(title='X', showgrid=False),
                            yaxis=dict(title='Y', showgrid=False),
                            zaxis=dict(showticklabels=False, showgrid=False),
                            aspectmode='data',
                            camera=dict(
                                eye=dict(x=0, y=0, z=2.5),
                                up=dict(x=0, y=1, z=0),
                                center=dict(x=0, y=0, z=0),
                                projection=dict(type='orthographic')
                            )
                        ),
                        height=700,
                        margin=dict(l=0, r=0, t=40, b=0),
                        hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    if percentage > 0:
                        st.error(f"🚨 **FAILURE RISK: {exceeding_count} nodes ({percentage:.1f}%)** exceed shear strength limit!")
                    else:
                        st.success(f"✅ All regions are within the shear strength limit")
                else:
                    st.info("ℹ️ CONTINUOUS VIEW - Enable filter above to identify overstressed regions")
                    fig = create_interactive_contour_plot(
                        nodes, elements, tau_max,
                        "Maximum Shear Stress (τmax)",
                        "τmax (Pa)",
                        height=700
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with subtab4:
                st.markdown("#### Principal Stress Trajectories")

                st.info("💡 **What are stress trajectories?** Lines showing the direction of principal stresses at each point. "
                       "These reveal how stress flows through the structure - critical for understanding load paths and failure modes.")

                st.markdown("""
                **Educational Insight:**
                - **Orange-red lines**: σ₁ direction (maximum principal stress - most critical for tensile failure)
                - **Cyan lines**: σ₂ direction (minimum principal stress - perpendicular to σ₁)
                - **Line direction**: Shows the axis along which the principal stress acts
                - **Key concept**: σ₁ and σ₂ are always perpendicular (90°) to each other!
                - Lines pass through each other forming an orthogonal grid pattern
                """)

                st.markdown("---")

                # Choose which principal stress to show
                trajectory_type = st.radio(
                    "Select Visualization Mode:",
                    ["Both σ₁ and σ₂ (Perpendicular)", "σ₁ Only (Maximum Principal)", "σ₂ Only (Minimum Principal)"],
                    index=0,  # Default to showing both
                    horizontal=False,
                    help="Choose which principal stress directions to visualize"
                )

                # Map radio selection to show_mode parameter
                if trajectory_type == "Both σ₁ and σ₂ (Perpendicular)":
                    show_mode = 'both'
                elif trajectory_type == "σ₁ Only (Maximum Principal)":
                    show_mode = 'sigma_1'
                else:  # "σ₂ Only (Minimum Principal)"
                    show_mode = 'sigma_2'

                # Create trajectory plot
                fig = create_principal_stress_trajectories_plot(
                    nodes, elements, stresses,
                    height=700,
                    show_mode=show_mode
                )
                st.plotly_chart(fig, use_container_width=True)

                # Educational notes
                st.markdown("---")
                st.markdown("#### 📚 Understanding Stress Trajectories")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    **Key Concepts:**
                    - Principal stresses act on planes with zero shear stress
                    - **σ₁ and σ₂ are ALWAYS perpendicular (90°)**
                    - These directions are called "principal directions"
                    - Stress trajectories show stress flow through structure
                    - The perpendicular grid pattern demonstrates orthogonality
                    """)
                with col2:
                    st.markdown("""
                    **Applications:**
                    - Optimizing material placement (e.g., fiber orientation in composites)
                    - Understanding crack propagation paths
                    - Designing reinforcement layouts in concrete
                    - Identifying natural load paths in topology optimization
                    - Photoelastic stress analysis validation
                    """)

                if show_mode == 'both':
                    st.success("✅ **ORTHOGONALITY DEMONSTRATION**: Notice how orange-red (σ₁) and cyan (σ₂) lines form a perpendicular grid at every point!")
                    st.caption("🔍 Mesh colored by Von Mises stress | Orange-red lines = σ₁ direction | Cyan lines = σ₂ direction (perpendicular to σ₁)")
                else:
                    st.caption("🔍 The mesh color shows the magnitude of the selected principal stress, while lines show its direction")

        with tab5:
            st.markdown("### Reaction Forces & Equilibrium")

            # Get reactions and loads
            reactions = results.get('reactions', np.array([[0, 0, 0]]))
            loads_array = results.get('loads_array', None)

            # Equilibrium check
            st.markdown("#### ⚖️ Equilibrium Verification")
            equilibrium = verify_equilibrium(reactions, loads_array, nodes)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ΣFx (Total)", f"{equilibrium['sum_Fx']:.3e} N")
                st.caption(f"Reactions: {equilibrium['reaction_Fx']:.3e} N")
                st.caption(f"Applied: {equilibrium['applied_Fx']:.3e} N")
            with col2:
                st.metric("ΣFy (Total)", f"{equilibrium['sum_Fy']:.3e} N")
                st.caption(f"Reactions: {equilibrium['reaction_Fy']:.3e} N")
                st.caption(f"Applied: {equilibrium['applied_Fy']:.3e} N")
            with col3:
                st.metric("ΣM (Total)", f"{equilibrium['sum_M']:.3e} N·m")

            if equilibrium['balanced']:
                st.success("✅ System is in equilibrium! (ΣFx ≈ 0, ΣFy ≈ 0, ΣM ≈ 0)")
            else:
                st.warning("⚠️ Equilibrium check shows non-zero residuals (may be numerical error)")

            st.markdown("---")

            # Reaction forces table
            st.markdown("#### 📋 Reaction Forces at Constrained Nodes")

            # Create DataFrame for better display
            import pandas as pd
            reaction_df = pd.DataFrame(reactions, columns=['Node ID', 'Rx (N)', 'Ry (N)'])
            reaction_df['Node ID'] = reaction_df['Node ID'].astype(int)
            reaction_df['Magnitude (N)'] = np.sqrt(reaction_df['Rx (N)']**2 + reaction_df['Ry (N)']**2)

            st.dataframe(
                reaction_df.style.format({
                    'Rx (N)': '{:.3e}',
                    'Ry (N)': '{:.3e}',
                    'Magnitude (N)': '{:.3e}'
                }),
                use_container_width=True
            )

            # Download reactions as CSV
            csv = reaction_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Reactions (CSV)",
                data=csv,
                file_name="reaction_forces.csv",
                mime="text/csv"
            )

            st.markdown("---")

            # Visualization
            st.markdown("#### 🎯 Force Diagram")
            st.info("💡 Red arrows = Reaction forces | Green arrows = Applied loads")

            fig = create_reaction_forces_plot(nodes, elements, reactions, loads_array, height=700)
            st.plotly_chart(fig, use_container_width=True)

            st.caption("🔍 Hover over arrows to see force values | Arrow length is proportional to force magnitude")

    except Exception as e:
        st.error(f"❌ Error generating interactive plots: {str(e)}")
        st.info("Field data is available in the results, but visualization failed.")

        # Fallback: show available data
        with st.expander("View Raw Data Summary"):
            st.write(f"Displacement shape: {results['displacements'].shape}")
            st.write(f"Strain shape: {results['strains'].shape}")
            st.write(f"Stress shape: {results['stresses'].shape}")
            st.code(f"Error details: {str(e)}")


def main():
    """Main application"""
    initialize_session_state()

    # Header
    st.markdown('<p class="main-header">🔧 SolidsPy based FEM Builder</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    with st.sidebar:
 #       st.image("https://img.icons8.com/clouds/100/000000/engineering.png", width=100)
        st.title("Navigation")

        page = st.radio(
            "Choose a page:",
            ["🏗️ Model Builder", "📂 Load GEO File", "📊 Analyze Existing Model", "📚 Load Example", "ℹ️ About"],
            index=0
        )

        st.markdown("---")
        st.markdown("### Quick Tips")
        if page == "📂 Load GEO File":
            st.info("💡 Upload your .geo file\n\n🔧 Define materials for physical groups\n\n🔒 Set boundary conditions\n\n⚡ Add loads\n\n✅ Generate mesh!")
        elif page == "📊 Analyze Existing Model":
            st.info("💡 Upload SolidsPy txt files\n\n🔬 Run FEA analysis\n\n📈 View results!")
        else:
            st.info("💡 Start by selecting a geometry type\n\n📐 Adjust parameters in real-time\n\n🔒 Add boundary conditions\n\n⚡ Define loads\n\n✅ Generate your model!")

    if page == "🏗️ Model Builder":
        show_model_builder()
    elif page == "📂 Load GEO File":
        show_geo_loader()
    elif page == "📊 Analyze Existing Model":
        show_analyze_existing()
    elif page == "📚 Load Example":
        show_examples()
    else:
        show_about()


def show_model_builder():
    """Show the main model builder interface"""

    # Model metadata
    st.markdown('<p class="section-header">📝 Model Information</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        model_name = st.text_input("Model Name", value="my_model", help="Unique name for your model")
    with col2:
        description = st.text_input("Description (optional)", value="", help="Brief description of the model")

    st.markdown("---")

    # Geometry selection
    st.markdown('<p class="section-header">🎯 Geometry Type</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        geometry_type = st.selectbox(
            "Select Geometry",
            [
                ("rectangle", "Rectangle - Simple rectangular plate"),
                ("layered_plate", "Layered Plate - Multi-material layers"),
                ("lshape", "L-Shape - L-shaped beam or bracket"),
                ("plate_with_hole", "Plate with Hole - Stress concentration analysis")
            ],
            format_func=lambda x: x[1]
        )
        geometry_type = geometry_type[0]  # Extract key

    with col2:
        geometry_preview(geometry_type)

    st.markdown("---")

    # Geometry parameters
    geom_params = create_geometry_params(geometry_type)

    st.markdown("---")

    # Materials
    materials = create_material_inputs(geometry_type)

    st.markdown("---")

    # Boundary conditions
    bcs = create_bc_inputs()

    st.markdown("---")

    # Loads
    loads = create_load_inputs()

    st.markdown("---")

    # Mesh parameters
    mesh_params = create_mesh_inputs()

    st.markdown("---")

    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Model Configuration", use_container_width=True):
            try:
                # Build YAML config
                config_dict = build_yaml_config(
                    model_name, description, geometry_type,
                    geom_params, materials, bcs, loads, mesh_params
                )

                # Convert to YAML string
                yaml_content = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)

                # Validate by loading
                config = FEMConfig(**config_dict)

                st.session_state.yaml_content = yaml_content
                st.session_state.config_dict = config_dict
                st.session_state.model_created = True

                st.success("✅ Model configuration created successfully!")

            except Exception as e:
                st.error(f"❌ Error creating model: {str(e)}")

    # Show results
    if st.session_state.model_created:
        st.markdown("---")
        st.markdown('<p class="section-header">📄 Generated Configuration</p>', unsafe_allow_html=True)

        # Display YAML
        st.code(st.session_state.yaml_content, language="yaml")

        # Download button
        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="📥 Download YAML",
                data=st.session_state.yaml_content,
                file_name=f"{model_name}.yaml",
                mime="text/yaml"
            )

        with col2:
            if st.button("🔄 Convert to SolidsPy Format"):
                try:
                    with st.spinner("Converting..."):
                        # Create temp directory
                        with tempfile.TemporaryDirectory() as tmpdir:
                            # Save YAML
                            yaml_path = Path(tmpdir) / f"{model_name}.yaml"
                            with open(yaml_path, 'w') as f:
                                f.write(st.session_state.yaml_content)

                            # Load config and convert
                            config = FEMConfig.from_yaml(str(yaml_path))
                            converter = FEMConverter(config, output_dir=tmpdir)
                            converter.convert()

                            # Read output files as strings
                            nodes = (Path(tmpdir) / "nodes.txt").read_text()
                            eles = (Path(tmpdir) / "eles.txt").read_text()
                            mater = (Path(tmpdir) / "mater.txt").read_text()

                            loads_file = Path(tmpdir) / "loads.txt"
                            loads_content = loads_file.read_text() if loads_file.exists() else None

                            # Read GEO and MSH files
                            geo_file = Path(tmpdir) / f"{model_name}.geo"
                            msh_file = Path(tmpdir) / f"{model_name}.msh"

                            geo_content = geo_file.read_text() if geo_file.exists() else None
                            msh_content = msh_file.read_text() if msh_file.exists() else None

                            # Also read arrays for solver
                            nodes_array = np.loadtxt(str(Path(tmpdir) / "nodes.txt"), ndmin=2)
                            elements_array = np.loadtxt(str(Path(tmpdir) / "eles.txt"), ndmin=2, dtype=int)
                            materials_array = np.loadtxt(str(Path(tmpdir) / "mater.txt"), ndmin=2)
                            loads_array = np.loadtxt(str(loads_file), ndmin=2) if loads_file.exists() else None

                            st.session_state.output_files = {
                                'yaml': st.session_state.yaml_content,
                                'geo': geo_content,
                                'msh': msh_content,
                                'nodes': nodes,
                                'eles': eles,
                                'mater': mater,
                                'loads': loads_content
                            }

                            st.session_state.output_arrays = {
                                'nodes': nodes_array,
                                'elements': elements_array,
                                'materials': materials_array,
                                'loads': loads_array
                            }

                            st.session_state.conversion_complete = True

                    st.success("✅ Conversion complete!")

                except Exception as e:
                    import traceback
                    st.error(f"❌ Conversion error: {str(e)}")
                    with st.expander("Show detailed error traceback"):
                        st.code(traceback.format_exc())

        with col3:
            if st.button("🔄 Start Over"):
                st.session_state.model_created = False
                st.session_state.conversion_complete = False
                st.rerun()

        # Show converted files
        if st.session_state.get('conversion_complete', False):
            st.markdown("---")
            st.markdown('<p class="section-header">✅ SolidsPy Output Files</p>', unsafe_allow_html=True)

            tab1, tab2, tab3, tab4 = st.tabs(["nodes.txt", "eles.txt", "mater.txt", "loads.txt"])

            with tab1:
                st.code(st.session_state.output_files['nodes'], language="text")
                st.download_button("Download nodes.txt", st.session_state.output_files['nodes'], "nodes.txt")

            with tab2:
                st.code(st.session_state.output_files['eles'], language="text")
                st.download_button("Download eles.txt", st.session_state.output_files['eles'], "eles.txt")

            with tab3:
                st.code(st.session_state.output_files['mater'], language="text")
                st.download_button("Download mater.txt", st.session_state.output_files['mater'], "mater.txt")

            with tab4:
                if st.session_state.output_files['loads']:
                    st.code(st.session_state.output_files['loads'], language="text")
                    st.download_button("Download loads.txt", st.session_state.output_files['loads'], "loads.txt")
                else:
                    st.info("No loads defined for this model")

            # Save to local folder with custom prefix
            st.markdown("---")
            st.markdown('<p class="section-header">💾 Save All Files to Local Folder</p>', unsafe_allow_html=True)

            st.info("💡 This will save ALL files (YAML, GEO, MSH, and TXT files) to your output folder with the chosen prefix.")

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Get model name from session state if available
                default_prefix = st.session_state.get('config_dict', {}).get('model_name', 'M')
                file_prefix = st.text_input(
                    "File Prefix",
                    value=default_prefix,
                    help="Prefix for all files (e.g., 'Ho' → Ho.yaml, Ho.geo, Ho.msh, Honodes.txt, ...)"
                )

            with col2:
                output_folder = st.text_input(
                    "Output Folder",
                    value="./output",
                    help="Local folder to save files (will be created if doesn't exist)"
                )

            with col3:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("💾 Save All Files", use_container_width=True):
                    try:
                        # Create output folder if it doesn't exist
                        output_path = Path(output_folder)
                        output_path.mkdir(parents=True, exist_ok=True)

                        # Save files with prefix
                        files_saved = []

                        # Save YAML configuration
                        if st.session_state.output_files.get('yaml'):
                            yaml_file = output_path / f"{file_prefix}.yaml"
                            with open(yaml_file, 'w') as f:
                                f.write(st.session_state.output_files['yaml'])
                            files_saved.append(str(yaml_file))

                        # Save GEO file (GMSH geometry)
                        if st.session_state.output_files.get('geo'):
                            geo_file = output_path / f"{file_prefix}.geo"
                            with open(geo_file, 'w') as f:
                                f.write(st.session_state.output_files['geo'])
                            files_saved.append(str(geo_file))

                        # Save MSH file (GMSH mesh)
                        if st.session_state.output_files.get('msh'):
                            msh_file = output_path / f"{file_prefix}.msh"
                            with open(msh_file, 'w') as f:
                                f.write(st.session_state.output_files['msh'])
                            files_saved.append(str(msh_file))

                        # Save nodes
                        nodes_file = output_path / f"{file_prefix}nodes.txt"
                        with open(nodes_file, 'w') as f:
                            f.write(st.session_state.output_files['nodes'])
                        files_saved.append(str(nodes_file))

                        # Save elements
                        eles_file = output_path / f"{file_prefix}eles.txt"
                        with open(eles_file, 'w') as f:
                            f.write(st.session_state.output_files['eles'])
                        files_saved.append(str(eles_file))

                        # Save materials
                        mater_file = output_path / f"{file_prefix}mater.txt"
                        with open(mater_file, 'w') as f:
                            f.write(st.session_state.output_files['mater'])
                        files_saved.append(str(mater_file))

                        # Save loads (if present)
                        if st.session_state.output_files.get('loads'):
                            loads_file = output_path / f"{file_prefix}loads.txt"
                            with open(loads_file, 'w') as f:
                                f.write(st.session_state.output_files['loads'])
                            files_saved.append(str(loads_file))

                        st.success(f"✅ All {len(files_saved)} files saved successfully to: `{output_folder}/`")

                        st.markdown("**Files created:**")
                        for file_path in files_saved:
                            st.markdown(f"- `{file_path}`")

                    except Exception as e:
                        st.error(f"❌ Error saving files: {str(e)}")

            # Run SolidsPy Solver
            if SOLIDSPY_AVAILABLE:
                st.markdown("---")
                st.markdown('<p class="section-header">🔬 Run FEA Analysis</p>', unsafe_allow_html=True)

                st.info("💡 Run SolidsPy solver to compute displacements, strains, and stresses")

                if st.button("🚀 Run SolidsPy Solver", key="solve_model", use_container_width=True):
                    with st.spinner("Running FEA analysis..."):
                        # Get arrays from session state
                        nodes_array = st.session_state.output_arrays['nodes']
                        elements_array = st.session_state.output_arrays['elements']
                        materials_array = st.session_state.output_arrays['materials']
                        loads_array = st.session_state.output_arrays.get('loads')

                        # Run solver
                        results = run_solidspy_solver(
                            nodes_array,
                            elements_array,
                            materials_array,
                            loads_array
                        )

                        # Cache results in session state so filter interactions don't rerun solver
                        st.session_state.solver_results = results
                        st.session_state.solver_run_complete = True

                # Display results if available (use cached results on rerun from filter interactions)
                if st.session_state.get('solver_run_complete', False):
                    display_solver_results(st.session_state.solver_results)
            else:
                st.markdown("---")
                st.warning("⚠️ SolidsPy not available. Solver functionality disabled.")
                if SOLIDSPY_ERROR:
                    st.error(f"Import error: {SOLIDSPY_ERROR}")
                st.info("To enable solver, ensure the `solidspy/` folder is in the project directory.")


def show_geo_loader():
    """Show the GEO file loader interface"""
    st.markdown('<p class="section-header">📂 Load External GEO File</p>', unsafe_allow_html=True)

    st.markdown("""
    This feature allows you to:
    - Upload an existing GMSH .geo file (created externally)
    - Define material properties for physical groups
    - Set boundary conditions and loads
    - Generate mesh and convert to SolidsPy format

    **Use case:** When you've created complex geometry in GMSH but want to use the GUI for the rest of the workflow.
    """)

    st.markdown("---")

    # Model name
    st.markdown('<p class="section-header">📝 Model Information</p>', unsafe_allow_html=True)
    model_name = st.text_input("Model Name", value="geo_model", help="Name for your model")

    st.markdown("---")

    # File upload or selection
    st.markdown('<p class="section-header">📁 Select GEO File</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Option 1: Upload File**")
        uploaded_file = st.file_uploader("Upload .geo file", type=['geo'])

    with col2:
        st.markdown("**Option 2: Select from templates/**")
        # List .geo files in templates folder
        templates_path = Path("templates")
        if templates_path.exists():
            geo_files = list(templates_path.glob("*.geo"))
            geo_file_names = [f.name for f in geo_files]
            if geo_file_names:
                selected_template = st.selectbox("Choose template:", [""] + geo_file_names)
            else:
                st.info("No .geo files found in templates/")
                selected_template = ""
        else:
            st.info("templates/ folder not found")
            selected_template = ""

    # Load the GEO content
    geo_content = None
    geo_filename = None

    if uploaded_file is not None:
        geo_content = uploaded_file.read().decode('utf-8')
        geo_filename = uploaded_file.name
        st.success(f"✅ Loaded: {geo_filename}")
    elif selected_template:
        geo_path = templates_path / selected_template
        with open(geo_path, 'r') as f:
            geo_content = f.read()
        geo_filename = selected_template
        st.success(f"✅ Loaded: {geo_filename}")

    if geo_content:
        st.markdown("---")
        st.markdown('<p class="section-header">👁️ GEO File Preview</p>', unsafe_allow_html=True)

        with st.expander("View GEO content", expanded=False):
            st.code(geo_content, language="text")

        st.markdown("---")

        # Extract physical groups info from GEO file
        st.markdown('<p class="section-header">📊 Physical Groups Detected</p>', unsafe_allow_html=True)

        # Parse physical groups from GEO content
        import re

        # Try both formats:
        # Format 1: Physical Surface("name", id) - with optional name
        # Format 2: Physical Surface(id) = {...}; - GMSH standard format

        phys_surfaces = []
        phys_lines = []

        # Format 1: Physical Surface("name", id) or Physical Surface(name, id)
        surfaces_fmt1 = re.findall(r'Physical\s+Surface\s*\(\s*"?([^"]*)"?\s*,\s*(\d+)\s*\)', geo_content)
        for name, pid in surfaces_fmt1:
            phys_surfaces.append((name, pid))

        lines_fmt1 = re.findall(r'Physical\s+Line\s*\(\s*"?([^"]*)"?\s*,\s*(\d+)\s*\)', geo_content)
        for name, pid in lines_fmt1:
            phys_lines.append((name, pid))

        # Format 2: Physical Surface(id) = {...};
        surfaces_fmt2 = re.findall(r'Physical\s+Surface\s*\(\s*(\d+)\s*\)\s*=', geo_content)
        for pid in surfaces_fmt2:
            # Generate default name if not already found
            if not any(p == pid for _, p in phys_surfaces):
                phys_surfaces.append((f"Surface_{pid}", pid))

        lines_fmt2 = re.findall(r'Physical\s+Line\s*\(\s*(\d+)\s*\)\s*=', geo_content)
        for pid in lines_fmt2:
            # Generate default name if not already found
            if not any(p == pid for _, p in phys_lines):
                phys_lines.append((f"Line_{pid}", pid))

        if phys_surfaces:
            st.markdown("**Physical Surfaces (for materials):**")
            for name, pid in phys_surfaces:
                st.markdown(f"- ID {pid}: {name if name else 'unnamed'}")

        if phys_lines:
            st.markdown("**Physical Lines (for BCs/loads):**")
            for name, pid in phys_lines:
                st.markdown(f"- ID {pid}: {name if name else 'unnamed'}")

        st.markdown("---")

        # Material properties
        st.markdown('<p class="section-header">🔧 Material Properties</p>', unsafe_allow_html=True)

        if phys_surfaces:
            st.info(f"Define material properties for {len(phys_surfaces)} physical surface(s)")
            materials = []

            for name, pid in phys_surfaces:
                st.markdown(f"**Physical Surface ID {pid}: {name if name else 'unnamed'}**")
                col1, col2 = st.columns(2)
                with col1:
                    E = st.number_input(f"Young's Modulus (Pa)", value=2.1e11, format="%.2e", key=f"E_{pid}")
                with col2:
                    nu = st.number_input(f"Poisson's Ratio", min_value=0.0, max_value=0.49, value=0.3, step=0.01, format="%.3f", key=f"nu_{pid}")

                materials.append({
                    'physical_id': int(pid),
                    'name': name if name else f'material_{pid}',
                    'E': E,
                    'nu': nu
                })
                st.divider()
        else:
            st.warning("⚠️ No Physical Surfaces found in GEO file. Add Physical Surface definitions to specify materials.")
            materials = []

        # Boundary conditions
        st.markdown('<p class="section-header">🔒 Boundary Conditions</p>', unsafe_allow_html=True)

        num_bcs = st.number_input("Number of Boundary Conditions", min_value=0, max_value=20, value=0, step=1)

        bcs = []
        for i in range(num_bcs):
            st.markdown(f"**BC {i+1}**")
            col1, col2, col3 = st.columns(3)

            with col1:
                bc_name = st.text_input("Name", value=f"bc_{i+1}", key=f"bc_name_geo_{i}")
                bc_phys_id = st.number_input("Physical Line ID", min_value=1, value=100+i, step=1, key=f"bc_phys_geo_{i}")

            with col2:
                x_constraint = st.selectbox("X Constraint", ["free", "fixed"], key=f"bc_x_geo_{i}")

            with col3:
                y_constraint = st.selectbox("Y Constraint", ["free", "fixed"], key=f"bc_y_geo_{i}")

            bcs.append({
                'name': bc_name,
                'physical_id': int(bc_phys_id),
                'constraints': {'x': x_constraint, 'y': y_constraint}
            })
            st.divider()

        # Loads
        st.markdown('<p class="section-header">⚡ Loads</p>', unsafe_allow_html=True)

        num_loads = st.number_input("Number of Loads", min_value=0, max_value=20, value=0, step=1)

        loads = []
        for i in range(num_loads):
            st.markdown(f"**Load {i+1}**")
            col1, col2, col3 = st.columns(3)

            with col1:
                load_name = st.text_input("Name", value=f"load_{i+1}", key=f"load_name_geo_{i}")
                load_phys_id = st.number_input("Physical Line ID", min_value=1, value=200+i, step=1, key=f"load_phys_geo_{i}")

            with col2:
                fx = st.number_input("Force X (N)", value=0.0, format="%.2f", key=f"load_fx_geo_{i}")

            with col3:
                fy = st.number_input("Force Y (N)", value=-1000.0, format="%.2f", key=f"load_fy_geo_{i}")

            loads.append({
                'name': load_name,
                'physical_id': int(load_phys_id),
                'force': {'x': fx, 'y': fy},
                'distribution': 'uniform'
            })
            st.divider()

        # Mesh settings
        st.markdown('<p class="section-header">🔲 Mesh Settings</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            mesh_size = st.number_input("Mesh Size (m)", min_value=0.001, value=0.1, step=0.01, format="%.3f")
        with col2:
            element_type = st.selectbox(
                "Element Type",
                options=["triangle", "quad"],
                index=0,
                help="Triangle for standard meshes, Quad if GEO file uses 'Recombine Surface'"
            )

        st.markdown("---")

        # Generate button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Mesh and Convert", use_container_width=True):
                try:
                    with st.spinner("Processing..."):
                        with tempfile.TemporaryDirectory() as tmpdir:
                            # Save GEO file
                            geo_path = Path(tmpdir) / f"{model_name}.geo"
                            with open(geo_path, 'w') as f:
                                f.write(geo_content)

                            # Run GMSH
                            from fem_converter import FEMConverter
                            converter = FEMConverter.__new__(FEMConverter)
                            gmsh_exe = converter._find_gmsh()

                            if not gmsh_exe:
                                st.error("❌ GMSH executable not found")
                                raise FileNotFoundError("GMSH not found")

                            msh_path = Path(tmpdir) / f"{model_name}.msh"
                            result = subprocess.run(
                                [gmsh_exe, str(geo_path), "-2", "-o", str(msh_path)],
                                capture_output=True,
                                text=True
                            )

                            if result.returncode != 0:
                                st.error(f"❌ GMSH Error: {result.stderr}")
                                raise RuntimeError("GMSH failed")

                            # Read mesh
                            import meshio
                            mesh = meshio.read(str(msh_path))
                            points = mesh.points
                            cells = mesh.cells
                            cell_data = mesh.cell_data

                            # Convert nodes
                            import preprocesor as msh_proc
                            nodes_array = msh_proc.node_writer(points, mesh.point_data)

                            # Convert elements
                            # Map element type to SolidsPy element ID
                            ele_type_map = {
                                'triangle': 3,
                                'quad': 2
                            }
                            ele_type_id = ele_type_map[element_type]

                            # For multiple materials
                            elements_list = []
                            nini = 0

                            for mat_idx, mat in enumerate(materials):
                                nf, layer_els = msh_proc.ele_writer(
                                    cells, cell_data,
                                    element_type,
                                    mat['physical_id'],  # Physical surface ID from GMSH
                                    ele_type_id,
                                    mat_idx,              # Material tag = row index in mater.txt (0, 1, 2, ...)
                                    nini
                                )
                                elements_list.append(layer_els)
                                nini = nf

                            if elements_list:
                                elements_array = np.vstack(elements_list)
                            else:
                                st.error("❌ No elements extracted. Check physical surface IDs.")
                                raise ValueError("No elements")

                            # Apply boundary conditions
                            for bc in bcs:
                                bc_x = -1 if bc['constraints']['x'] == "fixed" else 0
                                bc_y = -1 if bc['constraints']['y'] == "fixed" else 0
                                nodes_array = msh_proc.boundary_conditions(
                                    cells, cell_data,
                                    bc['physical_id'],
                                    nodes_array,
                                    bc_x, bc_y
                                )

                            # Apply loads
                            loads_array = None
                            if loads:
                                loads_list = []
                                for load in loads:
                                    load_array = msh_proc.loading(
                                        cells, cell_data,
                                        load['physical_id'],
                                        load['force']['x'],
                                        load['force']['y']
                                    )
                                    loads_list.append(load_array)

                                if loads_list:
                                    loads_array = np.vstack(loads_list)

                            # Create materials array (only E and nu for SolidsPy)
                            materials_array = np.zeros((len(materials), 2))
                            for i, mat in enumerate(materials):
                                materials_array[i, 0] = mat['E']
                                materials_array[i, 1] = mat['nu']

                            # Save to strings
                            from io import StringIO

                            nodes_str = StringIO()
                            np.savetxt(nodes_str, nodes_array, fmt=("%d", "%.4f", "%.4f", "%d", "%d"))

                            eles_str = StringIO()
                            fmt_elements = ["%d", "%d", "%d"] + ["%d"] * (elements_array.shape[1] - 3)
                            np.savetxt(eles_str, elements_array, fmt=fmt_elements)

                            mater_str = StringIO()
                            np.savetxt(mater_str, materials_array, fmt="%.6e")

                            loads_str = None
                            if loads_array is not None:
                                loads_io = StringIO()
                                np.savetxt(loads_io, loads_array, fmt=("%d", "%.6f", "%.6f"))
                                loads_str = loads_io.getvalue()

                            # Read GEO and MSH files
                            msh_content = msh_path.read_text()

                            st.session_state.output_files = {
                                'geo': geo_content,
                                'msh': msh_content,
                                'nodes': nodes_str.getvalue(),
                                'eles': eles_str.getvalue(),
                                'mater': mater_str.getvalue(),
                                'loads': loads_str
                            }

                            st.session_state.output_arrays = {
                                'nodes': nodes_array,
                                'elements': elements_array,
                                'materials': materials_array,
                                'loads': loads_array
                            }

                            st.session_state.conversion_complete = True
                            st.session_state.model_name_geo = model_name

                    st.success("✅ Conversion complete!")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

        # Show output
        if st.session_state.get('conversion_complete', False) and 'model_name_geo' in st.session_state:
            st.markdown("---")
            st.markdown('<p class="section-header">✅ Output Files</p>', unsafe_allow_html=True)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["nodes.txt", "eles.txt", "mater.txt", "loads.txt", "mesh"])

            with tab1:
                st.code(st.session_state.output_files['nodes'], language="text")
                st.download_button("Download nodes.txt", st.session_state.output_files['nodes'], "nodes.txt", key="dl_nodes_geo")

            with tab2:
                st.code(st.session_state.output_files['eles'], language="text")
                st.download_button("Download eles.txt", st.session_state.output_files['eles'], "eles.txt", key="dl_eles_geo")

            with tab3:
                st.code(st.session_state.output_files['mater'], language="text")
                st.download_button("Download mater.txt", st.session_state.output_files['mater'], "mater.txt", key="dl_mater_geo")

            with tab4:
                if st.session_state.output_files.get('loads'):
                    st.code(st.session_state.output_files['loads'], language="text")
                    st.download_button("Download loads.txt", st.session_state.output_files['loads'], "loads.txt", key="dl_loads_geo")
                else:
                    st.info("No loads defined")

            with tab5:
                st.info(f"MSH file: {len(st.session_state.output_files['msh'])} bytes")
                st.download_button("Download .msh file", st.session_state.output_files['msh'], f"{model_name}.msh", key="dl_msh_geo")

            # Save all files
            st.markdown("---")
            st.markdown('<p class="section-header">💾 Save All Files to Local Folder</p>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                file_prefix = st.text_input("File Prefix", value=model_name, key="prefix_geo")

            with col2:
                output_folder = st.text_input("Output Folder", value="./output", key="folder_geo")

            with col3:
                st.write("")
                st.write("")
                if st.button("💾 Save All Files", key="save_geo"):
                    try:
                        output_path = Path(output_folder)
                        output_path.mkdir(parents=True, exist_ok=True)

                        files_saved = []

                        # Save GEO
                        geo_file = output_path / f"{file_prefix}.geo"
                        with open(geo_file, 'w') as f:
                            f.write(st.session_state.output_files['geo'])
                        files_saved.append(str(geo_file))

                        # Save MSH
                        msh_file = output_path / f"{file_prefix}.msh"
                        with open(msh_file, 'w') as f:
                            f.write(st.session_state.output_files['msh'])
                        files_saved.append(str(msh_file))

                        # Save TXT files
                        for name in ['nodes', 'eles', 'mater']:
                            txt_file = output_path / f"{file_prefix}{name}.txt"
                            with open(txt_file, 'w') as f:
                                f.write(st.session_state.output_files[name])
                            files_saved.append(str(txt_file))

                        if st.session_state.output_files.get('loads'):
                            loads_file = output_path / f"{file_prefix}loads.txt"
                            with open(loads_file, 'w') as f:
                                f.write(st.session_state.output_files['loads'])
                            files_saved.append(str(loads_file))

                        st.success(f"✅ All {len(files_saved)} files saved to: `{output_folder}/`")

                        st.markdown("**Files created:**")
                        for file_path in files_saved:
                            st.markdown(f"- `{file_path}`")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

            # Run SolidsPy Solver
            if SOLIDSPY_AVAILABLE:
                st.markdown("---")
                st.markdown('<p class="section-header">🔬 Run FEA Analysis</p>', unsafe_allow_html=True)

                st.info("💡 Run SolidsPy solver to compute displacements, strains, and stresses")

                if st.button("🚀 Run SolidsPy Solver", key="solve_geo", use_container_width=True):
                    with st.spinner("Running FEA analysis..."):
                        # Get arrays from session state
                        nodes_array = st.session_state.output_arrays['nodes']
                        elements_array = st.session_state.output_arrays['elements']
                        materials_array = st.session_state.output_arrays['materials']
                        loads_array = st.session_state.output_arrays.get('loads')

                        # Run solver
                        results = run_solidspy_solver(
                            nodes_array,
                            elements_array,
                            materials_array,
                            loads_array
                        )

                        # Cache results in session state so filter interactions don't rerun solver
                        st.session_state.solver_results_geo = results
                        st.session_state.solver_run_complete_geo = True

                # Display results if available (use cached results on rerun from filter interactions)
                if st.session_state.get('solver_run_complete_geo', False):
                    display_solver_results(st.session_state.solver_results_geo)
            else:
                st.markdown("---")
                st.warning("⚠️ SolidsPy not available. Solver functionality disabled.")
                if SOLIDSPY_ERROR:
                    st.error(f"Import error: {SOLIDSPY_ERROR}")
                st.info("To enable solver, ensure the `solidspy/` folder is in the project directory.")


def show_analyze_existing():
    """Analyze existing SolidsPy model files"""
    st.markdown('<p class="section-header">📊 Analyze Existing SolidsPy Model</p>', unsafe_allow_html=True)

    st.markdown("""
    This page allows you to run FEA analysis on **existing SolidsPy txt files**.

    Upload your individual txt files (nodes, eles, mater, loads) to run analysis and visualize results.
    """)

    st.markdown("---")

    # Upload Files section
    st.markdown('<p class="section-header">📂 Upload SolidsPy Files</p>', unsafe_allow_html=True)

    nodes_array = None
    elements_array = None
    materials_array = None
    loads_array = None

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Required Files:**")

        nodes_file = st.file_uploader("Nodes file (nodes.txt)", type=['txt'], key="nodes_upload")
        eles_file = st.file_uploader("Elements file (eles.txt)", type=['txt'], key="eles_upload")
        mater_file = st.file_uploader("Materials file (mater.txt)", type=['txt'], key="mater_upload")

    with col2:
        st.markdown("**Optional Files:**")

        loads_file = st.file_uploader("Loads file (loads.txt)", type=['txt'], key="loads_upload")
        st.info("💡 Loads file is optional. Analysis can run without loads (free vibration, etc.)")

    # Process uploaded files
    if nodes_file and eles_file and mater_file:
        try:
            # Read uploaded files
            from io import StringIO

            nodes_array = np.loadtxt(StringIO(nodes_file.getvalue().decode('utf-8')), ndmin=2)
            elements_array = np.loadtxt(StringIO(eles_file.getvalue().decode('utf-8')), ndmin=2, dtype=int)
            materials_array = np.loadtxt(StringIO(mater_file.getvalue().decode('utf-8')), ndmin=2)

            if loads_file:
                loads_array = np.loadtxt(StringIO(loads_file.getvalue().decode('utf-8')), ndmin=2)

            st.success("✅ Files loaded successfully!")

            # Show file info
            st.markdown("---")
            st.markdown('<p class="section-header">📋 Model Information</p>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Nodes", len(nodes_array))
            with col2:
                st.metric("Elements", len(elements_array))
            with col3:
                st.metric("Materials", len(materials_array))

        except Exception as e:
            st.error(f"❌ Error loading files: {str(e)}")
            st.info("Make sure files are in correct SolidsPy format")

    # Run Solver
    if nodes_array is not None and elements_array is not None and materials_array is not None:
        if SOLIDSPY_AVAILABLE:
            st.markdown("---")
            st.markdown('<p class="section-header">🔬 Run FEA Analysis</p>', unsafe_allow_html=True)

            st.info("💡 Click below to run SolidsPy solver on the loaded model")

            if st.button("🚀 Run SolidsPy Solver", key="solve_existing", use_container_width=True):
                with st.spinner("Running FEA analysis..."):
                    # Run solver
                    results = run_solidspy_solver(
                        nodes_array,
                        elements_array,
                        materials_array,
                        loads_array
                    )

                    # Cache results in session state so filter interactions don't rerun solver
                    st.session_state.solver_results_existing = results
                    st.session_state.solver_run_complete_existing = True

            # Display results if available (use cached results on rerun from filter interactions)
            if st.session_state.get('solver_run_complete_existing', False):
                display_solver_results(st.session_state.solver_results_existing)
        else:
            st.markdown("---")
            st.warning("⚠️ SolidsPy not available. Solver functionality disabled.")
            if SOLIDSPY_ERROR:
                st.error(f"Import error: {SOLIDSPY_ERROR}")
            st.info("To enable solver, ensure the `solidspy/` folder is in the project directory.")


def show_examples():
    """Show example models"""
    st.markdown('<p class="section-header">📚 Example Models</p>', unsafe_allow_html=True)

    examples = {
        "Simple Cantilever Beam": "examples/simple_plate.yaml",
        "Layered Plate": "examples/layered_plate.yaml"
    }

    selected_example = st.selectbox("Choose an example:", list(examples.keys()))

    example_path = Path(examples[selected_example])

    if example_path.exists():
        with open(example_path, 'r') as f:
            content = f.read()

        st.code(content, language="yaml")

        if st.button("Load This Example"):
            st.session_state.yaml_content = content
            st.session_state.model_created = True
            st.success("✅ Example loaded! Go to Model Builder to view and modify.")
    else:
        st.warning(f"Example file not found: {example_path}")


def show_about():
    """Show about page"""
    st.markdown('<p class="section-header">ℹ️ About SolidsPy based FEM Builder</p>', unsafe_allow_html=True)

    st.markdown("""
    ### Welcome to the SolidsPy based FEM Builder!

    This interactive tool helps you create finite element models without writing code.

    #### Features:
    - 🎯 **4 Geometry Types**: Rectangle, Layered Plate, L-Shape, Plate with Hole
    - 🔧 **Material Properties**: Single or multi-material configurations
    - 🔒 **Boundary Conditions**: Visual edge selection
    - ⚡ **Loads**: Define forces on boundaries
    - 🔲 **Mesh Control**: Adjust mesh size and element type
    - 📥 **Export**: Download YAML configs and SolidsPy files

    #### How to Use:
    1. Select a geometry type
    2. Enter dimensions and parameters
    3. Define material properties
    4. Add boundary conditions and loads
    5. Configure mesh settings
    6. Generate and download your model!

    #### Documentation:
    - Full documentation: `docs/README.md`
    - Quick reference: `docs/QUICK_REFERENCE.md`
    - Getting started: `docs/GETTING_STARTED.md`

    ---

    **Version:** Phase 2B
    **Technology:** Streamlit + FEM Converter Pipeline
    **License:** Part of elementos_finitos_mesher toolkit
    """)

    st.info("💡 **Tip:** Start with an example model from the 'Load Example' page to see how it works!")


if __name__ == "__main__":
    main()
