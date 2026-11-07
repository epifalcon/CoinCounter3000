# CoinCounter3000

## Capture coin photos

Install the Python dependency:

```powershell
python3 -m pip install -r requirements.txt
```

Start the live camera preview:

```powershell
python3 camera_capture.py
```

Press **S** in the preview window to save a JPEG photo. Photos are saved in the
`captures` folder. Press **Q** or **Esc** to close the preview.

If the camera is not the default device, select another camera index:

```powershell
python3 camera_capture.py --camera 1
```

Use `--output-dir PATH` to choose another folder for saved photos.
