# Existing Folder

This folder is for storing SolidsPy input files that you want to analyze using the "Analyze Existing Model" option in the FEM Builder application.

## Required Files

Place your existing SolidsPy model files here:

- **nodes.txt** - Node coordinates and boundary conditions (required)
- **eles.txt** - Element connectivity and material IDs (required)
- **mater.txt** - Material properties (E, ν) (required)
- **loads.txt** - Applied loads at nodes (optional)

## File Format

### nodes.txt (N x 5)
```
node_id    x        y      bc_x  bc_y
0        0.000    0.000    -1    -1
1        0.100    0.000     0     0
...
```

### eles.txt (M x 7+)
```
ele_id  type  mat_id  node1  node2  node3  [node4...]
0       1     0       0      1      2
1       1     0       1      3      2
...
```

### mater.txt (K x 2)
```
2.1e+11  0.3
7.0e+10  0.33
...
```

### loads.txt (L x 3)
```
node_id    Fx         Fy
10        1000.0      0.0
11        1000.0      0.0
...
```

## Usage

1. Place your .txt files in this folder
2. In the FEM Builder application, go to "📊 Analyze Existing Model"
3. Upload each file individually
4. Click "Run SolidsPy Solver"
5. View results

## Notes

- Files can have any prefix (e.g., `model_nodes.txt`, `test_eles.txt`)
- Boundary conditions: -1 = fixed, 0 = free
