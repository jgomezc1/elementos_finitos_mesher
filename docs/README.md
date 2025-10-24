# FEM Preprocessing Automation

Automated preprocessing pipeline for Finite Element Analysis, converting high-level YAML configurations into SolidsPy-compatible input files.

## Features

✅ **YAML-based configuration** - Define models in human-readable format
✅ **Python template library** - Programmatic model creation
✅ **Multiple geometry types** - Rectangle, layered plate, L-shape, plate with hole
✅ **Automatic mesh generation** - GMSH integration
✅ **SolidsPy compatibility** - Direct output to SolidsPy format
✅ **Validation** - Schema validation with clear error messages

## Installation

### Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `numpy>=1.20.0`
- `meshio>=4.0.0`
- `pydantic>=2.0.0`
- `pyyaml>=6.0.0`

### GMSH

GMSH is required for mesh generation. Either:
- Place `gmsh.exe` in the project directory (already included), or
- Install GMSH system-wide from https://gmsh.info/

## Quick Start

### Method 1: YAML Configuration (Recommended)

1. Create a YAML configuration file:

```yaml
model_name: my_model
description: Example FEM model

geometry:
  type: rectangle
  length: 2.0
  height: 1.0

mesh:
  size: 0.1
  element_type: triangle

material:
  E: 2.1e11
  nu: 0.3

boundary_conditions:
  - name: fixed_edge
    location: left
    physical_id: 100
    constraints:
      x: fixed
      y: fixed

loads:
  - name: applied_force
    location: right
    physical_id: 200
    force:
      x: 0.0
      y: -1000.0
    distribution: uniform
```

2. Convert to SolidsPy format:

```bash
python fem_converter.py my_model.yaml -o ./output
```

3. Output files created:
- `output/nodes.txt` - Nodal coordinates and BCs
- `output/eles.txt` - Element connectivity
- `output/mater.txt` - Material properties
- `output/loads.txt` - Load vectors

### Method 2: Python Template Library

```python
from fem_templates import RectangularPlate

# Create model
beam = RectangularPlate(
    length=4.0,
    height=1.0,
    E=2.1e11,
    nu=0.3,
    mesh_size=0.1,
    model_name="cantilever"
)

# Add boundary conditions
beam.add_bc("left", x="fixed", y="fixed")

# Add loads
beam.add_load("right", fy=-1000.0)

# Save configuration
beam.save("cantilever.yaml")
```

Then convert:
```bash
python fem_converter.py cantilever.yaml
```

## Examples

See the `examples/` directory for:

- `layered_plate.yaml` - Multi-material layered plate
- `simple_plate.yaml` - Simple cantilever beam
- `create_layered_plate.py` - Python API example
- `create_cantilever.py` - Python API example

Run examples:
```bash
cd examples
python create_layered_plate.py
python ../fem_converter.py layered_plate_python.yaml
```

## Geometry Types

### 1. Rectangle

```yaml
geometry:
  type: rectangle
  length: 2.0
  height: 1.0
```

### 2. Layered Rectangle (Multi-material)

```yaml
geometry:
  type: rectangle
  length: 2.0
  height: 1.0

layers:
  - name: layer1
    region: [0.0, 0.5]
    physical_id: 1
    material:
      E: 1.0e6
      nu: 0.3

  - name: layer2
    region: [0.5, 1.0]
    physical_id: 2
    material:
      E: 2.0e6
      nu: 0.3
```

### 3. L-Shape

```yaml
geometry:
  type: lshape
  width: 3.0
  height: 3.0
  flange_width: 1.0
  flange_height: 1.0
```

### 4. Plate with Hole

```yaml
geometry:
  type: plate_with_hole
  length: 4.0
  height: 2.0
  hole_x: 2.0
  hole_y: 1.0
  hole_radius: 0.3
```

## Boundary Conditions

Supported locations:
- `left`, `right`, `top`, `bottom`

Example:
```yaml
boundary_conditions:
  - name: fixed_support
    location: left
    physical_id: 100
    constraints:
      x: fixed  # or "free"
      y: fixed  # or "free"
```

## Loads

```yaml
loads:
  - name: applied_load
    location: top
    physical_id: 200
    force:
      x: 0.0
      y: -1000.0
    distribution: uniform
```

## Python Template Library API

### Available Templates

- `RectangularPlate` - Simple rectangular geometry
- `LayeredPlate` - Multi-layer rectangular geometry
- `LShapeBeam` - L-shaped structure
- `PlateWithHole` - Plate with circular hole

### Example: Layered Plate

```python
from fem_templates import LayeredPlate

model = LayeredPlate(length=2.0, height=1.0, mesh_size=0.1)

# Add layers
model.add_layer("bottom", 0.0, 0.5, E=1e6, nu=0.3)
model.add_layer("top", 0.5, 1.0, E=2e6, nu=0.3)

# Add BCs and loads
model.add_bc("left", x="fixed")
model.add_load("top", fy=-100)

# Save
model.save("model.yaml")
```

## Command-Line Usage

```bash
# Basic usage
python fem_converter.py config.yaml

# Specify output directory
python fem_converter.py config.yaml -o ./results

# Help
python fem_converter.py --help
```

## Configuration Schema

Full schema documentation:

```yaml
model_name: string              # Required
description: string             # Optional

geometry:                       # Required
  type: rectangle | lshape | plate_with_hole
  # ... geometry-specific parameters

mesh:                           # Required
  size: float                   # Mesh element size
  element_type: triangle | triangle6 | quad
  algorithm: int                # Optional GMSH algorithm

material:                       # For single material
  E: float                      # Young's modulus
  nu: float                     # Poisson's ratio

layers:                         # For multi-material (alternative to material)
  - name: string
    region: [y_min, y_max]
    physical_id: int
    material:
      E: float
      nu: float

boundary_conditions:            # Required
  - name: string
    location: string
    physical_id: int
    constraints:
      x: fixed | free
      y: fixed | free

loads:                          # Optional
  - name: string
    location: string
    physical_id: int
    force:
      x: float
      y: float
    distribution: uniform
```

## Legacy Compatibility

The old `plate.py` script still works but is now superseded by:

```bash
# Old way
python plate.py

# New way (recommended)
python fem_converter.py examples/layered_plate.yaml
```

## Troubleshooting

### GMSH not found

Ensure `gmsh.exe` is in the project directory or install GMSH system-wide.

### Validation errors

The system validates all inputs. Error messages indicate:
- Which field has the error
- What constraint was violated
- How to fix it

Example:
```
ValidationError: flange_width must be <= width
```

### Duplicate physical IDs

All physical IDs (materials, BCs, loads) must be unique. Use different IDs for each entity.

## Project Structure

```
elementos_finitos_mesher/
├── fem_config.py           # Pydantic configuration models
├── geo_generator.py        # GMSH .geo file generator
├── fem_converter.py        # Main conversion script
├── fem_templates.py        # Python template library
├── preprocesor.py          # Mesh processing functions
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── examples/              # Example configurations
│   ├── layered_plate.yaml
│   ├── simple_plate.yaml
│   ├── create_layered_plate.py
│   └── create_cantilever.py
└── output/                # Default output directory
```

## Contributing

To add new geometry types:

1. Add geometry class to `fem_config.py`
2. Implement generation in `geo_generator.py`
3. Create template class in `fem_templates.py`
4. Add example to `examples/`

## License

This project is part of the elementos_finitos_mesher toolkit.
