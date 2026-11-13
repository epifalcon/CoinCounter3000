# CoinCounter3000

## Count coins and capture photos

Install the Python dependency:

```powershell
python3 -m pip install -r requirements.txt
```

Start the live camera preview:

```powershell
python3 camera_capture.py
```

Before counting, calibrate the camera scale: place a single known coin near the
center of the view, press **C**, then press **P** for penny, **N** for nickel,
**D** for dime, or **R** for quarter. The program uses that coin's known diameter
to estimate the sizes of other coins. The preview outlines size-matched coins,
labels each denomination, and displays the total value in the top-left corner.
Press **C** again to recalibrate if the camera position changes.

Press **S** to save an annotated JPEG in the `captures` folder. Saved photos
include the detected coin circles, denominations, and total. Press **Q** or
**Esc** to close the preview.

If the camera is not the default device, select another camera index:

```powershell
python3 camera_capture.py --camera 1
```

The detector uses circular edges and apparent coin diameter; it is a visual
estimate, not a trained coin-recognition model. Keep the camera fixed and
perpendicular to the surface, and keep coins flat, visible, and separated against
a contrasting background. Objects that are round and close to a coin's size can
still be mistaken for coins. Reflections, shadows, overlapping coins, camera
angle, and inaccurate calibration can affect the result. The coin calibration
only lasts until the program closes.

Tune detection for your camera and coin size with `--min-radius`, `--max-radius`,
`--min-distance`, and `--sensitivity`. Circle radii and distances are in pixels.
For example:

```powershell
python3 camera_capture.py --min-radius 20 --max-radius 90 --min-distance 45
```

`--max-radius 0` means no maximum. A lower `--sensitivity` may detect more coins
but can also add false detections. To skip interactive calibration, provide a
known camera scale with `--pixels-per-mm`. Use `--output-dir PATH` to choose
another folder for saved photos.
