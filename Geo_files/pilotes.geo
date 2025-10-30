// ==========================================================================
// Archivo para definir la geometría de la cimentación
// para el análisis de tensiones.
// ==========================================================================

// Se utiliza OpenCASCADE para poder utilizar operaciones booleanas.
SetFactory("OpenCASCADE");

// PARAMETROS GEOMETRICOS DE LA CIMENTACION
tema = 1;
he = 0.5;

DPilotes = 0.90;      // Diámetro de los pilotes
nPilotes = 2;         // Número de pilotes
hPilotes = 20.0;      // Profundidad de los pilotes.
hColumna = 0.1;       // Altura de la porcion de columna que sobresale.
hZapata =  1.0;       // Profundidad de la zapata.

AnchoLados = 20;      // Distancia a lado y lado del modelo para dejar el 

rectHe = 1.0;         // Tamaño caracteristico de los elements generales
piloteHe = 0.2;       // Tamaño caracteristico de los elementos en la zona del pilote


// DATOS GEOMETRICOS DE LA SEPARACION ENTRE COLUMNAS

// Separación entre columnas.
L1 = { 7.0, 8.5, 8.5, 7.0};
//L1 = { 15.0, 8.5, 8.5, 15.0};
L2 = { 7.5, 8.0, 7.5, 6.5};
L3 = { 8.0, 7.0, 6.5, 8.5};

// Anchos de columna (va por tema).
wColumna = { 0.9, 1.2, 1.0, 1.7 };


// Espesores de los estratos
nEstratos = 6;
tEstratos = { 2, 3, 3, 4, 10,10};

//Geometry.OCCUnionUnify = 1;
//Geometry.OCCBooleanPreserveNumbering = 0;

// ==========================================================================
// MACRO 1 -  GENERACIÓN DE RECTANGULO PARCIALMENTE.
// Esta macro se utiliza para generar un rectángulo a partir de conocer el
// lado superior (L3_id y sus dos puntos superiores P3_id -Derecho- y 
// P4_id - Izquierdo) y de conocer el punto incial (punto inferior izquierdo)
// del punto inicial y el punto final. 
//
//      P4*              L3*               P3*      *->Conocidos.
//                                    (C1x,C1y)
//       X-------------------------------X     
//       |                               |   
//    L4 |                               | L2  
//       |                               |   
//       X-------------------------------X    
//  (C0x,C0y)
//      P1              L1                P2     
//     
//
//    
// INPUTS:
//     - C0x C0y: Coordenada en x y y respectivamente que
//                del punto izquierdo inferior del rectangulo.
//     - C1x C1y: Coordenada en x y y respectivamente que
//                del punto derecho superior del rectangulo.
//	   - rectHe:  Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//     
// ==========================================================================
Macro RectanguloParcial
	
	// Generar puntos del rectangulo
	P1_id = newp; Point(P1_id) = {C0x,C0y,0,rectHe};
	P2_id = newp; Point(P2_id) = {C1x,C0y,0,rectHe};
	
	// Generar lineas del rectangulo
	L1_id = newl; Line(L1_id) = {P1_id,P2_id}; // Bottom
	L2_id = newl; Line(L2_id) = {P2_id,P3_id}; // Right
	L4_id = newl; Line(L4_id) = {P4_id,P1_id}; // Left

	Lp_id = newll; Curve Loop(Lp_id) = {L1_id, L2_id, -L3_id, L4_id};

	rectSurf_id = news; Surface(rectSurf_id) = {Lp_id};

Return
// **************************************************************************

// ==========================================================================
// MACRO 2 -  GENERACIÓN DE RECTANGULO.
// Esta macro se utiliza para generar un rectángulo a partir
// del punto inicial y el punto final. 
//
//      P4              L3                P3   
//                                    (C1x,C1y)
//       X-------------------------------X     
//       |                               |   
//    L4 |                               | L2  
//       |                               |   
//       X-------------------------------X    
//  (C0x,C0y)
//      P1              L1                P2     
//     
//
//    
// INPUTS:
//     - C0x C0y: Coordenada en x y y respectivamente que
//                del punto izquierdo inferior del rectangulo.
//     - C1x C1y: Coordenada en x y y respectivamente que
//                del punto derecho superior del rectangulo.
//	   - rectHe:  Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro RectanguloTotal
	
	// Generar puntos del rectangulo
	P1_id = newp; Point(P1_id) = {C0x,C0y,0,rectHe};
	P2_id = newp; Point(P2_id) = {C1x,C0y,0,rectHe};
	P3_id = newp; Point(P3_id) = {C1x,C1y,0,rectHe};
	P4_id = newp; Point(P4_id) = {C0x,C1y,0,rectHe};

	// Generar lineas del rectangulo
	L1_id = newl; Line(L1_id) = {P1_id,P2_id}; // Bottom
	L2_id = newl; Line(L2_id) = {P2_id,P3_id}; // Right
	L3_id = newl; Line(L3_id) = {P3_id,P4_id}; // Top
	L4_id = newl; Line(L4_id) = {P4_id,P1_id}; // Left

	Lp_id = newll; Curve Loop(Lp_id) = {L1_id, L2_id, L3_id, L4_id};

	rectSurf_id = news; Surface(rectSurf_id) = {Lp_id};

Return
// **************************************************************************


// ==========================================================================
// MACRO 3 -  Buscar Boundaries.
// Esta macro se utiliza Asignar los physical groups para los bordes
// izquierdo, derecho e inferior para todas las curvas de la lista de 
// superficies.
//
// INPUTS:
//     - Sirfaces: Lista de superficies para buscar los boundaries
//     - pgTagLeft: Tag del physical group del borde izquierdo.
//     - pgTagRight: Tag del physical group del borde derecho.
//     - pgTagBottom: Tag del physical group del borde inferior.
//	   - piloteHe: Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro BuscarBoundaries
	
	For i In {0:#Surfaces[]-1}

		Si = Surfaces[i];
		curves[] = Boundary{Surface{Si};};
		
		For j In {0:#curves[]-1}
			
			pts[] = Boundary{Line{curves[j]};};
			p1 = Point{pts[0]};
			p2 = Point{pts[1]};
			
			If (p1[0] == 0.0 && p2[0] == 0.0) // Left
				
				Physical Curve(pgTagLeft) += {Abs(curves[j])};

			ElseIf (p1[0] == wTotal && p2[0] == wTotal) // Right
				
				Physical Curve(pgTagRight) += {Abs(curves[j])};

			ElseIf (p1[1] == hTotal && p2[1] == hTotal) // Bottom

				Physical Curve(pgTagBottom) += {Abs(curves[j])};

			EndIf

		EndFor

		//Printf(" ----- ");
	EndFor

Return
// **************************************************************************

// ==========================================================================
// MACRO 4 -  Detectar superficies.
// Esta macro se utiliza Asignar los physical groups para los bordes
// izquierdo, derecho e inferior para todas las curvas de la lista de 
// superficies.
//
// INPUTS:
//     - Sirfaces: Lista de superficies para buscar los boundaries
//     - pgTagLeft: Tag del physical group del borde izquierdo.
//     - pgTagRight: Tag del physical group del borde derecho.
//     - pgTagBottom: Tag del physical group del borde inferior.
//	   - piloteHe: Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro DetectarSuperfFuerzas
	
	For i In {0:#SurfPilotes[]-1}

		Si = SurfPilotes[i];
		curves[] = Boundary{Surface{Si};};
		ncurves = #curves[];
		ListaSuperf = {};
		
		For j In {0:ncurves-1}
			pts[] = Boundary{Line{curves[j]};};
			p1 = Point{pts[0]};
			p2 = Point{pts[1]};
			//Printf ("PointY ( %g, %g)",p1[1],p2[1]);
			If (p1[1]>0.0 && p2[1]>0)
				ListaSuperf += {curves[j]};
			EndIf
			
		EndFor

		curves[] = ListaSuperf[];

		Call ComputePointMax;
		//Printf ("Ncurves: %g",#curves[]);

		For j In {0:#curves[]-1}
			
			pts[] = Boundary{Line{curves[j]};};
			p1 = Point{pts[0]};
			p2 = Point{pts[1]};

			Transfinite Curve(curves[j]) = 10;

			If (p1[0]==maxX || p2[0]==maxX)
				//Right
				Physical Curve(RightIdTag) = {Abs(curves[j])}; RightIdTag += 1;
			Else 
				Physical Curve(LeftIdTag) = {Abs(curves[j])}; LeftIdTag += 1;
			EndIf
			
		EndFor
		


	EndFor 
	
Return
// **************************************************************************


// ==========================================================================
// MACRO 4 -  Detectar superficies.
// Esta macro se utiliza Asignar los physical groups para los bordes
// izquierdo, derecho e inferior para todas las curvas de la lista de 
// superficies.
//
// INPUTS:
//     - Sirfaces: Lista de superficies para buscar los boundaries
//     - pgTagLeft: Tag del physical group del borde izquierdo.
//     - pgTagRight: Tag del physical group del borde derecho.
//     - pgTagBottom: Tag del physical group del borde inferior.
//	   - piloteHe: Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro DetectarSuperficies
	
	SurfPilotes={};

	SurfE0={};
	SurfE1={};
	SurfE2={};
	SurfE3={};
	SurfE4={};
	SurfE5={};

	For i In {0:#Superficies[]-1}

		Si = Superficies[i];
		curves[] = Boundary{Surface{Si};};
		ncurves = #curves[];

		Call ComputePointAverage;

		If (ncurves<6)
			// Estrato
			
			
			found = 1;
			hSearch = 0;
			estratoId = 4;
			h = 0.0;
			For j In {0:nEstratos-1}
				h = h - tEstratos[j];
				If (avgY > h && found)
					estratoId = j;
					found = 0;
				EndIf
			EndFor

			If (estratoId == 0)
				SurfE0+={Si};
			ElseIf (estratoId == 1)
				SurfE1+={Si};
			ElseIf (estratoId == 2)
				SurfE2+={Si};
			ElseIf (estratoId == 3)
				SurfE3+={Si};
			ElseIf (estratoId == 4)
				SurfE4+={Si};
			ElseIf (estratoId == 5)
				SurfE5+={Si};
			EndIf
		Else

			Call ComputePointMax;
			
			If (maxY>0)
				SurfPilotes+={Si};
			Else
				
				h = 0.0;
				found = 1;
				hSearch = 0;
				estratoId = 4;
				For j In {0:nEstratos-1}
					h = h - tEstratos[j];
					If (avgY > h && found)
						estratoId = j;
						found = 0;
					EndIf
				EndFor

				If (estratoId == 0)
					SurfE0+={Si};
				ElseIf (estratoId == 1)
					SurfE1+={Si};
				ElseIf (estratoId == 2)
					SurfE2+={Si};
				ElseIf (estratoId == 3)
					SurfE3+={Si};
				ElseIf (estratoId == 4)
					SurfE4+={Si};
				ElseIf (estratoId == 5)
					SurfE5+={Si};
				EndIf
			EndIf

			


		EndIf

	

	EndFor 
	
Return
// **************************************************************************

// ==========================================================================
// MACRO 4 -  Detectar superficies.
// Esta macro se utiliza Asignar los physical groups para los bordes
// izquierdo, derecho e inferior para todas las curvas de la lista de 
// superficies.
//
// INPUTS:
//     - Sirfaces: Lista de superficies para buscar los boundaries
//     - pgTagLeft: Tag del physical group del borde izquierdo.
//     - pgTagRight: Tag del physical group del borde derecho.
//     - pgTagBottom: Tag del physical group del borde inferior.
//	   - piloteHe: Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro ComputePointAverage
	
	avgX = 0;
	avgY = 0;

	For j In {0: #curves[]-1}

		pts[] = Boundary{Line{curves[j]};};
		p1 = Point{pts[0]};
		p2 = Point{pts[1]};

		avgX += p1[0]+p2[0];
		avgY += p1[1]+p2[1];


	EndFor			
	avgX = avgX /( 2.0 * #curves[]);
	avgY = avgY /( 2.0 * #curves[]);
	
Return 
// **************************************************************************

// ==========================================================================
// MACRO 4 -  Detectar superficies.
// Esta macro se utiliza Asignar los physical groups para los bordes
// izquierdo, derecho e inferior para todas las curvas de la lista de 
// superficies.
//
// INPUTS:
//     - Sirfaces: Lista de superficies para buscar los boundaries
//     - pgTagLeft: Tag del physical group del borde izquierdo.
//     - pgTagRight: Tag del physical group del borde derecho.
//     - pgTagBottom: Tag del physical group del borde inferior.
//	   - piloteHe: Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro ComputePointMax

	maxX = -1e30;
	maxY = -1e30;
	
	For j In {0:#curves[]-1}

		pts[] = Boundary{Line{curves[j]};};
		p1 = Point{pts[0]};
		p2 = Point{pts[1]};

		maxX = Max(Max(p1[0],maxX),p2[0]);
		maxY = Max(Max(p1[1],maxY),p2[1]);

	EndFor			

Return 
// **************************************************************************


// ==========================================================================
// MACRO 4 -  GENERACIÓN DE PILOTE.
// Esta macro se utiliza para generar un rectángulo a partir
// del punto inicial y el punto final. 
//
// INPUTS:
//     - CX: Coordenada en x de la pila.
//           del punto izquierdo inferior del rectangulo.
//     - nPilotes: Coordenada en x y y respectivamente que
//                del punto derecho superior del rectangulo.
//     - hColumna: Coordenada en x y y respectivamente que
//                del punto derecho superior del rectangulo.
//     - wColumna: 
//	   - piloteHe: Tamaño de elemento para los puntos del rectangulo.
//
// OUTPUTS:
//
// ==========================================================================
Macro GenerarPilotes
	
	
	ListaLineas = {};

	// Ancho de Zapata
	wZapata = (nPilotes-1)*DPilotes*(2.5) + DPilotes ;

	// Generar puntos del rectangulo 1, que contiene la zona de aplicación de cargas
	PL_id = newp; Point(PL_id) = {CX,hColumna,0,piloteHe};
	P2_id = newp; Point(P2_id) = {CX-wColumna[tema]/2,hColumna,0,piloteHe};
	P3_id = newp; Point(P3_id) = {CX-wColumna[tema]/2,0,0,piloteHe};
	P4_id = newp; Point(P4_id) = {CX-wZapata/2,0,0,piloteHe};
	P5_id = newp; Point(P5_id) = {CX-wZapata/2,-hZapata,0,piloteHe};
	
	//P4_id = newp; Point(P4_id) = {CX+wColumna[tema]/2,0,0,piloteHe};
	//P5_id = newp; Point(P5_id) = {CX+wColumna[tema]/2,hColumna,0,piloteHe};
	
	// Generar lineas del rectangulo
	L1_id = newl; Line(L1_id) = {PL_id,P2_id}; ListaLineas+={L1_id};
	L_id = newl; Line(L_id) = {P2_id,P3_id}; ListaLineas+={L_id};
	L_id = newl; Line(L_id) = {P3_id,P4_id}; ListaLineas+={L_id};
	L_id = newl; Line(L_id) = {P4_id,P5_id}; ListaLineas+={L_id};

	//// Pilotes
	//CxPilote = CX-(nPilotes-1)*DPilotes*(2.5)/2;
	P1_id = P5_id; 
	C0x_pilote = CX-wZapata/2;
	
	For i In {0:nPilotes-1}
		
		P2_id = newp; Point(P2_id) = {C0x_pilote,-hPilotes,0,piloteHe};
		P3_id = newp; Point(P3_id) = {C0x_pilote+DPilotes,-hPilotes,0,piloteHe};
		P4_id = newp; Point(P4_id) = {C0x_pilote+DPilotes,-hZapata,0,piloteHe};
		L_id = newl; Line(L_id) = {P1_id,P2_id}; ListaLineas+={L_id};
		L_id = newl; Line(L_id) = {P2_id,P3_id}; ListaLineas+={L_id};
		L_id = newl; Line(L_id) = {P3_id,P4_id}; ListaLineas+={L_id};

		
		If (i != nPilotes-1)
			P5_id = newp; Point(P5_id) = {C0x_pilote+DPilotes*2.5,-hZapata,0,piloteHe};
			L_id = newl; Line(L_id) = {P4_id,P5_id}; ListaLineas+={L_id};
	
			P1_id = P5_id;
		EndIf

		C0x_pilote+=2.5*DPilotes;

	EndFor

	P7_id = newp; Point(P7_id) = {CX+wZapata/2,0.0,0,piloteHe};
	P8_id = newp; Point(P8_id) = {CX+wColumna[tema]/2,0.0,0,piloteHe};
	PR_id = newp; Point(PR_id) = {CX+wColumna[tema]/2,hColumna,0,piloteHe};
	
	L_id = newl; Line(L_id) = {P4_id,P7_id}; ListaLineas+={L_id};
	L_id = newl; Line(L_id) = {P7_id,P8_id}; ListaLineas+={L_id};
	L_id = newl; Line(L_id) = {P8_id,PR_id}; ListaLineas+={L_id};
	L2_id = newl; Line(L2_id) = {PR_id,PL_id}; ListaLineas+={L2_id};

	//Physical Curve(pgTagSurfLeft) = {L1_id};
	//Physical Curve(pgTagSurfRight) = {L2_id};

	LoopId = newll; Curve Loop(LoopId) = {ListaLineas[]};

	Transfinite Curve{L1_id} = 10;
	Transfinite Curve{L2_id} = 10;

	pilote_id = news; Plane Surface(pilote_id) = {LoopId};
Return
// **************************************************************************


wTotal = L1[tema-1]+L2[tema-1]+L3[tema-1]+4*wColumna[tema-1]+2*AnchoLados;



C0x = 0.0;
C0y = 0.0;

C1x = wTotal;
C1y = 0.0;

// Primera llamada
P1_id = newp; Point(P1_id) = {C0x,C0y,0,rectHe};
P2_id = newp; Point(P2_id) = {C1x,C0y,0,rectHe};
L1_id = newl; Line(L1_id) = {P1_id,P2_id};

FixedXLines = {};
SurfaceList = {};

// Generar los estratos
For i In { 0: #tEstratos[]-1 }
	
	C0y = C0y - tEstratos[i];
	
	P3_id = P2_id; 	P4_id = P1_id;
	
	L3_id = L1_id;

	Call RectanguloParcial;
	
	// Agregar la superficie a una lista de superficies.
	SurfaceList += {rectSurf_id};

	// Agregar las líneas físicas de los estremos
	FixedXLines += {L2_id,L4_id};

	C1y = C0y;

EndFor

hTotal = C0y;

// Agregar todas las lineas laterales a la lista de physical curves.
//Physical Curve(100) = {FixedXLines[]};


ListaPilotes = {};
CX = AnchoLados + 0.5*wColumna;
pgTagSurfLeft = 20;  pgTagSurfRight = 21;
Call GenerarPilotes;
ListaPilotes+={pilote_id};

CX = CX + L1[tema-1] + wColumna;
pgTagSurfLeft = 30;  pgTagSurfRight = 31;
Call GenerarPilotes;
ListaPilotes+={pilote_id};

CX = CX + L2[tema-1] + wColumna;
pgTagSurfLeft = 40;  pgTagSurfRight = 41;
Call GenerarPilotes;
ListaPilotes+={pilote_id};

CX = CX + L3[tema-1] + wColumna;
pgTagSurfLeft = 50;  pgTagSurfRight = 51;
Call GenerarPilotes;
ListaPilotes+={pilote_id};

SurfacesE0 = {SurfaceList[0]};
SurfacesE1 = {SurfaceList[1]};
SurfacesE2 = {SurfaceList[2]};
SurfacesE3 = {SurfaceList[3]};
SurfacesE4 = {SurfaceList[4]};
SurfacesE5 = {SurfaceList[5]};


SurfacesE0[] = BooleanDifference{Surface{SurfacesE0[]};Delete;}{Surface{ListaPilotes[]};};
SurfacesE1[] = BooleanDifference{Surface{SurfacesE1[]};Delete;}{Surface{ListaPilotes[]};};
SurfacesE2[] = BooleanDifference{Surface{SurfacesE2[]};Delete;}{Surface{ListaPilotes[]};};
SurfacesE3[] = BooleanDifference{Surface{SurfacesE3[]};Delete;}{Surface{ListaPilotes[]};};
SurfacesE4[] = BooleanDifference{Surface{SurfacesE4[]};Delete;}{Surface{ListaPilotes[]};};
SurfacesE5[] = BooleanDifference{Surface{SurfacesE5[]};Delete;}{Surface{ListaPilotes[]};};

s[] = BooleanFragments{Surface{:};Delete;}{};

// Detectar las superficies:
Superficies[] = s[];
Call DetectarSuperficies;



pgTagLeft = 100;
pgTagRight = 100;
pgTagBottom = 200;

Physical Curve(pgTagLeft) = {};
Physical Curve(pgTagBottom) = {};


Surfaces[] = SurfE0[];
Call BuscarBoundaries;

Surfaces[] = SurfE1[];
Call BuscarBoundaries;

Surfaces[] = SurfE2[];
Call BuscarBoundaries;

Surfaces[] = SurfE3[];
Call BuscarBoundaries;

Surfaces[] = SurfE4[];
Call BuscarBoundaries;

Surfaces[] = SurfE5[];
Call BuscarBoundaries;


MeshSize{ PointsOf{Surface{Superficies[]};} } = rectHe;
MeshSize{ PointsOf{Surface{SurfPilotes[]};} } = piloteHe;


RightIdTag = 60;
LeftIdTag = 50;

Call DetectarSuperfFuerzas;


Physical Surface(500) = {SurfE0[]};
Physical Surface(400) = {SurfE1[]};
Physical Surface(300) = {SurfE2[]};
Physical Surface(200) = {SurfE3[]};
Physical Surface(100) = {SurfE4[]};
Physical Surface(4000) = {SurfE5[]};
Physical Surface(5000) = {SurfPilotes[]};

//s[] = BooleanFragments{Surface{:};Delete;}{};