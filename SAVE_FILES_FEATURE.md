# Save All Files to Local Folder Feature

## 🆕 New Feature Added to GUI!

You can now save **ALL generated files** (YAML, GEO, MSH, and TXT) to a local folder with a custom prefix - perfect for organizing multiple models and complete project archives!

---

## How It Works

### 1. Convert Your Model
In the GUI, after clicking **🔄 Convert to SolidsPy Format**, you'll see a new section:

```
💾 Save to Local Folder
┌────────────────────────────────────────────────┐
│ File Prefix: [Ho        ]                     │
│ Output Folder: [./output        ]             │
│ [💾 Save All Files]                            │
└────────────────────────────────────────────────┘
```

### 2. Enter Your Prefix
- **File Prefix:** Enter your custom prefix (e.g., "Ho", "Model1", "Test", etc.)
- **Output Folder:** Specify where to save (default: `./output`)
  - Folder will be created if it doesn't exist
  - Can be relative (`./output`) or absolute path

### 3. Click "💾 Save All Files"

**Result:**
```
output/
├── Ho.yaml        ✅ Configuration file
├── Ho.geo         ✅ GMSH geometry
├── Ho.msh         ✅ GMSH mesh
├── Honodes.txt    ✅ SolidsPy nodes
├── Hoeles.txt     ✅ SolidsPy elements
├── Homater.txt    ✅ SolidsPy materials
└── Holoads.txt    ✅ SolidsPy loads
```

**7 files saved in one click!**

---

## Use Cases

### 1. Complete Project Archive

**Everything in one place:**
```
output/
├── Ho.yaml        # Configuration (version control this!)
├── Ho.geo         # GMSH geometry (for modifications)
├── Ho.msh         # Generated mesh (for visualization)
├── Honodes.txt    # Analysis input
├── Hoeles.txt     # Analysis input
├── Homater.txt    # Analysis input
└── Holoads.txt    # Analysis input
```

**Benefits:**
- ✅ Complete reproducibility
- ✅ Can regenerate mesh from .geo
- ✅ Can modify config and reconvert
- ✅ All files organized together

### 2. Direct SolidsPy Integration

```python
import solidspy.solids as sol

# Load with your custom prefix
nodes, mats, elements, loads = sol.readin(folder='output/', prefix='Ho')

# Run FEA
disp = sol.solids_auto(nodes, mats, elements, loads)
```

### 3. Organize Multiple Models

```
output/
├── Beam1.yaml
├── Beam1.geo
├── Beam1.msh
├── Beam1nodes.txt
├── Beam1eles.txt
├── Beam1mater.txt
├── Beam1loads.txt
├── Beam2.yaml
├── Beam2.geo
├── Beam2.msh
├── Beam2nodes.txt
├── Beam2eles.txt
├── Beam2mater.txt
├── Beam2loads.txt
└── ...
```

### 4. Batch Processing

Create multiple models with different prefixes:
```python
for i, length in enumerate([2.0, 4.0, 6.0]):
    # Create model in GUI
    # Use prefix: f"Length{length}"
    # Save to output/
    pass
```

Then process all:
```python
for length in [2.0, 4.0, 6.0]:
    prefix = f"Length{length}"
    nodes, mats, elements, loads = sol.readin('output/', prefix=prefix)
    results[length] = sol.solids_auto(nodes, mats, elements, loads)
```

### 5. Version Control & Collaboration

**Commit to Git:**
```bash
git add output/Ho.yaml
git commit -m "Add cantilever beam model"
```

**Colleague can regenerate:**
```bash
python fem_converter.py output/Ho.yaml -o output/
```

**Or view mesh in GMSH:**
```bash
gmsh output/Ho.msh
```

---

## Examples

### Example 1: Simple Cantilever

**Prefix:** `Cantilever`
**Output Folder:** `./beam_analysis`

**Creates:**
```
beam_analysis/
├── Cantiilevernodes.txt
├── Cantiilevereles.txt
├── Cantilevermater.txt
└── Cantiileverloads.txt
```

### Example 2: Parametric Study

**Model 1:**
- Prefix: `Mesh01`
- Output: `./parametric`

**Model 2:**
- Prefix: `Mesh005`
- Output: `./parametric`

**Model 3:**
- Prefix: `Mesh001`
- Output: `./parametric`

**Result:**
```
parametric/
├── Mesh01nodes.txt
├── Mesh01eles.txt
├── Mesh01mater.txt
├── Mesh01loads.txt
├── Mesh005nodes.txt
├── Mesh005eles.txt
├── Mesh005mater.txt
├── Mesh005loads.txt
├── Mesh001nodes.txt
├── Mesh001eles.txt
├── Mesh001mater.txt
└── Mesh001loads.txt
```

Then compare mesh convergence!

---

## Benefits

### ✅ **Complete Archive**
- Save all 7 files with one click
- YAML, GEO, MSH, and 4 TXT files
- Everything needed for complete reproducibility

### ✅ **Convenience**
- No need to download files individually
- All files in one organized location
- Ready for immediate use

### ✅ **Organization**
- Custom prefixes for each model
- Dedicated output folders
- Easy to find and manage files

### ✅ **Reproducibility**
- YAML config for version control
- GEO file for geometry modifications
- MSH file for mesh visualization
- Complete project archive

### ✅ **SolidsPy Integration**
- Direct compatibility with SolidsPy `readin()` function
- Just specify folder and prefix
- No manual file handling

### ✅ **Version Control Friendly**
- Keep multiple versions of same model
- Track mesh refinement studies
- Parametric variations
- Git-friendly text files

### ✅ **Collaboration**
- Share complete model packages
- Colleagues can regenerate everything
- View meshes in GMSH
- Modify and rerun easily

### ✅ **Automation**
- Files ready for batch processing
- Scripted analysis workflows
- Reproducible research
- Parametric studies

---

## Default Behavior

- **Default Prefix:** Uses your model name from the GUI
- **Default Folder:** `./output` (in current directory)
- **Auto-Create:** Folder is created if it doesn't exist
- **Overwrite:** Files with same name will be overwritten

---

## Error Handling

### "Permission denied"
- Check you have write permissions to the folder
- Try a different output folder

### "Invalid path"
- Use valid folder path
- On Windows: `C:/Users/YourName/Documents/FEM/output`
- On Mac/Linux: `/home/yourname/fem/output` or `./output`

### "File exists"
- Files will be overwritten if they exist
- Use different prefix to keep both versions

---

## Tips

1. **Meaningful Prefixes**
   - ✅ `BeamL4` (descriptive)
   - ✅ `Plate_Fine` (clear)
   - ❌ `M1` (unclear)
   - ❌ `Test` (not specific)

2. **Folder Organization**
   ```
   project/
   ├── models/        (YAML configs)
   ├── output/        (txt files for SolidsPy)
   └── results/       (analysis results)
   ```

3. **Prefix Convention**
   - Include model type: `Cantilever`, `Plate`, `Bracket`
   - Include parameter: `Mesh01`, `Load1000`, `Steel`
   - Include date: `Model_2024_01_15`

4. **Batch Naming**
   ```
   Study1_Case1
   Study1_Case2
   Study1_Case3
   ```

---

## Screenshot Guide (Text Version)

```
After clicking "Convert to SolidsPy Format":
┌──────────────────────────────────────────────┐
│ ✅ SolidsPy Output Files                     │
├──────────────────────────────────────────────┤
│ [nodes.txt] [eles.txt] [mater.txt] [loads]  │
│                                              │
│ (Tab content with preview and individual    │
│  download buttons)                           │
└──────────────────────────────────────────────┘

New Section Appears Below:
┌──────────────────────────────────────────────┐
│ 💾 Save to Local Folder                     │
├──────────────────────────────────────────────┤
│ File Prefix:     [Ho          ]             │
│ Output Folder:   [./output    ]             │
│                                              │
│                  [💾 Save All Files]         │
└──────────────────────────────────────────────┘

After Clicking Save:
┌──────────────────────────────────────────────┐
│ ✅ Files saved successfully to: `./output/`  │
│                                              │
│ Files created:                               │
│ - `output/Honodes.txt`                      │
│ - `output/Hoeles.txt`                       │
│ - `output/Homater.txt`                      │
│ - `output/Holoads.txt`                      │
└──────────────────────────────────────────────┘
```

---

## Updated Workflow

### Complete GUI Workflow with Save Feature:

1. **Create Model** in Model Builder
2. **Generate** YAML configuration
3. **Convert** to SolidsPy format
4. **Review** output files in tabs
5. **Enter Prefix** (e.g., "Ho")
6. **Choose Folder** (e.g., "./output")
7. **Click "💾 Save All Files"**
8. **Files Created** - Ready to use!

### Then Use with SolidsPy:

```python
import solidspy.solids as sol

# Load your model
nodes, mats, elements, loads = sol.readin('output/', prefix='Ho')

# Solve
disp = sol.solids_auto(nodes, mats, elements, loads)

# Done!
```

---

## Comparison with Download Buttons

| Feature | Individual Downloads | Save to Folder |
|---------|---------------------|----------------|
| **Speed** | 4 clicks | 1 click |
| **Organization** | Browser downloads | Custom folder |
| **Naming** | Fixed names | Custom prefix |
| **Location** | Browser default | Your choice |
| **Batch** | Manual | Automatic |
| **SolidsPy** | Rename manually | Ready to use |

---

## Frequently Asked Questions

**Q: Can I change the prefix after saving?**
A: Yes, just change the prefix and click save again.

**Q: Will it overwrite existing files?**
A: Yes, files with the same name will be overwritten.

**Q: Can I use absolute paths?**
A: Yes, like `C:/MyProject/output` or `/home/user/fem/output`

**Q: What if the folder doesn't exist?**
A: It will be created automatically.

**Q: Can I save to multiple folders?**
A: Yes, just change the output folder and save again.

**Q: Is the prefix mandatory?**
A: No, you can use an empty prefix (files will be `nodes.txt`, etc.)

**Q: Can I use special characters in prefix?**
A: Stick to letters, numbers, and underscores for compatibility.

---

## Summary

The **Save to Local Folder** feature makes it easy to:

- ✅ Save all output files at once
- ✅ Organize with custom prefixes
- ✅ Integrate directly with SolidsPy
- ✅ Manage multiple models efficiently

**Perfect for production workflows and batch analysis!**

---

See **[GUI Guide](docs/GUI_GUIDE.md)** for complete GUI documentation.
