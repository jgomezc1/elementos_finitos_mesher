"""
FEM Configuration Schema
------------------------

Pydantic models for validating YAML configuration files.
"""
from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field, validator
import yaml


class Material(BaseModel):
    """Material properties"""
    E: float = Field(..., description="Young's modulus", gt=0)
    nu: float = Field(..., description="Poisson's ratio", ge=0, lt=0.5)

    class Config:
        extra = "forbid"


class GeometryRectangle(BaseModel):
    """Rectangle geometry parameters"""
    type: Literal["rectangle"] = "rectangle"
    length: float = Field(..., gt=0)
    height: float = Field(..., gt=0)

    class Config:
        extra = "forbid"


class GeometryLShape(BaseModel):
    """L-Shape geometry parameters"""
    type: Literal["lshape"] = "lshape"
    width: float = Field(..., gt=0, description="Total width")
    height: float = Field(..., gt=0, description="Total height")
    flange_width: float = Field(..., gt=0, description="Horizontal flange width")
    flange_height: float = Field(..., gt=0, description="Vertical flange height")

    @validator('flange_width')
    def validate_flange_width(cls, v, values):
        if 'width' in values and v > values['width']:
            raise ValueError('flange_width must be <= width')
        return v

    @validator('flange_height')
    def validate_flange_height(cls, v, values):
        if 'height' in values and v > values['height']:
            raise ValueError('flange_height must be <= height')
        return v

    class Config:
        extra = "forbid"


class GeometryPlateWithHole(BaseModel):
    """Plate with circular hole geometry"""
    type: Literal["plate_with_hole"] = "plate_with_hole"
    length: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    hole_x: float = Field(..., description="Hole center x-coordinate")
    hole_y: float = Field(..., description="Hole center y-coordinate")
    hole_radius: float = Field(..., gt=0)

    @validator('hole_x')
    def validate_hole_x(cls, v, values):
        if 'length' in values:
            if v < 0 or v > values['length']:
                raise ValueError(f'hole_x must be between 0 and {values["length"]}')
        return v

    @validator('hole_y')
    def validate_hole_y(cls, v, values):
        if 'height' in values:
            if v < 0 or v > values['height']:
                raise ValueError(f'hole_y must be between 0 and {values["height"]}')
        return v

    class Config:
        extra = "forbid"


class Layer(BaseModel):
    """Material layer definition for layered geometries"""
    name: str
    region: List[float] = Field(..., min_items=2, max_items=2,
                                 description="[y_min, y_max] for layer")
    physical_id: int = Field(..., ge=1, description="Physical surface ID")
    material: Material

    @validator('region')
    def validate_region(cls, v):
        if v[0] >= v[1]:
            raise ValueError('region[0] must be < region[1]')
        return v

    class Config:
        extra = "forbid"


class Constraints(BaseModel):
    """Boundary condition constraints"""
    x: Literal["fixed", "free"] = "free"
    y: Literal["fixed", "free"] = "free"

    class Config:
        extra = "forbid"


class BoundaryCondition(BaseModel):
    """Boundary condition definition"""
    name: str
    location: Union[str, List[float]] = Field(
        ...,
        description="Location: 'left', 'right', 'top', 'bottom' or [x1,y1,x2,y2] for line"
    )
    physical_id: int = Field(..., ge=1, description="Physical line ID")
    constraints: Constraints

    class Config:
        extra = "forbid"


class Force(BaseModel):
    """Force components"""
    x: float = 0.0
    y: float = 0.0

    class Config:
        extra = "forbid"


class Load(BaseModel):
    """Load definition"""
    name: str
    location: Union[str, List[float]] = Field(
        ...,
        description="Location: 'left', 'right', 'top', 'bottom' or [x1,y1,x2,y2] for line"
    )
    physical_id: int = Field(..., ge=1, description="Physical line ID")
    force: Force = Field(..., description="Total force on the line")
    distribution: Literal["uniform"] = "uniform"

    class Config:
        extra = "forbid"


class MeshParameters(BaseModel):
    """Mesh generation parameters"""
    size: float = Field(..., gt=0, description="Characteristic mesh size")
    element_type: Literal["triangle", "triangle6", "quad"] = "triangle"
    algorithm: Optional[int] = Field(None, ge=1, le=9, description="GMSH meshing algorithm")

    class Config:
        extra = "forbid"


class FEMConfig(BaseModel):
    """Complete FEM model configuration"""
    model_name: str = Field(..., description="Name of the model")
    description: Optional[str] = None

    geometry: Union[GeometryRectangle, GeometryLShape, GeometryPlateWithHole]
    mesh: MeshParameters

    # For simple single-material models
    material: Optional[Material] = None

    # For multi-material layered models
    layers: Optional[List[Layer]] = None

    boundary_conditions: List[BoundaryCondition]
    loads: Optional[List[Load]] = None

    @validator('layers')
    def validate_layers_or_material(cls, v, values):
        """Ensure either material or layers is specified, not both"""
        if v is not None and values.get('material') is not None:
            raise ValueError('Specify either "material" or "layers", not both')
        if v is None and values.get('material') is None:
            raise ValueError('Must specify either "material" or "layers"')
        return v

    @validator('layers')
    def validate_no_overlapping_layers(cls, v):
        """Ensure layers don't overlap"""
        if v is None:
            return v

        # Check for overlapping regions
        for i, layer1 in enumerate(v):
            for layer2 in v[i+1:]:
                y1_min, y1_max = layer1.region
                y2_min, y2_max = layer2.region

                # Check overlap
                if not (y1_max <= y2_min or y2_max <= y1_min):
                    raise ValueError(
                        f'Layers "{layer1.name}" and "{layer2.name}" overlap'
                    )
        return v

    @validator('boundary_conditions')
    def validate_unique_physical_ids(cls, v, values):
        """Ensure all physical IDs are unique"""
        all_ids = set()

        # Collect BC IDs
        for bc in v:
            if bc.physical_id in all_ids:
                raise ValueError(f'Duplicate physical_id: {bc.physical_id}')
            all_ids.add(bc.physical_id)

        # Collect load IDs
        if 'loads' in values and values['loads']:
            for load in values['loads']:
                if load.physical_id in all_ids:
                    raise ValueError(f'Duplicate physical_id: {load.physical_id}')
                all_ids.add(load.physical_id)

        # Collect layer IDs
        if 'layers' in values and values['layers']:
            for layer in values['layers']:
                if layer.physical_id in all_ids:
                    raise ValueError(f'Duplicate physical_id: {layer.physical_id}')
                all_ids.add(layer.physical_id)

        return v

    class Config:
        extra = "forbid"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'FEMConfig':
        """Load configuration from YAML file"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, yaml_path: str):
        """Save configuration to YAML file"""
        with open(yaml_path, 'w') as f:
            yaml.dump(
                self.dict(exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False
            )

    def get_solidspy_element_type(self) -> int:
        """Map mesh element type to SolidsPy element type ID"""
        mapping = {
            "triangle": 3,
            "triangle6": 2,
            "quad": 1
        }
        return mapping[self.mesh.element_type]
