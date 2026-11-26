"""Build the full-height walkthrough from the same geometry as the Cycles render."""
import bpy
import json
import pathlib
import math
import sys
from mathutils import Vector

root = pathlib.Path(__file__).resolve().parents[1]
source = root / "design/render.py"
namespace = {"__file__": str(source)}
exec(compile(source.read_text().split("\nargs=sys.argv", 1)[0], str(source), "exec"), namespace)
globals().update({key: namespace[key] for key in ("axon", "box", "panel", "rod", "rooms", "layout", "scale", "xy", "bounds", "plan_boxes", "light", "camera", "mat")})
from surfaces import strip_for_glb

scene = axon()
ceiling = 3.30
roof_prefixes = ("Walk ceiling", "Walk beam", "Walk services", "Aisle downlight", "Trimless downlight", "Recessed lamp")
fixtures = ("Oak desktop", "Upholstered seat", "Sofa base", "Circular table",
            "Boardroom oak tabletop", "Reception desk", "Pantry counter",
            "Refrigerator", "Rack shelf", "Product inspection island", "Packing bench top",
            "Presentation table", "Rolling equipment case", "Tripod leg")
structural = ("Proposed partition", "Existing structural core", "Existing column", "Existing core partition", "Fitout glass")

def resize_height(obj, top):
    bottom = obj.location.z - obj.dimensions.z / 2
    obj.scale.z *= (top - bottom) / obj.dimensions.z
    obj.location.z = (top + bottom) / 2

for obj in list(scene.objects):
    name = obj.name
    if obj.type != "MESH" or name.startswith(("Presentation backdrop", "Perimeter glazing head")):
        bpy.data.objects.remove(obj, do_unlink=True)
    elif name.startswith("Proposed partition") and abs(obj.location.x-xy(346,0)[0])<.005 and abs(obj.rotation_euler.z)>1:
        # Blackened bronze frames on the visitor-facing corridor, with actual
        # openings retained from the same door cuts as the printed plan.
        x,y=obj.location.x,obj.location.y
        length=(max(p[0] for p in obj.bound_box)-min(p[0] for p in obj.bound_box))*abs(obj.scale.x)
        bpy.data.objects.remove(obj,do_unlink=True)
        if length>.07:
            box("Fitout glass",x,y,.08,.038,length,3.11,"glass",0)
            for z in (.021,3.19):box("Glazing bronze rail",x,y,z,.085,length,.068,"bronze",.004)
            count=max(1,math.ceil(length/1.24))
            for j in range(count+1):
                box("Glazing bronze jamb",x,y-length/2+j*length/count,.03,.078,.063,3.22,"bronze",.003)
            box("Visitor glazing cove",x-.18,y,3.005,.035,length,.022,"warm")
    elif name.startswith(structural):
        resize_height(obj, ceiling)
    elif name.startswith("Window mullion"):
        resize_height(obj, 2.98)
    elif name.startswith("Car front"):
        resize_height(obj, 2.22)
    elif name.startswith("Acoustic fabric panel"):
        resize_height(obj, 3.06)

# The reference shows deep concrete beams and exposed tracks on the core side.
plan_boxes("Walk ceiling", layout["frame"], ceiling, .12, "e7e3da")
for v in (165, 348, 532, 716, 900, 1084):
    panel("Walk beam", xy(77,v), xy(1169,v), 2.97, .32, .49, "c7c1b5")
# Restrict exposed services to production. The guest aisle has a continuous soffit.
cx,cy,cw,cd=bounds((346,76,445,682))
box("Walk ceiling gallery",cx,cy,2.87,cw,cd,.20,"white",.009)
for v in range(103,680,61):
    lx,ly=xy(396,v)
    rod("Aisle downlight trim",(lx,ly,2.862),(lx,ly,2.875),.065,"bronze",28)
    rod("Aisle downlight lens",(lx,ly,2.860),(lx,ly,2.865),.040,"warm",28)
for offset, material, diameter in ((0,"steel",.028),(9,"9c6752",.018),(19,"glass",.034)):
    for u in (858,):
        a,b=xy(u+offset,83),xy(u+offset,1253)
        rod("Walk services pipe",(*a,2.92),(*b,2.92),diameter,material)
for y in (117,298,477,656,850,1032,1200):
    for u in ((858,1050) if y<680 else (220,405,858,1050)):
        x,z=xy(u,y)
        box("Walk services housing",x,z,2.86,.17,1.08,.075,"frame")
        box("Walk services diffuser",x,z,2.84,.12,1.02,.025,"warm")

# Walnut and warm indirect light give the client-facing suite the reference
# character. The live rooms keep blackout linings and acoustic panels.
for k in ("owner","meeting","reception"):
    x,y,w,d=bounds(rooms[k]["rect"])
    box("Walnut lining substrate",x-w/2+.13,y,.035,.055,d*.62,2.975,"bronze",.002)
    for i in range(13):
        yy=y-d*.31+(i+.5)*d*.62/13
        box("Walnut feature wall",x-w/2+.18,yy,.04,.12,d*.62/13-.014,2.96,"wood",.003)
    box("Walnut wall wash strip",x-w/2+.28,y,2.956,.035,d*.62,.023,"warm")
    box("Walk ceiling visitor soffit",x,y,3.035,w,d,.18,"white")
    # Continuous full-height joinery on the solid return, with a recessed plinth.
    wall_y=y-d/2+.105
    for i in range(7):
        xx=x+(i-3)*w/7
        box("Matched walnut lining",xx,wall_y,.105,w/7-.009,.07,2.85,"wood",.003)
    box("Bronze skirting",x,wall_y,.024,w,.066,.078,"bronze",.003)
    box("Shadow gap at crown",x,wall_y,2.96,w,.078,.047,"bronze",.003)
    box("Concealed wall washer",x,wall_y+.044,2.973,w-.09,.018,.013,"warm",.003)
    for i in (-1,0,1):
        px=x+i*w*.30
        rod("Trimless downlight",(px,y,3.014),(px,y,3.034),.067,"bronze",28)
        rod("Recessed lamp",(px,y,3.012),(px,y,3.016),.041,"warm",28)
    if k in ("owner","reception"):
        sofa_x=x-(.66 if k=="owner" else .83)
        sofa_y=y-(1.20 if k=="owner" else .75)
        box("Bound lounge rug",sofa_x,sofa_y+.49,.015,2.64,1.87,.019,"rug",.008)
        # Triptych in individual frames with relief panels and linen mounts.
        for i in (-1,0,1):
            px=sofa_x+i*.53
            box("Art bronze frame",px,wall_y+.069,1.16,.51,.068,.88,"bronze",.006)
            box("Art linen mount",px,wall_y+.105,1.18,.475,.009,.84,"linen",.003)
            # A continuous engraved landscape crosses the three linen panels.
            # Each sheet has the same margins; the profile continues across the frames.
            verts=[]; strips=[]
            for band in range(17):
                for step in range(25):
                    t=step/24
                    u=(i+1+t)/3
                    z=1.36+band*.019+.095*math.sin(u*6.7+band*.086)+.055*math.sin(u*16-band*.033)
                    base=len(verts)
                    verts.extend([(px+(t-.5)*.389,wall_y+.114,z+offset) for offset in (-.0019,.0019)])
                    if step:strips.append((base-2,base-1,base+1,base))
            engraving=bpy.data.meshes.new("Contour print")
            engraving.from_pydata(verts,[],strips);engraving.update()
            print_obj=bpy.data.objects.new("Contour print",engraving)
            bpy.context.collection.objects.link(print_obj);engraving.materials.append(mat("69574b"))
        # Slim picture light washing the three separate panels.
        box("Gallery light",sofa_x,wall_y+.19,2.21,1.52,.055,.035,"bronze",.012)
        box("Gallery diffuser",sofa_x,wall_y+.19,2.205,1.44,.036,.009,"warm",.003)

def vase_with_branches(x,y,z):
    profile=[(.062,0),(.091,.019),(.105,.065),(.104,.135),(.088,.19),(.051,.225),(.041,.266),(.045,.278),(.036,.279),(.032,.246)]
    vertices=[];faces=[]
    for r,h in profile:
        for i in range(48):
            a=i*math.tau/48
            vertices.append((x+r*math.cos(a),y+r*math.sin(a),z+h))
    for j in range(len(profile)-1):
        for i in range(48):
            a=j*48+i;b=j*48+(i+1)%48
            faces.append((a,b,b+48,a+48))
    mesh=bpy.data.meshes.new("Thrown stoneware");mesh.from_pydata(vertices,[],faces);mesh.update()
    vessel=bpy.data.objects.new("Thrown stoneware",mesh);bpy.context.collection.objects.link(vessel)
    mesh.materials.append(mat("bcb1a1"))
    for face in mesh.polygons:face.use_smooth=True
    for i in range(11):
        a=i*2.399963
        height=.35+(i%4)*.071
        tip=(x+math.cos(a)*(.15+(i%3)*.07),y+math.sin(a)*(.15+(i%3)*.07),z+height)
        rod("Branch",(x,y,z+.18),tip,.004,"514b37",6)
        for j in range(2):
            along=.73+j*.22
            centre=(x+(tip[0]-x)*along,y+(tip[1]-y)*along,z+.20+(height-.20)*along)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,location=centre)
            leaf=bpy.context.object;leaf.name="Eucalyptus leaf"
            leaf.scale=(.026,.052,.003);leaf.data.materials.append(mat(("607160","718678")[j]))
            leaf.rotation_euler=(.4,.32,a+j*.8)

x,y,w,d=bounds(rooms["meeting"]["rect"])
box("Meeting rug",x,y,.014,4.58,3.30,.013,"rug",.015)
rod("Pendant cable",(x,y,2.57),(x,y,3.055),.015,"bronze")
box("Pendant satin housing",x,y,2.49,2.70,.102,.065,"bronze",.018)
box("Pendant diffuser",x,y,2.475,2.58,.045,.016,"warm",.005)
vase_with_branches(x-.68,y-.18,.80)
box("Meeting notebook",x+.62,y-.31,.802,.29,.21,.029,"69574b",.009)
box("Meeting linen pages",x+.62,y-.31,.805,.279,.205,.019,"f2ede4",.004)
box("Art timber frame",x+.72,y-d/2+.23,1.22,1.02,.046,.84,"bronze",.01)
box("Art paper mount",x+.72,y-d/2+.259,1.255,.94,.014,.764,"ded4c4",.003)
for j,(shade,offset,height) in enumerate([("94765e",-.22,.36),("7a8071",.04,.44),("baa184",.22,.29)]):
    box("Art print relief",x+.72+offset,y-d/2+.269,1.39+j*.06,.263,.010,height,shade,.004)
x,y,w,d=bounds(rooms["reception"]["rect"])
dx,dy=namespace["reception_coffee_table_offset"]
vase_with_branches(x+dx,y+dy,.406)

edge_segments = [(72,67,1172,67),(72,1267,1172,1267),(72,67,72,1267),(1172,67,1172,1267)]
for u,v,U,V in edge_segments:
    a,b=xy(u,v),xy(U,V)
    panel("Window mid rail",a,b,1.09,.055,.044,"steel")
    panel("Window head",a,b,2.97,.33,.16,"frame")
    panel("Window glass",a,b,.23,2.73,.015,"glass")

# Opaque blackout linings are concept fit-out, inside the existing window line.
for k in ("studio-a","studio-b"):
    x,y,w,d=bounds(rooms[k]["rect"])
    box("Studio blackout lining",x+w/2-.068,y,0,.11,d,3.09,"ink")
    if k=="studio-a":
        box("North blackout lining",x,y+d/2-.06,0,w,.115,3.09,"green")
    for dx in (-w*.28,w*.27):
        rod("Studio track",(x+dx,y-d*.29,3.10),(x+dx,y+d*.31,3.10),.030)
        fixture=box("Studio softbox",x+dx,y-d*.20,2.65,.84,.43,.11,"steel")
        fixture.rotation_euler.x=-.30
        diffuser=box("Softbox emitter",x+dx,y-d*.19,2.63,.76,.39,.026,"warm")
        diffuser.rotation_euler.x=-.30
    if k=="studio-b":
        rod("Overhead product camera arm",(x-.68,y+d*.14,2.32),(x+.09,y+d*.14,2.32),.033)
        rod("Overhead camera support",(x-.68,y+d*.14,.99),(x-.68,y+d*.14,2.33),.032)
        box("Overhead product camera",x+.09,y+d*.14,2.14,.17,.21,.16,"steel")

bpy.context.view_layer.update()
colliders = []
for obj in scene.objects:
    if not obj.name.startswith(structural + fixtures):
        continue
    if obj.name.startswith("Rack shelf") and obj.location.z>.22:
        continue
    vertices = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    x1,x2 = min(p.x for p in vertices),max(p.x for p in vertices)
    z1,z2 = min(-p.y for p in vertices),max(-p.y for p in vertices)
    colliders.append([x1,z1,x2,z2])
for u,v,U,V in edge_segments + [tuple(r) for r in layout["lifts"]+layout["stairs"]]:
    a,b=xy(u,v),xy(U,V)
    colliders.append([min(a[0],b[0])-.07,min(-a[1],-b[1])-.07,max(a[0],b[0])+.07,max(-a[1],-b[1])+.07])
(root/"assets/walk-colliders.json").write_text(json.dumps([[round(v,4) for v in r] for r in colliders],separators=(",",":"))+"\n")

# Join objects by material and visibility. This keeps a handful of draw calls
# and lets the browser hide the ceiling without rebuilding the scene.
groups = {}
for obj in list(scene.objects):
    if obj.name.startswith("Window glass"):
        layer="Glazing"
    elif obj.name.startswith("Fitout glass"):
        layer="FitoutGlass"
    elif obj.name.startswith(roof_prefixes):
        layer="Roof"
    else:
        layer="Interior"
    material=obj.data.materials[0].name
    groups.setdefault((layer,material),[]).append(obj)

requested_views=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if "arrival" in requested_views or "meeting" in requested_views:
    # A separate ray-traced camera uses the same room geometry as the preview.
    # Reflections on glass are authored only for this offline view.
    for (layer,_),items in groups.items():
        if layer=="Glazing":
            for obj in items:obj.hide_render=True
        if layer=="FitoutGlass":
            clear=bpy.data.materials.new("Clear glazing");clear.use_nodes=True
            nodes=clear.node_tree.nodes;links=clear.node_tree.links;nodes.clear()
            transparent=nodes.new("ShaderNodeBsdfTransparent")
            principled=nodes.new("ShaderNodeBsdfPrincipled")
            principled.inputs["Base Color"].default_value=(.63,.57,.50,1)
            principled.inputs["Roughness"].default_value=.17
            mix=nodes.new("ShaderNodeMixShader");mix.inputs[0].default_value=.105
            output=nodes.new("ShaderNodeOutputMaterial")
            links.new(transparent.outputs[0],mix.inputs[1]);links.new(principled.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs[0])
            for obj in items:obj.data.materials[0]=clear
    tree=scene.world.node_tree
    world_image=tree.nodes.new("ShaderNodeTexEnvironment")
    world_image.image=bpy.data.images.load(str(root/"assets/materials/rooftop.hdr"),check_existing=True)
    tree.links.new(world_image.outputs["Color"],tree.nodes.get("Background").inputs[0])
    tree.nodes.get("Background").inputs[1].default_value=.58
    for side in ("owner","meeting","reception"):
        x,y,w,d=bounds(rooms[side]["rect"])
        light("Diffuse window light",(x-w/2+.27,y,2.37),(x+.70,y,1.1),137,2.35,(.86,.94,1))
        light("Interior warm fill",(x,y,2.91),(x,y,.6),96,2.1,(1,.82,.68))
    for v in (305,465,560,675):
        x,y=xy(396,v)
        light("Warm corridor downlight",(x,y,2.80),(x,y,0),50,1.15,(1,.87,.72))
    # The cove grazes the veneer and artwork instead of flattening the room.
    for side in ("owner","meeting","reception"):
        x,y,w,d=bounds(rooms[side]["rect"])
        light("Joinery wall wash",(x,y-d/2+.58,2.79),(x,y-d/2+.12,1.39),78,2.0,(1,.72,.48))
    scene.cycles.samples=42
    scene.cycles.adaptive_threshold=.035
    scene.cycles.max_bounces=10
    scene.render.resolution_x=1680;scene.render.resolution_y=1098
    x,y=xy(246,521);u,v=xy(180,618)
    x_meet,y_meet,w,d=bounds(rooms["meeting"]["rect"])
    views=[
        ("arrival",(x,y,1.63),(u,v,1.44),23),
        ("meeting",(x_meet+w*.43,y_meet-d*.42,1.52),(x_meet-.51,y_meet+.44,1.17),23),
    ]
    for name,position,target,lens in views:
        if "arrival" not in requested_views and name not in requested_views:continue
        camera(scene,position,target,lens=lens)
        scene.render.filepath=str(root/f"assets/{name}.jpg")
        bpy.ops.render.render(write_still=True)
    for (layer,material),items in groups.items():
        if layer=="Glazing":
            for obj in items:obj.hide_render=False
        if layer=="FitoutGlass":
            for obj in items:obj.data.materials[0]=mat(material)
    for obj in list(scene.objects):
        if obj.type!="MESH":bpy.data.objects.remove(obj,do_unlink=True)

bpy.ops.object.select_all(action="SELECT")
bpy.context.view_layer.objects.active = next(iter(scene.objects))
bpy.ops.object.convert(target="MESH")
for (layer,material),items in groups.items():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in items:obj.select_set(True)
    merged=items[0]
    bpy.context.view_layer.objects.active=merged
    if len(items)>1:bpy.ops.object.join()
    merged.name=f"{layer}_{material}"

strip_for_glb()
bpy.ops.export_scene.gltf(filepath=str(root/"assets/office-walk.glb"),export_format="GLB",export_yup=True,export_lights=False,export_cameras=False)
