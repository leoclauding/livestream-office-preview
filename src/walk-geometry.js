import { isFree } from "./walk-controls.js";

export const radius = .24;
export const planOrigin = [622, 667];
export const lobby = [621, 551];

export function planToWorld([x, y], scale) {
  return [(x - planOrigin[0]) * scale, (y - planOrigin[1]) * scale];
}

export function worldToPlan([x, z], scale) {
  return [x / scale + planOrigin[0], z / scale + planOrigin[1]];
}

export function collidersFromBounds(bounds) {
  return bounds.map(([minX, minZ, maxX, maxZ]) => ({minX, minZ, maxX, maxZ}));
}

export function reachableCells(layout, colliders) {
  const scale = layout.metresPerUnit, step = .21;
  const [left, top] = planToWorld(layout.frame.slice(0, 2), scale);
  const [right, bottom] = planToWorld(layout.frame.slice(2), scale);
  const width = Math.ceil((right - left) / step), height = Math.ceil((bottom - top) / step);
  const [sx, sz] = planToWorld(lobby, scale);
  const i = Math.round((sx - left) / step), j = Math.round((sz - top) / step);
  const start = j * width + i, ids = [start];
  const visited = new Uint8Array(width * height);
  visited[start] = 1;
  const toWorld = id => [left + (id % width) * step, top + Math.floor(id / width) * step];
  for (let index = 0; index < ids.length; index++) {
    const id = ids[index], u = id % width, v = Math.floor(id / width);
    const [x,z] = toWorld(id);
    for (const [a,b] of [[u+1,v],[u-1,v],[u,v+1],[u,v-1]]) {
      if (a < 0 || b < 0 || a >= width || b >= height) continue;
      const next = b * width + a;
      if (visited[next]) continue;
      const [nx,nz] = toWorld(next);
      visited[next] = 1;
      if (!isFree(nx,nz,radius,colliders) || !isFree((x+nx)/2,(z+nz)/2,radius,colliders)) continue;
      ids.push(next);
    }
  }
  return ids.map(toWorld);
}

export function roomView(room, walkable, scale) {
  const [x,y,x2,y2] = room.rect;
  const centre = [(x+x2)/2,(y+y2)/2];
  let wanted = centre, target = centre;
  if (room.door) {
    const [dx,dy,,side] = room.door;
    const inside = {E:[-50,0],W:[50,0],N:[0,48],S:[0,-48]}[side];
    wanted = [dx+inside[0],dy+inside[1]];
    if (room.id.startsWith("studio")) target = [centre[0],centre[1]-30];
  } else wanted=[x2-25,centre[1]];
  if (room.id==="reception") {
    wanted=[246,521]; target=[180,618];
  } else if (room.id==="green") {
    wanted=[810,178]; target=[748,156];
  }
  let closest=null, score=Infinity;
  for (const world of walkable) {
    const [px,py] = worldToPlan(world,scale);
    if (px<x+16 || px>x2-16 || py<y+16 || py>y2-16) continue;
    const d=(px-wanted[0])**2+(py-wanted[1])**2;
    if (d<score) {score=d;closest=world;}
  }
  if (!closest) return null;
  const [tx,tz]=planToWorld(target,scale);
  return {position:closest,yaw:Math.atan2(closest[0]-tx,closest[1]-tz)};
}
