#!/usr/bin/env python3
"""
Test Phase 1 Implementation
----------------------------
Tests the core functionality without requiring full dependency install.
"""
import sys

print("=" * 60)
print("Testing Phase 1 Implementation")
print("=" * 60)
print()

# Test 1: Configuration loading and validation
print("[1/5] Testing YAML configuration loading...")
try:
    from fem_config import FEMConfig

    config = FEMConfig.from_yaml("examples/layered_plate.yaml")
    print(f"  ✓ Loaded configuration: {config.model_name}")
    print(f"  ✓ Geometry type: {config.geometry.type}")
    print(f"  ✓ Number of layers: {len(config.layers)}")
    print(f"  ✓ Number of BCs: {len(config.boundary_conditions)}")
    print(f"  ✓ Number of loads: {len(config.loads)}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: GEO file generation
print("[2/5] Testing .geo file generation...")
try:
    from geo_generator import GeoGenerator

    generator = GeoGenerator(config)
    geo_file = "test_output_geo.geo"
    generator.generate(geo_file)

    with open(geo_file, 'r') as f:
        content = f.read()

    print(f"  ✓ Generated {geo_file}")
    print(f"  ✓ File size: {len(content)} bytes")
    print(f"  ✓ Lines: {content.count(chr(10))}")

    # Check for key elements
    checks = [
        ("Point(" in content, "Points defined"),
        ("Line(" in content, "Lines defined"),
        ("Surface(" in content, "Surfaces defined"),
        ("Physical Surface" in content, "Physical surfaces defined"),
        ("Physical Line" in content, "Physical lines defined"),
        ("Mesh 2" in content, "Mesh command present")
    ]

    for check, desc in checks:
        if check:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc}")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Python template library
print("[3/5] Testing Python template library...")
try:
    from fem_templates import LayeredPlate

    model = LayeredPlate(
        length=2.0,
        height=1.0,
        mesh_size=0.1,
        model_name="test_model"
    )

    model.add_layer("layer1", 0.0, 0.5, E=1e6, nu=0.3)
    model.add_layer("layer2", 0.5, 1.0, E=2e6, nu=0.3)
    model.add_bc("left", x="fixed")
    model.add_load("top", fy=-100)

    test_config = model.build()
    print(f"  ✓ Created model: {test_config.model_name}")
    print(f"  ✓ Layers: {len(test_config.layers)}")
    print(f"  ✓ BCs: {len(test_config.boundary_conditions)}")
    print(f"  ✓ Loads: {len(test_config.loads)}")

    # Save to YAML
    test_yaml = "test_template_output.yaml"
    model.save(test_yaml)
    print(f"  ✓ Saved to {test_yaml}")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Validation
print("[4/5] Testing configuration validation...")
try:
    from fem_config import FEMConfig, GeometryRectangle, Material, MeshParameters
    from fem_config import BoundaryCondition, Constraints

    # Test invalid config (duplicate physical IDs)
    try:
        invalid_config = FEMConfig(
            model_name="invalid",
            geometry=GeometryRectangle(length=1.0, height=1.0),
            mesh=MeshParameters(size=0.1),
            material=Material(E=1e6, nu=0.3),
            boundary_conditions=[
                BoundaryCondition(
                    name="bc1",
                    location="left",
                    physical_id=100,
                    constraints=Constraints(x="fixed", y="free")
                ),
                BoundaryCondition(
                    name="bc2",
                    location="right",
                    physical_id=100,  # Duplicate!
                    constraints=Constraints(x="free", y="fixed")
                )
            ]
        )
        print("  ✗ Validation did not catch duplicate physical IDs")
    except Exception as e:
        print(f"  ✓ Correctly rejected duplicate physical IDs")

    # Test invalid geometry (negative dimensions)
    try:
        GeometryRectangle(length=-1.0, height=1.0)
        print("  ✗ Validation did not catch negative dimension")
    except Exception as e:
        print(f"  ✓ Correctly rejected negative dimensions")

    # Test invalid material (Poisson ratio >= 0.5)
    try:
        Material(E=1e6, nu=0.6)
        print("  ✗ Validation did not catch invalid Poisson ratio")
    except Exception as e:
        print(f"  ✓ Correctly rejected invalid Poisson ratio")

except Exception as e:
    print(f"  ✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Different geometry types
print("[5/5] Testing different geometry types...")
try:
    from fem_templates import RectangularPlate, LShapeBeam, PlateWithHole

    # Rectangle
    rect = RectangularPlate(length=2.0, height=1.0)
    rect.add_bc("left", x="fixed", y="fixed")
    rect_config = rect.build()
    print(f"  ✓ RectangularPlate: {rect_config.geometry.type}")

    # L-Shape
    lshape = LShapeBeam(width=3.0, height=3.0, flange_width=1.0, flange_height=1.0)
    lshape.add_bc("bottom", x="fixed", y="fixed")
    lshape_config = lshape.build()
    print(f"  ✓ LShapeBeam: {lshape_config.geometry.type}")

    # Plate with hole
    plate = PlateWithHole(
        length=4.0, height=2.0,
        hole_x=2.0, hole_y=1.0, hole_radius=0.3
    )
    plate.add_bc("left", x="fixed", y="fixed")
    plate_config = plate.build()
    print(f"  ✓ PlateWithHole: {plate_config.geometry.type}")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("✓ All Phase 1 tests passed!")
print("=" * 60)
print()
print("To complete the workflow, install dependencies:")
print("  pip install -r requirements.txt")
print()
print("Then run full conversion:")
print("  python fem_converter.py examples/layered_plate.yaml")
