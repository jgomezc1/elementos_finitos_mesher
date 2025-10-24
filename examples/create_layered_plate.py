"""
Example: Creating a layered plate using Python API
"""
import sys
sys.path.append('..')

from fem_templates import LayeredPlate

# Create layered plate model
model = LayeredPlate(
    length=2.0,
    height=1.0,
    mesh_size=0.1,
    model_name="layered_plate_python"
)

# Add material layers
model.add_layer("lower_layer", y_min=0.0, y_max=0.5, E=1.0e6, nu=0.3)
model.add_layer("upper_layer", y_min=0.5, y_max=1.0, E=2.0e6, nu=0.3)

# Add boundary conditions
model.add_bc("left", x="fixed", y="free", name="lateral_support")
model.add_bc("bottom", x="free", y="fixed", name="bottom_support")

# Add loads
model.add_load("top", fx=0.0, fy=-2.0, name="top_pressure")

# Set description
model.set_description("Two-layer plate created with Python API")

# Save to YAML
model.save("layered_plate_python.yaml")

print("✓ Created layered_plate_python.yaml")
print("\nTo convert to SolidsPy format, run:")
print("  python ../fem_converter.py layered_plate_python.yaml")
