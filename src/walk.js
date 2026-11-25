import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
import {loadSurfaceSet,makeCorridorReflection,setSurface} from "./walk-surfaces.js";
import {WalkControls, isFree} from "./walk-controls.js";
import {collidersFromBounds, lobby, planToWorld, radius, reachableCells, roomView, worldToPlan} from "./walk-geometry.js";

const $ = id => document.getElementById(id);
const mobile = window.matchMedia("(pointer: coarse)").matches;
const view = $("view");
const assetRoot = new URL(".",import.meta.url);
const svgns = "http://www.w3.org/2000/svg";
const roomColours = {guest:"#e8caab",work:"#c9dfce",studio:"#b9cedf",logistics:"#e7d4a5"};

function svg(tag, attrs) {
  const el = document.createElementNS(svgns,tag);
  for (const [key,value] of Object.entries(attrs)) el.setAttribute(key,value);
  return el;
}

function makeMap(layout, onPick) {
  const [x,y,x2,y2] = layout.frame;
  const map = svg("svg",{viewBox:`${x-20} ${y-20} ${x2-x+40} ${y2-y+40}`,"aria-hidden":true});
  const rectangle = ([a,b,c,d],attrs) => svg("rect",{x:a,y:b,width:c-a,height:d-b,...attrs});
  map.append(rectangle(layout.frame,{fill:"#e4e8df",stroke:"#18382b","stroke-width":9}));
  for (const room of layout.rooms) map.append(rectangle(room.rect,{fill:roomColours[room.family],stroke:"#66766e","stroke-width":3}));
  for (const rect of layout.coreWalls) map.append(rectangle(rect,{fill:"#546364"}));
  for (const rect of [...layout.lifts,...layout.stairs]) map.append(rectangle(rect,{fill:"#879992"}));
  for (const [a,b] of layout.columns) map.append(rectangle([a-12,b-12,a+12,b+12],{fill:"#43534f"}));
  const pointer=svg("path",{d:"M 0 -43 L 23 24 L 0 13 L -23 24 Z",fill:"#a44128",stroke:"#fff","stroke-width":5});
  map.append(pointer);
  map.addEventListener("click",event=>{
    const matrix=map.getScreenCTM();
    if (!matrix) return;
    const point=new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse());
    onPick([point.x,point.y]);
  });
  $("minimap").replaceChildren(map);
  return (px,py,yaw) => pointer.setAttribute("transform",`translate(${px.toFixed(2)},${py.toFixed(2)}) rotate(${-yaw*180/Math.PI})`);
}

function addLighting(scene) {
  scene.add(new THREE.HemisphereLight("#d9e8ff","#a28971",.97));
  const sun=new THREE.DirectionalLight("#fff2dd",1.58);
  sun.position.set(-22,7,11);
  sun.castShadow=true;
  sun.shadow.mapSize.set(mobile?1024:2048,mobile?1024:2048);
  Object.assign(sun.shadow.camera,{left:-21,right:21,top:20,bottom:-20,near:.6,far:75});
  sun.shadow.camera.updateProjectionMatrix();
  sun.shadow.bias=-.00035;
  sun.shadow.normalBias=.023;
  sun.shadow.radius=mobile?2:3;
  scene.add(sun,sun.target);
  for(const [x,z,colour,power] of [[-8,-9,"#fff1dc",19],[-8,5,"#fff1dc",19],[8,6,"#fff5e7",21],[9.8,-11.6,"#fff1e1",29],[9.8,-6.15,"#def0ff",26],[0,10,"#fff1e1",18]]) {
    const light=new THREE.PointLight(colour,power,9,2);
    light.position.set(x,2.72,z);
    scene.add(light);
  }
  for(const z of [-8.7,-5.3,-2.4]){
    const lamp=new THREE.PointLight("#ffd4a4",10,5.5,2);lamp.position.set(-5.95,2.79,z);scene.add(lamp);
  }
}

async function checkedJSON(url) {
  const response=await fetch(url);
  if (!response.ok) throw new Error(`资源载入失败 (${response.status})`);
  return response.json();
}

async function start() {
  if (!document.createElement("canvas").getContext("webgl2")) {
    throw new Error("当前浏览器无法使用 WebGL 2。请尝试打开浏览器的图形加速功能。");
  }
  const renderer=new THREE.WebGLRenderer({canvas:view,antialias:!mobile,powerPreference:"default"});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,mobile?1.2:1.6));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.13;
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFShadowMap;
  renderer.shadowMap.autoUpdate=false;
  let loaded;
  const surfaces=checkedJSON(new URL("../design/material-library.json",assetRoot)).then(spec=>loadSurfaceSet(spec,assetRoot,renderer,mobile));
  try {
    loaded=await Promise.all([
      checkedJSON(new URL("../design/layout.json",assetRoot)),
      checkedJSON(new URL("walk-colliders.json?v=owner-lounge",assetRoot)),
      new GLTFLoader().loadAsync(new URL("office-walk.glb?v=owner-lounge",assetRoot).href),
      surfaces
    ]);
  } catch(error) {
    renderer.dispose();
    throw error;
  }
  const [layout,bounds,gltf,{sky,byKey}]=loaded;
  const scale=layout.metresPerUnit;
  const colliders=collidersFromBounds(bounds),walkable=reachableCells(layout,colliders);
  const scenes=new Map(layout.rooms.map(room=>[room.id,roomView(room,walkable,scale)]));
  const select=$("destination");
  for (const room of layout.rooms) if (scenes.get(room.id)) select.add(new Option(room.name,room.id));
  const scene=new THREE.Scene();
  scene.background=new THREE.Color("#c2d4e4");
  scene.fog=new THREE.FogExp2("#c2d4e4",.014);
  scene.environment=sky;
  scene.environmentIntensity=.52;
  scene.environmentRotation.y=.94+Math.PI;
  scene.backgroundRotation.y=.94+Math.PI;
  scene.backgroundIntensity=.82;
  scene.backgroundBlurriness=.018;
  const reflection=renderer.extensions.has("EXT_color_buffer_float")?makeCorridorReflection(mobile):null;
  if(reflection)scene.add(reflection);
  addLighting(scene);
  scene.add(gltf.scene);
  const roof=[],glass=[];
  const setMaterials=new Set();
  document.body.dataset.finish="scanned";
  gltf.scene.traverse(mesh=>{
    if (!mesh.isMesh) return;
    mesh.receiveShadow=true;
    mesh.castShadow=true;
    if(mesh.name.startsWith("Roof_")) {
      roof.push(mesh);
      mesh.castShadow=false;
    }
    const maps=byKey.get(mesh.material.name);
    if(maps&&!setMaterials.has(mesh.material)){
      setSurface(mesh.material,maps);
      setMaterials.add(mesh.material);
    }
    if(mesh.name.startsWith("Glazing_")||mesh.name.startsWith("FitoutGlass_")){
      const inside=mesh.name.startsWith("FitoutGlass_");
      glass.push(mesh);
      mesh.material=mesh.material.clone();
      mesh.material.color.set(inside?"#c6ab8f":"#8faaba");
      mesh.material.transparent=true;
      mesh.material.opacity=inside?.155:.065;
      mesh.material.roughness=.085;mesh.material.envMapIntensity=.80;
      mesh.material.depthWrite=false;
      mesh.material.side=THREE.DoubleSide;
      mesh.castShadow=false;
    }
  });
  const walkCamera=new THREE.PerspectiveCamera(66,1,.055,180);
  const overviewCamera=new THREE.PerspectiveCamera(41,1,.2,180);
  const orbit=new OrbitControls(overviewCamera,view);
  orbit.minDistance=16;orbit.maxDistance=93;orbit.maxPolarAngle=Math.PI*.45;
  orbit.enabled=false;orbit.target.set(0,0,0);
  const walker=new WalkControls(walkCamera,view,{joystick:$("joystick"),radius});
  walker.setModel({colliders,heights:{eye:1.65}});
  const startPos=planToWorld(lobby,scale);
  const arrival=planToWorld([397,626],scale);
  let overview=false,dirty=true,lastTime=0,currentRoom="";
  const markMap=makeMap(layout,point=>{
    const [x,z]=planToWorld(point,scale);
    if (!isFree(x,z,radius,colliders)) return;
    // Map jumps stay on the same connected, navigable part of the plan.
    if (!walkable.some(([wx,wz])=>Math.hypot(wx-x,wz-z)<.22)) return;
    walker.teleport([x,z]);setView(false);
  });
  function syncLocation() {
    const [x,y]=worldToPlan([walker.x,walker.z],scale);
    const room=layout.rooms.find(({rect:[a,b,c,d]})=>x>=a&&x<=c&&y>=b&&y<=d);
    const nearReception=x>346&&x<445&&y>=76&&y<=680;
    const nearLift=x>=445&&x<=813&&y>=503&&y<=601;
    const next=room?.name??(nearReception?"接待走廊":nearLift?"电梯厅":"公共走道");
    if (next!==currentRoom) {
      currentRoom=next;
      $("location").textContent=next;
    }
    markMap(x,y,walker.yaw);
  }
  function resize() {
    const w=view.clientWidth,h=view.clientHeight;
    if(!w||!h)return;
    renderer.setSize(w,h,false);
    for(const camera of [walkCamera,overviewCamera]) {
      camera.aspect=w/h;camera.updateProjectionMatrix();
    }
    dirty=true;
  }
  function setView(next) {
    overview=next;
    document.body.dataset.mode=next?"overview":"walk";
    walker.enabled=!next;
    orbit.enabled=next;
    if(next){
      const zoom=view.clientWidth<view.clientHeight?1.58:1;
      overviewCamera.position.set(30*zoom,36*zoom,38*zoom);
      orbit.target.set(0,0,0);orbit.update();
      walker.keys.clear();
      walker.stick=null;walker.look=null;walker.showStick();
    }
    for(const mesh of [...roof,...glass])mesh.visible=!next;
    scene.background=next?new THREE.Color("#d6ded5"):sky;
    scene.fog.density=next?0:.014;
    $("view-toggle").textContent=next?"继续漫游":"楼层鸟瞰";
    $("view-toggle").setAttribute("aria-pressed",String(next));
    $("help").textContent=next?"拖动旋转 · 滚轮或双指缩放":mobile?"左侧滑动移动 · 右侧滑动转向":"WASD 移动 · 拖动鼠标转向";
    renderer.shadowMap.needsUpdate=true;
    syncLocation();dirty=true;
  }
  function goTo(id) {
    const dest=scenes.get(id);
    if (id==="arrival") walker.teleport(arrival,.175);
    else if (dest) walker.teleport(dest.position,dest.yaw);
    else walker.teleport(startPos,Math.PI/2);
    select.value=dest||id==="arrival"?id:"lobby";
    setView(false);
  }
  function applyLink() {
    const params=new URLSearchParams(location.hash.slice(1));
    goTo(params.get("room")||"arrival");
    if (params.get("view")==="overview") setView(true);
  }
  select.addEventListener("change",()=>goTo(select.value));
  $("view-toggle").addEventListener("click",()=>setView(!overview));
  $("map-toggle").addEventListener("click",()=>{
    const panel=$("map-panel");
    panel.hidden=!panel.hidden;
    $("map-toggle").setAttribute("aria-expanded",String(!panel.hidden));
    if(!panel.hidden)syncLocation();
  });
  view.addEventListener("pointerdown",()=>view.focus({preventScroll:true}));
  orbit.addEventListener("change",()=>{dirty=true;});
  window.addEventListener("resize",resize);
  window.addEventListener("hashchange",applyLink);
  document.addEventListener("visibilitychange",()=>{lastTime=0;dirty=true;});
  view.addEventListener("webglcontextlost",event=>{
    event.preventDefault();
    document.body.dataset.state="error";
    $("status").querySelector("strong").textContent="3D 图形连接已中断";
    $("status").querySelector("span").textContent="请刷新页面继续漫游。";
  });
  resize();
  applyLink();
  for(const el of [select,$("view-toggle"),$("map-toggle")])el.disabled=false;
  document.body.dataset.state="ready";
  let renderedCamera="";
  renderer.setAnimationLoop(time=>{
    if(document.hidden || document.body.dataset.state!=="ready")return;
    const dt=Math.min(.045,(time-(lastTime||time))/1e3);lastTime=time;
    if(overview)orbit.update();
    else {
      walker.update(dt);
      const stamp=[walker.x,walker.z,walker.yaw,walker.pitch].join(",");
      if(stamp!==renderedCamera){dirty=true;renderedCamera=stamp;syncLocation();}
    }
    if(dirty){
      if(reflection)reflection.visible=!overview&&walker.x<-3.8&&walker.z<.7;
      renderer.render(scene,overview?overviewCamera:walkCamera);
      dirty=false;
    }
  });
}
start().catch(error=>{
  document.body.dataset.state="error";
  $("status").querySelector("strong").textContent="暂时无法开启 3D 漫游";
  $("status").querySelector("span").textContent=error.message;
  console.error(error);
});
