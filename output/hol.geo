// GMSH Geometry File
// Auto-generated from: my_model
// Element size: 0.1

SetFactory("OpenCASCADE");

Point(1) = {0, 0, 0, 0.1};
Point(2) = {4.0, 0, 0, 0.1};
Point(3) = {4.0, 2.0, 0, 0.1};
Point(4) = {0, 2.0, 0, 0.1};
Point(5) = {2.0, 1.0, 0, 0.1};
Point(6) = {2.3, 1.0, 0, 0.1};
Point(7) = {2.0, 1.3, 0, 0.1};
Point(8) = {1.7, 1.0, 0, 0.1};
Point(9) = {2.0, 0.7, 0, 0.1};

Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Circle(5) = {6, 5, 7};
Circle(6) = {7, 5, 8};
Circle(7) = {8, 5, 9};
Circle(8) = {9, 5, 6};

Line Loop(1) = {1, 2, 3, 4};
Curve Loop(2) = {5, 6, 7, 8};
Plane Surface(1) = {1, 2};

// Physical Groups

Physical Surface("material", 1) = {1};

// Boundary Conditions
Physical Line("bc_1", 100) = {4};

// Loads
Physical Line("load_1", 200) = {2};

// Mesh Settings
Mesh 2;
