"""Preview a camera and save still images for the CoinCounter3000 project."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2

COIN_TYPES = {
    ord("p"): ("Penny", 1, 19.05),
    ord("n"): ("Nickel", 5, 21.21),
    ord("d"): ("Dime", 10, 17.91),
    ord("r"): ("Quarter", 25, 24.26),
}
SIZE_TOLERANCE = 0.08


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
    parser.add_argument(
        "--min-radius",
        type=int,
        default=12,
        help="smallest coin radius to detect in pixels (default: 12)",
    )
    parser.add_argument(
        "--max-radius",
        type=int,
        default=0,
        help="largest coin radius in pixels; 0 means no limit (default: 0)",
    )
    parser.add_argument(
        "--min-distance",
        type=float,
        default=30,
        help="minimum distance between detected coin centers in pixels (default: 30)",
    )
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=30,
        help="circle detection sensitivity; lower detects more circles (default: 30)",
    )
    parser.add_argument(
        "--pixels-per-mm",
        type=float,
        default=0,
        help="known camera scale; otherwise calibrate in the preview with a known coin",
    )
    return parser.parse_args()


def find_coins(
    frame: cv2.typing.MatLike,
    min_radius: int,
    max_radius: int,
    min_distance: float,
    sensitivity: float,
) -> list[tuple[int, int, int]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (9, 9), 2)
    detected = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_distance,
        param1=100,
        param2=sensitivity,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if detected is None:
        return []

    return [
        (int(round(circle[0])), int(round(circle[1])), int(round(circle[2])))
        for circle in detected[0]
    ]


def classify_coins(
    circles: list[tuple[int, int, int]],
    pixels_per_mm: float,
) -> list[tuple[int, int, int, str, int]]:
    if pixels_per_mm <= 0:
        return []

    classified = []
    for x, y, radius in circles:
        diameter_mm = (radius * 2) / pixels_per_mm
        denomination = min(
            COIN_TYPES.values(),
            key=lambda coin: abs(diameter_mm - coin[2]) / coin[2],
        )
        name, value_cents, expected_diameter_mm = denomination
        relative_error = abs(diameter_mm - expected_diameter_mm) / expected_diameter_mm
        if relative_error <= SIZE_TOLERANCE:
            classified.append((x, y, radius, name, value_cents))
    return classified


def calibrate_scale(
    circles: list[tuple[int, int, int]],
    frame_shape: tuple[int, ...],
    coin_diameter_mm: float,
) -> float | None:
    if not circles:
        return None

    center_x = frame_shape[1] / 2
    center_y = frame_shape[0] / 2
    x, y, radius = min(
        circles,
        key=lambda circle: (circle[0] - center_x) ** 2 + (circle[1] - center_y) ** 2,
    )
    if radius <= 0:
        return None
    return (radius * 2) / coin_diameter_mm


def annotate_frame(
    frame: cv2.typing.MatLike,
    coins: list[tuple[int, int, int, str, int]],
    pixels_per_mm: float,
    calibration_mode: bool,
) -> cv2.typing.MatLike:
    annotated = frame.copy()
    total_cents = sum(coin[4] for coin in coins)
    for x, y, radius, name, value_cents in coins:
        cv2.circle(annotated, (x, y), radius, (0, 220, 0), 2, cv2.LINE_AA)
        cv2.putText(
            annotated,
            f"{name} {value_cents}c",
            (x - radius, y + radius + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 220, 0),
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        annotated,
        f"Coins: {len(coins)}",
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 220, 0),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        annotated,
        f"Total: ${total_cents // 100}.{total_cents % 100:02d}",
        (16, 66),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 220, 0),
        2,
        cv2.LINE_AA,
    )
    if calibration_mode:
        calibration_text = "Center one coin, then press P=penny N=nickel D=dime R=quarter"
    elif pixels_per_mm <= 0:
        calibration_text = "Not calibrated: press C, then identify one centered coin"
    else:
        calibration_text = "C: recalibrate"
    cv2.putText(
        annotated,
        calibration_text,
        (16, max(24, annotated.shape[0] - 18)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 220, 220),
        2,
        cv2.LINE_AA,
    )
    return annotated


def main() -> int:
    args = parse_args()
    if args.min_radius < 0 or args.max_radius < 0:
        print("Coin radii must be zero or greater.")
        return 2
    if args.max_radius and args.max_radius < args.min_radius:
        print("--max-radius must be greater than or equal to --min-radius.")
        return 2
    if args.min_distance <= 0 or args.sensitivity <= 0:
        print("--min-distance and --sensitivity must be greater than zero.")
        return 2
    if args.pixels_per_mm < 0:
        print("--pixels-per-mm must be zero or greater.")
        return 2

    camera = cv2.VideoCapture(args.camera)

    if not camera.isOpened():
        camera.release()
        print(
            f"Could not open camera {args.camera}. Check that it is connected "
            "and not being used by another app."
        )
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    window_name = "CoinCounter3000 - S: save photo | C: calibrate | Q/Esc: quit"
    last_message = ""
    message_until = 0.0
    tick_frequency = cv2.getTickFrequency()
    pixels_per_mm = args.pixels_per_mm
    calibration_mode = False
    print(f"Saving photos to: {args.output_dir}")
    if pixels_per_mm > 0:
        print(f"Using camera scale: {pixels_per_mm:.2f} pixels/mm")
    else:
        print("Press C, center a single known coin, then identify it to calibrate coin sizes.")
    print("Press S to save a photo. Press C to calibrate. Press Q or Esc to quit.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Could not read a frame from the camera.")
                return 1

            circles = find_coins(
                frame,
                args.min_radius,
                args.max_radius,
                args.min_distance,
                args.sensitivity,
            )
            coins = (
                classify_coins(circles, pixels_per_mm)
                if pixels_per_mm > 0
                else []
            )
            preview = annotate_frame(frame, coins, pixels_per_mm, calibration_mode)
            if cv2.getTickCount() < message_until:
                cv2.putText(
                    preview,
                    last_message,
                    (16, 64),
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
            if key == ord("c"):
                calibration_mode = True
                last_message = "Center one coin, then press P, N, D, or R"
                message_until = cv2.getTickCount() + 10 * tick_frequency
                continue
            if calibration_mode and key in COIN_TYPES:
                name, _, diameter_mm = COIN_TYPES[key]
                scale = calibrate_scale(circles, frame.shape, diameter_mm)
                if scale is None:
                    last_message = "No circle detected; try centering the coin and calibrate again"
                    message_until = cv2.getTickCount() + 3 * tick_frequency
                    print(last_message)
                else:
                    pixels_per_mm = scale
                    calibration_mode = False
                    last_message = f"Calibrated using {name} ({scale:.2f} pixels/mm)"
                    message_until = cv2.getTickCount() + 3 * tick_frequency
                    print(last_message)
                continue
            if key == ord("s"):
                filename = datetime.now().strftime("coin_%Y%m%d_%H%M%S_%f.jpg")
                image_path = args.output_dir / filename
                annotated = annotate_frame(frame, coins, pixels_per_mm, calibration_mode)
                if cv2.imwrite(str(image_path), annotated):
                    last_message = f"Saved {filename}"
                    message_until = cv2.getTickCount() + 2 * tick_frequency
                    total_cents = sum(coin[4] for coin in coins)
                    print(
                        f"Saved: {image_path} ({len(coins)} coins, "
                        f"${total_cents // 100}.{total_cents % 100:02d})"
                    )
                else:
                    print(f"Could not save photo: {image_path}")
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
