"""
GEO File Generator
------------------

Generates GMSH .geo files from FEM configuration.
"""
from fem_config import FEMConfig, GeometryRectangle, GeometryLShape, GeometryPlateWithHole
from typing import Dict, List, Tuple


class GeoGenerator:
    """Generates GMSH .geo files from configuration"""

    def __init__(self, config: FEMConfig):
        self.config = config
        self.point_counter = 1
        self.line_counter = 1
        self.surface_counter = 1
        self.loop_counter = 1
        self.points: Dict[str, int] = {}
        self.lines: Dict[str, int] = {}
        self.surfaces: Dict[str, int] = {}

        # Map location names to line IDs
        self.location_to_lines: Dict[str, List[int]] = {
            'left': [],
            'right': [],
            'top': [],
            'bottom': []
        }

    def generate(self, output_path: str):
        """Generate .geo file"""
        geo_lines = []

        # Header
        geo_lines.extend(self._generate_header())

        # Geometry-specific generation
        if isinstance(self.config.geometry, GeometryRectangle):
            if self.config.layers:
                geo_lines.extend(self._generate_layered_rectangle())
            else:
                geo_lines.extend(self._generate_simple_rectangle())
        elif isinstance(self.config.geometry, GeometryLShape):
            geo_lines.extend(self._generate_lshape())
        elif isinstance(self.config.geometry, GeometryPlateWithHole):
            geo_lines.extend(self._generate_plate_with_hole())

        # Physical groups
        geo_lines.extend(self._generate_physical_groups())

        # Mesh settings
        geo_lines.extend(self._generate_mesh_settings())

        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(geo_lines))

    def _generate_header(self) -> List[str]:
        """Generate file header"""
        lines = [
            "// GMSH Geometry File",
            f"// Auto-generated from: {self.config.model_name}",
        ]
        if self.config.description:
            lines.append(f"// Description: {self.config.description}")
        lines.extend([
            f"// Element size: {self.config.mesh.size}",
            "",
            "SetFactory(\"OpenCASCADE\");",
            ""
        ])
        return lines

    def _generate_simple_rectangle(self) -> List[str]:
        """Generate simple rectangle geometry"""
        geom = self.config.geometry
        mesh_size = self.config.mesh.size
        lines = []

        # Points
        p1 = self._add_point(0, 0, mesh_size, "bottom_left")
        p2 = self._add_point(geom.length, 0, mesh_size, "bottom_right")
        p3 = self._add_point(geom.length, geom.height, mesh_size, "top_right")
        p4 = self._add_point(0, geom.height, mesh_size, "top_left")

        lines.extend([
            f"Point({p1}) = {{0, 0, 0, {mesh_size}}};",
            f"Point({p2}) = {{{geom.length}, 0, 0, {mesh_size}}};",
            f"Point({p3}) = {{{geom.length}, {geom.height}, 0, {mesh_size}}};",
            f"Point({p4}) = {{0, {geom.height}, 0, {mesh_size}}};",
            ""
        ])

        # Lines
        l_bottom = self._add_line(p1, p2, "bottom")
        l_right = self._add_line(p2, p3, "right")
        l_top = self._add_line(p3, p4, "top")
        l_left = self._add_line(p4, p1, "left")

        lines.extend([
            f"Line({l_bottom}) = {{{p1}, {p2}}};  // bottom",
            f"Line({l_right}) = {{{p2}, {p3}}};  // right",
            f"Line({l_top}) = {{{p3}, {p4}}};  // top",
            f"Line({l_left}) = {{{p4}, {p1}}};  // left",
            ""
        ])

        self.location_to_lines['bottom'] = [l_bottom]
        self.location_to_lines['right'] = [l_right]
        self.location_to_lines['top'] = [l_top]
        self.location_to_lines['left'] = [l_left]

        # Surface
        loop_id = self.loop_counter
        self.loop_counter += 1
        surf_id = self.surface_counter
        self.surface_counter += 1

        lines.extend([
            f"Line Loop({loop_id}) = {{{l_bottom}, {l_right}, {l_top}, {l_left}}};",
            f"Plane Surface({surf_id}) = {{{loop_id}}};",
            ""
        ])

        self.surfaces['main'] = surf_id

        return lines

    def _generate_layered_rectangle(self) -> List[str]:
        """Generate layered rectangle geometry"""
        geom = self.config.geometry
        mesh_size = self.config.mesh.size
        layers = self.config.layers
        lines = []

        # Sort layers by y-coordinate
        sorted_layers = sorted(layers, key=lambda l: l.region[0])

        # Collect all y-coordinates
        y_coords = [0.0]
        for layer in sorted_layers:
            if layer.region[1] not in y_coords:
                y_coords.append(layer.region[1])

        # Create points
        point_grid = {}  # (x, y) -> point_id
        for y in y_coords:
            p_left = self._add_point(0, y, mesh_size)
            p_right = self._add_point(geom.length, y, mesh_size)
            point_grid[(0, y)] = p_left
            point_grid[(geom.length, y)] = p_right
            lines.append(f"Point({p_left}) = {{0, {y}, 0, {mesh_size}}};")
            lines.append(f"Point({p_right}) = {{{geom.length}, {y}, 0, {mesh_size}}};")

        lines.append("")

        # Create lines and surfaces for each layer
        left_lines = []
        right_lines = []

        for layer in sorted_layers:
            y_bottom = layer.region[0]
            y_top = layer.region[1]

            p_bl = point_grid[(0, y_bottom)]
            p_br = point_grid[(geom.length, y_bottom)]
            p_tr = point_grid[(geom.length, y_top)]
            p_tl = point_grid[(0, y_top)]

            l_bottom = self._add_line(p_bl, p_br)
            l_right = self._add_line(p_br, p_tr)
            l_top = self._add_line(p_tr, p_tl)
            l_left = self._add_line(p_tl, p_bl)

            left_lines.append(l_left)
            right_lines.append(l_right)

            lines.extend([
                f"Line({l_bottom}) = {{{p_bl}, {p_br}}};",
                f"Line({l_right}) = {{{p_br}, {p_tr}}};",
                f"Line({l_top}) = {{{p_tr}, {p_tl}}};",
                f"Line({l_left}) = {{{p_tl}, {p_bl}}};",
            ])

            # Create surface for this layer
            loop_id = self.loop_counter
            self.loop_counter += 1
            surf_id = self.surface_counter
            self.surface_counter += 1

            lines.extend([
                f"Line Loop({loop_id}) = {{{l_bottom}, {l_right}, {l_top}, {l_left}}};",
                f"Plane Surface({surf_id}) = {{{loop_id}}};",
                f"Physical Surface(\"{layer.name}\", {layer.physical_id}) = {{{surf_id}}};",
                ""
            ])

            # Track boundary lines
            if y_bottom == 0:
                self.location_to_lines['bottom'] = [l_bottom]
            if y_top == geom.height:
                self.location_to_lines['top'] = [l_top]

        self.location_to_lines['left'] = left_lines
        self.location_to_lines['right'] = right_lines

        return lines

    def _generate_lshape(self) -> List[str]:
        """Generate L-shape geometry"""
        geom = self.config.geometry
        mesh_size = self.config.mesh.size
        lines = []

        # L-shape points (7 points)
        # Create horizontal flange and vertical flange
        p1 = self._add_point(0, 0, mesh_size)
        p2 = self._add_point(geom.flange_width, 0, mesh_size)
        p3 = self._add_point(geom.flange_width, geom.height - geom.flange_height, mesh_size)
        p4 = self._add_point(geom.width, geom.height - geom.flange_height, mesh_size)
        p5 = self._add_point(geom.width, geom.height, mesh_size)
        p6 = self._add_point(0, geom.height, mesh_size)

        lines.extend([
            f"Point({p1}) = {{0, 0, 0, {mesh_size}}};",
            f"Point({p2}) = {{{geom.flange_width}, 0, 0, {mesh_size}}};",
            f"Point({p3}) = {{{geom.flange_width}, {geom.height - geom.flange_height}, 0, {mesh_size}}};",
            f"Point({p4}) = {{{geom.width}, {geom.height - geom.flange_height}, 0, {mesh_size}}};",
            f"Point({p5}) = {{{geom.width}, {geom.height}, 0, {mesh_size}}};",
            f"Point({p6}) = {{0, {geom.height}, 0, {mesh_size}}};",
            ""
        ])

        # Lines
        l1 = self._add_line(p1, p2)
        l2 = self._add_line(p2, p3)
        l3 = self._add_line(p3, p4)
        l4 = self._add_line(p4, p5)
        l5 = self._add_line(p5, p6)
        l6 = self._add_line(p6, p1)

        lines.extend([
            f"Line({l1}) = {{{p1}, {p2}}};",
            f"Line({l2}) = {{{p2}, {p3}}};",
            f"Line({l3}) = {{{p3}, {p4}}};",
            f"Line({l4}) = {{{p4}, {p5}}};",
            f"Line({l5}) = {{{p5}, {p6}}};",
            f"Line({l6}) = {{{p6}, {p1}}};",
            ""
        ])

        # Surface
        loop_id = self.loop_counter
        self.loop_counter += 1
        surf_id = self.surface_counter
        self.surface_counter += 1

        lines.extend([
            f"Line Loop({loop_id}) = {{{l1}, {l2}, {l3}, {l4}, {l5}, {l6}}};",
            f"Plane Surface({surf_id}) = {{{loop_id}}};",
            ""
        ])

        self.surfaces['main'] = surf_id
        self.location_to_lines['bottom'] = [l1]
        self.location_to_lines['left'] = [l6]
        self.location_to_lines['right'] = [l2, l4]
        self.location_to_lines['top'] = [l5]

        return lines

    def _generate_plate_with_hole(self) -> List[str]:
        """Generate plate with hole geometry"""
        geom = self.config.geometry
        mesh_size = self.config.mesh.size
        lines = []

        # Outer rectangle
        p1 = self._add_point(0, 0, mesh_size)
        p2 = self._add_point(geom.length, 0, mesh_size)
        p3 = self._add_point(geom.length, geom.height, mesh_size)
        p4 = self._add_point(0, geom.height, mesh_size)

        # Hole center and points on circle perimeter (for mesh control)
        p_center = self._add_point(geom.hole_x, geom.hole_y, mesh_size)
        p_right = self._add_point(geom.hole_x + geom.hole_radius, geom.hole_y, mesh_size)
        p_top = self._add_point(geom.hole_x, geom.hole_y + geom.hole_radius, mesh_size)
        p_left = self._add_point(geom.hole_x - geom.hole_radius, geom.hole_y, mesh_size)
        p_bottom = self._add_point(geom.hole_x, geom.hole_y - geom.hole_radius, mesh_size)

        lines.extend([
            f"Point({p1}) = {{0, 0, 0, {mesh_size}}};",
            f"Point({p2}) = {{{geom.length}, 0, 0, {mesh_size}}};",
            f"Point({p3}) = {{{geom.length}, {geom.height}, 0, {mesh_size}}};",
            f"Point({p4}) = {{0, {geom.height}, 0, {mesh_size}}};",
            f"Point({p_center}) = {{{geom.hole_x}, {geom.hole_y}, 0, {mesh_size}}};",
            f"Point({p_right}) = {{{geom.hole_x + geom.hole_radius}, {geom.hole_y}, 0, {mesh_size}}};",
            f"Point({p_top}) = {{{geom.hole_x}, {geom.hole_y + geom.hole_radius}, 0, {mesh_size}}};",
            f"Point({p_left}) = {{{geom.hole_x - geom.hole_radius}, {geom.hole_y}, 0, {mesh_size}}};",
            f"Point({p_bottom}) = {{{geom.hole_x}, {geom.hole_y - geom.hole_radius}, 0, {mesh_size}}};",
            ""
        ])

        # Outer lines
        l1 = self._add_line(p1, p2)
        l2 = self._add_line(p2, p3)
        l3 = self._add_line(p3, p4)
        l4 = self._add_line(p4, p1)

        lines.extend([
            f"Line({l1}) = {{{p1}, {p2}}};",
            f"Line({l2}) = {{{p2}, {p3}}};",
            f"Line({l3}) = {{{p3}, {p4}}};",
            f"Line({l4}) = {{{p4}, {p1}}};",
        ])

        self.location_to_lines['bottom'] = [l1]
        self.location_to_lines['right'] = [l2]
        self.location_to_lines['top'] = [l3]
        self.location_to_lines['left'] = [l4]

        # Circle (hole) - using 4 arcs for better mesh control
        arc1 = self.line_counter
        self.line_counter += 1
        arc2 = self.line_counter
        self.line_counter += 1
        arc3 = self.line_counter
        self.line_counter += 1
        arc4 = self.line_counter
        self.line_counter += 1

        lines.extend([
            f"Circle({arc1}) = {{{p_right}, {p_center}, {p_top}}};",
            f"Circle({arc2}) = {{{p_top}, {p_center}, {p_left}}};",
            f"Circle({arc3}) = {{{p_left}, {p_center}, {p_bottom}}};",
            f"Circle({arc4}) = {{{p_bottom}, {p_center}, {p_right}}};",
            ""
        ])

        # Surface with hole
        outer_loop = self.loop_counter
        self.loop_counter += 1
        hole_loop = self.loop_counter
        self.loop_counter += 1
        surf_id = self.surface_counter
        self.surface_counter += 1

        lines.extend([
            f"Line Loop({outer_loop}) = {{{l1}, {l2}, {l3}, {l4}}};",
            f"Curve Loop({hole_loop}) = {{{arc1}, {arc2}, {arc3}, {arc4}}};",
            f"Plane Surface({surf_id}) = {{{outer_loop}, {hole_loop}}};",
            ""
        ])

        self.surfaces['main'] = surf_id
        self.location_to_lines['hole'] = [arc1, arc2, arc3, arc4]

        return lines

    def _generate_physical_groups(self) -> List[str]:
        """Generate physical group definitions"""
        lines = ["// Physical Groups", ""]

        # Physical surfaces (if not already defined for layers)
        if not self.config.layers and self.config.material:
            surf_ids = [str(sid) for sid in self.surfaces.values()]
            lines.append(
                f'Physical Surface("material", 1) = {{{", ".join(surf_ids)}}};'
            )
            lines.append("")

        # Physical lines for boundary conditions
        if self.config.boundary_conditions:
            lines.append("// Boundary Conditions")
            for bc in self.config.boundary_conditions:
                line_ids = self._resolve_location(bc.location)
                line_ids_str = ", ".join(map(str, line_ids))
                lines.append(
                    f'Physical Line("{bc.name}", {bc.physical_id}) = {{{line_ids_str}}};'
                )
            lines.append("")

        # Physical lines for loads
        if self.config.loads:
            lines.append("// Loads")
            for load in self.config.loads:
                line_ids = self._resolve_location(load.location)
                line_ids_str = ", ".join(map(str, line_ids))
                lines.append(
                    f'Physical Line("{load.name}", {load.physical_id}) = {{{line_ids_str}}};'
                )
            lines.append("")

        return lines

    def _generate_mesh_settings(self) -> List[str]:
        """Generate mesh generation settings"""
        lines = ["// Mesh Settings"]
        if self.config.mesh.algorithm:
            lines.append(f"Mesh.Algorithm = {self.config.mesh.algorithm};")
        lines.extend(["Mesh 2;", ""])
        return lines

    def _add_point(self, x: float, y: float, size: float, name: str = None) -> int:
        """Add a point and return its ID"""
        point_id = self.point_counter
        self.point_counter += 1
        if name:
            self.points[name] = point_id
        return point_id

    def _add_line(self, p1: int, p2: int, name: str = None) -> int:
        """Add a line and return its ID"""
        line_id = self.line_counter
        self.line_counter += 1
        if name:
            self.lines[name] = line_id
        return line_id

    def _resolve_location(self, location) -> List[int]:
        """Resolve location string/list to line IDs"""
        if isinstance(location, str):
            if location in self.location_to_lines:
                return self.location_to_lines[location]
            else:
                raise ValueError(f"Unknown location: {location}")
        else:
            # Custom line coordinates [x1, y1, x2, y2]
            # For now, this would require more complex logic
            raise NotImplementedError("Custom line coordinates not yet supported")
