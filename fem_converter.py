#!/usr/bin/env python3
"""
FEM Converter
-------------

Unified converter for FEA preprocessing.
Converts YAML configuration to SolidsPy input files.

Usage:
    python fem_converter.py model.yaml [--output-dir OUTPUT_DIR]
"""
import argparse
import os
import sys
import subprocess
import numpy as np
import meshio
from pathlib import Path

from fem_config import FEMConfig
from geo_generator import GeoGenerator
import preprocesor as msh


class FEMConverter:
    """Main converter class"""

    def __init__(self, config: FEMConfig, output_dir: str = "./output"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # File paths
        self.geo_file = self.output_dir / f"{config.model_name}.geo"
        self.msh_file = self.output_dir / f"{config.model_name}.msh"

    def convert(self):
        """Run complete conversion pipeline"""
        print(f"=== FEM Converter: {self.config.model_name} ===")
        print(f"Output directory: {self.output_dir}")
        print()

        # Step 1: Generate .geo file
        print("[1/4] Generating .geo file...")
        self._generate_geo()
        print(f"      Created: {self.geo_file}")

        # Step 2: Run GMSH
        print("[2/4] Running GMSH...")
        self._run_gmsh()
        print(f"      Created: {self.msh_file}")

        # Step 3: Convert to SolidsPy format
        print("[3/4] Converting to SolidsPy format...")
        nodes, elements, loads, materials = self._convert_to_solidspy()
        print(f"      Nodes: {len(nodes)}")
        print(f"      Elements: {len(elements)}")
        if loads is not None:
            print(f"      Loads: {len(loads)}")

        # Step 4: Save output files
        print("[4/4] Saving output files...")
        self._save_solidspy_files(nodes, elements, loads, materials)

        print()
        print("✓ Conversion complete!")
        print()
        print("Output files:")
        print(f"  - {self.output_dir / 'nodes.txt'}")
        print(f"  - {self.output_dir / 'eles.txt'}")
        print(f"  - {self.output_dir / 'mater.txt'}")
        if loads is not None:
            print(f"  - {self.output_dir / 'loads.txt'}")

    def _generate_geo(self):
        """Generate GMSH .geo file"""
        generator = GeoGenerator(self.config)
        generator.generate(str(self.geo_file))

    def _run_gmsh(self):
        """Run GMSH to generate mesh"""
        # Try to find GMSH executable
        gmsh_exe = self._find_gmsh()

        if not gmsh_exe:
            raise FileNotFoundError(
                "GMSH executable not found. Please install GMSH or "
                "place gmsh.exe in the project directory."
            )

        # Run GMSH
        cmd = [gmsh_exe, str(self.geo_file), "-2", "-o", str(self.msh_file)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("GMSH Error:")
            print(result.stderr)
            raise RuntimeError("GMSH execution failed")

    def _find_gmsh(self):
        """Find GMSH executable"""
        # Check local directory first
        local_gmsh = Path("./gmsh.exe")
        if local_gmsh.exists():
            return str(local_gmsh)

        # Check if gmsh is in PATH
        try:
            result = subprocess.run(
                ["gmsh", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return "gmsh"
        except FileNotFoundError:
            pass

        return None

    def _convert_to_solidspy(self):
        """Convert mesh to SolidsPy format"""
        # Read mesh
        mesh = meshio.read(str(self.msh_file))
        points = mesh.points
        cells = mesh.cells
        cell_data = mesh.cell_data
        point_data = mesh.point_data

        # Convert nodes
        nodes_array = msh.node_writer(points, point_data)

        # Element type for SolidsPy
        ele_type = self.config.get_solidspy_element_type()

        # Convert elements
        if self.config.layers:
            # Multi-material case
            elements_list = []
            nini = 0

            for layer in self.config.layers:
                nf, layer_els = msh.ele_writer(
                    cells, cell_data,
                    self.config.mesh.element_type,
                    layer.physical_id,
                    ele_type,
                    layer.physical_id,  # Use physical_id as material ID
                    nini
                )
                elements_list.append(layer_els)
                nini = nf

            elements_array = np.vstack(elements_list)
        else:
            # Single material case
            nf, elements_array = msh.ele_writer(
                cells, cell_data,
                self.config.mesh.element_type,
                1,  # Physical surface ID
                ele_type,
                0,  # Material ID
                0
            )

        # Apply boundary conditions
        for bc in self.config.boundary_conditions:
            bc_x = -1 if bc.constraints.x == "fixed" else 0
            bc_y = -1 if bc.constraints.y == "fixed" else 0
            nodes_array = msh.boundary_conditions(
                cells, cell_data,
                bc.physical_id,
                nodes_array,
                bc_x, bc_y
            )

        # Apply loads
        loads_array = None
        if self.config.loads:
            loads_list = []
            for load in self.config.loads:
                load_array = msh.loading(
                    cells, cell_data,
                    load.physical_id,
                    load.force.x,
                    load.force.y
                )
                loads_list.append(load_array)

            if loads_list:
                loads_array = np.vstack(loads_list)

        # Create materials array
        materials_array = self._create_materials_array()

        return nodes_array, elements_array, loads_array, materials_array

    def _create_materials_array(self):
        """Create materials array for SolidsPy"""
        if self.config.layers:
            # One material per layer
            n_materials = len(self.config.layers)
            materials = np.zeros((n_materials, 3))

            for i, layer in enumerate(self.config.layers):
                materials[i, 0] = layer.material.E
                materials[i, 1] = layer.material.nu
                materials[i, 2] = 0.0  # Thickness (for 2D plane stress/strain)

        else:
            # Single material
            materials = np.zeros((1, 3))
            materials[0, 0] = self.config.material.E
            materials[0, 1] = self.config.material.nu
            materials[0, 2] = 0.0

        return materials

    def _save_solidspy_files(self, nodes, elements, loads, materials):
        """Save arrays to SolidsPy format files"""
        # Nodes
        np.savetxt(
            self.output_dir / "nodes.txt",
            nodes,
            fmt=("%d", "%.4f", "%.4f", "%d", "%d")
        )

        # Elements
        fmt_elements = ["%d", "%d", "%d"] + ["%d"] * (elements.shape[1] - 3)
        np.savetxt(
            self.output_dir / "eles.txt",
            elements,
            fmt=fmt_elements
        )

        # Materials
        np.savetxt(
            self.output_dir / "mater.txt",
            materials,
            fmt="%.6e"
        )

        # Loads (if any)
        if loads is not None:
            np.savetxt(
                self.output_dir / "loads.txt",
                loads,
                fmt=("%d", "%.6f", "%.6f")
            )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert YAML FEM configuration to SolidsPy input files"
    )
    parser.add_argument(
        "config",
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="./output",
        help="Output directory (default: ./output)"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = FEMConfig.from_yaml(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Run conversion
    try:
        converter = FEMConverter(config, args.output_dir)
        converter.convert()
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
