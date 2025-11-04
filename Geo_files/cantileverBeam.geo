// -----------------------------------------------------------------
// Gmsh .geo para Viga en Voladizo (Cantilever Beam) - 2D
// -----------------------------------------------------------------
// Este script crea una viga 2D (Plano XY).
// Define grupos físicos para:
// 1. La línea izquierda (empotramiento/fijo)
// 2. Una línea superior derecha (para aplicar carga)
// 3. La superficie total (para asignar material)
// -----------------------------------------------------------------

// 1. KERNEL Y PARÁMETROS DE GEOMETRÍA
SetFactory("OpenCASCADE");

// Dimensiones de la viga
L = 10.0;  // Longitud total en X
H = 1.0;   // Alto en Y (anteriormente era Z)

// Dimensiones de la zona de carga
LoadL = 2.0;   // Longitud de la zona de carga en X (en el extremo derecho)
MainL = L - LoadL; // Longitud de la parte principal de la viga

// Tolerancia para seleccionar entidades
tol = 1e-6;

// 2. CREACIÓN DE LA GEOMETRÍA
// Creamos dos rectángulos separados para definir la zona de carga
// en el borde superior del segundo.
// Sintaxis: Rectangle(tag) = {x, y, z, dx, dy};
Rectangle(1) = {0, 0, 0, MainL, H};
Rectangle(2) = {MainL, 0, 0, LoadL, H};

// Fusionamos las dos superficies en una sola.
BooleanFragments{ Surface{1, 2}; Delete; }{};
Synchronize;

// 3. DEFINICIÓN DE GRUPOS FÍSICOS (Physical Groups)
// Los grupos físicos ahora se aplican a Curvas (líneas) y Superficies (áreas).

// --- GRUPO 1: Borde Fijo (Empotramiento) ---
// Seleccionamos la línea (Curva) en X=0
FixedEdge[] = Curve In BoundingBox { -tol, -tol, -tol, tol, H+tol, tol };
Physical Curve("FixedSupport", 1) = {FixedEdge[]};

// --- GRUPO 2: Zona de Carga (Superior Derecha) ---
// Seleccionamos la línea superior (Y=H) SÓLO de la zona derecha (X > MainL)
LoadEdge[] = Curve In BoundingBox { MainL-tol, H-tol, -tol, L+tol, H+tol, tol };
Physical Curve("AppliedLoad", 2) = {LoadEdge[]};

// --- GRUPO 3: Superficie de la Viga (Material) ---
// Seleccionamos toda la superficie 2D
BeamArea[] = Surface In BoundingBox { -tol, -tol, -tol, L+tol, H+tol, tol };
Physical Surface("BeamMaterial", 10) = {BeamArea[]};

// 4. DEFINICIÓN Y GENERACIÓN DE LA MALLA

// "Malla triangular fina"
// Definimos un tamaño de malla "fino" (1/15 de la altura)
lc = H / 15;
Mesh.CharacteristicLengthMax = lc;

// Algoritmos de mallado 2D (Triangular)
Mesh.Algorithm = 6; // Frontal-Delaunay
Mesh.Optimize = 1;  // Optimizar la calidad de la malla

// 5. GENERAR MALLA 2D
//Mesh 2;

// 6. GUARDAR MALLA
//Save "cantileverBeam_2D.msh";