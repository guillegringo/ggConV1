"""Renders del emisor IR.  blender -b -P render_emisor.py"""
import bpy, math, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "stl"); REN = os.path.join(HERE, "renders"); os.makedirs(REN, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 1400, 900
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.94, 0.96, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

def mat(n, rgb, rough=0.55, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(n); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    return m

M = {"body": mat("body", (0.05, 0.05, 0.055), 0.6), "lid": mat("lid", (0.07, 0.07, 0.08), 0.6),
     "led": mat("led", (0.25, 0.1, 0.35), 0.15), "tv": mat("tv", (0.02, 0.02, 0.02), 0.3),
     "screen": mat("screen", (0.05, 0.08, 0.12), 0.1), "steel": mat("steel", (0.6, 0.6, 0.65), 0.3, 1.0)}

def load(name, m, loc=(0, 0, 0)):
    bpy.ops.wm.stl_import(filepath=os.path.join(STL, name)); o = bpy.context.selected_objects[0]
    o.data.materials.append(m); o.location = loc
    try: bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    except Exception: pass
    return o

def light(loc, e, size, tgt):
    d = bpy.data.lights.new("l%d" % len(bpy.data.lights), "AREA"); d.energy = e; d.size = size
    o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

cd = bpy.data.cameras.new("c"); cd.lens = 60; cd.clip_end = 20000
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
def shot(loc, tgt, f, lens=60):
    cam.location = loc; cd.lens = lens
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(REN, f); bpy.ops.render.render(write_still=True)

# --- emisor armado + despiece
head = load("ref_head.stl", M["body"]); lid = load("ref_lid.stl", M["lid"])
base = load("ref_base.stl", M["body"]); leds = load("ref_leds.stl", M["led"])
light((-150, -250, 200), 6e5, 200, (0, 15, 0)); light((200, -100, 150), 3e5, 150, (0, 15, 0))
light((0, 200, 250), 3e5, 200, (0, 15, 0))
tilt = math.radians(-12)
piv = bpy.data.objects.new("piv", None); sc.collection.objects.link(piv); piv.location = (0, 28, 0)
for o in (head, lid, leds):
    o.parent = piv; o.location = Vector(o.location) - Vector((0, 28, 0))
piv.rotation_euler = (tilt, 0, 0)
shot((-110, -150, 70), (0, 14, -4), "01_emisor_armado.png", 70)
piv.rotation_euler = (0, 0, 0)
lid.location.y += 25; base.location.z -= 30; leds.location.y -= 18
shot((-140, -120, 110), (0, 20, -8), "02_emisor_despiece.png", 60)
shot((120, 160, 90), (0, 20, -8), "03_emisor_atras.png", 60)
lid.location.y -= 25; base.location.z += 30; leds.location.y += 18

# --- en una tele de 55": 2 arriba y 2 abajo
TVW, TVH = 1220.0, 690.0
for o in (head, lid, base, leds): o.select_set(True)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 60, TVH / 2)); tv = bpy.context.object
tv.scale = (TVW + 20, 40, TVH + 20); tv.data.materials.append(M["tv"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 39.5, TVH / 2), rotation=(math.pi / 2, 0, 0))
sc_ = bpy.context.object; sc_.scale = (TVW, TVH, 1); sc_.data.materials.append(M["screen"])
group = [head, lid, base, leds]
spots = [(-TVW / 4, TVH + 10 + 19, -10), (TVW / 4, TVH + 10 + 19, -10), (-TVW / 4, -10 - 3 - 0, 12), (TVW / 4, -13, 12)]
for i, (x, z, t) in enumerate(spots):
    root = bpy.data.objects.new("e%d" % i, None); sc.collection.objects.link(root)
    root.location = (x, 40 - 14 - 30, z)
    for o in group:
        c = o.copy(); sc.collection.objects.link(c)
        c.parent = root if o.parent is None else None
        if o.parent is not None:
            c.parent = root; c.location = Vector(o.location) + Vector((0, 28, 0))
            c.rotation_euler = (0, 0, 0)
    root.rotation_euler = (math.radians(t), 0, 0)
for o in group: o.hide_render = True
light((-600, -2000, 1500), 3e7, 1500, (0, 0, 345))
shot((900, -2600, 900), (0, 0, 345), "04_en_la_tele.png", 40)
print("OK")
