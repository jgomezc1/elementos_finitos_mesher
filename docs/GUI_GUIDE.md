# FEM Model Builder - GUI User Guide

## 🎯 Welcome to Phase 2B!

The **FEM Model Builder** is a web-based graphical interface for creating finite element models without writing any code. Perfect for engineers, students, and researchers who want to quickly set up FEA models.

---

## 🚀 Quick Start

### Installation

1. **Install dependencies** (includes Streamlit):
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the GUI**:

   **Windows:**
   ```bash
   launch_gui.bat
   ```

   **Mac/Linux:**
   ```bash
   streamlit run fem_gui.py
   ```

3. **Access the interface**:
   - Browser will open automatically at `http://localhost:8501`
   - If not, manually navigate to the URL shown in terminal

---

## 📱 Interface Overview

### Three Main Pages

#### 1. 🏗️ **Model Builder**
Create new FEM models interactively

#### 2. 📚 **Load Example**
Start from pre-built example models

#### 3. ℹ️ **About**
Documentation and help

---

## 🏗️ Creating a Model (Step-by-Step)

### Step 1: Model Information

- **Model Name**: Unique identifier for your model
- **Description**: Optional brief description

### Step 2: Select Geometry Type

Choose from 4 geometry types:

#### **Rectangle** - Simple Rectangular Plate
```
┌─────────────────┐
│                 │
│   Rectangle     │
│                 │
└─────────────────┘
```
**Parameters:**
- Length (m)
- Height (m)

**Use Cases:**
- Cantilever beams
- Simple plates
- Beam bending analysis

---

#### **Layered Plate** - Multi-Material Layers
```
┌─────────────────┐
│   Material 2    │  ← Upper Layer
├─────────────────┤
│   Material 1    │  ← Lower Layer
└─────────────────┘
```
**Parameters:**
- Length (m)
- Height (m)
- Number of layers
- Each layer: Y-range, material properties

**Use Cases:**
- Composite materials
- Layered structures
- Material interface studies

---

#### **L-Shape** - L-Shaped Beam
```
┌───────┐
│       │
│       │  ← Vertical Flange
├───┐   │
│   │   │
│   └───┘
│       │  ← Horizontal Flange
└───────┘
```
**Parameters:**
- Total width (m)
- Total height (m)
- Horizontal flange width (m)
- Vertical flange height (m)

**Use Cases:**
- Brackets
- Structural beams
- Corner joints

---

#### **Plate with Hole** - Stress Concentration
```
┌─────────────────┐
│                 │
│       ●         │  ← Circular Hole
│                 │
└─────────────────┘
```
**Parameters:**
- Plate length (m)
- Plate height (m)
- Hole center X (m)
- Hole center Y (m)
- Hole radius (m)

**Use Cases:**
- Stress concentration analysis
- Perforated plates
- Fastener hole studies

---

### Step 3: Material Properties

#### **Single Material** (Rectangle, L-Shape, Plate with Hole)
- **Young's Modulus (E)**: Material stiffness (Pa)
- **Poisson's Ratio (ν)**: Lateral strain ratio (0.0 - 0.49)

**Common Values:**
| Material | E (Pa) | ν |
|----------|--------|---|
| Steel | 200e9 | 0.30 |
| Aluminum | 70e9 | 0.33 |
| Concrete | 25e9 | 0.20 |
| Wood | 10e9 | 0.35 |

#### **Multi-Material** (Layered Plate)
For each layer specify:
- **Name**: Layer identifier
- **Y min/max**: Vertical position range
- **Physical ID**: Unique identifier (1, 2, 3, ...)
- **E and ν**: Material properties

---

### Step 4: Boundary Conditions

Define where the structure is constrained.

**Number of BCs**: How many boundaries to constrain (0-10)

For each BC:
- **Name**: Identifier (e.g., "fixed_left")
- **Location**: Which edge
  - `left` - Left edge
  - `right` - Right edge
  - `top` - Top edge
  - `bottom` - Bottom edge
- **Physical ID**: Unique number (100, 101, 102, ...)
- **X Constraint**:
  - `fixed` - No movement in X direction
  - `free` - Free to move in X
- **Y Constraint**:
  - `fixed` - No movement in Y direction
  - `free` - Free to move in Y

**Common Configurations:**

| Support Type | X | Y | Description |
|--------------|---|---|-------------|
| Fixed | fixed | fixed | Fully constrained (wall) |
| Roller (horizontal) | free | fixed | Vertical support |
| Roller (vertical) | fixed | free | Horizontal support |

**Example: Cantilever Beam**
```yaml
BC 1: left, X=fixed, Y=fixed  # Fixed support
```

**Example: Simply Supported Beam**
```yaml
BC 1: left, X=fixed, Y=fixed   # Pin support
BC 2: right, X=free, Y=fixed   # Roller support
```

---

### Step 5: Loads

Define forces applied to the structure.

**Number of Loads**: How many load applications (0-10)

For each load:
- **Name**: Identifier (e.g., "top_pressure")
- **Location**: Which edge receives the load
- **Physical ID**: Unique number (200, 201, 202, ...)
- **Force X (N)**: Horizontal force component
- **Force Y (N)**: Vertical force component

**Sign Convention:**
- **Positive X**: → (right)
- **Negative X**: ← (left)
- **Positive Y**: ↑ (up)
- **Negative Y**: ↓ (down)

**Example: Downward Load**
```yaml
Load: top edge, Fx=0, Fy=-1000  # 1000 N downward
```

---

### Step 6: Mesh Settings

Control mesh density and element type.

**Mesh Size (m)**:
- Smaller = finer mesh, more accuracy, longer computation
- Typical range: 0.01 - 0.5
- **Recommendation**: Start with 0.1, refine as needed

**Element Type**:
- `triangle` - 3-node linear triangles (fastest, most common)
- `triangle6` - 6-node quadratic triangles (better accuracy)
- `quad` - 4-node quadrilaterals

**Mesh Algorithm** (optional):
- GMSH meshing algorithm (1-9)
- Default is usually fine
- Advanced users only

---

### Step 7: Generate Model

Click **🚀 Generate Model Configuration**

The system will:
1. ✅ Validate all inputs
2. ✅ Create YAML configuration
3. ✅ Display configuration preview
4. ✅ Enable download and conversion

---

## 📥 Output Options

### Option 1: Download YAML

Click **📥 Download YAML** to save the configuration file.

**Use later with:**
```bash
python fem_converter.py my_model.yaml -o results/
```

### Option 2: Convert to SolidsPy

Click **🔄 Convert to SolidsPy Format** for immediate conversion.

**Generates:**
- `nodes.txt` - Nodal coordinates and BCs
- `eles.txt` - Element connectivity
- `mater.txt` - Material properties
- `loads.txt` - Load vectors

**Three ways to get the files:**

1. **Download individually** from the tabs shown
2. **Download with browser** - Standard browser downloads
3. **💾 Save All Files to Local Folder** - NEW! Save everything at once with custom prefix

#### Save All Files to Local Folder (NEW!)

After conversion, you'll see a new section:

**File Prefix:** Enter your prefix (e.g., "Ho")
**Output Folder:** Specify folder (default: `./output`)
**Click "💾 Save All Files"**

**Result:**
```
output/
├── Ho.yaml        # Configuration file
├── Ho.geo         # GMSH geometry
├── Ho.msh         # GMSH mesh
├── Honodes.txt    # SolidsPy nodes
├── Hoeles.txt     # SolidsPy elements
├── Homater.txt    # SolidsPy materials
└── Holoads.txt    # SolidsPy loads
```

**7 files saved in one click!**

**Perfect for:**
- Complete project archives
- Using directly with SolidsPy (just specify the prefix!)
- Organizing multiple models
- Version control (commit the YAML!)
- Batch analysis workflows
- Viewing meshes in GMSH

**Use with SolidsPy:**
```python
import solidspy.solids as sol

# Load files with your custom prefix
nodes, mats, elements, loads = sol.readin(folder='output/', prefix='Ho')

# Run analysis
disp = sol.solids_auto(nodes, mats, elements, loads)
```

**View mesh in GMSH:**
```bash
gmsh output/Ho.msh
```

**Regenerate from config:**
```bash
python fem_converter.py output/Ho.yaml -o output/
```

**Benefits:**
- ✅ Complete archive (all source and output files)
- ✅ All files in one place
- ✅ Custom naming for organization
- ✅ No manual file renaming
- ✅ Ready for immediate analysis
- ✅ Fully reproducible
- ✅ Easy to share with colleagues

---

## 📚 Using Example Models

### Load an Example

1. Go to **📚 Load Example** page
2. Select an example:
   - **Simple Cantilever Beam**
   - **Layered Plate**
3. Click **Load This Example**
4. Return to **🏗️ Model Builder**
5. Modify as needed

---

## 💡 Tips & Best Practices

### Getting Started
- ✅ Start with an example model
- ✅ Modify one parameter at a time
- ✅ Use meaningful names for BCs and loads
- ✅ Keep physical IDs unique

### Mesh Quality
- 🔹 Start with coarse mesh (0.1)
- 🔹 Refine near stress concentrations
- 🔹 For plate with hole: use mesh_size ≤ 0.01

### Physical IDs
- 🔸 Materials: 1, 2, 3, ...
- 🔸 BCs: 100, 101, 102, ...
- 🔸 Loads: 200, 201, 202, ...
- 🔸 **All must be unique!**

### Common Errors

**Error:** "Duplicate physical_id"
- **Solution**: Make sure all IDs are unique across materials, BCs, and loads

**Error:** "region[0] must be < region[1]"
- **Solution**: For layers, Y min must be less than Y max

**Error:** "flange_width must be <= width"
- **Solution**: For L-shape, flanges can't be larger than total dimensions

---

## 🎨 Common Model Templates

### 1. Cantilever Beam

**Geometry:** Rectangle (4.0 x 1.0 m)
**Material:** Steel (E=200e9, ν=0.3)
**BC:** Left edge fixed (X=fixed, Y=fixed)
**Load:** Right edge, Fy=-1000 N

---

### 2. Simply Supported Beam

**Geometry:** Rectangle (6.0 x 1.0 m)
**Material:** Steel (E=200e9, ν=0.3)
**BC 1:** Left edge pin (X=fixed, Y=fixed)
**BC 2:** Right edge roller (X=free, Y=fixed)
**Load:** Top edge center, Fy=-2000 N

---

### 3. Composite Plate

**Geometry:** Layered Plate (2.0 x 1.0 m)
**Layer 1:** Carbon fiber (0.0-0.2 m, E=150e9, ν=0.25)
**Layer 2:** Honeycomb core (0.2-0.8 m, E=1e9, ν=0.3)
**Layer 3:** Carbon fiber (0.8-1.0 m, E=150e9, ν=0.25)
**BC:** All edges fixed
**Load:** Uniform pressure on top

---

### 4. Stress Concentration Study

**Geometry:** Plate with Hole (4.0 x 2.0 m, hole at 2.0, 1.0, r=0.3)
**Material:** Aluminum (E=70e9, ν=0.33)
**BC:** Left edge fixed
**Load:** Right edge tension (Fx=10000 N)
**Mesh:** Fine (size=0.01 for accuracy near hole)

---

## 🔧 Troubleshooting

### GUI Won't Start

**Problem:** Command not found
**Solution:**
```bash
pip install streamlit
```

**Problem:** Port already in use
**Solution:**
```bash
streamlit run fem_gui.py --server.port 8502
```

---

### Validation Errors

The GUI validates inputs in real-time. If you see an error:

1. Read the error message carefully
2. Check the highlighted field
3. Adjust the value
4. Try generating again

---

### GMSH Not Found

**Problem:** "GMSH executable not found"
**Solution:** Verify `gmsh.exe` is in project directory

---

## 🎓 Workflow Examples

### Research Workflow

1. Create model in GUI
2. Download YAML
3. Version control the YAML file
4. Share with collaborators
5. They regenerate from YAML

### Teaching Workflow

1. Instructor creates example models
2. Students load examples in GUI
3. Students modify parameters
4. Observe how changes affect results

### Production Workflow

1. Create template in GUI
2. Download YAML
3. Modify YAML programmatically for parametric studies
4. Batch convert with `fem_converter.py`

---

## 📖 Related Documentation

- **[Quick Reference](QUICK_REFERENCE.md)** - Command-line usage
- **[Complete Reference](README.md)** - Full API documentation
- **[Getting Started](GETTING_STARTED.md)** - Installation guide
- **[Phase 2 Summary](PHASE2_SUMMARY.md)** - GUI implementation details

---

## 🆘 Getting Help

### In-App Help
- Click **ℹ️ About** page for quick tips
- Hover over input fields for tooltips

### Documentation
- Check `docs/` folder
- Read error messages carefully

### Examples
- Start with provided examples
- Modify incrementally

---

## 🎉 Success Checklist

Before clicking generate:

- [ ] Model name is unique and descriptive
- [ ] Geometry parameters are positive
- [ ] Material properties are realistic
- [ ] All physical IDs are unique
- [ ] At least one BC is defined
- [ ] Mesh size is appropriate (0.01 - 0.5)
- [ ] Load directions use correct signs

---

**Congratulations! You're ready to create FEM models with the GUI!** 🚀

For advanced features, see the Python API in `docs/README.md`.
