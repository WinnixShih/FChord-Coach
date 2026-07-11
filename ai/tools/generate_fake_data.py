"""
Synthetic landmark generator — for pipeline smoke-testing ONLY.

Produces fake MediaPipe-style hand landmarks in the exact format
`dataset.py` expects:

    data/<label>/0000.json
    { "label": "<label>", "nodes": [[x,y,z], ...] }   # 21 nodes

Labels match graph.py::LABEL_MAP exactly:
    correct, err_index_low, err_index_angle,
    err_thumb_wrong, err_wrist_far, not_fchord

Usage:
    python -m ai.tools.generate_fake_data --out_dir ai/data --n_per_class 150
"""
import argparse
import json
import os
import numpy as np

LABELS = [
    "correct",
    "err_index_low",
    "err_index_angle",
    "err_thumb_wrong",
    "err_wrist_far",
    "not_fchord",
]

# ── baseline "correct F chord" hand shape ───────────────────────────
# 21 MediaPipe landmarks, normalized 0-1 coords, rough F-barre posture.
# Index 0 = wrist, 1-4 = thumb, 5-8 = index, 9-12 = middle,
# 13-16 = ring, 17-20 = pinky.
BASE_HAND = np.array([
    [0.50, 0.85, 0.00],   # 0 wrist
    [0.42, 0.78, -0.02],  # 1 thumb cmc
    [0.36, 0.68, -0.03],  # 2 thumb mcp
    [0.33, 0.58, -0.04],  # 3 thumb ip
    [0.31, 0.50, -0.05],  # 4 thumb tip
    [0.44, 0.55, -0.01],  # 5 index mcp
    [0.44, 0.42, -0.02],  # 6 index pip  (barre position — flat across)
    [0.44, 0.33, -0.02],  # 7 index dip
    [0.44, 0.25, -0.02],  # 8 index tip
    [0.50, 0.53, 0.00],   # 9 middle mcp
    [0.51, 0.38, -0.01],  # 10 middle pip
    [0.51, 0.27, -0.01],  # 11 middle dip
    [0.51, 0.18, -0.01],  # 12 middle tip
    [0.56, 0.55, 0.01],   # 13 ring mcp
    [0.58, 0.42, 0.01],   # 14 ring pip
    [0.59, 0.32, 0.01],   # 15 ring dip
    [0.60, 0.24, 0.01],   # 16 ring tip
    [0.61, 0.58, 0.02],   # 17 pinky mcp
    [0.63, 0.48, 0.02],   # 18 pinky pip
    [0.64, 0.40, 0.02],   # 19 pinky dip
    [0.65, 0.33, 0.02],   # 20 pinky tip
], dtype=np.float64)


def apply_error(nodes: np.ndarray, label: str, rng: np.random.Generator) -> np.ndarray:
    """Displace specific joints to simulate each error type."""
    nodes = nodes.copy()

    if label == "correct":
        pass  # baseline shape, noise added later

    elif label == "err_index_low":
        # index finger sags below the barre line instead of staying flat
        nodes[6:9, 1] += rng.uniform(0.06, 0.12)  # pip/dip/tip drop down (y+)

    elif label == "err_index_angle":
        # index finger angled instead of straight across the barre
        shift = rng.uniform(0.05, 0.10)
        nodes[7, 0] += shift * 0.6
        nodes[8, 0] += shift

    elif label == "err_thumb_wrong":
        # thumb wraps over the top / wrong position
        nodes[2:5, 1] -= rng.uniform(0.10, 0.18)
        nodes[2:5, 0] += rng.uniform(0.03, 0.08)

    elif label == "err_wrist_far":
        # wrist positioned too far from the fretboard plane (z offset + shift)
        nodes[0, 2] += rng.uniform(0.08, 0.15)
        nodes[0, 1] += rng.uniform(0.04, 0.08)

    elif label == "not_fchord":
        # a different, unrelated hand shape (fingers loosely spread/curled)
        nodes[5:, 1] += rng.uniform(-0.15, 0.15, size=(16,))
        nodes[5:, 0] += rng.uniform(-0.10, 0.10, size=(16,))

    else:
        raise ValueError(f"Unknown label: {label}")

    return nodes


def randomize(nodes: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Add per-sample noise + slight rotation/scale to mimic different
    hands, angles, and MediaPipe detection jitter."""
    nodes = nodes.copy()

    # small gaussian jitter per joint
    nodes += rng.normal(0, 0.008, size=nodes.shape)

    # slight 2D rotation around wrist (xy plane)
    theta = rng.uniform(-0.15, 0.15)  # ~ +/-8.6 deg
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    wrist = nodes[0, :2].copy()
    rel = nodes[:, :2] - wrist
    rot = np.stack([
        rel[:, 0] * cos_t - rel[:, 1] * sin_t,
        rel[:, 0] * sin_t + rel[:, 1] * cos_t,
    ], axis=1)
    nodes[:, :2] = rot + wrist

    # slight uniform scale (different hand sizes / camera distance)
    scale = rng.uniform(0.92, 1.08)
    nodes[:, :2] = wrist + (nodes[:, :2] - wrist) * scale

    # clip to plausible normalized range
    nodes[:, 0] = np.clip(nodes[:, 0], 0.0, 1.0)
    nodes[:, 1] = np.clip(nodes[:, 1], 0.0, 1.0)

    return nodes


def main(out_dir: str, n_per_class: int, seed: int):
    rng = np.random.default_rng(seed)

    total = 0
    for label in LABELS:
        label_dir = os.path.join(out_dir, label)
        os.makedirs(label_dir, exist_ok=True)

        for i in range(n_per_class):
            nodes = apply_error(BASE_HAND, label, rng)
            nodes = randomize(nodes, rng)

            sample = {
                "label": label,
                "nodes": nodes.tolist(),
            }
            path = os.path.join(label_dir, f"{i:04d}.json")
            with open(path, "w") as f:
                json.dump(sample, f)
            total += 1

        print(f"[OK] {label}: {n_per_class} samples -> {label_dir}")

    print(f"\nDone. Total: {total} synthetic samples in {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", default="ai/data", help="output root dir (mirrors data/<label>/*.json)")
    parser.add_argument("--n_per_class", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.out_dir, args.n_per_class, args.seed)