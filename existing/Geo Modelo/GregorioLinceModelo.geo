// Input .geo for rectangular domain with a hole and curved left side
// author: Juan Gomez (adapted)
// Units: meters

c = 0.10; // target element size

// ----- Rectangle corners (outer boundary) -----
Point(1) = {0.0, 0.0, 0, c};   // bottom-left (geometric corner, not used as straight edge)
Point(2) = {4.0, 0.0, 0, c};   // bottom-right
Point(3) = {4.0, 2.0, 0, c};   // top-right
Point(4) = {0.0, 2.0, 0, c};   // top-left

// ----- Curved left boundary (arc) -----
// Replace the straight line from (0,0) to (0,2) by a circular arc
// Center chosen so the arc bulges inward: center at (0.5, 1.0), radius = 0.5 m
Point(100) = {0.5, 1.0, 0, c}; // arc center

// ----- Circular hole (center 1,1; diameter 0.5 => radius 0.25) -----
Point(10) = {1.0, 1.0, 0, c};      // hole center
Point(11) = {1.25, 1.00, 0, c};    // +x
Point(12) = {1.00, 1.25, 0, c};    // +y
Point(13) = {0.75, 1.00, 0, c};    // -x
Point(14) = {1.00, 0.75, 0, c};    // -y

// ----- Outer boundary lines (go counter-clockwise) -----
Line(1) = {1, 2};                 // bottom
Line(2) = {2, 3};                 // right
Line(3) = {3, 4};                 // top
Circle(4) = {4, 100, 1};          // left curved side: arc from (0,2) -> (0,0) with center (0.5,1)

// Assemble outer loop
Line Loop(101) = {1, 2, 3, 4};

// ----- Hole boundary (four arcs around the center) -----
Circle(5) = {11, 10, 12};
Circle(6) = {12, 10, 13};
Circle(7) = {13, 10, 14};
Circle(8) = {14, 10, 11};

// Hole loop
Line Loop(201) = {5, 6, 7, 8};

// ----- Surfaces (outer with an internal hole) -----
Plane Surface(1) = {101, 201};

// ----- (Optional) Meshing directives -----
// Recombine Surface {1};      // uncomment for quad-dominant mesh
// Transfinite Curve {5,6,7,8} = 60 Using Progression 1; // sample control on hole
// Transfinite Curve {1,2,3,4} = 100 Using Progression 1;

// ----- Physical groups -----
Physical Surface("Domain", 100) = {1};
Physical Line("Bottom",   1000) = {1};
Physical Line("Right",    2000) = {2};
Physical Line("Top",      3000) = {3};
Physical Line("LeftArc",  4000) = {4};
Physical Line("Hole",     5000) = {5,6,7,8};
