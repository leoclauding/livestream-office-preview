"""Render the office model and its two studio interiors with Blender Cycles."""
import bpy, json, math, pathlib, sys
from mathutils import Vector
from functools import lru_cache
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from surfaces import BY_KEY, apply_shader, map_uv

root = pathlib.Path(__file__).resolve().parents[1]
layout = json.loads((root / "design/layout.json").read_text())
assets = root / "assets"
scale = layout["metresPerUnit"]
rooms = {r["id"]: r for r in layout["rooms"]}
reception_coffee_table_offset = (-.83, .38)
colours = {
    "honed":"b3a899","rug":"b8a794","linen":"e0d8cb","accentStone":"978b7c","mirror":"dddddd","displayGlass":"171b1b",
    "frame":"37332e","cream":"b5a995","white":"f1e9dc","wood":"795437",
    "oak":"a27a55","green":"595f49","rust":"a37858","blue":"515e60",
    "core":"8a8174","steel":"2b2927","carpet":"aca193","sand":"caba9f",
    "floor":"827569","ink":"312c27","glass":"b5c2c4","warm":"ffd6a1",
    "sage":"9c9d87","cases":"947653","screen":"2e4548","bronze":"524039"
}

def rgb(h):
    c = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return [x/12.92 if x < .04045 else ((x+.055)/1.055)**2.4 for x in c]

@lru_cache
def mat(key):
    m=bpy.data.materials.new(key);m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    color=rgb(colours.get(key,key))
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=.48 if key in ("steel","glass","screen") else .72
    if key=="steel": p.inputs["Metallic"].default_value=.32
    if key=="displayGlass":
        p.inputs["Roughness"].default_value=.16
        p.inputs["Coat Weight"].default_value=.45
    if key=="mirror":
        p.inputs["Base Color"].default_value=(.88,.88,.86,1)
        p.inputs["Metallic"].default_value=1
        p.inputs["Roughness"].default_value=.07
    if key=="bronze":
        p.inputs["Metallic"].default_value=.55
        p.inputs["Roughness"].default_value=.31
    if key in ("warm","screen"):
        p.inputs["Emission Color"].default_value=(*color,1)
        p.inputs["Emission Strength"].default_value=3 if key=="warm" else .45
    if key in BY_KEY:
        apply_shader(m,key,rgb)
    elif key in ("carpet","sand","cream","blue","green"):
        nodes=m.node_tree.nodes
        noise=nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=115
        bump=nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.17;bump.inputs["Distance"].default_value=.018
        m.node_tree.links.new(noise.outputs["Fac"],bump.inputs["Height"])
        m.node_tree.links.new(bump.outputs["Normal"],p.inputs["Normal"])
    return m

def box(name,x,y,z,w,d,h,colour="cream",bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z+h/2))
    o=bpy.context.object;o.name=name;o.dimensions=(w,d,h)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat(colour))
    if colour in BY_KEY: map_uv(o,colour)
    if bevel:
        b=o.modifiers.new("Soft edges","BEVEL");b.width=min(bevel,h/3,d/3,w/3);b.segments=2
        n=o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return o

def rod(name,a,b,r,colour="steel",verts=12):
    a,b=Vector(a),Vector(b)
    delta=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name
    o.rotation_euler=delta.to_track_quat("Z","Y").to_euler();o.data.materials.append(mat(colour))
    if colour in BY_KEY: map_uv(o,colour)
    return o

def panel(name,a,b,z,h,t,colour="cream"):
    x1,y1=a;x2,y2=b
    o=box(name,(x1+x2)/2,(y1+y2)/2,z,math.hypot(x2-x1,y2-y1),t,h,colour)
    o.rotation_euler.z=math.atan2(y2-y1,x2-x1)
    return o

def furnish_desk(x,y,w=1.55,depth=.72,direction=1,vanity=False):
    box("Oak desktop",x,y,.73,w,depth,.06,"oak")
    for dx in (-1,1):
        box("Steel desk leg",x+dx*(w/2-.08),y,.025,.063,depth*.78,.70,"steel")
    if vanity:
        mirror_y=y+.30
        box("Vanity mirror surround",x,mirror_y, .82,1.30,.067,.85,"bronze",.027)
        box("Silvered mirror",x,mirror_y-.039,.84,1.25,.012,.81,"mirror",.018)
        for dx in (-.57,.57):
            box("Vanity light blade",x+dx,mirror_y-.047,.90,.022,.010,.68,"warm",.005)
        rod("Vanity jar",(x-.6,y,.79),(x-.6,y,.94),.067,"floor",32)
    else:
        box("Monitor stand",x,y+direction*.16,.79,.07,.085,.22,"steel")
        box("Monitor housing",x,y+direction*.20,1.01,.54,.033,.32,"steel")
        box("Monitor",x,y+direction*.18,1.019,.516,.009,.297,"screen")
        box("Keyboard",x,y-direction*.10,.79,.36,.14,.022,"steel")
    chair(x,y-direction*.78,direction, "blue")

def chair(x,y,direction=1,colour="green"):
    box("Upholstered seat",x,y,.43,.51,.48,.11,colour,.05)
    box("Chair back",x,y-direction*.21,.53,.48,.09,.39,colour,.045)
    for side in (-1,1):
        rod("Arm rest post",(x+side*.228,y-.02,.46),(x+side*.228,y-.02,.64),.013,"bronze")
        box("Upholstered arm cap",x+side*.228,y,.64,.048,.29,.038,colour,.012)
    rod("Chair foot",(x,y,.06),(x,y,.43),.046)
    for alpha in range(0,360,72):
        a=math.radians(alpha)
        rod("Chair base",(x,y,.11),(x+math.cos(a)*.25,y+math.sin(a)*.25,.06),.018)

def conference_chair(x,y,direction):
    box("Upholstered seat",x,y,.416,.50,.48,.102,"rust",.046)
    # A curved tub back wraps down toward the arms on a four-leg walnut frame.
    verts=[];faces=[]
    for j in range(33):
        t=(j/32-.5)*math.pi*.94
        px=.239*math.sin(t)
        py=-direction*.22*math.cos(t)
        top=.654+.245*math.cos(t)**.72
        for inset,z in ((1,.475),(1,top),(.86,top-.003),(.86,.49)):
            verts.append((px*inset,py*inset,z))
        if j:
            a=j*4
            for k in range(4):
                n=(k+1)%4
                faces.append((a+k-4,a+n-4,a+n,a+k))
    faces.extend([(3,2,1,0),(128,129,130,131)])
    if direction>0:faces=[tuple(reversed(face)) for face in faces]
    mesh=bpy.data.meshes.new("Moulded chair back");mesh.from_pydata(verts,[],faces);mesh.update()
    back=bpy.data.objects.new("Chair back",mesh);bpy.context.collection.objects.link(back)
    back.location=(x,y,0);mesh.materials.append(mat("rust"));map_uv(back,"rust")
    for face in mesh.polygons:face.use_smooth=True
    bevel=back.modifiers.new("Upholstered edge","BEVEL");bevel.width=.009;bevel.segments=3
    for side in (-1,1):
        for end in (-1,1):
            rod("Tapered chair rail",(x+side*.204,y+end*.192,.022),(x+side*.166,y+end*.15,.43),.020,"wood",16)

def shelf(x,y,w,depth=.48,levels=4,height=1.9):
    for dx in (-1,1):
        for dy in (-1,1):box("Rack upright",x+dx*(w/2-.03),y+dy*(depth/2-.02),0,.045,.045,height,"steel")
    for k in range(levels):
        z=.13+k*(height-.25)/levels
        box("Rack shelf",x,y,z,w,depth,.045,"wood")
        for j in range(3):
            bx=x+(j-1)*w/3
            box("Inventory box",bx,y,z+.045,w*.22,depth*.75,.19+.035*(j%2),["cases","cream","sage"][j])
            box("Stock label",bx,y-depth*.38,z+.10,w*.10,.009,.05,"white",0)

def sofa(x,y,w=2.5,colour="green",*,facing):
    """A positive facing opens toward +Y in the Blender floor plan."""
    def pad(name, px, py, z, width, depth, height, finish, angle=0):
        # Shape a rounded, gently crowned cushion with a continuous shell.
        def signed(v, exponent):
            return math.copysign(abs(v)**exponent, v)
        verts=[]; faces=[]
        rings=16; sides=32
        for j in range(rings+1):
            lat=math.pi*(j/rings-.5)
            for i in range(sides):
                lon=math.tau*i/sides
                a=signed(math.cos(lat),.38)
                verts.append((a*signed(math.cos(lon),.32)*width/2,
                              a*signed(math.sin(lon),.32)*depth/2,
                              signed(math.sin(lat),.38)*height/2))
        for j in range(rings):
            for i in range(sides):
                k=j*sides+i; n=j*sides+(i+1)%sides
                faces.append((k,n,n+sides,k+sides))
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
        obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
        obj.location=(px,py,z);obj.rotation_euler.x=angle
        mesh.materials.append(mat(finish))
        for face in mesh.polygons:face.use_smooth=True
        map_uv(obj,finish)

    box("Recessed sofa plinth",x,y,.037,w-.16,.65,.115,"wood",.025)
    box("Sofa base",x,y,.14,w,.83,.23,colour,.065)
    box("Sofa back",x,y-facing*.35,.33,w,.15,.45,colour,.055)
    for side in (-1,1):
        pad("Bolstered arm",x+side*(w/2-.092),y,.48,.184,.82,.37,colour)
    channels=6 if w>1.6 else 4
    pitch=(w-.35)/channels
    for i in range(channels):
        px=x+(i-(channels-1)/2)*pitch
        pad("Channel upholstery",px,y+facing*.046,.399,pitch+.004,.71,.185,colour)
    for side in (-1,1):
        pad("Loose back pillow",x+side*(w-.40)*.25,y-facing*.244,.667,
            (w-.42)/2,.17,.45,colour,-facing*.14)

def round_table(x,y,r=.46,h=.71,colour="oak"):
    if colour=="honed":
        bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=r*.53,radius2=r*.34,depth=h-.022,location=(x,y,(h+.022)/2))
        foot=bpy.context.object;foot.name="Tapered stone pedestal"
        foot.data.materials.append(mat("accentStone"));map_uv(foot,"accentStone")
        rod("Bronze table lip",(x,y,h-.009),(x,y,h+.003),r*.97,"bronze",64)
    else:
        rod("Table pedestal",(x,y,.025),(x,y,h),.065)
    rod("Circular table",(x,y,h),(x,y,h+.055),r,colour,48)

def light(name,position,target,power,size,colour=(1,.95,.86),shape="DISK"):
    data=bpy.data.lights.new(name,"AREA");data.energy=power;data.shape=shape;data.size=size;data.color=colour
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=position
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()

def setup(kind):
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.samples=32 if kind!="axon" else 24
    scene.cycles.use_denoising=True
    scene.cycles.adaptive_threshold=.055
    scene.cycles.max_bounces=6
    scene.render.image_settings.file_format="JPEG";scene.render.image_settings.quality=89
    scene.render.resolution_x=1560 if kind=="axon" else 1280
    scene.render.resolution_y=1230 if kind=="axon" else 850
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get("Background").inputs[0].default_value=(.68,.77,.92,1)
    scene.world.node_tree.nodes.get("Background").inputs[1].default_value=.48 if kind=="axon" else .27
    scene.view_settings.view_transform="AgX"
    return scene

def camera(scene,pos,target,ortho=None,lens=28):
    bpy.ops.object.camera_add(location=pos)
    cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens=lens;cam.data.clip_end=150
    if ortho:
        cam.data.type="ORTHO";cam.data.ortho_scale=ortho
    scene.camera=cam

def tripod(x,y,z=1.42):
    for a in (0,120,240):
        ang=math.radians(a)
        rod("Tripod leg",(x+math.cos(ang)*.46,y+math.sin(ang)*.46,.03),(x,y,z-.16),.021)
    rod("Head column",(x,y,z-.26),(x,y,z),.038)
    box("Cinema camera",x,y,z,.20,.30,.16,"ink",.027)
    rod("Camera lens",(x,y+.11,z+.083),(x,y+.29,z+.083),.075,"steel")
    box("Camera battery",x,y-.162,z+.026,.153,.063,.12,"steel",.011)
    box("Monitor bezel",x-.12,y-.11,z+.183,.213,.028,.128,"steel",.008)
    box("On-board monitor",x-.12,y-.127,z+.192,.193,.006,.108,"screen",.004)
    rod("Pan handle",(x+.09,y-.04,z-.035),(x+.19,y-.38,z-.19),.014,"steel")
    for j in range(3):
        rod("Lens control ring",(x,y+.16+j*.045,z+.083),(x,y+.179+j*.045,z+.083),.081,"ink",32)
    rod("Top handle",(x,y-.09,z+.226),(x,y+.12,z+.226),.016,"steel",16)
    rod("Grip mount",(x,y+.10,z+.15),(x,y+.10,z+.226),.015,"steel",16)

def product_table(x,y,main=True):
    w=2.45 if main else 1.85
    box("Presentation table",x,y,.18,w,.85,.72,"oak" if main else "cream",.10)
    box("Base plinth",x,y,.025,w-.25,.68,.16,"steel",.04)
    box("Countertop",x,y,.9,w+.05,.90,.062,"white",.025)
    for i,(c,h) in enumerate([("rust",.24),("sage",.32),("sand",.17),("white",.26)]):
        bx=x+(i-1.5)*.34
        if i%2==0:
            rod("Display product",(bx,y+.13,.962),(bx,y+.13,.962+h),.073,c,40)
            rod("Vessel lid",(bx,y+.13,.962+h),(bx,y+.13,.986+h),.076,"bronze",40)
        else:
            box("Display product",bx,y+.13,.962,.18,.16,h,c,.009)
        box("Product label",bx,y+.044,1.02,.10,.012,.085,"cream")

def studio_props(w,d,main,full=False):
    backdrop="green" if main else "blue"
    for i in range(16):
        x=-w/2+(i+.5)*w/16
        box("Acoustic fabric panel",x,d/2-.18,0,w/16-.018,.14,3.04 if full else 1.17,backdrop,.013)
    # A layered display recess gives small products a readable silhouette on camera.
    back_y=d/2-.31
    box("Display recess",0,back_y,.38,w*.65,.065,2.22,"wood",.016)
    box("Inset stone lining",0,back_y-.045,.50,w*.60,.033,1.93,"honed",.009)
    for z in (.85,1.56):
        box("Display ledge",0,back_y-.16,z,w*.59,.32,.045,"wood",.009)
        box("Shelf light",0,back_y-.28,z-.011,w*.56,.021,.012,"warm",.003)
        for j in range(3):
            px=(j-1)*w*.19
            rod("Ceramic product vessel",(px,back_y-.15,z+.045),(px,back_y-.15,z+.22+.055*j),.08,("sage","white","cases")[j],32)
    product_table(0,d*.14,main)
    tripod(-w*.22,-d*.17,1.25)
    if main:tripod(w*.24,-d*.20,1.36)
    if full:
        for x in (-w*.28,w*.27):
            z=2.78
            rod("Light track",(x,-d*.29,3.10),(x,d*.31,3.10),.036)
            o=box("Softbox",x,-d*.22,z,.87,.43,.11,"steel");o.rotation_euler.x=-.29
            o=box("Softbox diffuser",x,-d*.21,z-.014,.79,.39,.027,"warm");o.rotation_euler.x=-.29
            light("Studio softlight",(x,-d*.21,z-.055),(0,d*.16,.9),140,.94,(1,.91,.82))
        for x in (-w*.36,w*.36):
            box("Vertical stage light",x,d/2-.32,.24,.037,.052,2.46,"warm")
            light("Wall wash",(x,d/2-.55,1.5),(x,d/2-.1,1.15),38,1.05,(.74,.88,1))
        if not main:
            rod("Overhead product camera arm",(-.68,d*.14,2.32),(.09,d*.14,2.32),.033)
            rod("Camera support",(-.68,d*.14,.99),(-.68,d*.14,2.33),.032)
            box("Overhead product camera",.09,d*.14,2.14,.17,.21,.16,"steel")
    shelf(-w*.37,d*.12,.70,.36,4,1.28)
    box("Rolling equipment case",w*.38,-d*.02,.06,.54,.48,.61,"steel",.035)

def interior(kind):
    main=kind=="studio-a";r=rooms[kind]["rect"];w=(r[2]-r[0])*scale;d=(r[3]-r[1])*scale
    scene=setup(kind)
    box("Matte studio floor",0,0,-.16,w,d,.16,"carpet" if main else "sand")
    box("Left acoustic wall",-w/2,0,0,.18,d,3.16,"ink")
    box("Right acoustic wall",w/2,0,0,.18,d,3.16,"ink")
    box("Stage backdrop wall",0,d/2,0,w,.18,3.16,"green" if main else "blue")
    box("Dark studio ceiling",0,0,3.16,w,d,.14,"ink")
    for side in (-1,1):
        for i in range(10):
            box("Acoustic wall rib",side*(w/2-.11),-d/2+.28+i*(d-.56)/9,.22,.043,.25,2.75,"frame")
    studio_props(w,d,main,True)
    light("Soft fill",(0,-d*.47,2.85),(0,d*.17,1.0),155,3.4,(.82,.9,1))
    light("Backdrop key",(0,d*.36,2.95),(0,d*.43,1.25),85,2.3)
    camera(scene,(w*.31,-d*.48,1.77),(0,d*.14,1.29),lens=22 if main else 20)
    return scene

def xy(u,v): return ((u-622)*scale,(667-v)*scale)

def bounds(rect):
    x1,y1,x2,y2=rect;x,y=xy((x1+x2)/2,(y1+y2)/2)
    return x,y,(x2-x1)*scale,(y2-y1)*scale

def plan_boxes(name,rect,z,h,colour):
    return box(name,*bounds(rect)[:2],z,*bounds(rect)[2:],h,colour)

def wall_segments(r):
    x1,y1,x2,y2=r["rect"]
    edges={"N":(x1,x2,y1),"S":(x1,x2,y2),"E":(y1,y2,x2),"W":(y1,y2,x1)}
    for side,(a,b,fixed) in edges.items():
        if side=="N" and y1==76 or side=="E" and x2==1163 or side=="W" and x1==82 or side=="S" and y2==1257:continue
        door=r.get("door")
        cut=min(max(door[1],a),b) if door and side==door[3] and side in ("E","W") else (door[0] if door and side==door[3] else None)
        parts=[(a,b)] if cut is None else [(a,max(a,cut-door[2]/2)),(min(b,cut+door[2]/2),b)]
        for lo,hi in parts:
            if hi-lo<3:continue
            yield (xy(lo,fixed),xy(hi,fixed)) if side in ("N","S") else (xy(fixed,lo),xy(fixed,hi))

def axon():
    scene=setup("axon")
    plan_boxes("Concrete perimeter slab",layout["frame"],-.29,.27,"frame")
    plan_boxes("Open circulation floor",layout["frame"],-.035,.037,"floor")
    zone_floor={"guest":"floor","work":"carpet","studio":"blue","logistics":"c9b899"}
    open_rooms={"desks","content"}
    walls={}
    for r in rooms.values():
        plan_boxes(r["name"],r["rect"],.003,.010,zone_floor[r["family"]])
        if r["id"] in open_rooms:continue
        for a,b in wall_segments(r):
            key=tuple(sorted((a,b))); walls[key]="blue" if r["family"]=="studio" else "cream"
    for (a,b),colour in walls.items():panel("Proposed partition",a,b,.008,1.45,.12,colour)
    for rect in layout["coreWalls"]:plan_boxes("Existing structural core",rect,.008,1.82,"core")
    for x,y in layout["columns"]:
        a,b=xy(x,y);box("Existing column",a,b,0,.61,.61,1.95,"frame")
    for rect in layout["lifts"]:
        x,y,w,d=bounds(rect)
        box("Elevator shaft",x,y,.012,w,d,.095,"steel")
        panel("Car front",(x-w/2,y-d/2),(x+w/2,y-d/2),.10,1.05,.055,"steel")
        box("Elevator car",x,y,.105,w*.79,d*.77,.065,"glass")
    for rect in layout["stairs"]:
        x,y,w,d=bounds(rect)
        for i in range(12):box("Stair flight",x-w/2+(i+.5)*w/12,y,.01,w/12,d*.72,.08+i*.075,"cream",.008)
        for dy in (-1,1):panel("Stair handrail",(x-w/2,y+dy*d/2),(x+w/2,y+dy*d/2),1.02,.055,.045,"steel")
    for a,b,c,d in layout["existingThin"]:panel("Existing core partition",xy(a,b),xy(c,d),.01,1.28,.075,"core")
    for u,v,U,V in [(72,67,1172,67),(72,1267,1172,1267),(72,67,72,1267),(1172,67,1172,1267)]:
        a,b=xy(u,v),xy(U,V);panel("Perimeter glazing sill",a,b,0,.20,.11,"frame")
        panel("Perimeter glazing head",a,b,1.28,.046,.063,"steel")
        for i in range(1,16):
            x=a[0]+(b[0]-a[0])*i/16;y=a[1]+(b[1]-a[1])*i/16
            box("Window mullion",x,y,.20,.038,.038,1.09,"steel",.004)
    for k in ("desks","content","control"):
        x,y,w,d=bounds(rooms[k]["rect"])
        n=3 if k=="desks" else (4 if k=="content" else 2)
        row_offsets={"desks":(-2.45,-1.48,1.48,2.45),"content":(-.93,.93),"control":(0,)}
        if k=="desks":x+=.29
        for j,dy in enumerate(row_offsets[k]):
            for i in range(n):furnish_desk(x+(i-(n-1)/2)*1.73,y+dy,1.53,direction=1 if j%2==0 else -1)
    x,y,w,d=bounds(rooms["owner"]["rect"])
    furnish_desk(x+.65,y+.8,1.90,.83,-1)
    sofa(x-.66,y-1.20,2.05,"rust",facing=1)
    round_table(x-.66,y-.03,.38,.37,"honed")
    x,y,w,d=bounds(rooms["meeting"]["rect"])
    box("Boardroom oak tabletop",x,y,.73,3.22,1.22,.07,"oak",.09)
    for dx in (-1.2,1.2):box("Boardroom base",x+dx,y,.03,.14,.76,.70,"steel")
    for j in range(5):
        for dy in (-1,1):conference_chair(x+(j-2)*.58,y+dy*1.03,-dy)
    box("Presentation display",x,y+d/2-.18,1.08,1.65,.049,.94,"steel",.018)
    box("Display glass",x,y+d/2-.209,1.10,1.615,.011,.90,"displayGlass",.006)
    x,y,w,d=bounds(rooms["reception"]["rect"])
    box("Reception desk",x+1.20,y+.58,.09,1.52,.62,.77,"wood",.035)
    box("Counter foot",x+1.20,y+.58,.018,1.38,.52,.072,"bronze",.014)
    box("Honed counter slab",x+1.20,y+.58,.86,1.58,.68,.045,"honed",.011)
    for j in range(28):
        box("Reeded counter face",x+.48+j*.053,y+.258,.12,.026,.025,.71,"oak",.009)
    sofa(x-.83,y-.75,2.24,"rust",facing=1)
    dx,dy=reception_coffee_table_offset
    round_table(x+dx,y+dy,.34,.35,"honed")
    x,y,w,d=bounds(rooms["pantry"]["rect"])
    box("Pantry counter",x,y-d/2+.40,0,4.72,.69,.91,"oak");box("Stone countertop",x,y-d/2+.4,.91,4.77,.72,.05,"white")
    counter_y=y-d/2+.40
    for i in range(6):
        px=x+(i-2.5)*.77
        box("Pantry inset door",px,counter_y+.355,.10,.756,.028,.76,"wood",.007)
        box("Finger pull",px,counter_y+.373,.798,.51,.024,.012,"bronze",.003)
    box("Stone splashback",x,y-d/2+.094,.96,4.69,.046,.59,"honed",.006)
    box("Pantry oak ledge",x,y-d/2+.19,1.51,4.66,.29,.046,"wood",.008)
    box("Shelf underside light",x,y-d/2+.26,1.497,4.40,.023,.013,"warm",.003)
    box("Coffee machine",x-1.52,counter_y, .965,.37,.39,.41,"steel",.033)
    box("Coffee machine face",x-1.52,counter_y+.205,1.21,.34,.040,.13,"bronze",.012)
    for i in range(4):
        px=x-.6+i*.32
        rod("Stoneware cup",(px,y-d/2+.205,1.556),(px,y-d/2+.205,1.66),.061,"white",32)
        rod("Cup interior",(px,y-d/2+.205,1.66),(px,y-d/2+.205,1.662),.052,"cases",32)
    box("Sink",x+.91,y-d/2+.40,.956,.59,.39,.026,"steel",.05)
    rod("Tap riser",(x+.91,y-d/2+.64,.96),(x+.91,y-d/2+.64,1.14),.017)
    rod("Tap spout",(x+.91,y-d/2+.64,1.14),(x+.91,y-d/2+.45,1.14),.017)
    box("Refrigerator",x+w/2-.44,y-d/2+.49,0,.59,.64,1.55,"steel")
    for dx in (-1.40,1.18):
        round_table(x+dx,y+.42,.58)
        chair(x+dx,y+1.24,-1);chair(x+dx,y-.49,1)
    for k in ("stock","dispatch","prep","green"):
        x,y,w,d=bounds(rooms[k]["rect"])
        left_shift=.38 if k=="prep" else 0
        for dx in (-w*.32+left_shift,w*.32): shelf(x+dx,y+d*.32,w*.28,.47,4)
        if k=="dispatch":
            for dy in (-1.7,.4):
                box("Packing bench top",x,y+dy,.85,2.42,.76,.07,"oak")
                for ax in (-1,1):
                    for ay in (-1,1):box("Packing bench leg",x+ax*1.10,y+dy+ay*.28,.015,.05,.05,.835,"steel")
                box("Packing mat",x+.52,y+dy,.922,.79,.47,.015,"sage")
                box("Carton ready to pack",x-.59,y+dy,.92,.43,.35,.24,"cases")
        if k=="green":
            furnish_desk(x+1.34,y+.23,1.63,direction=1,vanity=True)
            sofa(x-1.40,y-.83,1.50,"rust",facing=1)
        if k=="prep": box("Product inspection island",x,y-.27,.05,2.64,.83,.85,"oak",.06)
        if k=="stock":
            for dx in (-w*.31,0,w*.31):shelf(x+dx,y-d*.32,w*.26,.46,4)
    for k in ("studio-a","studio-b"):
        x,y,w,d=bounds(rooms[k]["rect"])
        before=set(bpy.context.scene.objects)
        studio_props(w,d,k=="studio-a")
        for o in set(bpy.context.scene.objects)-before:o.location.x+=x;o.location.y+=y
    box("Presentation backdrop",0,0,-.48,120,120,.09,"dce0dc",0)
    light("Large daylight",(-13,-8,22),(0,0,0),3500,13,(1,.90,.79))
    light("Soft blue bounce",(13,7,16),(0,0,0),2450,11,(.78,.88,1))
    camera(scene,(27,-34,39),(-.30,0,.05),ortho=44.5)
    return scene

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
for kind in args or ["axon","studio-a","studio-b"]:
    scene=axon() if kind=="axon" else interior(kind)
    scene.render.filepath=str(assets/f"{kind}.jpg")
    bpy.ops.render.render(write_still=True)
