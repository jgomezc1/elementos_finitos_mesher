# Getting Started with FEM Preprocessing Automation

## Phase 1 Implementation Complete! 🎉

Your FEM preprocessing workflow has been fully automated. Here's what's been created:

## What's New

### ✅ Complete Automation Pipeline

```
YAML Config → .geo Generation → GMSH Mesh → SolidsPy Files
```

### ✅ Three Ways to Create Models

1. **YAML Configuration Files** (Recommended)
2. **Python Template Library** (Programmatic)
3. **Legacy plate.py** (Still works)

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `numpy` - Numerical computing
- `meshio` - Mesh file I/O
- `pydantic` - Configuration validation
- `pyyaml` - YAML parsing

### 2. Verify GMSH

GMSH executable (`gmsh.exe`) is already in your project directory. You're ready to go!

## Quick Examples

### Example 1: Recreate Your Current plate.py Model

**Old way:**
```bash
python plate.py  # Hardcoded parameters
```

**New way:**
```bash
python fem_converter.py examples/layered_plate.yaml -o output
```

**Result:** Same output files, but now:
- ✅ No hardcoded values
- ✅ Reusable configuration
- ✅ Version controllable
- ✅ Self-documenting

### Example 2: Create Custom Model with Python

```python
from fem_templates import LayeredPlate

# Create model
model = LayeredPlate(length=2.0, height=1.0, mesh_size=0.1)

# Add materials
model.add_layer("steel", y_min=0.0, y_max=0.5, E=200e9, nu=0.3)
model.add_layer("aluminum", y_min=0.5, y_max=1.0, E=70e9, nu=0.33)

# Add boundary conditions
model.add_bc("left", x="fixed", y="free")
model.add_bc("bottom", x="free", y="fixed")

# Add loads
model.add_load("top", fy=-1000.0)

# Save configuration
model.save("my_model.yaml")
```

Then convert:
```bash
python fem_converter.py my_model.yaml
```

### Example 3: Simple Cantilever Beam

```bash
python fem_converter.py examples/simple_plate.yaml -o results
```

Output:
```
results/
├── nodes.txt    # Ready for SolidsPy
├── eles.txt     # Ready for SolidsPy
├── mater.txt    # Ready for SolidsPy
└── loads.txt    # Ready for SolidsPy
```

## File Structure Overview

```
elementos_finitos_mesher/
│
├── fem_converter.py          ← Main script (run this!)
├── fem_config.py             ← Configuration schema
├── geo_generator.py          ← GMSH .geo generator
├── fem_templates.py          ← Python template library
├── preprocesor.py            ← Mesh conversion (updated)
│
├── examples/
│   ├── layered_plate.yaml          ← Your current model
│   ├── simple_plate.yaml           ← Cantilever beam
│   ├── create_layered_plate.py     ← Python API demo
│   └── create_cantilever.py        ← Python API demo
│
├── README.md                 ← Full documentation
├── GETTING_STARTED.md        ← This file
├── requirements.txt          ← Dependencies
└── gmsh.exe                  ← Mesh generator
```

## Step-by-Step Workflow

### Starting from Scratch

**Step 1:** Create YAML configuration

```yaml
# my_model.yaml
model_name: my_analysis
description: Custom FEA model

geometry:
  type: rectangle
  length: 3.0
  height: 1.5

mesh:
  size: 0.05
  element_type: triangle

material:
  E: 2.0e11
  nu: 0.3

boundary_conditions:
  - name: fixed_left
    location: left
    physical_id: 100
    constraints:
      x: fixed
      y: fixed

loads:
  - name: distributed_load
    location: top
    physical_id: 200
    force:
      x: 0.0
      y: -5000.0
    distribution: uniform
```

**Step 2:** Convert to SolidsPy format

```bash
python fem_converter.py my_model.yaml -o analysis_output
```

**Step 3:** Check output

```bash
ls analysis_output/
# nodes.txt  eles.txt  mater.txt  loads.txt
```

**Step 4:** Use with SolidsPy

```python
import solidspy as sp

# Load files
nodes, mats, elements, loads = sp.readin(folder='analysis_output/')

# Run analysis
disp = sp.solids_auto(nodes, mats, elements, loads)
```

## Common Use Cases

### Use Case 1: Parametric Study

Create multiple configurations programmatically:

```python
from fem_templates import RectangularPlate

for length in [1.0, 2.0, 3.0, 4.0]:
    beam = RectangularPlate(
        length=length,
        height=1.0,
        E=2.1e11,
        nu=0.3,
        model_name=f"beam_L{length}"
    )
    beam.add_bc("left", x="fixed", y="fixed")
    beam.add_load("right", fy=-1000.0)
    beam.save(f"beam_L{length}.yaml")
```

Then batch convert:
```bash
for file in beam_*.yaml; do
    python fem_converter.py "$file" -o "results_$(basename $file .yaml)"
done
```

### Use Case 2: Multi-Material Layers

```yaml
layers:
  - name: concrete
    region: [0.0, 0.3]
    physical_id: 1
    material:
      E: 25e9
      nu: 0.2

  - name: steel_rebar
    region: [0.3, 0.35]
    physical_id: 2
    material:
      E: 200e9
      nu: 0.3

  - name: concrete_top
    region: [0.35, 0.6]
    physical_id: 3
    material:
      E: 25e9
      nu: 0.2
```

### Use Case 3: Complex Boundary Conditions

```yaml
boundary_conditions:
  - name: fixed_base
    location: bottom
    physical_id: 100
    constraints:
      x: fixed
      y: fixed

  - name: roller_left
    location: left
    physical_id: 101
    constraints:
      x: fixed
      y: free

  - name: roller_right
    location: right
    physical_id: 102
    constraints:
      x: fixed
      y: free
```

## Advantages Over Old Workflow

| Feature | Old (plate.py) | New (fem_converter) |
|---------|----------------|---------------------|
| Configuration | Hardcoded | YAML file |
| Reusability | Copy/edit code | Reuse YAML |
| Version Control | Difficult | Easy (text files) |
| Validation | Runtime errors | Schema validation |
| Documentation | Comments | Self-documenting |
| Parametric Studies | Manual | Programmatic |
| Error Messages | Cryptic | Clear & helpful |
| Templates | None | 4 geometry types |

## Migration Guide

### Migrating from plate.py

**Your current plate.py:**
```python
# Hardcoded values
nf, els1_array = msh.ele_writer(cells, cell_data, "triangle", 100, 3, 0, 0)
nodes_array = msh.boundary_conditions(cells, cell_data, 300, nodes_array, -1, 0)
cargas = msh.loading(cells, cell_data, 500, 0.0, -2.0)
```

**Equivalent YAML:**
```yaml
layers:
  - physical_id: 100  # Instead of magic number 100
    material:
      E: 1.0e6
      nu: 0.3

boundary_conditions:
  - physical_id: 300  # Named boundary condition
    constraints:
      x: fixed
      y: free

loads:
  - physical_id: 500  # Named load
    force:
      x: 0.0
      y: -2.0
```

**Benefits:**
- Physical IDs have context (names)
- Material properties visible
- Easy to modify without code changes

## Troubleshooting

### Error: "No module named 'pydantic'"

```bash
pip install pydantic pyyaml
```

### Error: "GMSH executable not found"

Verify `gmsh.exe` is in the project directory:
```bash
ls gmsh.exe
```

### Error: "Duplicate physical_id"

Each physical group needs a unique ID. Check your YAML:
```yaml
# ✗ Wrong
boundary_conditions:
  - physical_id: 100
  - physical_id: 100  # Duplicate!

# ✓ Correct
boundary_conditions:
  - physical_id: 100
  - physical_id: 101
```

### Validation Error

Pydantic provides helpful messages:
```
ValidationError: region[0] must be < region[1]
```

This tells you exactly what's wrong and where.

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test with provided example:**
   ```bash
   python fem_converter.py examples/layered_plate.yaml
   ```

3. **Create your first model:**
   - Copy `examples/simple_plate.yaml`
   - Modify parameters
   - Run converter

4. **Try Python API:**
   ```bash
   cd examples
   python create_cantilever.py
   python ../fem_converter.py cantilever_beam.yaml
   ```

5. **Read full documentation:**
   - See `README.md` for complete reference

## Support

For issues or questions:
1. Check `README.md` for detailed documentation
2. Review examples in `examples/` directory
3. Examine error messages (they're designed to be helpful!)

---

**Congratulations! Your FEM preprocessing is now fully automated.** 🚀
