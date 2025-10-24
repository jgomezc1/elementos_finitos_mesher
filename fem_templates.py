"""
FEM Template Library
--------------------

Python API for creating common FEM geometries.
"""
from fem_config import (
    FEMConfig, GeometryRectangle, GeometryLShape, GeometryPlateWithHole,
    Material, Layer, BoundaryCondition, Load, MeshParameters,
    Constraints, Force
)
from typing import List, Literal


class BaseTemplate:
    """Base class for FEM templates"""

    def __init__(self, model_name: str = "model"):
        self.model_name = model_name
        self.description = None
        self.mesh_size = 0.1
        self.mesh_algorithm = None
        self.element_type = "triangle"
        self.boundary_conditions = []
        self.loads = []
        self._next_physical_id = 100

    def set_mesh(self, size: float, element_type: str = "triangle", algorithm: int = None):
        """Set mesh parameters"""
        self.mesh_size = size
        self.element_type = element_type
        self.mesh_algorithm = algorithm
        return self

    def set_description(self, description: str):
        """Set model description"""
        self.description = description
        return self

    def add_bc(self, location: str, x: str = "free", y: str = "free", name: str = None):
        """Add boundary condition"""
        if name is None:
            name = f"bc_{location}"

        bc = BoundaryCondition(
            name=name,
            location=location,
            physical_id=self._next_physical_id,
            constraints=Constraints(x=x, y=y)
        )
        self.boundary_conditions.append(bc)
        self._next_physical_id += 1
        return self

    def add_load(self, location: str, fx: float = 0.0, fy: float = 0.0,
                 distribution: str = "uniform", name: str = None):
        """Add load"""
        if name is None:
            name = f"load_{location}"

        load = Load(
            name=name,
            location=location,
            physical_id=self._next_physical_id,
            force=Force(x=fx, y=fy),
            distribution=distribution
        )
        self.loads.append(load)
        self._next_physical_id += 1
        return self

    def _get_mesh_params(self):
        """Get mesh parameters"""
        return MeshParameters(
            size=self.mesh_size,
            element_type=self.element_type,
            algorithm=self.mesh_algorithm
        )


class RectangularPlate(BaseTemplate):
    """Simple rectangular plate with single material"""

    def __init__(self, length: float, height: float, E: float = 1e6, nu: float = 0.3,
                 mesh_size: float = 0.1, model_name: str = "rectangular_plate"):
        super().__init__(model_name)
        self.length = length
        self.height = height
        self.E = E
        self.nu = nu
        self.mesh_size = mesh_size

    def set_material(self, E: float, nu: float):
        """Set material properties"""
        self.E = E
        self.nu = nu
        return self

    def build(self) -> FEMConfig:
        """Build FEMConfig object"""
        geometry = GeometryRectangle(
            length=self.length,
            height=self.height
        )

        material = Material(E=self.E, nu=self.nu)

        config = FEMConfig(
            model_name=self.model_name,
            description=self.description,
            geometry=geometry,
            mesh=self._get_mesh_params(),
            material=material,
            boundary_conditions=self.boundary_conditions,
            loads=self.loads if self.loads else None
        )

        return config

    def save(self, yaml_path: str):
        """Save configuration to YAML file"""
        config = self.build()
        config.to_yaml(yaml_path)


class LayeredPlate(BaseTemplate):
    """Rectangular plate with multiple material layers"""

    def __init__(self, length: float, height: float, mesh_size: float = 0.1,
                 model_name: str = "layered_plate"):
        super().__init__(model_name)
        self.length = length
        self.height = height
        self.mesh_size = mesh_size
        self.layers = []
        self._material_physical_id = 1

    def add_layer(self, name: str, y_min: float, y_max: float, E: float, nu: float):
        """Add a material layer"""
        layer = Layer(
            name=name,
            region=[y_min, y_max],
            physical_id=self._material_physical_id,
            material=Material(E=E, nu=nu)
        )
        self.layers.append(layer)
        self._material_physical_id += 1
        self._next_physical_id = max(self._next_physical_id, self._material_physical_id + 100)
        return self

    def build(self) -> FEMConfig:
        """Build FEMConfig object"""
        if not self.layers:
            raise ValueError("At least one layer must be added")

        geometry = GeometryRectangle(
            length=self.length,
            height=self.height
        )

        config = FEMConfig(
            model_name=self.model_name,
            description=self.description,
            geometry=geometry,
            mesh=self._get_mesh_params(),
            layers=self.layers,
            boundary_conditions=self.boundary_conditions,
            loads=self.loads if self.loads else None
        )

        return config

    def save(self, yaml_path: str):
        """Save configuration to YAML file"""
        config = self.build()
        config.to_yaml(yaml_path)


class LShapeBeam(BaseTemplate):
    """L-shaped beam geometry"""

    def __init__(self, width: float, height: float,
                 flange_width: float, flange_height: float,
                 E: float = 1e6, nu: float = 0.3,
                 mesh_size: float = 0.1,
                 model_name: str = "lshape_beam"):
        super().__init__(model_name)
        self.width = width
        self.height = height
        self.flange_width = flange_width
        self.flange_height = flange_height
        self.E = E
        self.nu = nu
        self.mesh_size = mesh_size

    def set_material(self, E: float, nu: float):
        """Set material properties"""
        self.E = E
        self.nu = nu
        return self

    def build(self) -> FEMConfig:
        """Build FEMConfig object"""
        geometry = GeometryLShape(
            width=self.width,
            height=self.height,
            flange_width=self.flange_width,
            flange_height=self.flange_height
        )

        material = Material(E=self.E, nu=self.nu)

        config = FEMConfig(
            model_name=self.model_name,
            description=self.description,
            geometry=geometry,
            mesh=self._get_mesh_params(),
            material=material,
            boundary_conditions=self.boundary_conditions,
            loads=self.loads if self.loads else None
        )

        return config

    def save(self, yaml_path: str):
        """Save configuration to YAML file"""
        config = self.build()
        config.to_yaml(yaml_path)


class PlateWithHole(BaseTemplate):
    """Rectangular plate with circular hole"""

    def __init__(self, length: float, height: float,
                 hole_x: float, hole_y: float, hole_radius: float,
                 E: float = 1e6, nu: float = 0.3,
                 mesh_size: float = 0.001,
                 model_name: str = "plate_with_hole"):
        super().__init__(model_name)
        self.length = length
        self.height = height
        self.hole_x = hole_x
        self.hole_y = hole_y
        self.hole_radius = hole_radius
        self.E = E
        self.nu = nu
        self.mesh_size = mesh_size

    def set_material(self, E: float, nu: float):
        """Set material properties"""
        self.E = E
        self.nu = nu
        return self

    def build(self) -> FEMConfig:
        """Build FEMConfig object"""
        geometry = GeometryPlateWithHole(
            length=self.length,
            height=self.height,
            hole_x=self.hole_x,
            hole_y=self.hole_y,
            hole_radius=self.hole_radius
        )

        material = Material(E=self.E, nu=self.nu)

        config = FEMConfig(
            model_name=self.model_name,
            description=self.description,
            geometry=geometry,
            mesh=self._get_mesh_params(),
            material=material,
            boundary_conditions=self.boundary_conditions,
            loads=self.loads if self.loads else None
        )

        return config

    def save(self, yaml_path: str):
        """Save configuration to YAML file"""
        config = self.build()
        config.to_yaml(yaml_path)


# Convenience function
def create_model(geometry_type: str, **kwargs):
    """Factory function to create templates"""
    templates = {
        "rectangle": RectangularPlate,
        "layered_plate": LayeredPlate,
        "lshape": LShapeBeam,
        "plate_with_hole": PlateWithHole
    }

    if geometry_type not in templates:
        raise ValueError(
            f"Unknown geometry type: {geometry_type}. "
            f"Available: {list(templates.keys())}"
        )

    return templates[geometry_type](**kwargs)
