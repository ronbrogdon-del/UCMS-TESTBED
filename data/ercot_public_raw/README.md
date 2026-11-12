# ERCOT Public Raw Data

This directory is intended for the original, unmodified ERCOT public data files
(hourly load by weather zone and historical RTM hub/load zone prices) for years
2011 and 2019–2024.

## Status
The full manifest with source URLs, filenames, and DocIDs is in `ERCOT_DATA_MANIFEST.txt`.

Binary files (ZIP/XLS, ~1–14 MB each, total ~100 MB) could not be pushed through the
connected GitHub API tool, which accepts only text content. The files were successfully
downloaded as originals in the conversation workspace.

## How to add the binaries
1. Clone this repo.
2. Copy the downloaded files from the conversation artifacts into `data/ercot_public_raw/`
   (load files into a `load/` subfolder and price files into a `prices/` subfolder if preferred).
3. Commit and push.

Alternatively, use the GitHub web UI "Add file" / upload feature, or Git LFS if preferred
for large binaries.

All source URLs are listed in the manifest so the files can be re-downloaded if needed.
