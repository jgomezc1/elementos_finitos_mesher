# FEM Preprocessing Automation

Automated preprocessing pipeline for Finite Element Analysis, converting YAML configurations into SolidsPy-compatible input files.

## 🆕 NEW: Web-Based GUI (Phase 2B)

**Create FEM models without coding!**

```bash
# Install dependencies (includes Streamlit)
pip install -r requirements.txt

# Launch web interface
streamlit run fem_gui.py
# or double-click: launch_gui.bat (Windows)
```

Browser opens at `http://localhost:8501` with interactive model builder!

**See [GUI Guide](docs/GUI_GUIDE.md) for complete tutorial.**

---

## Quick Start (Command Line)

```bash
# Install dependencies
pip install -r requirements.txt

# Convert YAML to SolidsPy format
python fem_converter.py examples/layered_plate.yaml -o output/
```

## Usage

### Method 1: Web GUI (Recommended for Beginners) 🆕
```bash
streamlit run fem_gui.py
```
- Interactive interface
- No coding required
- Real-time validation
- Immediate download

### Method 2: YAML Configuration
```bash
python fem_converter.py my_model.yaml -o results/
```

### Method 3: Python API
```python
from fem_templates import RectangularPlate

beam = RectangularPlate(length=4.0, height=1.0, E=2.1e11, nu=0.3)
beam.add_bc("left", x="fixed", y="fixed")
beam.add_load("right", fy=-1000)
beam.save("beam.yaml")
```

### Method 4: From Jupyter Notebook
```python
# Option 1: Shell command
!python fem_converter.py my_model.yaml -o output/

# Option 2: Direct import (recommended)
from fem_config import FEMConfig
from fem_converter import FEMConverter

config = FEMConfig.from_yaml("my_model.yaml")
converter = FEMConverter(config, output_dir="./output")
converter.convert()
```

## Documentation

📚 **Complete documentation available in [`docs/`](docs/) folder:**

- **[GUI User Guide](docs/GUI_GUIDE.md)** - Web interface tutorial 🆕
- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Step-by-step tutorial
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Command cheat sheet
- **[Complete Reference](docs/README.md)** - Full documentation
- **[Phase 1 Summary](docs/PHASE1_SUMMARY.md)** - Core implementation
- **[Phase 2B Summary](docs/PHASE2B_SUMMARY.md)** - GUI implementation 🆕

## Project Structure

```
elementos_finitos_mesher/
│
├── fem_converter.py          # Main conversion script
├── fem_config.py             # Configuration schema
├── fem_gui.py                # Streamlit GUI application
├── geo_generator.py          # GMSH .geo generator
├── fem_templates.py          # Python template library
├── preprocesor.py            # Mesh processing
│
├── examples/                 # Example YAML configurations
├── Geo_files/                # GMSH geometry files for "Load GEO File" option
├── existing/                 # Folder for SolidsPy input files to analyze
├── docs/                     # Documentation
├── solidspy/                 # FEA solver library
├── templates/                # GMSH geometry templates
├── output/                   # Working directory for generated files
└── requirements.txt          # Dependencies
```

## Folders for GUI Usage

- **`Geo_files/`** - Place your GMSH .geo files here for the "Load GEO File" option
  - Includes example geometries: dam, flamant, inclusion, pilotes, ring
- **`existing/`** - Place your SolidsPy .txt files here for the "Analyze Existing Model" option
  - Upload nodes.txt, eles.txt, mater.txt, loads.txt for direct analysis

## Examples

See [`examples/`](examples/) directory:
- `layered_plate.yaml` - Multi-material plate
- `simple_plate.yaml` - Cantilever beam
- `lshape.yaml` - L-shaped structure
- `create_layered_plate.py` - Python API example
- `create_cantilever.py` - Python API example

## Features

✅ YAML-based configuration
✅ Python template library
✅ Automatic mesh generation
✅ SolidsPy compatibility
✅ Schema validation
✅ Multiple geometry types (rectangle, L-shape, plate with hole)

## Requirements

- Python 3.6+
- numpy >= 1.20.0
- meshio >= 4.0.0
- pydantic >= 2.0.0
- pyyaml >= 6.0.0
- GMSH (included as gmsh.exe)

## License

Part of the elementos_finitos_mesher toolkit.
