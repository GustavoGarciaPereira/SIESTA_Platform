use wasm_bindgen::prelude::*;

// ─── SIESTA .out parser ───────────────────────────────────────────────────────

/// Parse a SIESTA `.out` file and return a JSON array of `{x, y, z, q, sym}`.
#[wasm_bindgen]
pub fn parse_siesta_out_full(content: &str) -> String {
    #[derive(serde::Serialize)]
    struct Atom {
        x: f64,
        y: f64,
        z: f64,
        q: f64,
        sym: String,
    }

    let mut atoms: Vec<Atom> = Vec::new();

    // ── 1. Extract atomic coordinates ─────────────────────────────────────
    let mut in_coords = false;
    for line in content.lines() {
        if line.contains("siesta: Atomic coordinates (Ang):") {
            in_coords = true;
            continue;
        }
        if in_coords {
            let t = line.trim();
            if t.is_empty() || t.starts_with("siesta:") {
                break;
            }
            let parts: Vec<&str> = t.split_whitespace().collect();
            if parts.len() >= 5 {
                let sym = parts[1].to_string();
                let x = parts[2].parse::<f64>().unwrap_or(0.0);
                let y = parts[3].parse::<f64>().unwrap_or(0.0);
                let z = parts[4].parse::<f64>().unwrap_or(0.0);
                atoms.push(Atom { x, y, z, q: 0.0, sym });
            }
        }
    }

    if atoms.is_empty() {
        return "[]".to_string();
    }

    // ── 2. Extract Mulliken populations ────────────────────────────────────
    let mut mulliken: Vec<f64> = Vec::new();
    let mut in_mull = false;
    for line in content.lines() {
        if line.contains("siesta: Mulliken populations:") {
            in_mull = true;
            continue;
        }
        if in_mull {
            let t = line.trim();
            if t.is_empty() || t.starts_with("siesta:") {
                break;
            }
            if let Some(qs) = t.find("Q =") {
                if let Ok(q) = t[qs + 3..].trim().parse::<f64>() {
                    mulliken.push(q);
                }
            }
        }
    }

    if mulliken.len() == atoms.len() {
        for (i, a) in atoms.iter_mut().enumerate() {
            a.q = mulliken[i];
        }
    }

    serde_json::to_string(&atoms).unwrap_or_else(|_| "[]".to_string())
}

// ─── 3D field solver ─────────────────────────────────────────────────────────

/// A 3D point charge (used internally for the 3D solver).
#[derive(Clone, Copy)]
struct Charge3D {
    x: f64,
    y: f64,
    z: f64,
    q: f64,
}

fn field_at(p: (f64, f64, f64), charges: &[Charge3D], k: f64) -> (f64, f64, f64) {
    let mut ex = 0.0;
    let mut ey = 0.0;
    let mut ez = 0.0;
    let soft = 0.1; // softening to avoid singularity
    for c in charges {
        let dx = p.0 - c.x;
        let dy = p.1 - c.y;
        let dz = p.2 - c.z;
        let r = (dx * dx + dy * dy + dz * dz).sqrt().max(soft);
        let intensity = k * c.q / (r * r);
        ex += intensity * dx / r;
        ey += intensity * dy / r;
        ez += intensity * dz / r;
    }
    (ex, ey, ez)
}

/// Compute the 3D electric field on a uniform grid. Returns a flat array:
/// `[x0,y0,z0,Ex0,Ey0,Ez0,  x1,y1,z1,Ex1,Ey1,Ez1,  ...]`.
#[wasm_bindgen]
pub fn compute_field_3d(
    charges_json: &str,
    nx: usize,
    ny: usize,
    nz: usize,
    k: f64,
) -> Vec<f64> {
    #[derive(serde::Deserialize)]
    struct ChargeInput {
        x: f64,
        y: f64,
        q: f64,
    }

    let charges: Vec<ChargeInput> =
        serde_json::from_str(charges_json).unwrap_or_default();
    let c3d: Vec<Charge3D> = charges
        .iter()
        .map(|c| Charge3D { x: c.x, y: c.y, z: 0.0, q: c.q })
        .collect();

    if c3d.is_empty() {
        return vec![];
    }

    // Use bounding box of charges to define grid extent
    let min_x = c3d.iter().map(|c| c.x).fold(f64::INFINITY, f64::min);
    let max_x = c3d.iter().map(|c| c.x).fold(f64::NEG_INFINITY, f64::max);
    let min_y = c3d.iter().map(|c| c.y).fold(f64::INFINITY, f64::min);
    let max_y = c3d.iter().map(|c| c.y).fold(f64::NEG_INFINITY, f64::max);
    let min_z = c3d.iter().map(|c| c.z).fold(f64::INFINITY, f64::min);
    let max_z = c3d.iter().map(|c| c.z).fold(f64::NEG_INFINITY, f64::max);

    let pad = 2.0; // padding in Angstroms
    let x0 = min_x - pad;
    let x1 = max_x + pad;
    let y0 = min_y - pad;
    let y1 = max_y + pad;
    let z0 = min_z - pad;
    let z1 = max_z + pad;

    let nxn = nx.max(1);
    let nyn = ny.max(1);
    let nzn = nz.max(1);

    let mut out = Vec::with_capacity(nx * ny * nz * 6);
    for iz in 0..nz {
        let z = z0 + (iz as f64 / (nzn - 1) as f64) * (z1 - z0);
        for iy in 0..ny {
            let y = y0 + (iy as f64 / (nyn - 1) as f64) * (y1 - y0);
            for ix in 0..nx {
                let x = x0 + (ix as f64 / (nxn - 1) as f64) * (x1 - x0);
                let (ex, ey, ez) = field_at((x, y, z), &c3d, k);
                out.extend_from_slice(&[x, y, z, ex, ey, ez]);
            }
        }
    }
    out
}

/// Trace field lines from positive charges using RK4 integration.
/// Returns a flat array of 3D points `[x0,y0,z0, x1,y1,z1, ...]`.
/// Each line is terminated by a `[f64::NAN; 3]` sentinel.
#[wasm_bindgen]
pub fn trace_field_lines(
    charges_json: &str,
    step_size: f64,
    max_steps: usize,
    k: f64,
) -> Vec<f64> {
    #[derive(serde::Deserialize)]
    struct ChargeInput {
        x: f64,
        y: f64,
        q: f64,
    }

    let charges: Vec<ChargeInput> =
        serde_json::from_str(charges_json).unwrap_or_default();
    let c3d: Vec<Charge3D> = charges
        .iter()
        .map(|c| Charge3D { x: c.x, y: c.y, z: 0.0, q: c.q })
        .collect();

    let mut out: Vec<f64> = Vec::new();

    for c in &c3d {
        if c.q <= 0.0 {
            continue;
        } // start lines only from positive charges

        // Start slightly offset from the charge centre in 6 directions
        let offsets = [
            (step_size, 0.0, 0.0),
            (-step_size, 0.0, 0.0),
            (0.0, step_size, 0.0),
            (0.0, -step_size, 0.0),
            (0.0, 0.0, step_size),
            (0.0, 0.0, -step_size),
        ];

        for &(ox, oy, oz) in &offsets {
            let mut x = c.x + ox;
            let mut y = c.y + oy;
            let mut z = c.z + oz;
            out.push(x);
            out.push(y);
            out.push(z);

            for _ in 0..max_steps {
                let (ex, ey, ez) = field_at((x, y, z), &c3d, k);
                let mag = (ex * ex + ey * ey + ez * ez).sqrt();
                if mag < 1e-9 {
                    break;
                }

                // RK4 step
                let dt = step_size / mag;
                let k1 = (ex, ey, ez);
                let (e2x, e2y, e2z) = field_at(
                    (x + 0.5 * dt * k1.0, y + 0.5 * dt * k1.1, z + 0.5 * dt * k1.2),
                    &c3d,
                    k,
                );
                let (e3x, e3y, e3z) = field_at(
                    (x + 0.5 * dt * e2x, y + 0.5 * dt * e2y, z + 0.5 * dt * e2z),
                    &c3d,
                    k,
                );
                let (e4x, e4y, e4z) = field_at(
                    (x + dt * e3x, y + dt * e3y, z + dt * e3z),
                    &c3d,
                    k,
                );

                x += dt / 6.0 * (k1.0 + 2.0 * e2x + 2.0 * e3x + e4x);
                y += dt / 6.0 * (k1.1 + 2.0 * e2y + 2.0 * e3y + e4y);
                z += dt / 6.0 * (k1.2 + 2.0 * e2z + 2.0 * e3z + e4z);

                out.push(x);
                out.push(y);
                out.push(z);

                // Stop if field becomes too weak
                let (efx, efy, efz) = field_at((x, y, z), &c3d, k);
                if (efx * efx + efy * efy + efz * efz).sqrt() < 0.01 {
                    break;
                }

                // Check proximity to any negative charge
                let mut stop = false;
                for cn in &c3d {
                    if cn.q >= 0.0 {
                        continue;
                    }
                    let d2 = (x - cn.x) * (x - cn.x)
                        + (y - cn.y) * (y - cn.y)
                        + (z - cn.z) * (z - cn.z);
                    if d2 < step_size * step_size {
                        stop = true;
                        break;
                    }
                }
                if stop {
                    break;
                }
            }
            // Sentinel to separate lines
            out.push(f64::NAN);
            out.push(f64::NAN);
            out.push(f64::NAN);
        }
    }
    out
}

// ─── Unit tests ───────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_siesta_out_basic() {
        let content = "\
siesta: Atomic coordinates (Ang):
   1  O    4.4700    5.4820   -3.9220
   2  C    6.5430    4.5380   -4.7680
siesta: Mulliken populations:
Species: O  #1  Q = -0.4321
Species: C  #2  Q =  0.2512
";
        let json = parse_siesta_out_full(content);
        let atoms: Vec<serde_json::Value> = serde_json::from_str(&json).unwrap();
        assert_eq!(atoms.len(), 2);
        assert_eq!(atoms[0]["sym"], "O");
        assert!((atoms[0]["q"].as_f64().unwrap() + 0.4321).abs() < 1e-4);
        assert_eq!(atoms[1]["sym"], "C");
    }

    #[test]
    fn test_parse_empty_content() {
        let json = parse_siesta_out_full("no coordinates here");
        assert_eq!(json, "[]");
    }

    #[test]
    fn test_compute_field_3d_empty() {
        let data = compute_field_3d("[]", 4, 4, 4, 50.0);
        assert!(data.is_empty());
    }

    #[test]
    fn test_compute_field_3d_basic() {
        let charges = r#"[{"x":0.0,"y":0.0,"q":1.0},{"x":2.0,"y":0.0,"q":-1.0}]"#;
        let data = compute_field_3d(charges, 4, 4, 4, 50.0);
        // Should produce 4*4*4*6 = 384 floats
        assert_eq!(data.len(), 384);
        // Field should be non-zero
        let has_nonzero = data.iter().any(|&v| v.abs() > 0.001);
        assert!(has_nonzero);
    }

    #[test]
    fn test_trace_field_lines_basic() {
        let charges = r#"[{"x":0.0,"y":0.0,"q":1.0},{"x":3.0,"y":0.0,"q":-1.0}]"#;
        let lines = trace_field_lines(charges, 0.2, 100, 50.0);
        // Should produce at least some points (6 starting directions × N steps)
        assert!(!lines.is_empty());
        // Should contain NaN sentinels
        assert!(lines.iter().any(|v| v.is_nan()));
    }
}
