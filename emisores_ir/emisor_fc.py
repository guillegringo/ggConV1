# -*- coding: utf-8 -*-
"""
Emisores IR para GUN4IR - sistema modular.

  CAPSULA  = cabezal (3 LEDs IR 5 mm + resistencia) + tapa con pestana de bisagra.  Se suelda una vez.
  SOPORTES = distintas piezas que terminan en la misma HORQUILLA ESTANDAR (eje M3 + heat insert):
     V1 base        -> arriba de una tele gruesa / apoyada en el mueble
     V2 gancho      -> clip para el borde de una tele finita (arriba, o invertido abajo)
     V3 pared       -> atornillada a la pared: proyector o tele colgada (con separador)
     V4 arcade      -> capsula redonda que se empotra en un agujero de boton de 30 mm
     V5 hub         -> caja de empalme: 1 USB entra, 4 emisores salen

Ejecutar:  "D:/Program Files/FreeCAD 1.0/bin/FreeCADCmd.exe" emisor_fc.py
Salida:    stl/  (piezas para imprimir)   escenas/  (piezas en posicion para los renders)
Ejes: X a lo ancho de la tele, Y profundidad (-Y = hacia el jugador), Z arriba.
"""
import math, os, json
import FreeCAD as App
import Part, MeshPart
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(HERE, "stl")
SCN = os.path.join(HERE, "escenas")
for d in (OUT, SCN):
    os.makedirs(d, exist_ok=True)

# =========================== capsula ===========================
HEAD_W, HEAD_H, HEAD_D = 46.0, 18.0, 20.0
WALL = 2.2
R_OUT = 3.0
LED_D, LED_HOLE, LED_FLANGE_D, LED_FLANGE_T = 5.0, 5.15, 6.1, 1.2
LED_X = (-9.0, 0.0, 9.0)
LID_T = 2.5
BOSS_X = 18.5
INSERT_D, INSERT_H = 4.2, 6.0
CABLE_D = 4.6
CABLE_X = (-8.0, 8.0)

# =========================== horquilla estandar ===========================
TAB_T = 6.6                         # pestana de la tapa (va entre las dos orejas)
PIV_Y = HEAD_D + LID_T + 5.5        # eje de giro, en coordenadas de la capsula: (0, PIV_Y, 0)
FORK_T = 7.0
FORK_GAP = 0.2
MOUNT_TOP = -16.0                   # cara superior de cualquier soporte (deja inclinar +-25 grados)

# =========================== soportes ===========================
BASE_T = 3.0
BASE_Y = (14.0, 44.0)
BASE_W = 40.0
# V2 gancho
CLIP_W = 24.0
CLIP_YF = 12.0                      # donde queda el frente de la tele (bajo la capsula)
CLIP_T_LIST = (8, 12, 18, 25)       # espesores de tele a exportar (medir el borde de la tuya)
CLIP_LIP = 4.0                      # cuanto baja la pestana delantera (tapa el marco, no la imagen)
CLIP_ARM = 24.0                     # largo del brazo trasero
CLIP_PINCH = 2.0                    # grados que el brazo se cierra para apretar
# V3 pared
WALL_W = 40.0
WALL_H = 46.0
WALL_STANDOFFS = (0, 40)            # 0 = proyector / pared; 40 = tele colgada (LEDs al ras del frente)
# V4 arcade
ARC_HOLE = 30.0                     # agujero de boton arcade estandar
ARC_FLANGE_D, ARC_FLANGE_T = 37.0, 2.5
ARC_PANELS = (3, 18)                # espesor del panel: acrilico/metal 3 mm, MDF 18 mm
ARC_INNER_D = 21.0
ARC_TAIL = 16.0                     # largo detras de la ranura (LEDs, resistencia, cable)
ARC_GROOVE_W, ARC_GROOVE_D = 2.2, 2.2
ARC_LED_R = 5.5                     # LEDs en triangulo
# V5 hub
HUB_L, HUB_W, HUB_H = 58.0, 36.0, 20.0

# =========================== utilidades ===========================
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cyl_y(x, z, r, y0, y1):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))

def cyl_x(y, z, r, x0, x1):
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))

def cyl_z(x, y, r, z0, z1):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))

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
    if not es:
        return s
    try:
        f = s.makeFillet(r, es)
        if f.isValid():
            return f
    except Exception as ex:
        print("  fillet fallo", label, ex)
    return s

def profile_yz(pts, x0, x1):
    """extruye un perfil (y, z) a lo largo de X"""
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))

# =========================== capsula ===========================
def make_head():
    w2, h2 = HEAD_W / 2, HEAD_H / 2
    h = box(-w2, w2, 0, HEAD_D, -h2, h2)
    h = fillet(h, R_OUT, lambda e: is_dir(e, V(0, 1, 0)), "head long")
    h = fillet(h, 2.0, lambda e: e.BoundBox.YMax < 1e-3, "head front")
    h = h.cut(box(-w2 + WALL, w2 - WALL, WALL, HEAD_D + 1, -h2 + WALL, h2 - WALL))
    for sx in (-1, 1):
        b = cyl_y(sx * BOSS_X, 0, 3.5, WALL - 0.01, HEAD_D)
        b = b.fuse(box(min(sx * BOSS_X, sx * (BOSS_X + 3.5)), max(sx * BOSS_X, sx * (BOSS_X + 3.5)),
                       WALL - 0.01, HEAD_D, -3.5, 3.5))
        h = h.fuse(b.common(box(-w2 + 0.5, w2 - 0.5, 0, HEAD_D, -h2 + 0.5, h2 - 0.5)))
        h = h.cut(cyl_y(sx * BOSS_X, 0, INSERT_D / 2, HEAD_D - INSERT_H, HEAD_D + 1))
        h = h.cut(cyl_y(sx * BOSS_X, 0, 1.3, WALL + 0.8, HEAD_D))
    for x in LED_X:
        h = h.cut(cyl_y(x, 0, LED_HOLE / 2, -1, WALL + 1))
        h = h.cut(cyl_y(x, 0, LED_FLANGE_D / 2, WALL - LED_FLANGE_T + 0.3, WALL + 1))
    return h.removeSplitter()

def make_lid():
    w2, h2 = HEAD_W / 2, HEAD_H / 2
    y0, y1 = HEAD_D, HEAD_D + LID_T
    lid = box(-w2, w2, y0, y1, -h2, h2)
    lid = fillet(lid, R_OUT, lambda e: is_dir(e, V(0, 1, 0)), "lid")
    tab = box(-TAB_T / 2, TAB_T / 2, y1 - 0.01, PIV_Y, -6, 6).fuse(cyl_x(PIV_Y, 0, 6, -TAB_T / 2, TAB_T / 2))
    lid = lid.fuse(tab).cut(cyl_x(PIV_Y, 0, 1.7, -10, 10))
    for sx in (-1, 1):
        lid = lid.cut(cyl_y(sx * BOSS_X, 0, 1.7, y0 - 3, y1 + 1))
        lid = lid.cut(cyl_y(sx * BOSS_X, 0, 3.1, y1 - 0.8, y1 + 1))
    for x in CABLE_X:
        lid = lid.cut(cyl_y(x, -2.0, CABLE_D / 2, y0 - 3, y1 + 1))
    return lid.removeSplitter()

def make_leds_ref(positions, axis_y0):
    """LEDs de referencia (para renders): cada uno O5 con domo, apuntando a -Y"""
    leds = None
    for x, z in positions:
        tip = axis_y0 - 7.4 + LED_FLANGE_T
        l = cyl_y(x, z, LED_D / 2, tip, axis_y0 + 0.3)
        l = l.fuse(Part.makeSphere(LED_D / 2, V(x, tip, z)))
        l = l.fuse(cyl_y(x, z, 2.9, axis_y0, axis_y0 + 0.3))
        leds = l if leds is None else leds.fuse(l)
    return leds

# =========================== horquilla ===========================
def fork_solid(zb=MOUNT_TOP):
    xi = TAB_T / 2 + FORK_GAP
    out = None
    for sx in (-1, 1):
        xa, xb = (xi, xi + FORK_T) if sx > 0 else (-xi - FORK_T, -xi)
        t = box(xa, xb, PIV_Y - 6, PIV_Y + 6, zb - 0.01, 0).fuse(cyl_x(PIV_Y, 0, 6, xa, xb))
        t = t.fuse(box(xa, xb, PIV_Y + 6 - 0.01, PIV_Y + 12, zb - 0.01, zb + 6))
        out = t if out is None else out.fuse(t)
    return out

def fork_cut(shape):
    xi = TAB_T / 2 + FORK_GAP
    s = shape.cut(cyl_x(PIV_Y, 0, 1.7, -30, 30))
    s = s.cut(cyl_x(PIV_Y, 0, INSERT_D / 2, xi + FORK_T - INSERT_H, xi + FORK_T + 1))
    s = s.cut(cyl_x(PIV_Y, 0, 3.1, -xi - FORK_T - 1, -xi - FORK_T + 3.0))
    return s

# =========================== V1 base ===========================
def make_base():
    b = box(-BASE_W / 2, BASE_W / 2, BASE_Y[0], BASE_Y[1], MOUNT_TOP - BASE_T, MOUNT_TOP)
    b = fillet(b, 4.0, lambda e: is_dir(e, V(0, 0, 1)), "base")
    return fork_cut(b.fuse(fork_solid())).removeSplitter()

# =========================== V2 gancho ===========================
def make_clip(T):
    zt, zb = MOUNT_TOP, MOUNT_TOP - 3.0            # puente
    yf = CLIP_YF
    y_end = max(yf + T + 2.5, PIV_Y + 13)
    hw = CLIP_W / 2
    bridge = box(-hw, hw, yf - 2.5, y_end, zb, zt)
    lip = profile_yz([(yf - 2.5, zt), (yf, zt), (yf, zb - CLIP_LIP), (yf - 1.2, zb - CLIP_LIP), (yf - 2.5, zb - CLIP_LIP + 1.3)], -hw, hw)
    arm = box(-hw, hw, yf + T, yf + T + 2.5, zb - CLIP_ARM, zt)
    arm.rotate(V(0, yf + T, zb), V(1, 0, 0), -CLIP_PINCH)               # se cierra: muerde la tele
    bump = cyl_x(yf + T - 0.2, zb - CLIP_ARM + 3, 1.0, -hw, hw)         # nervio de agarre
    bump.rotate(V(0, yf + T, zb), V(1, 0, 0), -CLIP_PINCH)
    c = bridge.fuse([lip, arm, bump])
    c = fillet(c, 1.2, lambda e: is_dir(e, V(1, 0, 0)) and abs(e.BoundBox.ZMin - zt) < 1e-3 and e.BoundBox.YMin > yf + T, "clip top")
    return fork_cut(c.fuse(fork_solid())).removeSplitter()

# =========================== V3 pared ===========================
def make_wall(standoff):
    zt, zb = MOUNT_TOP, MOUNT_TOP - 3.0
    yw = BASE_Y[1] + standoff                       # cara delantera de la placa de pared
    hw = WALL_W / 2
    shelf = box(-hw, hw, BASE_Y[0], yw + 0.01, zb, zt)
    plate = box(-hw, hw, yw, yw + 4, zb, zb + WALL_H)
    plate = fillet(plate, 4.0, lambda e: is_dir(e, V(0, 1, 0)) and e.BoundBox.ZMin > zb + 1, "wall top")
    ribs = [profile_yz([(PIV_Y + 12, zt - 0.01), (yw + 0.01, zt - 0.01), (yw + 0.01, zt + min(24, 10 + standoff * 0.5))], x, x + 3)
            for x in (-hw, hw - 3)]
    w = shelf.fuse([plate] + ribs)
    for z in (zb + 18, zb + WALL_H - 9):            # tornillos de pared (tarugo de 5 + tornillo 3.5)
        w = w.cut(cyl_y(0, z, 2.1, yw - 1, yw + 5))
        w = w.cut(Part.makeCone(4.2, 2.1, 2.2, V(0, yw - 0.01, z), V(0, 1, 0)))
    return fork_cut(w.fuse(fork_solid())).removeSplitter()

# =========================== V4 arcade ===========================
def arc_led_positions():
    return [(ARC_LED_R * math.cos(math.radians(a)), ARC_LED_R * math.sin(math.radians(a))) for a in (90, 210, 330)]

def make_arcade(panel):
    r_body = ARC_HOLE / 2 - 0.3
    y_groove = panel + 0.2
    y_end = y_groove + ARC_GROOVE_W + ARC_TAIL
    b = cyl_y(0, 0, ARC_FLANGE_D / 2, -ARC_FLANGE_T, 0)
    b = b.fuse(cyl_y(0, 0, r_body, -0.01, y_end))
    b = fillet(b, 1.0, lambda e: e.BoundBox.YMax < -ARC_FLANGE_T + 1e-3, "arc front")
    b = b.cut(cyl_y(0, 0, r_body + 1, y_groove, y_groove + ARC_GROOVE_W).cut(cyl_y(0, 0, r_body - ARC_GROOVE_D, y_groove - 1, y_groove + ARC_GROOVE_W + 1)))
    b = b.cut(cyl_y(0, 0, ARC_INNER_D / 2, 0.0, y_end + 1))
    for x, z in arc_led_positions():
        b = b.cut(cyl_y(x, z, LED_HOLE / 2, -ARC_FLANGE_T - 1, 1))
        b = b.cut(cyl_y(x, z, LED_FLANGE_D / 2, -LED_FLANGE_T + 0.3, 1))
    return b.removeSplitter(), y_groove, y_end

def make_arcade_cap(y_end):
    c = cyl_y(0, 0, ARC_HOLE / 2 - 0.3, y_end, y_end + 2.0)
    c = c.fuse(cyl_y(0, 0, ARC_INNER_D / 2 - 0.15, y_end - 4, y_end + 0.01))
    c = c.cut(cyl_y(0, 0, ARC_INNER_D / 2 - 1.8, y_end - 5, y_end - 0.01 + 0.0))
    c = c.cut(cyl_y(0, 0, CABLE_D / 2, y_end - 6, y_end + 3))
    return c.removeSplitter()

def make_arcade_clip(y_groove):
    r_in = ARC_HOLE / 2 - 0.3 - ARC_GROOVE_D + 0.15
    c = cyl_y(0, 0, ARC_FLANGE_D / 2 + 1, y_groove + 0.05, y_groove + ARC_GROOVE_W - 0.15)
    c = c.cut(cyl_y(0, 0, r_in, y_groove - 1, y_groove + 3))
    c = c.cut(box(-r_in * 0.86, r_in * 0.86, y_groove - 1, y_groove + 3, -40, -r_in * 0.3))     # boca: entra a presion
    c = c.fuse(box(-4, 4, y_groove + 0.05, y_groove + ARC_GROOVE_W - 0.15, ARC_FLANGE_D / 2 - 1, ARC_FLANGE_D / 2 + 6))  # orejita
    return c.removeSplitter()

# =========================== V5 hub ===========================
def make_hub():
    l2, w2 = HUB_L / 2, HUB_W / 2
    b = box(-l2, l2, -w2, w2, 0, HUB_H)
    b = fillet(b, 3.0, lambda e: is_dir(e, V(0, 0, 1)), "hub")
    b = b.cut(box(-l2 + 2, l2 - 2, -w2 + 2, w2 - 2, 2, HUB_H + 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = cyl_z(sx * (l2 - 5), sy * (w2 - 5), 3.5, 1.9, HUB_H)
            b = b.fuse(p.cut(cyl_z(sx * (l2 - 5), sy * (w2 - 5), INSERT_D / 2, HUB_H - INSERT_H, HUB_H + 1)))
    b = b.cut(cyl_x(0, HUB_H / 2 + 1, CABLE_D / 2, -l2 - 1, -l2 + 3))                       # entrada USB
    for y in (-9.6, -3.2, 3.2, 9.6):                                                       # 4 salidas
        b = b.cut(cyl_x(y, HUB_H / 2 + 1, CABLE_D / 2, l2 - 3, l2 + 1))
    for sx in (-1, 1):                                                                     # orejas para atornillar
        e = box(sx * l2 - (8 if sx > 0 else -8) * 0 + (0 if sx > 0 else -8), sx * l2 + (8 if sx > 0 else 0), -6, 6, 0, 2.5)
        e = e.cut(cyl_z(sx * (l2 + 4), 0, 1.8, -1, 4))
        b = b.fuse(e)
    return b.removeSplitter()

def make_hub_lid():
    l2, w2 = HUB_L / 2, HUB_W / 2
    t = box(-l2, l2, -w2, w2, HUB_H, HUB_H + 2)
    t = fillet(t, 3.0, lambda e: is_dir(e, V(0, 0, 1)), "hub lid")
    t = t.fuse(box(-l2 + 2.2, l2 - 2.2, -w2 + 2.2, w2 - 2.2, HUB_H - 1.5, HUB_H + 0.01)
               .cut(box(-l2 + 3.4, l2 - 3.4, -w2 + 3.4, w2 - 3.4, HUB_H - 2, HUB_H + 0.1)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            t = t.cut(cyl_z(sx * (l2 - 5), sy * (w2 - 5), 4.0, HUB_H - 2, HUB_H + 0.01))
            t = t.cut(cyl_z(sx * (l2 - 5), sy * (w2 - 5), 1.7, HUB_H - 3, HUB_H + 3))
    t = t.cut(cyl_z(0, 0, 2.0, HUB_H - 2, HUB_H + 3))          # opcional: LED testigo de 3 mm
    return t.removeSplitter()

# =========================== exportar ===========================
def export(shape, path, defl=0.03):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=defl, AngularDeflection=0.2, Relative=False)
    m.write(path)
    bb = shape.BoundBox
    ok = "valido" if shape.isValid() else "NO VALIDO"
    print("  ->", os.path.relpath(path, HERE), ok, [round(v, 1) for v in (bb.XLength, bb.YLength, bb.ZLength)])
    return [round(v, 1) for v in (bb.XLength, bb.YLength, bb.ZLength)]

def flat(shape, rot_axis=None, angle=0, drop=True):
    s = shape.copy()
    if rot_axis is not None:
        s.rotate(V(0, 0, 0), rot_axis, angle)
    bb = s.BoundBox
    s.translate(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, -bb.ZMin))
    return s

def capsule_at(tilt_deg, head, lid, leds):
    out = []
    for s in (head, lid, leds):
        c = s.copy()
        c.rotate(V(0, PIV_Y, 0), V(1, 0, 0), tilt_deg)
        out.append(c)
    return out

def placed(shape, rot=None, move=V(0, 0, 0)):
    s = shape.copy()
    if rot is not None:
        s.rotate(rot[0], rot[1], rot[2])
    s.translate(move)
    return s

def scene(name, dark, led, ctx, screen=None):
    d = os.path.join(SCN, name)
    os.makedirs(d, exist_ok=True)
    def fuse(lst):
        lst = [x for x in lst if x is not None]
        return lst[0].fuse(lst[1:]) if len(lst) > 1 else lst[0]
    export(fuse(dark), os.path.join(d, "dark.stl"), 0.06)
    export(fuse(led), os.path.join(d, "led.stl"), 0.08)
    if ctx:
        export(fuse(ctx), os.path.join(d, "ctx.stl"), 0.2)
    if screen:
        export(fuse(screen), os.path.join(d, "screen.stl"), 0.2)

def main():
    sizes = {}
    head, lid = make_head(), make_lid()
    leds = make_leds_ref([(x, 0) for x in LED_X], WALL - LED_FLANGE_T + 0.3)
    base = make_base()
    clips = {T: make_clip(T) for T in CLIP_T_LIST}
    walls = {S: make_wall(S) for S in WALL_STANDOFFS}
    arcs = {P: make_arcade(P) for P in ARC_PANELS}
    hub, hub_lid = make_hub(), make_hub_lid()

    print("== piezas para imprimir ==")
    sizes["capsula_cabezal"] = export(flat(head, V(1, 0, 0), 90), os.path.join(OUT, "capsula_cabezal.stl"))
    l = lid.copy(); l.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    sizes["capsula_tapa"] = export(flat(l), os.path.join(OUT, "capsula_tapa.stl"))
    sizes["v1_base"] = export(flat(base), os.path.join(OUT, "v1_base.stl"))
    for T, c in clips.items():
        sizes["v2_gancho_T%02d" % T] = export(flat(c, V(0, 1, 0), 90), os.path.join(OUT, "v2_gancho_T%02d.stl" % T))
    for S, w in walls.items():
        sizes["v3_pared_S%02d" % S] = export(flat(w, V(0, 1, 0), 90), os.path.join(OUT, "v3_pared_S%02d.stl" % S))
    for P, (body, yg, ye) in arcs.items():
        sizes["v4_arcade_cuerpo_P%02d" % P] = export(flat(body, V(1, 0, 0), -90), os.path.join(OUT, "v4_arcade_cuerpo_P%02d.stl" % P))
        sizes["v4_arcade_tapa_P%02d" % P] = export(flat(make_arcade_cap(ye), V(1, 0, 0), -90), os.path.join(OUT, "v4_arcade_tapa_P%02d.stl" % P))
    sizes["v4_arcade_clip"] = export(flat(make_arcade_clip(arcs[ARC_PANELS[0]][1]), V(1, 0, 0), -90), os.path.join(OUT, "v4_arcade_clip.stl"))
    sizes["v5_hub_caja"] = export(flat(hub), os.path.join(OUT, "v5_hub_caja.stl"))
    sizes["v5_hub_tapa"] = export(flat(hub_lid, V(1, 0, 0), 180), os.path.join(OUT, "v5_hub_tapa.stl"))

    print("== escenas ==")
    # V1: tele gruesa vieja (arriba) - capsula sobre la tapa de la tele, inclinada hacia abajo
    cap = capsule_at(12, head, lid, leds)
    tv_top = MOUNT_TOP - BASE_T
    scene("v1_tele_gruesa",
          [base, cap[0], cap[1]], [cap[2]],
          [box(-160, 160, 8, 240, tv_top - 260, tv_top)],
          [box(-150, 150, 7.5, 8, tv_top - 250, tv_top - 12)])
    # V2: tele finita, gancho arriba y otro invertido abajo
    T = 12
    c = clips[T]
    cap = capsule_at(12, head, lid, leds)
    top = [c, cap[0], cap[1]]
    tvz = MOUNT_TOP - 3.0
    H = 160.0
    flip = (V(0, 0, 0), V(0, 1, 0), 180)
    cap2 = capsule_at(12, head, lid, leds)
    bottom = [placed(s, flip, V(0, 0, 2 * tvz - H)) for s in (c, cap2[0], cap2[1])]
    scene("v2_tele_finita",
          top + bottom, [cap[2], placed(cap2[2], flip, V(0, 0, 2 * tvz - H))],
          [box(-170, 170, CLIP_YF, CLIP_YF + T, tvz - H, tvz)],
          [box(-165, 165, CLIP_YF - 0.3, CLIP_YF, tvz - H + 5, tvz - 5)])
    # V3a: proyector - soporte a la pared sobre la tela
    w = walls[0]
    cap = capsule_at(15, head, lid, leds)
    yw = BASE_Y[1] + 0 + 4
    zb = MOUNT_TOP - 3.0
    scene("v3_proyector",
          [w, cap[0], cap[1]], [cap[2]],
          [box(-260, 260, yw, yw + 10, zb - 330, zb + 120)],
          [box(-200, 200, yw - 1, yw, zb - 300, zb - 20)])
    # V3b: tele colgada - soporte con separador debajo de la tele, invertido
    w = walls[40]
    cap = capsule_at(15, head, lid, leds)
    yw = BASE_Y[1] + 40 + 4
    parts = [placed(s, flip) for s in (w, cap[0], cap[1])]
    tv_bot = -zb + 25
    scene("v3_tele_colgada",
          parts, [placed(cap[2], flip)],
          [box(-260, 260, yw, yw + 10, -200, 380), box(-200, 200, yw - 45, yw - 12, tv_bot, tv_bot + 230)],
          [box(-195, 195, yw - 45.4, yw - 45, tv_bot + 5, tv_bot + 225)])
    # V4: arcade, panel de 18 mm
    body, yg, ye = arcs[18]
    aleds = make_leds_ref(arc_led_positions(), -LED_FLANGE_T + 0.3)
    panel = box(-90, 90, 0, 18, -60, 60).cut(cyl_y(0, 0, ARC_HOLE / 2, -1, 19))
    scene("v4_arcade",
          [body, make_arcade_cap(ye), make_arcade_clip(yg)], [aleds],
          [panel], None)
    # V5: hub
    scene("v5_hub", [hub, placed(hub_lid, None, V(0, 0, 14))], [cyl_z(0, 0, 1.5, HUB_H + 14, HUB_H + 19)], None, None)

    json.dump(sizes, open(os.path.join(OUT, "medidas.json"), "w"), indent=1)
    print("OK")

main()
