#[derive(Clone, Copy, Debug)]
pub struct Weapon {
    pub id: &'static str,
    pub offhand: bool,
    pub speed: f32,
    pub reach: f64,
    pub frames: &'static [[f32; 7]],
}

pub fn ray_box(
    eye: [f64; 3],
    dir: [f64; 3],
    lo: [f64; 3],
    hi: [f64; 3],
    reach: f64,
) -> Option<f64> {
    let mut near: f64 = 0.0;
    let mut far = reach;
    for a in 0..3 {
        if dir[a].abs() < 1e-9 {
            if eye[a] < lo[a] || eye[a] > hi[a] {
                return None;
            }
        } else {
            let x = (lo[a] - eye[a]) / dir[a];
            let y = (hi[a] - eye[a]) / dir[a];
            near = near.max(x.min(y));
            far = far.min(x.max(y));
        }
    }
    (near <= far && far >= 0.0).then_some(near)
}

pub fn pose(frames: &[[f32; 7]], progress: f32, offhand: bool) -> [f32; 6] {
    let mut result = [0.0; 6];
    if !progress.is_finite() || !(0.0..1.0).contains(&progress) {
        return result;
    }
    for pair in frames.windows(2) {
        if progress >= pair[0][0] && progress <= pair[1][0] {
            let t = (progress - pair[0][0]) / (pair[1][0] - pair[0][0]);
            let t = t * t * (3.0 - 2.0 * t);
            for i in 0..6 {
                result[i] = pair[0][i + 1] + (pair[1][i + 1] - pair[0][i + 1]) * t;
            }
            break;
        }
    }
    if offhand {
        result[1] = -result[1];
        result[2] = -result[2];
        result[3] = -result[3];
    }
    result
}

pub fn request(data: &[u8]) -> Option<usize> {
    match data {
        [1, hand @ 0..=1] => Some(*hand as usize),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_forged_hand_and_trailing_data() {
        assert_eq!(request(&[1, 1]), Some(1));
        for packet in [&[1, 2][..], &[1, 0, 3], &[0, 0], &[]] {
            assert_eq!(request(packet), None);
        }
    }
    #[test]
    fn ray_must_intersect_a_target_in_reach() {
        assert_eq!(
            ray_box(
                [0.0; 3],
                [0.0, 0.0, 1.0],
                [-0.5, -0.5, 2.0],
                [0.5, 0.5, 3.0],
                2.5
            ),
            Some(2.0)
        );
        assert_eq!(
            ray_box(
                [0.0; 3],
                [0.0, 0.0, 1.0],
                [1.0, 1.0, 2.0],
                [2.0, 2.0, 3.0],
                5.0
            ),
            None
        );
        assert_eq!(
            ray_box(
                [0.0; 3],
                [0.0, 0.0, 1.0],
                [-0.5, -0.5, 3.0],
                [0.5, 0.5, 4.0],
                2.5
            ),
            None
        );
    }
    #[test]
    fn pose_returns_to_rest_and_mirrors_offhand() {
        let frames = [
            [0.0; 7],
            [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ];
        assert_eq!(pose(&frames, 0.5, true), [1.0, -2.0, -3.0, -4.0, 5.0, 6.0]);
        assert_eq!(pose(&frames, 1.0, false), [0.0; 6]);
        assert_eq!(pose(&frames, f32::NAN, false), [0.0; 6]);
    }
}
