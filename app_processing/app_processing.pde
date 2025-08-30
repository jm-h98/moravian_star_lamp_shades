import controlP5.*;

ControlP5 cp5;

// The mounting assembly consists of a transition segment that connects the cylinder’s top to the mounting cylinder plus a mounting cylinder with fixed dimensions.
final float mountCylinderOuterDiameter = 13;
final float mountCylinderHeight        = 5.5;
float transitionHeight                 = 15;
float transitionWidth                  = 0;
int overhangAngle                      = 30;

// --- Slider Range Variables ---
final int topDiameterMin      = ceil(mountCylinderOuterDiameter) + 3, topDiameterMax    = 100;
final int middleDiameterMin   = 30, middleDiameterMax = 120;
final int bottomDiameterMin   = 30, bottomDiameterMax = 120;
final int overhangAngleMin    = 30, overhangAngleMax  = 80;
final int cylinderHeightMin   = 50, cylinderHeightMax = 120;
final float featureCountMin   = 1, featureCountMax   = 10;
final int detailMin           = 25, detailMax         = 300;
final float featureDepthMaxMax= 4;                                  // maximum feature depth independent from topDiameter
float featureDepthMin         = 0, featureDepthMax   = 4;

// ==========================
// PARAMETERS
// ==========================

// These three parameters control the horizontal diameter (in x–z) at the top, at the middle (u=0.5), and at the bottom (rim).
// this later may be changed to n diameters with adaptable u
int topDiameter    = 30;    // horizontal diameter at the top of the cylinder
int middleDiameter = 70;    // horizontal diameter at mid–height
int bottomDiameter = 60;    // horizontal diameter at the bottom rim

// The profile is drawn from y = cylinderHeight/2 (top) to y = -cylinderHeight/2 (rim).
int cylinderHeight   = 80;

// --- Design parameters ---
int featureCount    = 6;
float featureDepth    = 2;

// --- Design Mode ---
int designMode = -1;
int interpolation = 0;      // to set interpolation method: 1 = lagrangian, 0 = bezier, 2 = linear

int detail = 150;                 // resolution (more → smoother)
final float density = 1.31;       // for bambulab pla matte
final float pricePerKilo = 16.99; // for bambulab pla matte

// Rotation variables (mouse–drag to rotate)
float rotationX = PI;
float rotationY = 0;
float rotationSpeed = 0;  // slow automatic rotation about Y
float zoom = 3.0; // for mouse wheel zooming

Slider topDiameterSlider, middleDiameterSlider, bottomDiameterSlider, featureDepthSlider;
Button exportButton, costButton, randomizeButton, saveDesignButton, loadDesignButton;
DropdownList dlist;

// ==========================
// SETUP & DRAW
// ==========================
void setup() {
  size(1400, 1000, P3D);

  // Initialize the ControlP5 UI library.
  cp5 = new ControlP5(this);

  // --- Sliders for the numeric parameters ---
  topDiameterSlider = cp5.addSlider("topDiameter")
    .setPosition(20, 20)
    .setSize(200, 20)
    .setRange(topDiameterMin, topDiameterMax)
    .setValue(topDiameter);

  middleDiameterSlider = cp5.addSlider("middleDiameter")
    .setPosition(20, 50)
    .setSize(200, 20)
    .setRange(middleDiameterMin, middleDiameterMax)
    .setValue(middleDiameter);

  bottomDiameterSlider = cp5.addSlider("bottomDiameter")
    .setPosition(20, 80)
    .setSize(200, 20)
    .setRange(bottomDiameterMin, bottomDiameterMax)
    .setValue(bottomDiameter);

  cp5.addSlider("cylinderHeight")
    .setPosition(20, 110)
    .setSize(200, 20)
    .setRange(cylinderHeightMin, cylinderHeightMax)
    .setValue(cylinderHeight);

  cp5.addSlider("featureCount")
    .setPosition(20, 170)
    .setSize(200, 20)
    .setRange(featureCountMin, featureCountMax)
    .setNumberOfTickMarks((int)(featureCountMax - featureCountMin + 1))
    .setDecimalPrecision(0)
    .setValue(featureCount);

  cp5.addSlider("interplationMethod")
    .setPosition(20, 200)
    .setSize(200, 20)
    .setRange(0, 2)
    .setNumberOfTickMarks(3)
    .setDecimalPrecision(0)
    .setValue(interpolation);

  featureDepthSlider = cp5.addSlider("featureDepth")
    .setPosition(20, 230)
    .setSize(200, 20)
    .setRange(featureDepthMin, featureDepthMax)
    .setDecimalPrecision(2)
    .setValue(featureDepth);

  cp5.addSlider("detail")
    .setPosition(20, 260)
    .setSize(200, 20)
    .setRange(detailMin, detailMax)
    .setValue(detail);

  cp5.addSlider("overhangAngle")
    .setPosition(20, 290)
    .setSize(200, 20)
    .setRange(overhangAngleMin, overhangAngleMax)
    .setValue(overhangAngle);

  randomizeButton = cp5.addButton("randomizeDesign")
    .setPosition(20, 330)
    .setSize(200, 30)
    .setLabel("Randomize Design");

  saveDesignButton = cp5.addButton("saveDesign")
    .setPosition(20, 370)
    .setSize(200, 30)
    .setLabel("Save Design");

  loadDesignButton = cp5.addButton("loadDesign")
    .setPosition(20, 400)
    .setSize(200, 30)
    .setLabel("Load Design");

  // --- Drop–down list for design mode selection ---
  dlist = cp5.addDropdownList("designModeSelector")
    .setSize(200, 150)
    .setBarHeight(20)
    .setItemHeight(20);

  dlist.addItem("Ripples", 1);
  dlist.addItem("Spirals", 2);
  dlist.addItem("Ridges", 3);
  dlist.addItem("Crosshatch", 4);
  dlist.addItem("Double sine", 5);
  dlist.addItem("Twisted pulse", 6);
  dlist.addItem("Weave", 7);
  dlist.addItem("Moire", 8);
  dlist.addItem("Michelin", 9);
  dlist.addItem("Michelin (spitz)", 10);
  dlist.addItem("Michelin (Spirale)", 11);
  dlist.addItem("Shards", 12);

  // Set the default design mode in the drop–down list.
  dlist.setValue(designMode);

  // --- Button to trigger STL export ---
  exportButton = cp5.addButton("exportSTL")
    .setSize(200, 30)
    .setLabel("Export STL");
}

void draw() {
  background(50);
  lights();

  calculateOptimalTransitionHeight();

  // Top-right: drop-down list
  // We reposition it based on the current window width.
  if (dlist != null) {
    dlist.setPosition(width - dlist.getWidth() - 20, 20);
  }

  // Bottom-right: export button
  if (exportButton != null) {
    exportButton.setPosition(width - exportButton.getWidth() - 20, height - exportButton.getHeight() - 20);
  }

  pushMatrix(); //so that the ui is not affexted by rotations
  translate(width/2, height/2, 0);
  scale(zoom);
  rotateY(rotationY);
  rotateX(rotationX);

  drawMainCylinder();
  drawTransitionSegment();
  drawMountCylinder();
  popMatrix();

  rotationY += rotationSpeed;
}

void controlEvent(ControlEvent theEvent) {
  if (theEvent.getController().getName().equals("designModeSelector")) {
    // theEvent.getValue() returns the index (0 for first item, etc.)
    // so add 1 to match designMode numbers:
    designMode = int(theEvent.getValue()) + 1;
  }
  if (theEvent.isFrom(topDiameterSlider) || theEvent.isFrom(middleDiameterSlider) || theEvent.isFrom(bottomDiameterSlider)) {
    updateFeatureDepth();
  }
}

void updateFeatureDepth() {
  // to prevent clipping and features blocking the lamp space, we adjust the featureDepth if needed
  float outerRadius = mountCylinderOuterDiameter / 2;
  float smallestMainCylinderRadius = (min(topDiameter + transitionWidth, bottomDiameter, middleDiameter)) / 2;
  featureDepthMax = min(smallestMainCylinderRadius - outerRadius, featureDepthMaxMax);
  featureDepthSlider.setRange(featureDepthMin, featureDepthMax);
  featureDepth = min(featureDepthMax, featureDepth);
}

// ==========================
// DESIGN MODES
// ==========================
/*
  Returns an offset (to be added to the base horizontal radius) based on designMode
*/
float designOffset(float u, float v) {
  float offset = 0;
  
  switch(designMode) {
    case 1:
      offset = featureDepth * sin(featureCount * PI * u) * cos(featureCount * v);
      break;
    case 2:
      offset = featureDepth * sin(featureCount * (v + PI * u));
      break;
    case 3:
      offset = featureDepth * abs(sin(featureCount * v));
      break;
    case 4:
      offset = featureDepth * (abs(sin(featureCount * PI * u)) + abs(sin(featureCount * v)));
      break;
    case 5:
      offset = featureDepth * sin(featureCount * (v + u)) * sin(featureCount * (v - u));
      break;
    case 6:
      offset = featureDepth * sin(featureCount * (v + 0.5 * sin(TWO_PI * u)));
      break;
    case 7:
      offset = featureDepth * ( abs(sin(featureCount * v)) - abs(sin(featureCount * PI * u)) );
      break;
    case 8:
      offset = featureDepth * 0.5 * ( sin(featureCount * v) + sin((featureCount + 1) * v + TWO_PI * u) );
      break;
    case 9:
      offset = featureDepth * 0.7 * cos(featureCount * TWO_PI * u);
      break;
    case 10:
      float phase = featureCount * u;
      offset = featureDepth * 0.8 * abs(2.0 * (phase - floor(phase + 0.5)));
      break;
    case 11:
      offset = featureDepth * 0.9 * abs(sin(featureCount * PI * u + v));
      break;
    case 12:
      float d = cos(featureCount * TWO_PI * u + 2.0 * v) + 0.7 * sin(featureCount * v + u * 2.7);
      offset = featureDepth * 0.5 * d;
      break;
    case 13:
      float facetsU = 10;  // Number of "longitude" facets
      float facetsV = 8;   // Number of "latitude" facets
      float quantU = floor(u * facetsU) / facetsU;
      float quantV = floor(v * facetsV) / facetsV;
      offset = featureDepth * noise(quantU * 10, quantV * 10);
      print(offset);
      break;
    default:
      break;
  }
  return offset;
}

float triangleWave(float x, float period) {
    // Ensure a positive remainder.
    float local = x % period;
    if (local < 0) {
        local += period;
    }
    float t = local / period;
    if (t <= 0.5) {
        return 2 * t;
    } else {
        return 2 * (1 - t);
    }
}

// ==========================
// MAIN CYLINDER FUNCTIONS
// ==========================
/*
   The outer (and inner) surface of the cylinder is generated as a revolving surface
   with parameters u (vertical, 0 = top, 1 = rim) and v (angle 0 to 2PI).
   The horizontal profile is defined by an interpolation.
   Then the design–dependent offset is added.
*/
float quadraticProfile(float u) {
  if(interpolation == 1){
    // lagrange interpolation of horizontal profile:
    // u = 0 → topDiameter/2,  u = 0.5 → middleDiameter/2,  u = 1 → bottomDiameter/2.
    return (2 * (u - 1) * ( u - 0.5f) * topDiameter) - (4 * ( u - 1) * u * middleDiameter) + (2 * u * (u - 0.5f) * bottomDiameter);
  } else {
    // bezier interpolation of horizontal profile:
    // u = 0 → topDiameter/2,  u = 0.5 → control point,  u = 1 → bottomDiameter/2.
    return ((1 - u) * (1 - u) * (topDiameter / 2.0)) + (2 * (1 - u) * u * (middleDiameter / 2.0)) + (u * u * (bottomDiameter / 2.0));
  }
}

PVector computeOuterVertex(float u, float v) {
  float baseR = quadraticProfile(u);
  float offset = designOffset(u, v);
  float effectiveR = baseR + offset;
  float x = effectiveR * cos(v);
  float z = effectiveR * sin(v);
  float y = lerp(cylinderHeight / 2.0, -cylinderHeight / 2.0, u);
  return new PVector(x, y, z);
}

PVector computeInnerVertex(float u, float v) {
  PVector outer = computeOuterVertex(u, v);
  // Compute the radial distance in the xz-plane for the outer vertex
  float outerR = sqrt(outer.x * outer.x + outer.z * outer.z);
  float innerR = max(outerR, 0);
  // Calculate the inner vertex position
  float x = innerR * cos(v);
  float z = innerR * sin(v);
  return new PVector(x, outer.y, z);
}

void drawMainCylinder(){
  // --- Outer Surface ---
  fill(150, 0, 0);
  noStroke();
  
  beginShape(QUADS);
  for (int i = 0; i < detail; i++){
    float u1 = map(i, 0, detail, 0, 1);
    float u2 = map(i + 1, 0, detail, 0, 1);
    for (int j = 0; j < detail; j++){
      float v1 = map(j, 0, detail, 0, TWO_PI);
      float v2 = map(j + 1, 0, detail, 0, TWO_PI);
      PVector p1 = computeOuterVertex(u1, v1);
      PVector p2 = computeOuterVertex(u2, v1);
      PVector p3 = computeOuterVertex(u2, v2);
      PVector p4 = computeOuterVertex(u1, v2);
      vertex(p1.x, p1.y, p1.z);
      vertex(p2.x, p2.y, p2.z);
      vertex(p3.x, p3.y, p3.z);
      vertex(p4.x, p4.y, p4.z);
    }
  }
  endShape();
}

// ==========================
// TRANSITION SEGMENT
// ==========================
/*
  This transition region (height = transitionHeight) connects the main cylinder’s top to the mounting cylinder.
  Its bottom edge is taken directly from the main cylinder’s top vertices (u = 0), while its top edge is a fixed circle.
  For each vertical step the vertex positions are linearly interpolated.
*/
void drawTransitionSegment(){
  float transBottomY = cylinderHeight / 2.0;            // cylinder’s top (y-level)
  float transTopY = transBottomY + transitionHeight;    // top of transition region
  
  // For the mounting cylinder, the bottom rim is fixed:
  float fixedOuterTop = mountCylinderOuterDiameter / 2.0;
  float fixedInnerTop = fixedOuterTop;
  
  int vSteps = detail;  // vertical resolution
  
  // --- Outer Tapered Surface ---
  fill(180, 180, 250);
  noStroke();
  
  beginShape(QUADS);
  for (int i = 0; i < vSteps; i++){
    float t1 = i / float(vSteps);
    float t2 = (i + 1) / float(vSteps);
    float y1 = lerp(transBottomY, transTopY, t1);
    float y2 = lerp(transBottomY, transTopY, t2);
    for (int j = 0; j < detail; j++){
      float a1 = map(j, 0, detail, 0, TWO_PI);
      float a2 = map(j + 1, 0, detail, 0, TWO_PI);
      
      // Bottom edge from cylinder’s outer vertices (u = 0)
      PVector bottomV1 = computeOuterVertex(0, a1);
      PVector bottomV2 = computeOuterVertex(0, a2);
      // Top edge from fixed mounting cylinder outer rim
      PVector topV1 = new PVector(fixedOuterTop * cos(a1), transTopY, fixedOuterTop * sin(a1));
      PVector topV2 = new PVector(fixedOuterTop * cos(a2), transTopY, fixedOuterTop * sin(a2));
      
      float x1 = lerp(bottomV1.x, topV1.x, t1);
      float z1 = lerp(bottomV1.z, topV1.z, t1);
      float x2 = lerp(bottomV1.x, topV1.x, t2);
      float z2 = lerp(bottomV1.z, topV1.z, t2);
      float x3 = lerp(bottomV2.x, topV2.x, t2);
      float z3 = lerp(bottomV2.z, topV2.z, t2);
      float x4 = lerp(bottomV2.x, topV2.x, t1);
      float z4 = lerp(bottomV2.z, topV2.z, t1);
      
      vertex(x1, y1, z1);
      vertex(x2, y2, z2);
      vertex(x3, y2, z3);
      vertex(x4, y1, z4);
    }
  }
  endShape();
}

void calculateOptimalTransitionHeight(){
  // maximum qoverhead of the bambulabs is 30°. The transition region should by definition be only as large as neccessary.
  // to achieve minimal size, the height needs to be automatically adjusted to be such that the angle towards the main cylinders top surface is 30°
  transitionWidth = (topDiameter - mountCylinderOuterDiameter) / 2.0; //topDiameter >= mountCylinderOuterDiameter
  transitionHeight = transitionWidth * tan(radians(overhangAngle));
}

void randomizeDesign(){
  topDiameter    = int(random(topDiameterMin, topDiameterMax));
  middleDiameter = int(random(middleDiameterMin, middleDiameterMax));
  bottomDiameter = int(random(bottomDiameterMin, bottomDiameterMax));
  cylinderHeight = int(random(cylinderHeightMin, cylinderHeightMax));
  featureCount   = int(random(featureCountMin, featureCountMax));
  designMode     = int(random(0, 11));
  
  updateFeatureDepth();
  featureDepth   = random(featureDepthMin, featureDepthMax);
  featureDepthSlider.setValue(featureDepth);
  
  
  // update slider values
  topDiameterSlider.setValue(topDiameter);
  middleDiameterSlider.setValue(middleDiameter);
  bottomDiameterSlider.setValue(bottomDiameter);
  cp5.getController("cylinderHeight").setValue(cylinderHeight);
  cp5.getController("featureCount").setValue(featureCount);
  dlist.setValue(designMode);
}


// ==========================
// MOUNTING CYLINDER
// ==========================
/*
   The mounting cylinder is drawn as a fixed hollow tube. Its bottom is at y = cylinderHeight/2 + transitionHeight and its top is mountCylinderHeight above that.
*/
void drawMountCylinder(){
  float cylBottomY = cylinderHeight / 2.0 + transitionHeight;
  float cylTopY = cylBottomY + mountCylinderHeight;
  float outerRadius = mountCylinderOuterDiameter / 2.0;
  float innerRadius = outerRadius;
  
  // --- Outer Surface ---
  fill(100, 100, 250);
  noStroke();
  
  beginShape(QUAD_STRIP);
  for (int i = 0; i <= detail; i++){
    float angle = map(i, 0, detail, 0, TWO_PI);
    float x = outerRadius * cos(angle);
    float z = outerRadius * sin(angle);
    vertex(x, cylBottomY, z);
    vertex(x, cylTopY, z);
  }
  endShape();
}

// ==========================
// STL EXPORT FUNCTIONS
// ==========================

// We want the exported STL to be oriented with the mounting cylinder "up" – that is, using z as vertical.
// To do this, transform every vertex from (x, y, z) to (x, z, y).
PVector transformVertex(PVector p) {
  return new PVector(p.x, p.z, p.y);
}

// Helper: create name and save parameters
String createName(){
  return designMode + "_" + topDiameter + "_" + middleDiameter + "_" + bottomDiameter + "_" + cylinderHeight + "_" + featureCount + "_" + String.format("%.02f", featureDepth) + "_" + detail;
}

// Helper: export a quad as two triangles.
void exportQuad(PVector p1, PVector p2, PVector p3, PVector p4, PrintWriter out) {
  writeFacet(p1, p2, p3, out);
  writeFacet(p1, p3, p4, out);
}

// Helper: compute facet normal and write facet in STL format.
void writeFacet(PVector a, PVector b, PVector c, PrintWriter out) {
  // Transform vertices for proper orientation:
  PVector A = transformVertex(a);
  PVector B = transformVertex(b);
  PVector C = transformVertex(c);
  PVector normal = computeNormal(A, B, C);
  out.println("facet normal " + normal.x + " " + normal.y + " " + normal.z);
  out.println("  outer loop");
  out.println("    vertex " + A.x + " " + A.y + " " + A.z);
  out.println("    vertex " + B.x + " " + B.y + " " + B.z);
  out.println("    vertex " + C.x + " " + C.y + " " + C.z);
  out.println("  endloop");
  out.println("endfacet");
}

// Helper: compute the normal vector of a facet defined by vertices A, B, and C.
PVector computeNormal(PVector A, PVector B, PVector C) {
  PVector U = PVector.sub(B, A);
  PVector V = PVector.sub(C, A);
  PVector N = U.cross(V);
  N.normalize();
  return N;
}

void exportSTL() {
  PrintWriter out = createWriter(createName() + ".stl");
  out.println("solid exported_object");
  
  // =============================================================
  // 1) MAIN CYLINDER (the lampshade body)
  // =============================================================
  
  // --- (a) Export MAIN CYLINDER Outer Lateral Surface ---
  for (int i = 0; i < detail; i++){
    float u1 = map(i, 0, detail, 0, 1);
    float u2 = map(i + 1, 0, detail, 0, 1);
    for (int j = 0; j < detail; j++){
      float v1 = map(j, 0, detail, 0, TWO_PI);
      float v2 = map(j + 1, 0, detail, 0, TWO_PI);
      PVector p1 = computeOuterVertex(u1, v1);
      PVector p2 = computeOuterVertex(u2, v1);
      PVector p3 = computeOuterVertex(u2, v2);
      PVector p4 = computeOuterVertex(u1, v2);
      exportQuad(p1, p2, p3, p4, out);
    }
  }
  
  // --- (b) Export MAIN CYLINDER Bottom Cap (flat)
  {
    PVector centerBottom = new PVector(0, -cylinderHeight/2.0, 0);
    for (int j = 0; j < detail; j++){
      float v1 = map(j, 0, detail, 0, TWO_PI);
      float v2 = map(j + 1, 0, detail, 0, TWO_PI);
      PVector p1 = computeOuterVertex(1, v1);
      PVector p2 = computeOuterVertex(1, v2);
      writeFacet(centerBottom, p1, p2, out);
    }
  }
  
  // =============================================================
  // 2) TRANSITION SEGMENT
  // =============================================================
  for (int i = 0; i < detail; i++){
    float t1 = i / float(detail);
    float t2 = (i + 1) / float(detail);
    float y1 = lerp(cylinderHeight/2.0, cylinderHeight/2.0 + transitionHeight, t1);
    float y2 = lerp(cylinderHeight/2.0, cylinderHeight/2.0 + transitionHeight, t2);
    for (int j = 0; j < detail; j++){
      float a1 = map(j, 0, detail, 0, TWO_PI);
      float a2 = map(j + 1, 0, detail, 0, TWO_PI);
      
      // Bottom edge is taken from the main cylinder’s outer vertices (i.e. u=0)
      PVector bottomV1 = computeOuterVertex(0, a1);
      PVector bottomV2 = computeOuterVertex(0, a2);
      // Top edge is a fixed circle (outer rim of the mounting cylinder)
      float topR = mountCylinderOuterDiameter / 2.0;
      PVector topV1 = new PVector(topR * cos(a1), cylinderHeight/2.0 + transitionHeight, topR * sin(a1));
      PVector topV2 = new PVector(topR * cos(a2), cylinderHeight/2.0 + transitionHeight, topR * sin(a2));
      
      float x1 = lerp(bottomV1.x, topV1.x, t1);
      float z1 = lerp(bottomV1.z, topV1.z, t1);
      PVector p1 = new PVector(x1, y1, z1);
      
      float x2 = lerp(bottomV1.x, topV1.x, t2);
      float z2 = lerp(bottomV1.z, topV1.z, t2);
      PVector p2 = new PVector(x2, y2, z2);
      
      float x3 = lerp(bottomV2.x, topV2.x, t2);
      float z3 = lerp(bottomV2.z, topV2.z, t2);
      PVector p3 = new PVector(x3, y2, z3);
      
      float x4 = lerp(bottomV2.x, topV2.x, t1);
      float z4 = lerp(bottomV2.z, topV2.z, t1);
      PVector p4 = new PVector(x4, y1, z4);
      
      exportQuad(p1, p2, p3, p4, out);
    }
  }
  
  // =============================================================
  // 3) MOUNTING CYLINDER
  // =============================================================
  
  // --- (a) Outer Curved Surface ---
  {
    float cylBottomY = cylinderHeight/2.0 + transitionHeight;
    float cylTopY = cylBottomY + mountCylinderHeight;
    for (int i = 0; i < detail; i++){
      float a1 = map(i, 0, detail, 0, TWO_PI);
      float a2 = map(i + 1, 0, detail, 0, TWO_PI);
      PVector p1 = new PVector(mountCylinderOuterDiameter/2.0 * cos(a1), cylBottomY, mountCylinderOuterDiameter/2.0 * sin(a1));
      PVector p2 = new PVector(mountCylinderOuterDiameter/2.0 * cos(a1), cylTopY, mountCylinderOuterDiameter/2.0 * sin(a1));
      PVector p3 = new PVector(mountCylinderOuterDiameter/2.0 * cos(a2), cylTopY, mountCylinderOuterDiameter/2.0 * sin(a2));
      PVector p4 = new PVector(mountCylinderOuterDiameter/2.0 * cos(a2), cylBottomY, mountCylinderOuterDiameter/2.0 * sin(a2));
      exportQuad(p1, p2, p3, p4, out);
    }
  }
  
  // --- (b) Top Cap (flat) ---
  // Instead of exporting a top rim (and inner surface) we now close the mounting cylinder with a flat cap
  {
    float cylBottomY = cylinderHeight/2.0 + transitionHeight;
    float cylTopY = cylBottomY + mountCylinderHeight;
    float outerRadius = mountCylinderOuterDiameter / 2.0;
    PVector centerTop = new PVector(0, cylTopY, 0);
    for (int j = 0; j < detail; j++){
      float a1 = map(j, 0, detail, 0, TWO_PI);
      float a2 = map(j + 1, 0, detail, 0, TWO_PI);
      PVector p1 = new PVector(outerRadius * cos(a1), cylTopY, outerRadius * sin(a1));
      PVector p2 = new PVector(outerRadius * cos(a2), cylTopY, outerRadius * sin(a2));
      writeFacet(centerTop, p2, p1, out);
    }
  }
  
  out.println("endsolid exported_object");
  out.flush();
  out.close();
  println("Export complete: " + createName() + ".stl");
}

void saveDesign(){
  String[] lines = new String[1];
  lines[0] = topDiameter + "," + middleDiameter + "," + bottomDiameter + "," +
             cylinderHeight + "," + featureCount + "," +
             featureDepth + "," + detail + "," + overhangAngle + "," + designMode;
  saveStrings(createName() + ".txt", lines);
  println("Design saved.");
}

void loadDesign(){
  // file chooser dialog with callback
  selectInput("Select a design file (.txt)", "fileSelected");
}

void fileSelected(File selection) {
  if (selection == null) {
    println("No file was selected.");
    return;
  }
  String[] lines = loadStrings(selection.getAbsolutePath());
  
  if (lines != null && lines.length > 0) {
    String[] tokens = split(lines[0], ",");
    if (tokens.length >= 9) {
      topDiameter    = int(tokens[0]);
      middleDiameter = int(tokens[1]);
      bottomDiameter = int(tokens[2]);
      cylinderHeight = int(tokens[3]);
      featureCount   = int(tokens[4]);
      featureDepth   = float(tokens[5]);
      detail         = int(tokens[6]);
      overhangAngle  = int(tokens[7]);
      designMode     = int(tokens[8]);

      // Update the UI elements accordingly:
      featureDepthSlider.setValue(featureDepth);
      topDiameterSlider.setValue(topDiameter);
      middleDiameterSlider.setValue(middleDiameter);
      bottomDiameterSlider.setValue(bottomDiameter);
      cp5.getController("cylinderHeight").setValue(cylinderHeight);
      cp5.getController("featureCount").setValue(featureCount);
      cp5.getController("detail").setValue(detail);
      cp5.getController("overhangAngle").setValue(overhangAngle);
      if (dlist != null) {
         dlist.setValue(designMode - 1);
      }
      
      println("Design loaded from: " + selection.getAbsolutePath());
    } else {
      println("Error: Design file format invalid.");
    }
  } else {
    println("Error: Could not load file " + selection.getAbsolutePath());
  }
}

// ==========================
// MOUSE EVENTS
// ==========================

void mouseDragged(){
  if (!cp5.isMouseOver()) {
    float sensitivity = 0.01;
    rotationY -= (pmouseX - mouseX) * sensitivity;
    rotationX += (mouseY - pmouseY) * sensitivity;
  }
}

void mouseWheel(MouseEvent event){
  float e = event.getCount();
  float zoomSensitivity = 0.05;
  zoom -= e * zoomSensitivity;
  zoom = max(0.1, zoom);
}
