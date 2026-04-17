"""
Labeling tool — press SPACE to save a sample, Q to quit.
Usage:
    python tools/label.py --label correct
    python tools/label.py --label err_index_low
"""
import argparse
import json
import os
import time
import cv2
import mediapipe as mp

LABELS = ["correct","err_index_low","err_index_angle","err_thumb_wrong","err_wrist_far","not_fchord"]

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils


def main(label: str):
    assert label in LABELS, f"Invalid label. Choose from: {LABELS}"

    out_dir = os.path.join("data", label)
    os.makedirs(out_dir, exist_ok=True)
    existing = len([f for f in os.listdir(out_dir) if f.endswith(".json")])
    count = existing

    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    cap   = cv2.VideoCapture(0)

    print(f"\nLabel: [{label}]  Existing: {existing}")
    print("SPACE = save sample    Q = quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        detected = False
        nodes    = None

        if result.multi_hand_landmarks:
            lm       = result.multi_hand_landmarks[0]
            nodes    = [[l.x, l.y, l.z] for l in lm.landmark]
            detected = True
            mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        status_color = (0, 200, 80) if detected else (0, 60, 220)
        status_text  = f"[{label}]  saved: {count}" if detected else "No hand detected"
        cv2.putText(frame, status_text, (12, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        cv2.imshow("Label Tool — SPACE save  Q quit", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(' ') and detected:
            sample = {"label": label, "nodes": nodes, "timestamp": time.time()}
            path   = os.path.join(out_dir, f"{count:04d}.json")
            json.dump(sample, open(path, "w"))
            count += 1
            print(f"  Saved {path}  (total: {count})")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone. Total saved: {count} samples for [{label}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=LABELS)
    args = parser.parse_args()
    main(args.label)
