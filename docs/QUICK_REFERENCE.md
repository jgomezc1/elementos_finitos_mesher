# FEM Converter - Quick Reference

## Installation

```bash
pip install -r requirements.txt
```

## Basic Usage

```bash
# Convert YAML to SolidsPy format
python fem_converter.py model.yaml

# Specify output directory
python fem_converter.py model.yaml -o results/
```

## YAML Template

```yaml
model_name: my_model
description: Optional description

geometry:
  type: rectangle  # or lshape, plate_with_hole
  length: 2.0
  height: 1.0

mesh:
  size: 0.1
  element_type: triangle  # or triangle6, quad

material:  # For single material
  E: 2.1e11
  nu: 0.3

# OR for multi-material:
layers:
  - name: layer1
    region: [0.0, 0.5]
    physical_id: 1
    material: {E: 1.0e6, nu: 0.3}

boundary_conditions:
  - name: bc_name
    location: left  # or right, top, bottom
    physical_id: 100
    constraints: {x: fixed, y: free}  # fixed or free

loads:
  - name: load_name
    location: top
    physical_id: 200
    force: {x: 0.0, y: -1000.0}
    distribution: uniform
```

## Python API

### Rectangle
```python
from fem_templates import RectangularPlate

model = RectangularPlate(length=4.0, height=1.0, E=2.1e11, nu=0.3)
model.add_bc("left", x="fixed", y="fixed")
model.add_load("right", fy=-1000)
model.save("beam.yaml")
```

### Layered Plate
```python
from fem_templates import LayeredPlate

model = LayeredPlate(length=2.0, height=1.0, mesh_size=0.1)
model.add_layer("bottom", 0.0, 0.5, E=1e6, nu=0.3)
model.add_layer("top", 0.5, 1.0, E=2e6, nu=0.3)
model.add_bc("left", x="fixed")
model.add_load("top", fy=-100)
model.save("layered.yaml")
```

### L-Shape
```python
from fem_templates import LShapeBeam

model = LShapeBeam(
    width=3.0, height=3.0,
    flange_width=1.0, flange_height=1.0,
    E=2.1e11, nu=0.3
)
model.add_bc("bottom", x="fixed", y="fixed")
model.save("lshape.yaml")
```

### Plate with Hole
```python
from fem_templates import PlateWithHole

model = PlateWithHole(
    length=4.0, height=2.0,
    hole_x=2.0, hole_y=1.0, hole_radius=0.3,
    E=2.1e11, nu=0.3
)
model.add_bc("left", x="fixed", y="fixed")
model.save("plate_hole.yaml")
```

## Common Patterns

### Cantilever Beam
```yaml
geometry: {type: rectangle, length: 4.0, height: 1.0}
boundary_conditions:
  - {location: left, physical_id: 100, constraints: {x: fixed, y: fixed}}
loads:
  - {location: right, physical_id: 200, force: {x: 0, y: -1000}}
```

### Simply Supported Beam
```yaml
boundary_conditions:
  - {location: left, physical_id: 100, constraints: {x: fixed, y: fixed}}
  - {location: right, physical_id: 101, constraints: {x: free, y: fixed}}
loads:
  - {location: top, physical_id: 200, force: {y: -1000}}
```

### Fixed-Fixed Beam
```yaml
boundary_conditions:
  - {location: left, physical_id: 100, constraints: {x: fixed, y: fixed}}
  - {location: right, physical_id: 101, constraints: {x: fixed, y: fixed}}
loads:
  - {location: top, physical_id: 200, force: {y: -1000}}
```

## Geometry Types

| Type | Parameters |
|------|------------|
| `rectangle` | `length`, `height` |
| `lshape` | `width`, `height`, `flange_width`, `flange_height` |
| `plate_with_hole` | `length`, `height`, `hole_x`, `hole_y`, `hole_radius` |

## Element Types

| Type | Description | Nodes per Element |
|------|-------------|-------------------|
| `triangle` | Linear triangle | 3 |
| `triangle6` | Quadratic triangle | 6 |
| `quad` | Linear quadrilateral | 4 |

## Boundary Condition Locations

- `left` - Left edge
- `right` - Right edge
- `top` - Top edge
- `bottom` - Bottom edge

## Material Properties

| Property | Description | Typical Range |
|----------|-------------|---------------|
| `E` | Young's modulus (Pa) | 1e9 - 1e12 |
| `nu` | Poisson's ratio | 0.0 - 0.49 |

Common values:
- Steel: E=200e9, nu=0.3
- Aluminum: E=70e9, nu=0.33
- Concrete: E=25e9, nu=0.2

## Output Files

| File | Contents |
|------|----------|
| `nodes.txt` | Node ID, X, Y, BC_X, BC_Y |
| `eles.txt` | Element ID, Type, Material, Node IDs |
| `mater.txt` | E, nu, thickness |
| `loads.txt` | Node ID, Force_X, Force_Y |

## Validation Rules

- ✅ Dimensions must be > 0
- ✅ Poisson's ratio: 0 ≤ nu < 0.5
- ✅ Physical IDs must be unique
- ✅ Layers cannot overlap
- ✅ Mesh size must be > 0

## Examples

Run provided examples:
```bash
# Layered plate (your current model)
python fem_converter.py examples/layered_plate.yaml

# Simple cantilever
python fem_converter.py examples/simple_plate.yaml

# Create from Python
cd examples
python create_cantilever.py
python ../fem_converter.py cantilever_beam.yaml
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| `No module named 'pydantic'` | `pip install pydantic pyyaml` |
| `GMSH executable not found` | Verify `gmsh.exe` exists in project dir |
| `Duplicate physical_id` | Use unique IDs for all entities |
| `ValidationError` | Check error message for specific field |

## Tips

1. **Start simple:** Use `examples/simple_plate.yaml` as template
2. **Validate early:** YAML errors caught before GMSH runs
3. **Use names:** Give meaningful names to BCs and loads
4. **Version control:** Commit YAML files, not .msh files
5. **Parametric studies:** Use Python API to generate multiple configs

## Full Documentation

- **Tutorial:** `GETTING_STARTED.md`
- **Complete reference:** `README.md`
- **Implementation details:** `PHASE1_SUMMARY.md`
