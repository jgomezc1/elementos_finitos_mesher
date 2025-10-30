// Input .geo for thin ring
// author: Juan Gomez

c = 0.1;    // for size elements

// Define vertex points
Point(1) = {0.00, 1.5, 0, c};	    // {x,y,z, size}
Point(2) = {1.50, 0.0, 0, c};
Point(3) = {2.00, 0.0, 0, c};
Point(4) = {0.00, 2.0, 0, c};
Point(5) = {0.00, 0.0, 0, c};

// Define boundary lines
Circle(1) = {1, 5, 2};    // {Initial_point, end_point}
Line(2) = {2, 3};
Circle(3) = {3, 5, 4};
Line(4) = {4, 1};

// Joint Lines
Line Loop(1) = {1, 2, 3, 4};     // {Id_line1,id_line2, ... }

// surface for mesh     // {Id_Loop}
Plane Surface(1) = {1};

// For Mesh 4 nodes
//Recombine Surface {1};    // {Id_Surface}

// "Structured" mesh 
Transfinite Line {1, 3} = 20 Using Progression 1;
Transfinite Line {4, 2} = 6 Using Progression 1;
Transfinite Surface {1};    // {Id_Surface}

Physical Surface(100) = {1};

// cargas
Physical Line(100)={1};

// left BC
Physical Line(400)={4};
// Bottom BC
Physical Line(200)={2};


