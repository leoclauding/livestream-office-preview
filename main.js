const svgns = "http://www.w3.org/2000/svg";
const colours = { guest: "#efdac3", work: "#dbe8dd", studio: "#d5e0ec", logistics: "#eedfbb" };
const routeNotes = {
  guest: ["#94572f", "从电梯厅进入接待区，再前往会客会议室。"],
  studio: ["#375d96", "样品从准备区经同侧走廊送入直播间，导播与剪辑区也设在这段走廊。"],
  logistics: ["#705024", "仓储与包装区相邻。收货及发货口按物业安排确认。"]
};
const openRooms = new Set(["desks", "content"]);
const numberOfRooms = document.querySelector("#room-select");
const routeControls = document.querySelector("#routes");
const userSelection = { room: "studio-a", route: "" };

function svgElement(tag, attrs, text = "") {
  const el = document.createElementNS(svgns, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text) el.textContent = text;
  return el;
}
function rect(coords, attrs = {}) {
  const [x, y, x2, y2] = coords;
  return svgElement("rect", {x, y, width: x2-x, height: y2-y, ...attrs});
}
function line(x1,y1,x2,y2,attrs={}) {
  return svgElement("line",{x1,y1,x2,y2,...attrs});
}
function proposedDoor(door) {
  const [x,y,w,side] = door;
  const horizontal = side === "N" || side === "S";
  const group = svgElement("g", {"pointer-events":"none"});
  if (horizontal) {
    group.append(line(x-w/2,y,x+w/2,y,{stroke:"#fcfcf8","stroke-width":8}));
    group.append(line(x-w/2,y,x-w/2,y+(side==="N"?w*.58:-w*.58),{stroke:"#4d6359","stroke-width":2}));
  } else {
    group.append(line(x,y-w/2,x,y+w/2,{stroke:"#fcfcf8","stroke-width":8}));
    group.append(line(x,y-w/2,x+(side==="W"?w*.58:-w*.58),y-w/2,{stroke:"#4d6359","stroke-width":2}));
  }
  return group;
}

function start(layout) {
  const svg = svgElement("svg",{viewBox:"20 17 1200 1300",role:"group","aria-label":"直播电商办公室分区及动线"});
  svg.append(rect(layout.frame,{fill:"#efeee7",stroke:"#465550","stroke-width":5,rx:3}));
  const glass = {stroke:"#9baaa1","stroke-width":2,"stroke-dasharray":"28 4"};
  svg.append(rect([79,74,1165,1260],{fill:"none",...glass}));
  const roomTargets = new Map();
  for (const room of layout.rooms) {
    const zone = rect(room.rect,{class:"zone",fill:colours[room.family],rx:2,role:"button",tabindex:0,"aria-label":room.name,"aria-pressed":false,
      "stroke-dasharray":openRooms.has(room.id) ? "12 6" : "none"});
    zone.addEventListener("click",()=>selectRoom(room.id));
    zone.addEventListener("keydown",event=>{
      if (event.key==="Enter" || event.key===" ") {
        event.preventDefault();
        selectRoom(room.id);
      }
    });
    svg.append(zone);
    roomTargets.set(room.id,zone);
  }
  const structure = svgElement("g",{"pointer-events":"none","aria-hidden":"true"});
  for (const [x,y] of layout.columns) structure.append(rect([x-12,y-12,x+12,y+12],{fill:"#3b484b"}));
  for (const wall of layout.coreWalls) structure.append(rect(wall,{fill:"#505e62"}));
  for (const s of layout.existingThin) structure.append(line(...s,{stroke:"#84928b","stroke-width":4}));
  for (const bounds of layout.lifts) {
    const [x,y,x2,y2]=bounds;
    structure.append(rect(bounds,{fill:"#bcc9c5",stroke:"#5b6867","stroke-width":2}));
    structure.append(line(x+6,y+5,x2-6,y2-5,{stroke:"#71817c","stroke-width":1.5}),line(x2-6,y+5,x+6,y2-5,{stroke:"#71817c","stroke-width":1.5}));
  }
  for (const [x,y,x2,y2] of layout.stairs) {
    structure.append(rect([x,y,x2,y2],{rx:30,fill:"#d3d9d0",stroke:"#76847d","stroke-width":2}));
    for(let i=1;i<13;i++){
      const t=x+i*(x2-x)/13;
      structure.append(line(t,y+8,t,y2-8,{stroke:"#87948c","stroke-width":1.6}));
    }
    structure.append(line(x+10,(y+y2)/2,x2-10,(y+y2)/2,{stroke:"#657971","stroke-width":2}));
  }
  for (const room of layout.rooms) if (room.door) structure.append(proposedDoor(room.door));
  svg.append(structure);
  const routes = new Map();
  const routeGroup = svgElement("g",{"aria-hidden":true});
  for (const route of layout.routes) {
    const p = route.points.at(-1);
    const lineEl = svgElement("polyline",{points:route.points.map(point=>point.join(",")).join(" "),class:"route-line",stroke:routeNotes[route.id][0]});
    const group=svgElement("g",{visibility:"hidden","pointer-events":"none"});
    group.append(lineEl,svgElement("circle",{cx:p[0],cy:p[1],r:12,fill:routeNotes[route.id][0],stroke:"#fff","stroke-width":3}));
    routeGroup.append(group);
    routes.set(route.id,group);
  }
  svg.append(routeGroup);
  const labels=svgElement("g",{"aria-hidden":"true"});
  for (const room of layout.rooms) {
    const [x,y,x2,y2]=room.rect;
    labels.append(svgElement("text",{class:"plan-label",x:(x+x2)/2,y:(y+y2)/2+9},room.name));
  }
  labels.append(svgElement("text",{class:"core-label",x:624,y:553},"电梯厅"));
  labels.append(svgElement("text",{class:"core-label",x:633,y:1018},"南侧通道"));
  svg.append(labels);
  document.querySelector("#floorplan").replaceChildren(svg);

  function selectRoom(id) {
    const room=layout.rooms.find(item=>item.id===id);
    if (!room) return;
    userSelection.room=id;
    numberOfRooms.value=id;
    for(const [key,target] of roomTargets) target.setAttribute("aria-pressed",String(key===id));
    document.querySelector("#room-en").textContent=room.en;
    document.querySelector("#room-name").textContent=room.name;
    document.querySelector("#room-detail").textContent=room.detail;
    document.querySelector("#room-walk").href=`./walk.html#room=${room.id}`;
    const renderLink=document.querySelector("#room-render");
    renderLink.hidden=!room.render;
    if (room.render) renderLink.href=`#${room.render}`;
  }

  numberOfRooms.replaceChildren(...layout.rooms.map(room=>new Option(room.name,room.id)));
  numberOfRooms.addEventListener("change",()=>selectRoom(numberOfRooms.value));
  selectRoom(userSelection.room);
  const resetText = document.querySelector("#route-description").textContent;
  for (const route of layout.routes) {
    const button=document.createElement("button");
    button.type="button";
    button.dataset.route=route.id;
    button.textContent=route.label;
    button.setAttribute("aria-pressed","false");
    button.addEventListener("click",()=>{
      const id=userSelection.route===route.id?"":route.id;
      userSelection.route=id;
      for(const [key,el] of routes) el.setAttribute("visibility",key===id?"visible":"hidden");
      for(const el of routeControls.querySelectorAll("button")) el.setAttribute("aria-pressed",String(el.dataset.route===id));
      document.querySelector("#route-description").textContent=id?routeNotes[id][1]:resetText;
    });
    routeControls.append(button);
  }
}
const mount = document.querySelector("#floorplan");
try {
  const response=await fetch("./design/layout.json");
  if (!response.ok) throw new Error(`Floor plan HTTP ${response.status}`);
  start(await response.json());
} catch (error) {
  mount.textContent="暂时无法加载平面图，请刷新页面。";
  numberOfRooms.disabled=true;
  console.error(error);
}
