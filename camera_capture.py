"""Preview a camera and save still images for the CoinCounter3000 project."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show a live camera preview and save coin photos."
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="camera device index (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "captures",
        help="directory for saved photos (default: ./captures)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    camera = cv2.VideoCapture(args.camera)

    if not camera.isOpened():
        camera.release()
        print(
            f"Could not open camera {args.camera}. Check that it is connected "
            "and not being used by another app."
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    window_name = "CoinCounter3000 Camera - S: save photo | Q/Esc: quit"
    last_message = ""
    message_until = 0.0
    print(f"Saving photos to: {args.output_dir}")
    print("Press S to save a photo. Press Q or Esc to quit.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Could not read a frame from the camera.")
                return 1

            preview = frame.copy()
            if cv2.getTickCount() < message_until:
                cv2.putText(
                    preview,
                    last_message,
                    (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 220, 0),
                    2,
                    cv2.LINE_AA,
                )

            cv2.imshow(window_name, preview)
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break
            if key == ord("s"):
                filename = datetime.now().strftime("coin_%Y%m%d_%H%M%S_%f.jpg")
                image_path = args.output_dir / filename
                if cv2.imwrite(str(image_path), frame):
                    last_message = f"Saved {filename}"
                    message_until = cv2.getTickCount() + 2 * cv2.getTickFrequency()
                    print(f"Saved: {image_path}")
                else:
                    print(f"Could not save photo: {image_path}")
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
