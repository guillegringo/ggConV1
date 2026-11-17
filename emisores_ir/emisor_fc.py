# -*- coding: utf-8 -*-
"""
Emisor IR para GUN4IR (se imprimen 4 iguales): cabezal con 3 LEDs IR de 5 mm + resistencia,
tapa trasera atornillada, y base con horquilla para inclinarlo (bisagra a friccion con M3).

Ejecutar:  "D:/Program Files/FreeCAD 1.0/bin/FreeCADCmd.exe" emisor_fc.py   -> stl/
Ejes: X a lo ancho de la tele, Y profundidad (-Y = hacia el jugador), Z arriba.
"""
import math, os
import FreeCAD as App
import Part, MeshPart
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)

# ---------------- parametros ----------------
HEAD_W, HEAD_H, HEAD_D = 46.0, 18.0, 20.0   # cabezal (sin tapa)
WALL = 2.2
R_OUT = 3.0
LED_D, LED_HOLE, LED_FLANGE_D, LED_FLANGE_T = 5.0, 5.15, 6.1, 1.2   # LED IR de 5 mm estandar
LED_X = (-9.0, 0.0, 9.0)                     # separacion de los 3 LEDs
LID_T = 2.5
BOSS_X = 18.5
INSERT_D, INSERT_H = 4.2, 6.0
CABLE_D = 4.6                                # cable USB (~3.5-4 mm)
CABLE_X = (-8.0, 8.0)                        # entrada y salida (cadena entre emisores)
# bisagra
TAB_T = 6.6                                  # pestaña de la tapa
PIV_Y = HEAD_D + LID_T + 5.5                 # eje de giro (detras de la tapa)
FORK_T = 7.0
FORK_GAP = 0.2
BASE_TOP = -16.0                             # cara superior de la base (deja inclinar +-25 grados)
BASE_T = 3.0
BASE_Y = (14.0, 44.0)
BASE_W = 40.0

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cyl_y(x, z, r, y0, y1):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))

def cyl_x(y, z, r, x0, x1):
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))

def is_dir(e, d):
    try:
        p0, p1 = e.Vertexes[0].Point, e.Vertexes[-1].Point
    except Exception:
        return False
    dv = p1 - p0
    if dv.Length < 1e-6 or abs(e.Length - dv.Length) > 1e-4:
        return False
    return abs(abs(dv.normalize().dot(d)) - 1) < 1e-3

def fillet(s, r, pred, label):
    es = [e for e in s.Edges if pred(e)]
    try:
        f = s.makeFillet(r, es)
        if f.isValid():
            return f
    except Exception as ex:
        print("  fillet fallo", label, ex)
    return s

# ---------------- cabezal ----------------
def make_head():
    w2, h2 = HEAD_W / 2, HEAD_H / 2
    h = box(-w2, w2, 0, HEAD_D, -h2, h2)
    h = fillet(h, R_OUT, lambda e: is_dir(e, V(0, 1, 0)), "head long")
    h = fillet(h, 2.0, lambda e: e.BoundBox.YMax < 1e-3, "head front")
    h = h.cut(box(-w2 + WALL, w2 - WALL, WALL, HEAD_D + 1, -h2 + WALL, h2 - WALL))
    # torretas para la tapa
    for sx in (-1, 1):
        b = cyl_y(sx * BOSS_X, 0, 3.5, WALL - 0.01, HEAD_D)
        b = b.fuse(box(sx * BOSS_X - 3.5 if sx < 0 else sx * BOSS_X - 0.0, sx * BOSS_X + (0.0 if sx < 0 else 3.5),
                       WALL - 0.01, HEAD_D, -3.5, 3.5))
        h = h.fuse(b.common(box(-w2 + 0.5, w2 - 0.5, 0, HEAD_D, -h2 + 0.5, h2 - 0.5)))
        h = h.cut(cyl_y(sx * BOSS_X, 0, INSERT_D / 2, HEAD_D - INSERT_H, HEAD_D + 1))
        h = h.cut(cyl_y(sx * BOSS_X, 0, 1.3, WALL + 0.8, HEAD_D))          # guia: deja pasar la punta del M3x10
    # LEDs: agujero pasante + alojamiento del reborde por dentro
    for x in LED_X:
        h = h.cut(cyl_y(x, 0, LED_HOLE / 2, -1, WALL + 1))
        h = h.cut(cyl_y(x, 0, LED_FLANGE_D / 2, WALL - LED_FLANGE_T + 0.3, WALL + 1))
    # nervio bajo los LEDs: tope para que entren derechos
    return h.removeSplitter()

# ---------------- tapa con pestaña ----------------
def make_lid():
    w2, h2 = HEAD_W / 2, HEAD_H / 2
    y0, y1 = HEAD_D, HEAD_D + LID_T
    lid = box(-w2, w2, y0, y1, -h2, h2)
    lid = fillet(lid, R_OUT, lambda e: is_dir(e, V(0, 1, 0)), "lid")
    # pestaña de la bisagra
    tab = box(-TAB_T / 2, TAB_T / 2, y1 - 0.01, PIV_Y, -6, 6).fuse(cyl_x(PIV_Y, 0, 6, -TAB_T / 2, TAB_T / 2))
    lid = lid.fuse(tab)
    lid = lid.cut(cyl_x(PIV_Y, 0, 1.7, -10, 10))
    for sx in (-1, 1):
        lid = lid.cut(cyl_y(sx * BOSS_X, 0, 1.7, y0 - 3, y1 + 1))
        lid = lid.cut(cyl_y(sx * BOSS_X, 0, 3.1, y1 - 0.8, y1 + 1))     # asiento de la cabeza
    for x in CABLE_X:
        lid = lid.cut(cyl_y(x, -2.0, CABLE_D / 2, y0 - 3, y1 + 1))
    return lid.removeSplitter()

# ---------------- base con horquilla ----------------
def make_base():
    b = box(-BASE_W / 2, BASE_W / 2, BASE_Y[0], BASE_Y[1], BASE_TOP - BASE_T, BASE_TOP)
    b = fillet(b, 4.0, lambda e: is_dir(e, V(0, 0, 1)), "base")
    xi = TAB_T / 2 + FORK_GAP
    for sx in (-1, 1):
        xa, xb = (xi, xi + FORK_T) if sx > 0 else (-xi - FORK_T, -xi)
        t = box(xa, xb, PIV_Y - 6, PIV_Y + 6, BASE_TOP - 0.01, 0).fuse(cyl_x(PIV_Y, 0, 6, xa, xb))
        # refuerzo
        t = t.fuse(box(xa, xb, PIV_Y + 6 - 0.01, PIV_Y + 12, BASE_TOP - 0.01, BASE_TOP + 6))
        b = b.fuse(t)
    b = b.cut(cyl_x(PIV_Y, 0, 1.7, -30, 30))
    b = b.cut(cyl_x(PIV_Y, 0, INSERT_D / 2, xi + FORK_T - INSERT_H, xi + FORK_T + 1))      # insert lado +X
    b = b.cut(cyl_x(PIV_Y, 0, 3.1, -xi - FORK_T - 1, -xi - FORK_T + 3.0))                 # cabeza lado -X
    return b.removeSplitter()

def export(shape, name, defl=0.03):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=defl, AngularDeflection=0.2, Relative=False)
    m.write(os.path.join(OUT, name))
    bb = shape.BoundBox
    print("  ->", name, "valido" if shape.isValid() else "NO VALIDO",
          [round(v, 1) for v in (bb.XLength, bb.YLength, bb.ZLength)])

def main():
    head, lid, base = make_head(), make_lid(), make_base()
    # piezas en posicion (para renders)
    export(head, "ref_head.stl"); export(lid, "ref_lid.stl"); export(base, "ref_base.stl")
    # LEDs de referencia
    leds = None
    for x in LED_X:
        l = cyl_y(x, 0, LED_D / 2, WALL - LED_FLANGE_T + 0.3 - 7.4 + LED_FLANGE_T, WALL + 0.3)
        l = l.fuse(Part.makeSphere(LED_D / 2, V(x, WALL - LED_FLANGE_T + 0.3 - 7.4 + LED_FLANGE_T, 0)))
        l = l.fuse(cyl_y(x, 0, 2.9, WALL - LED_FLANGE_T + 0.3, WALL + 0.3 + 0.0))
        leds = l if leds is None else leds.fuse(l)
    export(leds, "ref_leds.stl", 0.05)
    # orientadas para imprimir
    h = head.copy(); h.rotate(V(0, 0, 0), V(1, 0, 0), 90); export(h, "print_cabezal.stl")
    l = lid.copy(); l.rotate(V(0, 0, 0), V(1, 0, 0), 90); l.translate(V(0, 0, -HEAD_D)); export(l, "print_tapa.stl")
    b = base.copy(); b.translate(V(0, 0, -(BASE_TOP - BASE_T))); export(b, "print_base.stl")
    print("OK")

main()
