"""Renders de las versiones de emisores IR.   blender -b -P render_emisor.py
Lee escenas/<nombre>/{dark,led,ctx,screen}.stl (generadas por emisor_fc.py) y stl/*.stl.
"""
import bpy, math, os, glob
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SCN, STL, REN = (os.path.join(HERE, d) for d in ("escenas", "stl", "renders"))
os.makedirs(REN, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    try: sc.view_settings.view_transform = "Standard"
    except Exception: pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.95, 0.96, 0.97, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    return sc

def mat(n, rgb, rough=0.55, metal=0.0, emit=None):
    m = bpy.data.materials.new(n); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    return m

def load(path, m, smooth=True):
    bpy.ops.wm.stl_import(filepath=path); o = bpy.context.selected_objects[0]
    o.data.materials.append(m)
    if smooth:
        try: bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
        except Exception: pass
    return o

def bbox(objs):
    bpy.context.view_layer.update()          # aplica escalas/posiciones recien asignadas
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    for o in objs:
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    return lo, hi

def lights(sc, center, r):
    for loc, e in (((-1.2, -2.0, 1.6), 3.0), ((1.6, -0.8, 1.0), 1.5), ((0.3, 1.8, 1.8), 1.2)):
        d = bpy.data.lights.new("l%d" % len(bpy.data.lights), "AREA"); d.size = r * 3
        d.energy = e * (r * 5) ** 2 * 1.2
        o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o)
        o.location = center + Vector(loc) * r * 5
        o.rotation_euler = (center - o.location).to_track_quat("-Z", "Y").to_euler()

def shoot(sc, focus, fname, direction=(-0.6, -1.0, 0.55), margin=1.5, lens=50):
    lo, hi = bbox(focus)
    center = (lo + hi) / 2
    r = (hi - lo).length / 2 * margin
    cd = bpy.data.cameras.new("c"); cd.lens = lens; cd.clip_end = 1e5
    cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    fov = 2 * math.atan(18 / lens) * 0.62
    cam.location = center + Vector(direction).normalized() * (r / math.sin(fov / 2))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    lights(sc, center, r)
    sc.render.filepath = os.path.join(REN, fname)
    bpy.ops.render.render(write_still=True)
    print("render", fname)

M = None
def mats():
    return {"dark": mat("dark", (0.045, 0.047, 0.055), 0.6), "led": mat("led", (0.35, 0.12, 0.5), 0.15),
            "ctx": mat("ctx", (0.55, 0.56, 0.58), 0.7), "screen": mat("screen", (0.03, 0.05, 0.08), 0.12),
            "part": mat("part", (0.1, 0.11, 0.13), 0.55)}

# (escena, archivo, direccion de camara, foco: "dark" o "all", margen)
SHOTS = [
    ("v1_tele_gruesa", "v1_tele_gruesa.png", (-0.7, -1.0, 0.45), "dark", 2.6),
    ("v2_tele_finita", "v2_tele_finita.png", (-0.8, -1.0, 0.35), "dark", 1.25),
    ("v2_tele_finita", "v2_gancho_perfil.png", (-1.0, -0.05, 0.12), "top", 1.6),
    ("v3_proyector", "v3_proyector.png", (-0.7, -1.0, 0.4), "dark", 3.2),
    ("v3_tele_colgada", "v3_tele_colgada.png", (-0.9, -1.0, 0.1), "dark", 3.0),
    ("v4_arcade", "v4_arcade_frente.png", (-0.5, -1.0, 0.45), "all", 1.0),
    ("v4_arcade", "v4_arcade_atras.png", (0.6, 1.0, 0.5), "dark", 1.4),
    ("v5_hub", "v5_hub.png", (-0.8, -1.0, 0.9), "dark", 1.3),
]

for scene_name, fname, direction, focus, margin in SHOTS:
    sc = reset(); M = mats()
    d = os.path.join(SCN, scene_name)
    objs = {}
    for k in ("dark", "led", "ctx", "screen"):
        p = os.path.join(d, k + ".stl")
        if os.path.exists(p):
            objs[k] = load(p, M[k], k in ("dark", "led"))
    if focus == "top":
        # perfil del gancho: corte de la tele (12 mm) en vez de la tele entera
        for k in ("ctx", "screen"):
            if k in objs: objs[k].hide_render = True
        lo, hi = bbox([objs["dark"]])
        bpy.ops.mesh.primitive_cube_add(size=1)
        tv = bpy.context.object; tv.data.materials.append(M["ctx"])
        tv.scale = (30, 12, 70); tv.location = (0, 12 + 6, -19 - 35)
        bpy.ops.mesh.primitive_cube_add(size=1)
        dummy = bpy.context.object; dummy.hide_render = True
        dummy.scale = (50, 50, 60); dummy.location = (0, 25, hi.z - 32)
        fo = [dummy]
    elif focus == "all":
        fo = list(objs.values())
    else:
        fo = [objs["dark"]]
    shoot(sc, fo, fname, direction, margin)

# lamina con todas las piezas para imprimir
sc = reset(); M = mats()
files = sorted(glob.glob(os.path.join(STL, "*.stl")))
x = y = 0.0; row_h = 0.0; placed = []
for f in files:
    o = load(f, M["part"])
    lo, hi = bbox([o])
    w, h = hi.x - lo.x, hi.y - lo.y
    if x + w > 330:
        x = 0; y -= row_h + 18; row_h = 0
    o.location = (x - lo.x, y - hi.y, -lo.z)
    x += w + 18; row_h = max(row_h, h)
    placed.append(o)
shoot(sc, placed, "piezas_para_imprimir.png", (0.0, -0.45, 1.0), 0.62, 50)
print("OK")
