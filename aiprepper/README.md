# AI Prepper Tagging Tool

Simple PyQt6 desktop app for image-by-image captioning with sidecar `.txt` files.

## Features

- Scan a folder and load all images.
- Navigate one image at a time with **Previous/Next** buttons or left/right arrow keys.
- **Jump to Image**: Use the spinbox to jump directly to any image in the folder.
- Keep a persistent trigger word across images.
- Write captions and save each caption to a text sidecar with the same name as the image.
  - Example: `photo_001.jpg` -> `photo_001.txt`
- Reuse previous captions from dropdown history.
- Drag a crop box on the preview and crop the current image in two ways:
  - `Crop Image`: replaces current image (optional backup to `_original_backup/`).
  - `Save Crop Variant`: keeps original and creates new files like `image_crop1.jpg`, `image_crop2.jpg`, etc.
  - `Revert Crop`: restore the original from backup (button only enabled if backup exists).
- **AI Image Analysis** (local, runs offline):
  - Click `AI Analyze` to generate detailed descriptions from images.
  - AI labels are saved as `image_AI.txt` so you can distinguish them from manual labels.
  - If an image already has a caption, the AI will analyze it and suggest improvements.
  - Review and edit AI-generated labels before accepting.
  - **Batch AI Analysis**: Specify a range (e.g., images 10-50) and run AI analysis on all of them at once with a progress bar.
    - Skips images that already have AI labels.
    - Perfect for testing AI quality on a subset before processing entire datasets.
- Delete unwanted images directly from the app (also deletes matching `.txt` sidecar if present).

## Setup

```bash
pip install -r requirements.txt
```

Note: The first run will download the AI model (~1 GB). Subsequent runs are instant.

## Run

```bash
python app.py
```

## Notes

- Caption history and trigger settings are saved in your home directory at `.aiprepper_settings.json`.
- `Ctrl+S` saves the current caption quickly.
- AI analysis uses a local transformer model (BLIP) - no internet or external API required.
