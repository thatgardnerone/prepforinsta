# prepforinsta

A fast CLI tool to prepare images for Instagram publishing, optimized for Apple Silicon.

## Features

Automatically processes images to meet Instagram's optimal specifications:

- **Portrait images**: Center-cropped to 4:5 ratio, scaled to 1080×1350px
- **Landscape images**: Scaled to max 1350px long edge (preserves aspect ratio)
- **Square images**: Scaled to 1080×1080px
- **All images**:
  - Subtle sharpening for screen viewing (can be disabled with `--no-sharpen`)
  - Converted to sRGB color space
  - Saved as progressive JPEG with optimized quality
  - Automatically reduced to stay under 8MB file size limit
  - EXIF data stripped for privacy (use `--keep-exif` to preserve GPS/DateTime)

## Installation

1. Clone or navigate to this directory
2. Install with Poetry:

```bash
poetry install
```

3. The `prepforinsta` command will be available in your Poetry environment

## Usage

### Basic usage

Process all images in a folder (outputs to `INPUT_FOLDER/INSTA`):

```bash
prepforinsta ~/pictures/vacation
```

### Specify output folder

```bash
prepforinsta ~/pictures/vacation ~/pictures/ready-for-instagram
```

### Process a single image

```bash
prepforinsta ~/pictures/vacation/IMG_1234.jpg
```

### Options

```bash
prepforinsta [INPUT_PATH] [OUTPUT_PATH] [OPTIONS]

Options:
  --quality INTEGER RANGE  Starting JPEG quality (60-100). Auto-reduces if
                          needed to meet 8MB limit. [default: 100]
  --no-sharpen            Skip sharpening (useful if images are pre-sharpened
                          in Lightroom)
  --keep-exif             Preserve GPS and DateTime EXIF data (stripped by
                          default for privacy)
  --max-size FLOAT        Target max file size in MB. Enables size-constrained
                          mode (no cropping, preserves aspect ratio)
  -f, --force             Overwrite existing output files (skipped by default)
  --dry-run               Show what would be processed without processing
  -v, --verbose           Show detailed processing information
  --help                  Show this message and exit
```

### Examples

**Dry run to see what will be processed:**
```bash
prepforinsta ~/pictures/vacation --dry-run
```

**Verbose output with detailed info:**
```bash
prepforinsta ~/pictures/vacation -v
```

**Custom quality starting point:**
```bash
prepforinsta ~/pictures/vacation --quality 95
```

**Skip sharpening (for pre-sharpened exports):**
```bash
prepforinsta ~/pictures/vacation --no-sharpen
```

**Keep GPS/DateTime for Instagram auto-location:**
```bash
prepforinsta ~/pictures/vacation --keep-exif
```

**Size-constrained mode for PurplePort (6MB limit):**
```bash
prepforinsta ~/pictures/vacation --max-size 6
```

## Size-Constrained Mode

When using `--max-size`, the tool operates in size-constrained mode:

- **No cropping** - preserves original aspect ratio
- **No fixed dimensions** - scales down to fit within size limit
- **Balances quality + resolution** - reduces both for optimal result

This is useful for platforms like PurplePort that have file size limits but don't require specific aspect ratios.

## Supported Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)

## How It Works

1. **Detects orientation**: Classifies each image as portrait, landscape, or square
2. **Crops/scales appropriately**:
   - Portrait: Center crop to 4:5, then scale to 1080×1350px
   - Landscape: Scale down so longest edge is 1350px
   - Square: Scale to 1080×1080px
3. **Color correction**: Converts to sRGB (Instagram's standard color space)
4. **Sharpening**: Applies subtle unsharp mask for screen viewing (skip with `--no-sharpen`)
5. **EXIF handling**: Strips all metadata for privacy (use `--keep-exif` to preserve GPS/DateTime)
6. **Size optimization**: Saves as progressive JPEG, automatically reducing quality if needed to stay under 8MB

## Instagram Optimization Tips

This tool handles the technical requirements, but for best results:

- **Before export from Lightroom**: Apply your full editing workflow as normal
- **Export settings from Lightroom**: Full resolution, high quality, light sharpening for matte prints
- **Run this tool**: Handles Instagram-specific sizing, color space, and screen sharpening
- **Upload to Instagram**: Images will be optimized for the platform with minimal quality loss

## Why These Settings?

- **4:5 portrait ratio**: Instagram's maximum portrait ratio, gives you the most screen real estate
- **1350px max**: Instagram's recommended maximum dimension
- **Progressive JPEG**: Better loading experience on mobile
- **sRGB color space**: Instagram converts to sRGB anyway; doing it upfront gives you more control
- **Screen sharpening**: Compensates for Instagram's compression while avoiding oversharpening
- **8MB limit**: Instagram's file size maximum

## Technical Details

- Built with **Pillow** for fast image processing on Apple Silicon
- **Click** for modern CLI interface
- **piexif** for EXIF metadata handling
- Optimized for Apple Silicon Macs with native ARM64 wheels

## License

MIT
