// First-person walking: keyboard, mouse drag and a touch joystick, with
// circle-vs-box collision against model.colliders.

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// Pushes a circle at (x, z) out of every box. If that cannot be done cleanly
// (a gap narrower than the walker), returns `fallback` instead.
export function resolveCollisions(x, z, r, colliders, fallback = null) {
  const x0 = x, z0 = z;
  for (let iter = 0; iter < 8; iter++) {
    let moved = false;
    for (const c of colliders) {
      const px = clamp(x, c.minX, c.maxX), pz = clamp(z, c.minZ, c.maxZ);
      const dx = x - px, dz = z - pz;
      const d2 = dx * dx + dz * dz;
      if (d2 >= r * r) continue;
      if (d2 > 1e-10) {
        const d = Math.sqrt(d2);
        x = px + (dx / d) * r;
        z = pz + (dz / d) * r;
      } else {
        const l = x - c.minX, rr = c.maxX - x, t = z - c.minZ, b = c.maxZ - z;
        const m = Math.min(l, rr, t, b);
        if (m === l) x = c.minX - r;
        else if (m === rr) x = c.maxX + r;
        else if (m === t) z = c.minZ - r;
        else z = c.maxZ + r;
      }
      moved = true;
    }
    if (!moved) return [x, z];
  }
  if (isFree(x, z, r - 0.002, colliders)) return [x, z];
  return fallback || [x0, z0];
}

export function isFree(x, z, r, colliders) {
  return colliders.every((c) => {
    const dx = Math.max(c.minX - x, 0, x - c.maxX), dz = Math.max(c.minZ - z, 0, z - c.maxZ);
    return dx * dx + dz * dz >= r * r;
  });
}

export class WalkControls {
  constructor(camera, dom, { joystick, radius = 0.22 } = {}) {
    this.camera = camera;
    this.dom = dom;
    this.joystick = joystick;
    this.radius = radius;
    this.eye = 1.6;
    this.x = 0; this.z = 0; this.yaw = 0; this.pitch = -0.05;
    this.colliders = [];
    this.enabled = true;
    this.keys = new Set();
    this.stick = null;   // { id, ox, oy, dx, dy }
    this.look = null;    // { id, x, y }
    this.listen();
  }

  setModel(model) {
    this.colliders = model.colliders;
    this.eye = model.heights.eye;
  }

  teleport([x, z], yaw = this.yaw) {
    [this.x, this.z] = resolveCollisions(x, z, this.radius, this.colliders);
    this.yaw = yaw;
    this.pitch = -0.05;
    this.apply();
  }

  listen() {
    const typing = (e) => /^(INPUT|SELECT|TEXTAREA)$/.test(e.target?.tagName);
    window.addEventListener('keydown', (e) => {
      if (typing(e) || e.metaKey || e.ctrlKey) return;
      if (/^(Arrow|Key[WASDQE]$|Shift)/.test(e.code)) {
        this.keys.add(e.code);
        if (e.code.startsWith('Arrow')) e.preventDefault();
      }
    });
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());

    const el = this.dom;
    el.addEventListener('pointerdown', (e) => {
      if (!this.enabled) return;
      if (e.pointerType === 'touch' && e.clientX < window.innerWidth * 0.45 && !this.stick) {
        this.stick = { id: e.pointerId, ox: e.clientX, oy: e.clientY, dx: 0, dy: 0 };
        this.showStick();
      } else if (!this.look) {
        this.look = { id: e.pointerId, x: e.clientX, y: e.clientY };
      } else return;
      el.setPointerCapture(e.pointerId);
    });
    el.addEventListener('pointermove', (e) => {
      if (this.stick && e.pointerId === this.stick.id) {
        const dx = e.clientX - this.stick.ox, dy = e.clientY - this.stick.oy;
        const len = Math.hypot(dx, dy), max = 48;
        const k = len > max ? max / len : 1;
        this.stick.dx = (dx * k) / max;
        this.stick.dy = (dy * k) / max;
        this.showStick();
      } else if (this.look && e.pointerId === this.look.id) {
        const k = e.pointerType === 'touch' ? 0.006 : 0.0035;
        this.yaw -= (e.clientX - this.look.x) * k;
        this.pitch = clamp(this.pitch - (e.clientY - this.look.y) * k, -1.2, 1.2);
        this.look.x = e.clientX;
        this.look.y = e.clientY;
      }
    });
    const end = (e) => {
      if (this.stick && e.pointerId === this.stick.id) { this.stick = null; this.showStick(); }
      if (this.look && e.pointerId === this.look.id) this.look = null;
    };
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
  }

  showStick() {
    const j = this.joystick;
    if (!j) return;
    if (!this.stick) { j.hidden = true; return; }
    j.hidden = false;
    j.style.left = `${this.stick.ox}px`;
    j.style.top = `${this.stick.oy}px`;
    j.firstElementChild.style.transform = `translate(${this.stick.dx * 48}px, ${this.stick.dy * 48}px)`;
  }

  update(dt) {
    if (!this.enabled) return;
    const k = this.keys;
    let fwd = 0, side = 0, turn = 0;
    if (k.has('KeyW') || k.has('ArrowUp')) fwd += 1;
    if (k.has('KeyS') || k.has('ArrowDown')) fwd -= 1;
    if (k.has('KeyD')) side += 1;
    if (k.has('KeyA')) side -= 1;
    if (k.has('ArrowLeft') || k.has('KeyQ')) turn += 1;
    if (k.has('ArrowRight') || k.has('KeyE')) turn -= 1;
    if (this.stick) { fwd -= this.stick.dy; side += this.stick.dx; }
    this.yaw += turn * 1.8 * dt;

    const run = k.has('ShiftLeft') || k.has('ShiftRight') ? 1.8 : 1;
    const len = Math.hypot(fwd, side);
    if (len > 0.05) {
      const n = Math.min(1, len);
      fwd /= len; side /= len;
      const sin = Math.sin(this.yaw), cos = Math.cos(this.yaw);
      // Yaw 0 looks down -Z; right-hand side is +X.
      const vx = (-sin * fwd + cos * side) * 1.4 * run * n;
      const vz = (-cos * fwd - sin * side) * 1.4 * run * n;
      const dist = Math.hypot(vx, vz) * dt;
      const steps = Math.max(1, Math.ceil(dist / 0.06));
      for (let i = 0; i < steps; i++) {
        [this.x, this.z] = resolveCollisions(this.x + (vx * dt) / steps, this.z + (vz * dt) / steps, this.radius, this.colliders, [this.x, this.z]);
      }
    }
    this.apply();
  }

  apply() {
    this.camera.position.set(this.x, this.eye, this.z);
    this.camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
  }
}
