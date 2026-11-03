// Gear train with a crank and piston, written by Claude for funkbox.
// Teeth 24 : 12 : 8. Each gear moves 24 teeth per loop, so they turn 1, 2 and 3 times
// and every frame of the last turn flows back into the first.
const float M = 0.046;                 // module: pitch radius = teeth * M / 2
const float K = 24.0;                  // teeth that pass the mesh point per loop

float gear(vec2 p, vec2 c, float n, float a, out float body) {
  vec2 q = p - c;
  float r = length(q), ang = atan(q.y, q.x);
  float R = n * M * 0.5;
  float prof = R + 0.85 * M * clamp(1.7 * cos(n * (ang - a)), -1.0, 1.0);
  float aa = fwidth(r) * 1.2;
  float solid = 1.0 - smoothstep(prof - aa, prof + aa, r);
  // hub, a ring and five spokes
  float hole = 1.0 - smoothstep(0.16 * R - aa, 0.16 * R + aa, r);
  float rim = smoothstep(0.62 * R - aa, 0.62 * R + aa, r);
  float spoke = 1.0 - smoothstep(0.07 * R - aa, 0.07 * R + aa,
                 abs(sin(2.5 * (ang - a))) * r);
  float inner = max(rim, max(spoke, smoothstep(0.30 * R + aa, 0.30 * R - aa, r)));
  body = solid * (1.0 - hole) * inner;
  return r / R;
}

float box(vec2 p, vec2 c, vec2 h) {
  vec2 d = abs(p - c) - h;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float seg(vec2 p, vec2 a, vec2 b) {
  vec2 pa = p - a, ba = b - a;
  return length(pa - ba * clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0));
}

vec4 effect(vec2 p) {
  float th = iPhase;
  float n1 = 24.0, n2 = 12.0, n3 = 8.0;
  float R1 = n1 * M * 0.5, R2 = n2 * M * 0.5, R3 = n3 * M * 0.5;
  vec2 c1 = vec2(-0.2, 0.6);
  float f12 = radians(40.0), f13 = radians(135.0);
  vec2 c2 = c1 + (R1 + R2) * vec2(cos(f12), sin(f12));
  vec2 c3 = c1 + (R1 + R3) * vec2(cos(f13), sin(f13));
  float k1 = 0.0;
  float k2 = f12 + PI - (PI - n1 * (f12 - k1)) / n2;
  float k3 = f13 + PI - (PI - n1 * (f13 - k1)) / n3;
  float a1 = k1 - th * K / n1;          // clockwise, 1 turn per loop
  float a2 = k2 + th * K / n2;          // 2 turns
  float a3 = k3 + th * K / n3;          // 3 turns

  // background: dark blueprint grid
  vec3 col = mix(vec3(0.04, 0.05, 0.09), vec3(0.08, 0.06, 0.14), 0.5 + 0.25 * p.y);
  vec2 g = abs(fract(p * 8.0) - 0.5);
  col += 0.035 * (1.0 - smoothstep(0.0, 0.03, min(g.x, g.y)));

  // piston cylinder and crank (pin on gear 1)
  float L = 0.95, rc = 0.22;
  vec2 pin = c1 + rc * vec2(cos(a1), sin(a1));
  float dx = pin.x - c1.x;
  vec2 head = vec2(c1.x, pin.y - sqrt(L * L - dx * dx));
  float aa = fwidth(p.y) * 1.5;
  float wall = min(abs(p.x - c1.x - 0.19), abs(p.x - c1.x + 0.19));
  float cyl = (1.0 - smoothstep(0.012 - aa, 0.012 + aa, wall)) * step(p.y, c1.y - 0.66) * step(c1.y - 1.32, p.y);
  col = mix(col, vec3(0.45, 0.5, 0.6), cyl);
  float hd = box(p, head, vec2(0.165, 0.1));
  col = mix(col, palette(0.75), 1.0 - smoothstep(-aa, aa, hd));
  col = mix(col, palette(0.75) * 0.5, 1.0 - smoothstep(-aa, aa, abs(hd + 0.03) - 0.006));

  float b; float rr;
  rr = gear(p, c3, n3, a3, b); col = mix(col, palette(0.55) * (0.85 + 0.15 * rr), b);
  rr = gear(p, c2, n2, a2, b); col = mix(col, palette(0.35) * (0.85 + 0.15 * rr), b);
  rr = gear(p, c1, n1, a1, b); col = mix(col, palette(0.12) * (0.85 + 0.15 * rr), b);

  // connecting rod over the gear
  float rod = seg(p, pin, head) - 0.028;
  col = mix(col, vec3(0.92, 0.9, 0.85), 1.0 - smoothstep(-aa, aa, rod));
  float pd = length(p - pin) - 0.04;
  col = mix(col, vec3(0.15), 1.0 - smoothstep(-aa, aa, pd));
  float hp = length(p - head) - 0.035;
  col = mix(col, vec3(0.15), 1.0 - smoothstep(-aa, aa, hp));
  return vec4(col, 1.0);
}
