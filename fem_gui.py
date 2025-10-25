#!/usr/bin/env python3
"""
FEM Model Builder - Streamlit GUI
----------------------------------

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

from fem_config import FEMConfig
from fem_converter import FEMConverter
from fem_templates import RectangularPlate, LayeredPlate, LShapeBeam, PlateWithHole


# Page configuration
st.set_page_config(
    page_title="FEM Model Builder",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
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


def main():
    """Main application"""
    initialize_session_state()

    # Header
    st.markdown('<p class="main-header">🔧 FEM Model Builder</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/100/000000/engineering.png", width=100)
        st.title("Navigation")

        page = st.radio(
            "Choose a page:",
            ["🏗️ Model Builder", "📂 Load GEO File", "📚 Load Example", "ℹ️ About"],
            index=0
        )

        st.markdown("---")
        st.markdown("### Quick Tips")
        if page == "📂 Load GEO File":
            st.info("💡 Upload your .geo file\n\n🔧 Define materials for physical groups\n\n🔒 Set boundary conditions\n\n⚡ Add loads\n\n✅ Generate mesh!")
        else:
            st.info("💡 Start by selecting a geometry type\n\n📐 Adjust parameters in real-time\n\n🔒 Add boundary conditions\n\n⚡ Define loads\n\n✅ Generate your model!")

    if page == "🏗️ Model Builder":
        show_model_builder()
    elif page == "📂 Load GEO File":
        show_geo_loader()
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

                            # Read output files
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

                            st.session_state.output_files = {
                                'yaml': st.session_state.yaml_content,
                                'geo': geo_content,
                                'msh': msh_content,
                                'nodes': nodes,
                                'eles': eles,
                                'mater': mater,
                                'loads': loads_content
                            }
                            st.session_state.conversion_complete = True

                    st.success("✅ Conversion complete!")

                except Exception as e:
                    st.error(f"❌ Conversion error: {str(e)}")

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

                            # Create materials array
                            materials_array = np.zeros((len(materials), 3))
                            for i, mat in enumerate(materials):
                                materials_array[i, 0] = mat['E']
                                materials_array[i, 1] = mat['nu']
                                materials_array[i, 2] = 0.0

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
    st.markdown('<p class="section-header">ℹ️ About FEM Model Builder</p>', unsafe_allow_html=True)

    st.markdown("""
    ### Welcome to the FEM Model Builder!

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
