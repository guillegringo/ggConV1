"""Renders y video del ensamblado en Blender.
blender -b -P render_blender.py -- stills        -> renders/*.png
blender -b -P render_blender.py -- anim          -> renders/ensamblado.mp4
(unidades: 1 unidad de Blender = 1 mm)
"""
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")
REN = os.path.join(HERE, "renders")
os.makedirs(REN, exist_ok=True)
MODE = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "stills"
CENTER = Vector((86, 0, 63))

# ------------------------------------------------------------------ escena
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
world = bpy.data.worlds.new("w"); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.93, 0.94, 0.96, 1); bg.inputs[1].default_value = 0.6

def mat(name, rgb, rough=0.55, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = "BLENDED"
        except Exception: m.blend_method = "BLEND"
    return m

M = {
    "shell": mat("shell", (0.045, 0.047, 0.052), 0.62),
    "shell2": mat("shell2", (0.06, 0.062, 0.07), 0.62),
    "ghost": mat("ghost", (0.3, 0.32, 0.36), 0.4, alpha=0.18),
    "orange": mat("orange", (0.95, 0.32, 0.03), 0.45),
    "red": mat("red", (0.75, 0.04, 0.03), 0.4),
    "black": mat("black", (0.01, 0.01, 0.01), 0.3),
    "pcb": mat("pcb", (0.02, 0.25, 0.12), 0.5),
    "metal": mat("metal", (0.75, 0.75, 0.78), 0.25, 1.0),
    "brass": mat("brass", (0.8, 0.55, 0.2), 0.3, 1.0),
    "steel": mat("steel", (0.55, 0.57, 0.62), 0.3, 1.0),
    "tact": mat("tact", (0.08, 0.08, 0.08), 0.5),
}

def load(name, material, smooth=True):
    path = os.path.join(OUT, name)
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]
    o.name = name[:-4]
    o.data.materials.append(material)
    if smooth:
        try:
            bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
        except Exception:
            try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
            except Exception: pass
    return o

P = {}
P["L"] = load("gun_L.stl", M["shell"])
P["R"] = load("gun_R.stl", M["shell2"])
P["trig"] = load("gun_trigger.stl", M["orange"])
P["cam"] = load("ref_camera.stl", M["black"])
P["pcb"] = load("ref_promicro_pcb.stl", M["pcb"], False)
P["usb"] = load("ref_promicro_usb.stl", M["metal"], False)
P["sw"] = load("ref_switch.stl", M["black"], False)
P["tactL"] = load("ref_tact_L.stl", M["tact"], False)
P["tactR"] = load("ref_tact_R.stl", M["tact"], False)
P["capsL"] = load("ref_caps_L.stl", M["red"])
P["capsR"] = load("ref_caps_R.stl", M["red"])

# piso con sombra
bpy.ops.mesh.primitive_plane_add(size=3000, location=(86, 0, -0.5))
floor = bpy.context.object
fm = mat("floor", (0.9, 0.9, 0.92), 0.8); floor.data.materials.append(fm)
try: floor.is_shadow_catcher = True
except Exception: pass

def add_light(kind, loc, energy, size=200, rot=None):
    d = bpy.data.lights.new(kind + str(len(bpy.data.lights)), kind)
    d.energy = energy
    if kind == "AREA": d.size = size
    o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o)
    o.location = loc
    look(o, CENTER)
    return o

def look(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()

add_light("AREA", (-150, -400, 350), 4.0e6, 400)
add_light("AREA", (350, 300, 250), 2.0e6, 300)
add_light("AREA", (86, -50, 600), 1.5e6, 500)

cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 70; cam_d.clip_end = 10000
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam

def shot(loc, target, fname, lens=70):
    cam.location = loc; cam_d.lens = lens; look(cam, target)
    sc.render.filepath = os.path.join(REN, fname)
    bpy.ops.render.render(write_still=True)
    print("render", fname)

# ------------------------------------------------------------------ stills
if MODE == "stills":
    shot((-60, -620, 120), CENTER, "01_lado_izquierdo.png", 60)
    shot((420, -430, 260), CENTER, "02_tres_cuartos.png", 60)
    shot((-300, 420, 180), CENTER, "03_lado_derecho.png", 60)
    # vista abierta: mitad derecha fantasma para ver el interior
    P["R"].data.materials[0] = M["ghost"]
    for k in ("capsR", "tactR"): P[k].hide_render = True
    shot((86, 640, 90), CENTER, "04_interior.png", 60)
    P["R"].hide_render = True
    shot((150, 420, 300), CENTER, "05_interior_34.png", 60)


# ------------------------------------------------------------------ animacion
if MODE == "anim":
    import json
    LAY = json.load(open(os.path.join(OUT, "layout.json")))
    FPS = 30
    T_END = 14.0
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, int(T_END * FPS)
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    try: sc.eevee.taa_render_samples = 24
    except Exception: pass

    def cyl(name, r, y0, y1, x, z, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=abs(y1 - y0), vertices=24,
                                            location=(x, (y0 + y1) / 2, z), rotation=(math.pi / 2, 0, 0))
        o = bpy.context.object; o.name = name; o.data.materials.append(material); return o

    # heat inserts (mitad izquierda) y tornillos (desde la derecha)
    hs, inner, tt, ih = LAY["head_seat"], LAY["inner"], LAY["trig_t"], LAY["insert_h"]
    inserts, screws = [], []
    for i, (x, z) in enumerate(LAY["bosses"]):
        inserts.append(cyl("ins%d" % i, 2.3, -5.7, 0, x, z, M["brass"]))
        s = cyl("scr%d" % i, 1.5, -hs, hs, x, z, M["steel"])
        h = cyl("head%d" % i, 2.75, hs, hs + 3, x, z, M["steel"])
        h.parent = s; h.location = h.location - s.location; h.matrix_parent_inverse.identity()
        screws.append(s)
    px, pz = LAY["pivot"]
    inserts.append(cyl("insP", 2.3, -(tt / 2 + 0.4 + 5.7), -(tt / 2 + 0.4), px, pz, M["brass"]))
    sp = cyl("scrP", 1.5, -13.5, inner - 1, px, pz, M["steel"])
    hp = cyl("headP", 2.75, inner - 1, inner + 2, px, pz, M["steel"])
    hp.parent = sp; hp.location = hp.location - sp.location; hp.matrix_parent_inverse.identity()
    screws.append(sp)

    # jerarquia: "spin" gira todo; "hinge" abre la mitad derecha como un libro
    spin = bpy.data.objects.new("spin", None); sc.collection.objects.link(spin); spin.location = CENTER
    hinge = bpy.data.objects.new("hinge", None); sc.collection.objects.link(hinge)
    HZ = 135.0
    hinge.parent = spin; hinge.location = Vector((0, 0, HZ)) - CENTER
    for k in ("R", "sw", "tactR", "capsR"):
        o = P[k]; o.parent = hinge; o.location = (0, 0, -HZ)
    for o in list(P.values()) + inserts + screws:
        if o.parent is None:
            o.parent = spin; o.location = o.location - CENTER

    def key(o, attr, t, value):
        setattr(o, attr, value); o.keyframe_insert(attr, frame=int(t * FPS) + 1)

    def fly(o, t0, t1, offset):
        base = o.location.copy()
        key(o, "location", 0, base + Vector(offset)); key(o, "location", t0, base + Vector(offset))
        key(o, "location", t1, base)

    def hide_until(o, t):
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
        o.hide_render = False; o.keyframe_insert("hide_render", frame=int(t * FPS))

    for i, o in enumerate(inserts): fly(o, 0.3 + 0.05 * i, 1.2 + 0.05 * i, (0, 45, 0))
    fly(P["cam"], 1.3, 2.3, (90, 0, 0))
    fly(P["pcb"], 2.3, 3.3, (0, 0, -90)); fly(P["usb"], 2.3, 3.3, (0, 0, -90))
    fly(P["trig"], 3.3, 4.3, (0, 0, -80))
    fly(P["sw"], 4.3, 5.1, (0, -50, 0))
    for k in ("tactL", "capsL"): fly(P[k], 5.1, 6.0, (0, 50, 0))
    for k in ("tactR", "capsR"): fly(P[k], 5.1, 6.0, (0, -50, 0))
    key(hinge, "rotation_euler", 0, (math.pi, 0, 0)); key(hinge, "rotation_euler", 6.3, (math.pi, 0, 0))
    key(hinge, "rotation_euler", 8.0, (0, 0, 0))
    for i, o in enumerate(screws):
        hide_until(o, 8.2)
        fly(o, 8.2 + 0.06 * i, 9.2 + 0.06 * i, (0, 50, 0))
    key(spin, "rotation_euler", 0, (0, 0, 0)); key(spin, "rotation_euler", 9.8, (0, 0, 0))
    key(spin, "rotation_euler", 13.6, (0, 0, -2 * math.pi))

    # camara con objetivo animado
    tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    cam_d.lens = 50
    key(cam, "location", 0, Vector((150, 700, 260))); key(tgt, "location", 0, Vector((86, 0, 125)))
    key(cam, "location", 6.3, Vector((150, 700, 260))); key(tgt, "location", 6.3, Vector((86, 0, 125)))
    key(cam, "location", 8.2, Vector((170, 470, 200))); key(tgt, "location", 8.2, Vector((86, 0, 66)))

    frames = os.path.join(REN, "frames")
    os.makedirs(frames, exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(frames, "f")
    bpy.ops.render.render(animation=True)
    print("anim ok")
