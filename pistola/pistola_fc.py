# -*- coding: utf-8 -*-
"""
Lightgun GUN4IR estilo pistola real - modelo CAD en FreeCAD (OpenCASCADE).
Ejecutar:  "D:/Program Files/FreeCAD 1.0/bin/FreeCADCmd.exe" pistola_fc.py
Genera STL en ./out/ (coordenadas del arma y orientadas para imprimir).

Ejes: X hacia la pantalla, Z arriba, Y lateral (izquierda = -Y). Corte en Y = 0.
"""
import math, os, sys
import FreeCAD as App
import Part, Mesh, MeshPart
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)

# =============================== parametros ===============================
HW    = 15.0          # media anchura (arma de 30 mm)
WALL  = 2.5
INNER = HW - WALL     # 12.5

# corredera (slide) y armazon (frame)
SL_X0, SL_X1 = 0.0, 172.0
SL_Z0, SL_Z1 = 92.0, 122.0
FR_X0, FR_X1 = 60.0, 166.0
FR_Z0 = 80.0

# camara DFRobot SEN0158 (plano oficial): O16.45 x 34.1 + cola O7.69 x 7
CAM_D, CAM_LEN = 16.45 + 0.25, 34.1
CAM_Z = 107.0
CAM_LIP, CAM_LIP_D, CAM_TAIL_D = 1.2, 14.0, 13.0
CAM_X1 = SL_X1 - CAM_LIP
CAM_X0 = CAM_X1 - CAM_LEN - 0.2
CAV_X1 = 128.0                      # fin de la cavidad; adelante es bloque macizo

# Pro Micro USB-C (medidas probadas en el case anterior)
PCB_L, PCB_W, PCB_T = 35.0, 18.0, 1.6
USB_W, USB_H, USB_OUT = 9.0, 3.3, 1.0
PCB_GAP = 0.15
PCB_Y0 = -(USB_H / 2 + PCB_T)       # cara inferior de la placa (lado izquierdo)

# mango
GA = 17.0                           # inclinacion
GB = V(24, 0, 7)                    # centro de la base
GL = 100.0
G_B = 15.0                          # media anchura del mango (= HW: apoya plano en la cama)

def g_back(v):   # lomo: palm swell + base ensanchada + cola de castor
    return (21 + 3 * math.exp(-((v - 40) / 16) ** 2) + 2 * max(0, 1 - v / 8)
            + (14 * ((v - 60) / 36) ** 2 if v > 60 else 0))

def g_win(v):
    return math.sin(math.pi * (v - 3) / 55) if 3 < v < 58 else 0

def g_front(v):  # frente: 3 apoyos de dedos
    return 20 + 2 * max(0, 1 - v / 8) - 1.4 * math.cos(2 * math.pi * (v - 12) / 18) * g_win(v)

# gatillo + microswitch subminiatura 12.8 x 6.5 x 5.8 (Candy-HO)
PIVOT = (78.0, 88.0)                # (x, z)
TRIG_T = 7.4
TUNE_Z = 97.0
SW_L, SW_H, SW_T = 12.8, 6.5, 5.8
SW_X = 86.0
SW_Z0 = TUNE_Z - SW_L / 2

# botones tact 12x12x7.3
TACT, TACT_BODY, TACT_STEM = 12.0, 3.6, 3.7
CAP_FL_D, CAP_FL_T, CAP_D, CAP_HOLE, CAP_OUT = 11.0, 1.2, 8.6, 9.0, 2.0
BTN_L = [(40, 107), (56, 107)]      # A, B (izquierda, pulgar)
BTN_R = [(100, 107), (116, 107)]    # START, SELECT (derecha)

# tornilleria
INSERT_D, INSERT_H = 4.2, 6.0
HEAD_SEAT = 5.0                     # -> M3 x 10
BOSS_XZ = [(12, 99), (12, 115), (78, 116), (100, 86), (134, 88), (134, 118)]
BOSS_GRIP = [(-14, 14), (13, 50), (-14, 62)]   # (u, v)

# ============================== utilidades ===============================
def gpt(u, v, w=0.0):
    a = math.radians(GA)
    return V(GB.x + v * math.sin(a) + u * math.cos(a), w, GB.z + v * math.cos(a) - u * math.sin(a))

def to_grip(shape):
    """Pasa un solido modelado en coord. locales (X=u, Y=w, Z=v) al mango."""
    s = shape.copy()
    s.rotate(V(0, 0, 0), V(0, 1, 0), GA)
    s.translate(GB)
    return s

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cyl_y(x, z, r, y0, y1):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))

def cyl_x(y, z, r, x0, x1):
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))

def edges_where(shape, pred):
    return [e for e in shape.Edges if pred(e)]

def is_dir(e, d, tol=1e-3):
    """True si la arista es una recta en la direccion d"""
    try:
        p0, p1 = e.Vertexes[0].Point, e.Vertexes[-1].Point
    except Exception:
        return False
    dv = p1 - p0
    if dv.Length < 1e-6 or abs(e.Length - dv.Length) > 1e-4:
        return False
    return abs(abs(dv.normalize().dot(d)) - 1) < tol

def try_fillet(shape, r, edges, label):
    if not edges:
        return shape
    try:
        f = shape.makeFillet(r, edges)
        if f.isValid():
            return f
    except Exception as ex:
        print("  fillet fallo", label, ex)
    return shape

def rounded_rect_face_yz(y0, y1, z0, z1, r_top, r_bot, x):
    """Seccion (en un plano X=cte) rectangular con esquinas redondeadas."""
    b = box(x, x + 1, y0, y1, z0, z1)
    b = try_fillet(b, r_top, edges_where(b, lambda e: is_dir(e, V(1, 0, 0)) and e.BoundBox.ZMin > z1 - 1e-3), "rt")
    b = try_fillet(b, r_bot, edges_where(b, lambda e: is_dir(e, V(1, 0, 0)) and e.BoundBox.ZMax < z0 + 1e-3), "rb")
    return b

# ============================ forma exterior ==============================
def make_slide():
    L = SL_X1 - SL_X0
    s = box(SL_X0, SL_X1, -HW, HW, SL_Z0, SL_Z1)
    # perfil lateral: nariz inclinada adelante, cola levemente inclinada atras
    prof = [(SL_X0 + 2, SL_Z0), (SL_X1, SL_Z0), (SL_X1, SL_Z1 - 7), (SL_X1 - 9, SL_Z1),
            (SL_X0 + 1, SL_Z1), (SL_X0, SL_Z1 - 3)]
    side = smooth_face_xz(prof, -HW - 1, 1.5, 1.0).extrude(V(0, 2 * HW + 2, 0))
    # seccion transversal: lomo bien redondeado (R7), base apenas redondeada
    sec = rounded_rect_face_yz(-HW, HW, SL_Z0, SL_Z1, 7.0, 1.0, SL_X0 - 5)
    sec = sec.Faces[[i for i, fc in enumerate(sec.Faces) if abs(fc.CenterOfMass.x - (SL_X0 - 5)) < 1e-6][0]]
    longi = sec.extrude(V(SL_X1 - SL_X0 + 10, 0, 0))
    s = side.common(longi).removeSplitter()
    s = try_fillet(s, 1.5, edges_where(s, lambda e: not is_dir(e, V(1, 0, 0)) and e.BoundBox.XMin > SL_X1 - 12), "slide front")
    return s

def make_frame():
    f = box(FR_X0, FR_X1, -HW, HW, FR_Z0, SL_Z0 + 2)
    f = try_fillet(f, 4.0, edges_where(f, lambda e: is_dir(e, V(1, 0, 0)) and e.BoundBox.ZMax < FR_Z0 + 1e-3), "frame bot")
    f = try_fillet(f, 3.0, edges_where(f, lambda e: e.BoundBox.XMin > FR_X1 - 1e-3 and e.BoundBox.ZMax < SL_Z0 + 1), "frame front")
    # ranuras de riel (estetica)
    for x in (128, 138, 148, 158):
        f = f.cut(box(x, x + 3.5, -HW - 1, HW + 1, FR_Z0 - 1, FR_Z0 + 1.6))
    return f

def section_wire(v, shrink=0.0, n_pts=56):
    af, ab, b = g_front(v) - shrink, g_back(v) - shrink, G_B - shrink
    pts = []
    for k in range(n_pts):
        t = 2 * math.pi * k / n_pts
        c, s = math.cos(t), math.sin(t)
        if c >= 0:
            u = af * math.copysign(abs(c) ** (2 / 2.4), c)
        else:
            u = -ab * abs(c) ** (2 / 3.2)
        w = b * math.copysign(abs(s) ** (2 / 3.0), s)
        pts.append(gpt(u, v, w))
    bs = Part.BSplineCurve()
    bs.interpolate(pts, PeriodicFlag=True)
    return Part.Wire(bs.toShape())

def make_grip(shrink=0.0, v0=0.0, v1=GL):
    vs = [v0] + [v for v in range(int(v0) + 4, int(v1), 4)] + [v1]
    wires = [section_wire(v, shrink) for v in vs]
    return Part.makeLoft(wires, True, False, False)

def smooth_face_xz(pts, y, r_out, r_in):
    """cara plana (plano Y=y) con esquinas redondeadas (abrir + cerrar con offset 2D)"""
    face = Part.Face(Part.makePolygon([V(x, y, z) for x, z in pts] + [V(pts[0][0], y, pts[0][1])]))
    f = face.makeOffset2D(-r_out, join=0).makeOffset2D(r_out, join=0)      # esquinas convexas
    f = f.makeOffset2D(r_in, join=0).makeOffset2D(-r_in, join=0)           # esquinas concavas
    return f

def make_guard():
    # perfil lateral (x, z) del guardamonte: frente cuadrado tipo Glock, barra inferior con leve curva
    pts = [(48, 47), (106, 47), (118, 52), (124, 62), (125, FR_Z0 + 3), (115, FR_Z0 + 3),
           (115, 66), (112, 60), (105, 55), (48, 55)]
    f = smooth_face_xz(pts, -7.0, 2.5, 4.0)
    g = f.extrude(V(0, 14, 0))
    g = try_fillet(g, 3.0, edges_where(g, lambda e: not is_dir(e, V(0, 1, 0)) and e.BoundBox.ZMax < FR_Z0 - 1), "guard edges")
    return g

def make_beavertail():
    # cola de castor: cubre la membrana entre pulgar e indice, une lomo del mango con la corredera
    pts = [(30, SL_Z0 + 1), (2, SL_Z0 + 1), (-3, SL_Z0 - 1.5), (0, SL_Z0 - 5), (10, SL_Z0 - 7.5),
           (20, SL_Z0 - 10), (28, SL_Z0 - 16)]
    f = smooth_face_xz(pts, -12.0, 2.0, 6.0)
    b = f.extrude(V(0, 24, 0))
    b = try_fillet(b, 5.0, edges_where(b, lambda e: not is_dir(e, V(0, 1, 0)) and e.BoundBox.ZMax < SL_Z0 + 0.5), "beaver")
    return b

def make_sights():
    rear = box(5, 13, -8, 8, SL_Z1 - 1, SL_Z1 + 4).cut(box(4, 14, -1.75, 1.75, SL_Z1 + 1.5, SL_Z1 + 5))
    rear = try_fillet(rear, 1.0, edges_where(rear, lambda e: is_dir(e, V(0, 1, 0)) and e.BoundBox.ZMin > SL_Z1 + 3), "rear sight")
    front = box(SL_X1 - 13, SL_X1 - 8, -1.75, 1.75, SL_Z1 - 7, SL_Z1 + 3.5)
    front = try_fillet(front, 1.5, edges_where(front, lambda e: is_dir(e, V(0, 1, 0)) and e.BoundBox.ZMin > SL_Z1 + 3), "front sight")
    return rear.fuse(front)

def make_cosmetic_cuts():
    cuts = []
    # estrias de la corredera (atras y adelante), en ambos lados
    for side in (-1, 1):
        y0 = HW - 0.8 if side > 0 else -HW - 1
        y1 = HW + 1 if side > 0 else -HW + 0.8
        for i in range(7):
            x = 9 + i * 4.2
            g = box(x, x + 1.4, y0, y1, SL_Z0 + 5, SL_Z1 - 4)
            g.rotate(V(x, 0, SL_Z0 + 5), V(0, 1, 0), -8)
            cuts.append(g)
        for i in range(5):
            x = 138 + i * 4.2
            g = box(x, x + 1.4, y0, y1, SL_Z0 + 5, SL_Z1 - 7)
            g.rotate(V(x, 0, SL_Z0 + 5), V(0, 1, 0), -8)
            cuts.append(g)
        # linea de union corredera / armazon
        cuts.append(box(FR_X0 + 4, FR_X1 - 2, y0 + (0.2 if side > 0 else 0), y1 - (0 if side > 0 else 0.2), SL_Z0 - 0.4, SL_Z0 + 0.4))
    # ventana de expulsion (lado derecho, arriba)
    cuts.append(box(68, 100, HW - 1.0, HW + 1, SL_Z1 - 9, SL_Z1 + 1))
    cuts.append(box(68, 100, 2, HW + 1, SL_Z1 - 1.0, SL_Z1 + 1))
    return cuts

# ============================== interior ==============================
def make_cavity():
    c1 = box(5, CAV_X1, -INNER, INNER, SL_Z0 + WALL, SL_Z1 - WALL)
    c1 = try_fillet(c1, 3.5, edges_where(c1, lambda e: is_dir(e, V(1, 0, 0)) and e.BoundBox.ZMin > SL_Z1 - WALL - 1e-3), "cav top")
    c2 = box(FR_X0 + WALL, CAV_X1, -INNER, INNER, FR_Z0 + WALL, SL_Z0 + WALL + 1)
    c2 = try_fillet(c2, 1.5, edges_where(c2, lambda e: is_dir(e, V(1, 0, 0)) and e.BoundBox.ZMax < FR_Z0 + WALL + 1e-3), "cav bot")
    c3 = make_grip(shrink=WALL, v0=WALL, v1=GL + 2)
    return c1.fuse([c2, c3])

def tact_pod(x, z, side):
    """devuelve (solido, corte, trabas) para un pulsador tact en la pared side (-1 izq, +1 der)"""
    g = TACT + 0.2
    def yr(a, b):  # rango Y medido desde el plano hacia afuera
        return (a, b) if side > 0 else (-b, -a)
    y0, y1 = yr(INNER - 9.3, INNER + 0.01)
    solid = box(x - 7.3, x + 7.3, y0, y1, z - 7.9, z + 7.9)
    a, b = yr(INNER - 7.9, INNER + 0.01)
    cut = box(x - g / 2, x + g / 2, a, b, z - g / 2, z + g / 2)
    a, b = yr(INNER - 10.6, INNER - 7.8)
    cut = cut.fuse(box(x - g / 2, x + g / 2, a, b, z - 6.9, z + 6.9))
    a, b = yr(INNER - 1, HW + 2)
    cut = cut.fuse(cyl_y(x, z, CAP_HOLE / 2, a, b))
    a, b = yr(INNER - 9.3, INNER - 8.5)
    lips = box(x - g / 2, x - g / 2 + 0.45, a, b, z - 4, z + 4).fuse(box(x + g / 2 - 0.45, x + g / 2, a, b, z - 4, z + 4))
    return solid, cut, lips

def switch_block(side):
    y0, y1 = (0.8, INNER) if side > 0 else (-INNER, -0.8)
    blk = box(SW_X - 0.1, SW_X + SW_H + 0.1 + 1.6, y0, y1, SW_Z0 - 1.6, SW_Z0 + SW_L + 1.6)
    cut = box(SW_X - 0.1, SW_X + SW_H + 0.1, -SW_T / 2 - 0.1, SW_T / 2 + 0.1, SW_Z0 - 0.1, SW_Z0 + SW_L + 0.1)
    return blk, cut

def promicro_seat_L():
    """paredes, rieles y tope que encastran la placa (mitad izquierda), coord. locales del mango"""
    yb = PCB_Y0                  # -3.25
    yt = yb + PCB_T              # -1.65
    w2 = PCB_W / 2 + PCB_GAP
    v0, v1 = WALL, WALL + PCB_L + PCB_GAP
    parts = []
    for s in (-1, 1):
        ux = (w2, w2 + 1.2) if s > 0 else (-w2 - 1.2, -w2)
        parts.append(box(ux[0], ux[1], -INNER, 0, v0, v1 + 1.2))           # paredes
        ux = (w2 - 1.15, w2) if s > 0 else (-w2, -w2 + 1.15)
        parts.append(box(ux[0], ux[1], -INNER, yb, v0, v1))                # rieles bajo la placa
    parts.append(box(-w2 - 1.2, w2 + 1.2, -INNER, yt, v1, v1 + 1.2))       # tope
    sh = parts[0].fuse(parts[1:])
    return to_grip(sh)

def promicro_press_R():
    return to_grip(box(-4, 4, -0.7, INNER + 1, WALL + 16, WALL + 20))   # va de la pared hasta el chip

def usb_cut():
    a = box(-(USB_W + 0.3) / 2, (USB_W + 0.3) / 2, -USB_H / 2 - 0.15, USB_H / 2 + 0.15, -1, WALL + 1)
    b = box(-6.75, 6.75, -4.0, 4.0, -1, WALL - USB_OUT)
    return to_grip(a.fuse(b))

def boss_points():
    pts = list(BOSS_XZ)
    for u, v in BOSS_GRIP:
        p = gpt(u, v)
        pts.append((p.x, p.z))
    return pts

# ============================== gatillo y botones ==============================
def make_trigger():
    px, pz = PIVOT
    blade = [(73, 88), (82.5, 88), (83, 80), (84.5, 71), (84, 63), (82, 57.5), (79, 55), (77.3, 56.5),
             (79, 62), (78.7, 70), (77, 78), (75.5, 84)]
    bs = Part.BSplineCurve()
    bs.interpolate([V(x, -TRIG_T / 2, z) for x, z in blade], PeriodicFlag=True)
    face = Part.Face(Part.Wire(bs.toShape()))
    t = face.extrude(V(0, TRIG_T, 0))
    t = t.fuse(cyl_y(px, pz, 5, -TRIG_T / 2, TRIG_T / 2))
    t = t.fuse(box(px - 3, px + 4, -TRIG_T / 2, TRIG_T / 2, pz, TUNE_Z + 3.5))
    t = t.cut(cyl_y(px, pz, 1.75, -TRIG_T, TRIG_T))
    t = t.cut(cyl_x(0, TUNE_Z, 1.3, px - 10, px + 10))          # tornillo de ajuste M3 (autorroscante)
    return t.removeSplitter()

def make_cap():
    c = Part.makeCylinder(CAP_FL_D / 2, CAP_FL_T)
    k = Part.makeCylinder(CAP_D / 2, CAP_FL_T + WALL + CAP_OUT)
    c = c.fuse(k)
    c = try_fillet(c, 0.8, edges_where(c, lambda e: e.BoundBox.ZMin > CAP_FL_T + WALL + CAP_OUT - 1e-3), "cap")
    return c

# ============================== ensamble ==============================
def export(shape, name, defl=0.04):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=defl, AngularDeflection=0.25, Relative=False)
    m.write(os.path.join(OUT, name))
    print("  ->", name, "valido" if shape.isValid() else "NO VALIDO", [round(x, 1) for x in
          (shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength)])

def main():
    print("forma exterior...")
    outer = make_slide().fuse([make_frame(), make_grip(), make_guard(), make_beavertail(), make_sights()]).removeSplitter()
    try:
        outer = outer.cut(make_cosmetic_cuts())
    except Exception as ex:
        print("  cortes esteticos fallaron:", ex)
    print("interior...")
    cav = make_cavity()
    shell = outer.cut(cav)

    # cortes comunes a ambas mitades
    common_cuts = [
        cyl_x(0, CAM_Z, CAM_LIP_D / 2, CAM_X1 - 0.01, SL_X1 + 5),
        cyl_x(0, CAM_Z, CAM_D / 2, CAM_X0, CAM_X1),
        cyl_x(2.0, CAM_Z, CAM_TAIL_D / 2, CAV_X1 - 3, CAM_X0 + 0.01),
        box(73.5, 85.5, -TRIG_T / 2 - 0.4, TRIG_T / 2 + 0.4, 74, FR_Z0 + WALL + 1),   # ranura del gatillo
        usb_cut(),
    ]
    bosses = boss_points()
    halves = {}
    for side in (-1, 1):
        name = "L" if side < 0 else "R"
        print("mitad", name, "...")
        hb = box(-50, 300, -HW - 5, 0, -50, 200) if side < 0 else box(-50, 300, 0, HW + 5, -50, 200)
        ys = (lambda a, b: (-b, -a)) if side < 0 else (lambda a, b: (a, b))

        feats = []
        for x, z in bosses:
            feats.append(cyl_y(x, z, 4.0, *ys(0, INNER + 0.01)))
        feats.append(cyl_y(PIVOT[0], PIVOT[1], 4.5, *ys(TRIG_T / 2 + 0.4, INNER + 0.01)))
        blk, sw_cut = switch_block(side)
        feats.append(blk)
        pods = [tact_pod(x, z, side) for x, z in (BTN_L if side < 0 else BTN_R)]
        feats += [p[0] for p in pods]
        if side < 0:
            feats.append(promicro_seat_L())

        h = shell.common(hb)
        f = feats[0].fuse(feats[1:]).common(outer).common(hb)
        h = h.fuse(f)

        cuts = list(common_cuts) + [sw_cut] + [p[1] for p in pods]
        # tornillos desde la DERECHA (cabeza embutida); heat inserts en la IZQUIERDA (cara limpia)
        for x, z in bosses:
            if side > 0:
                cuts.append(cyl_y(x, z, 1.7, -1, HW + 2))
                cuts.append(cyl_y(x, z, 3.25, HEAD_SEAT, HW + 2))
            else:
                cuts.append(cyl_y(x, z, INSERT_D / 2, -INSERT_H, 1))
                cuts.append(cyl_y(x, z, 1.3, -11, 1))
        if side > 0:   # eje del gatillo: M3 x 25 desde la derecha
            cuts.append(cyl_y(PIVOT[0], PIVOT[1], 1.7, -1, HW + 2))
            cuts.append(cyl_y(PIVOT[0], PIVOT[1], 3.25, INNER - 1, HW + 2))
        else:
            cuts.append(cyl_y(PIVOT[0], PIVOT[1], 1.7, -13, 1))
            cuts.append(cyl_y(PIVOT[0], PIVOT[1], INSERT_D / 2, -(TRIG_T / 2 + 0.4 + INSERT_H), -(TRIG_T / 2 + 0.39)))
        h = h.cut(cuts)
        adds = [p[2] for p in pods]
        if side > 0:
            adds.append(promicro_press_R())
        h = h.fuse(adds).removeSplitter()
        halves[name] = h

    trig = make_trigger()
    cap = make_cap()

    print("exportando...")
    export(halves["L"], "gun_L.stl")
    export(halves["R"], "gun_R.stl")
    export(trig, "gun_trigger.stl")
    # piezas orientadas para imprimir (cara exterior sobre la cama)
    pl = halves["L"].copy(); pl.rotate(V(0, 0, 0), V(1, 0, 0), 90);  pl.translate(V(0, 0, HW)); export(pl, "print_left.stl")
    pr = halves["R"].copy(); pr.rotate(V(0, 0, 0), V(1, 0, 0), -90); pr.translate(V(0, 0, HW)); export(pr, "print_right.stl")
    pt = trig.copy(); pt.rotate(V(0, 0, 0), V(1, 0, 0), 90); pt.translate(V(-60, -50, TRIG_T / 2)); export(pt, "print_trigger.stl")
    caps = cap.fuse([cap.translated(V(14 * i, 0, 0)) for i in range(1, 4)])
    export(caps, "print_caps.stl")

    # modelos de referencia para renders / video
    cam = cyl_x(0, CAM_Z, 16.45 / 2, CAM_X1 - CAM_LEN, CAM_X1).fuse(cyl_x(2.0, CAM_Z, 7.69 / 2, CAM_X1 - CAM_LEN - 7, CAM_X1 - CAM_LEN))
    export(cam, "ref_camera.stl", 0.1)
    w2 = PCB_W / 2
    pm = box(-w2, w2, PCB_Y0, PCB_Y0 + PCB_T, WALL, WALL + PCB_L)
    usb = box(-USB_W / 2, USB_W / 2, PCB_Y0 + PCB_T, PCB_Y0 + PCB_T + USB_H, WALL - USB_OUT, WALL + 6.5)
    export(to_grip(pm), "ref_promicro_pcb.stl", 0.1)
    export(to_grip(usb), "ref_promicro_usb.stl", 0.1)
    export(box(SW_X, SW_X + SW_H, -SW_T / 2, SW_T / 2, SW_Z0, SW_Z0 + SW_L), "ref_switch.stl", 0.1)
    for nm, lst, side in (("L", BTN_L, -1), ("R", BTN_R, 1)):
        tl, cl = [], []
        for x, z in lst:
            yb = INNER - CAP_FL_T - TACT_STEM - TACT_BODY
            a, b = (yb, yb + TACT_BODY) if side > 0 else (-yb - TACT_BODY, -yb)
            tl.append(box(x - 6, x + 6, a, b, z - 6, z + 6))
            c = cap.copy()
            c.rotate(V(0, 0, 0), V(1, 0, 0), -90 if side > 0 else 90)
            c.translate(V(x, (INNER - CAP_FL_T) * side, z))
            cl.append(c)
        export(tl[0].fuse(tl[1:]), "ref_tact_%s.stl" % nm, 0.1)
        export(cl[0].fuse(cl[1:]), "ref_caps_%s.stl" % nm, 0.05)
    import json
    json.dump({"bosses": boss_points(), "pivot": PIVOT, "head_seat": HEAD_SEAT, "inner": INNER,
               "trig_t": TRIG_T, "insert_h": INSERT_H},
              open(os.path.join(OUT, "layout.json"), "w"))
    print("OK")

main()
