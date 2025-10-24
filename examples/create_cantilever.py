"""
Example: Creating a simple cantilever beam using Python API
"""
import sys
sys.path.append('..')

from fem_templates import RectangularPlate

# Create cantilever beam
beam = RectangularPlate(
    length=4.0,
    height=1.0,
    E=2.1e11,
    nu=0.3,
    mesh_size=0.1,
    model_name="cantilever_beam"
)

# Fixed left end
beam.add_bc("left", x="fixed", y="fixed", name="fixed_end")

# Load on right end
beam.add_load("right", fx=0.0, fy=-1000.0, name="tip_load")

# Description
beam.set_description("Cantilever beam with tip load")

# Save
beam.save("cantilever_beam.yaml")

print("✓ Created cantilever_beam.yaml")
print("\nTo convert to SolidsPy format, run:")
print("  python ../fem_converter.py cantilever_beam.yaml")
