# Geo_files Folder

This folder contains GMSH geometry (.geo) files for use with the "Load GEO File" option in the FEM Builder application.

## Available Geometry Files

- **dam.geo** - Dam structure analysis
- **flamant.geo** - Flamant problem (point load on half-space)
- **inclusion.geo** - Inclusion problem (embedded material)
- **pilotes.geo** - Pile foundation analysis
- **ring.geo** - Ring structure under loading

## Usage

1. In the FEM Builder application, go to "📂 Load GEO File"
2. Upload one of these .geo files
3. Define materials for physical groups
4. Set boundary conditions
5. Apply loads
6. Generate mesh and run analysis

## Creating Your Own .geo Files

You can create custom GMSH geometry files and place them in this folder. Refer to GMSH documentation for geometry scripting syntax.
