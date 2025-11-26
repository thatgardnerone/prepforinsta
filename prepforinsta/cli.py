"""CLI interface for Instagram image preparation tool."""

import sys
from pathlib import Path
from typing import List

import click

from .processor import ImageProcessor


# Supported image formats
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


def find_images(input_path: Path) -> List[Path]:
    """Find all image files in the input path."""
    images = []

    if input_path.is_file():
        # Single file
        if input_path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(input_path)
    elif input_path.is_dir():
        # Directory - find all images
        for ext in IMAGE_EXTENSIONS:
            images.extend(input_path.glob(f'*{ext}'))
            images.extend(input_path.glob(f'*{ext.upper()}'))
    else:
        # Try glob pattern
        images.extend(Path('.').glob(str(input_path)))

    return sorted(set(images))


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path(), required=False)
@click.option(
    '--quality',
    default=100,
    type=click.IntRange(60, 100),
    help='Starting JPEG quality (60-100). Will be reduced if needed to meet 8MB limit.'
)
@click.option(
    '--no-sharpen',
    is_flag=True,
    help='Skip sharpening (useful if images are pre-sharpened in Lightroom).'
)
@click.option(
    '--keep-exif',
    is_flag=True,
    help='Preserve GPS and DateTime EXIF data (stripped by default for privacy).'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be processed without actually processing.'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Show detailed processing information.'
)
def main(input_path: str, output_path: str, quality: int, no_sharpen: bool, keep_exif: bool, dry_run: bool, verbose: bool):
    """
    Prepare images for Instagram publishing.

    Processes images to Instagram's optimal specifications:
    - Portrait images: cropped to 4:5 ratio, scaled to 1080x1350px
    - Landscape images: scaled to max 1350px long edge
    - Square images: scaled to 1080x1080px
    - All images: sharpened for screens, converted to sRGB, saved as progressive JPEG <8MB

    INPUT_PATH: File, directory, or glob pattern of images to process

    OUTPUT_PATH: Destination folder (optional, defaults to INPUT_PATH/INSTA)
    """
    # Parse paths
    input_path = Path(input_path).resolve()

    if output_path:
        output_path = Path(output_path).resolve()
    else:
        # Default to INSTA subfolder
        if input_path.is_file():
            output_path = input_path.parent / 'INSTA'
        else:
            output_path = input_path / 'INSTA'

    # Find all images
    images = find_images(input_path)

    if not images:
        click.echo(click.style('No images found in input path.', fg='red'), err=True)
        sys.exit(1)

    click.echo(f"Found {len(images)} image(s) to process")
    click.echo(f"Output directory: {output_path}")

    if dry_run:
        click.echo(click.style('\nDRY RUN - No files will be modified', fg='yellow'))
        for img in images:
            click.echo(f"  Would process: {img.name}")
        return

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Process images
    processor = ImageProcessor(start_quality=quality, no_sharpen=no_sharpen, keep_exif=keep_exif)
    success_count = 0
    error_count = 0

    with click.progressbar(
        images,
        label='Processing images',
        show_pos=True,
        item_show_func=lambda x: x.name if x else ''
    ) as progress_images:
        for img_path in progress_images:
            output_file = output_path / f"{img_path.stem}.jpg"

            try:
                result = processor.process_image(img_path, output_file, verbose=verbose)
                success_count += 1

                if verbose:
                    click.echo(
                        f"\n  {img_path.name} -> {output_file.name}\n"
                        f"    Orientation: {result['orientation']}\n"
                        f"    Size: {result['final_size'][0]}x{result['final_size'][1]}px\n"
                        f"    Quality: {result['quality']}\n"
                        f"    File size: {result['file_size_mb']:.2f} MB"
                    )

            except Exception as e:
                error_count += 1
                click.echo(
                    click.style(f"\n  Error processing {img_path.name}: {e}", fg='red'),
                    err=True
                )

    # Summary
    click.echo(f"\n{click.style('Done!', fg='green', bold=True)}")
    click.echo(f"Successfully processed: {success_count}")
    if error_count > 0:
        click.echo(click.style(f"Errors: {error_count}", fg='red'))
    click.echo(f"Output location: {output_path}")


if __name__ == '__main__':
    main()
