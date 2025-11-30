"""Image processing logic for Instagram preparation."""

import io
from pathlib import Path
from typing import Tuple

import piexif
from PIL import Image, ImageFilter, ImageCms


class ImageProcessor:
    """Handles image processing for Instagram optimization."""

    # Instagram size constraints
    PORTRAIT_SIZE = (1080, 1350)  # 4:5 ratio
    LANDSCAPE_MAX_LONG_EDGE = 1350
    SQUARE_SIZE = (1080, 1080)  # 1:1 ratio
    MAX_FILE_SIZE_MB = 8
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    # Sharpening parameters for screen viewing (subtle, professional levels)
    SHARPEN_RADIUS = 0.8
    SHARPEN_PERCENT = 50
    SHARPEN_THRESHOLD = 2

    def __init__(self, start_quality: int = 100, no_sharpen: bool = False, keep_exif: bool = False):
        """Initialize processor with options."""
        self.start_quality = start_quality
        self.no_sharpen = no_sharpen
        self.keep_exif = keep_exif

    @staticmethod
    def _get_orientation(img: Image.Image) -> str:
        """Determine if image is portrait, landscape, or square."""
        width, height = img.size
        aspect_ratio = width / height

        # Consider square if within 2% of 1:1
        if 0.98 <= aspect_ratio <= 1.02:
            return "square"
        elif height > width:
            return "portrait"
        else:
            return "landscape"

    @staticmethod
    def _center_crop_to_ratio(img: Image.Image, target_ratio: float) -> Image.Image:
        """Center crop image to target aspect ratio (width/height)."""
        width, height = img.size
        current_ratio = width / height

        if current_ratio > target_ratio:
            # Image is too wide, crop width
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        else:
            # Image is too tall, crop height
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))

        return img

    @staticmethod
    def _resize_to_fit(img: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
        """Resize image to fit within max_size while maintaining aspect ratio."""
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img

    @staticmethod
    def _resize_landscape(img: Image.Image, max_long_edge: int) -> Image.Image:
        """Resize landscape image so longest edge is max_long_edge."""
        width, height = img.size
        if width > height:
            # Width is longer
            if width > max_long_edge:
                new_width = max_long_edge
                new_height = int(height * (max_long_edge / width))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # Height is longer
            if height > max_long_edge:
                new_height = max_long_edge
                new_width = int(width * (max_long_edge / height))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return img

    def _apply_screen_sharpening(self, img: Image.Image) -> Image.Image:
        """Apply unsharp mask sharpening optimized for screen viewing."""
        return img.filter(
            ImageFilter.UnsharpMask(
                radius=self.SHARPEN_RADIUS,
                percent=self.SHARPEN_PERCENT,
                threshold=self.SHARPEN_THRESHOLD
            )
        )

    @staticmethod
    def _convert_to_srgb(img: Image.Image) -> Image.Image:
        """Convert image to sRGB color space (Instagram standard)."""
        # If image has an embedded profile, convert to sRGB
        if img.mode == 'RGB' and 'icc_profile' in img.info:
            try:
                # Create sRGB profile
                srgb_profile = ImageCms.createProfile("sRGB")

                # Get the embedded profile
                input_profile = ImageCms.ImageCmsProfile(io.BytesIO(img.info['icc_profile']))

                # Convert to sRGB
                img = ImageCms.profileToProfile(img, input_profile, srgb_profile, outputMode='RGB')
            except Exception:
                # If conversion fails, just continue without conversion
                pass

        # Ensure RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')

        return img

    @staticmethod
    def _preserve_gps_datetime(exif_dict: dict) -> dict:
        """Create new EXIF dict with only GPS and DateTime tags preserved."""
        new_exif = {"0th": {}, "Exif": {}, "GPS": {}}

        # Preserve GPS data if present
        if "GPS" in exif_dict and exif_dict["GPS"]:
            new_exif["GPS"] = exif_dict["GPS"]

        # Preserve DateTime tags
        if "0th" in exif_dict:
            for tag in [piexif.ImageIFD.DateTime]:
                if tag in exif_dict["0th"]:
                    new_exif["0th"][tag] = exif_dict["0th"][tag]

        if "Exif" in exif_dict:
            for tag in [piexif.ExifIFD.DateTimeOriginal, piexif.ExifIFD.DateTimeDigitized]:
                if tag in exif_dict["Exif"]:
                    new_exif["Exif"][tag] = exif_dict["Exif"][tag]

        return new_exif

    def _save_with_size_optimization(
        self,
        img: Image.Image,
        output_path: Path,
        exif_bytes: bytes = None
    ) -> int:
        """Save image as progressive JPEG, optimizing quality to stay under size limit."""
        quality = self.start_quality
        min_quality = 60

        while quality >= min_quality:
            buffer = io.BytesIO()
            save_kwargs = {
                "format": "JPEG",
                "quality": quality,
                "optimize": True,
                "progressive": True,
            }

            if exif_bytes:
                save_kwargs["exif"] = exif_bytes

            img.save(buffer, **save_kwargs)
            size = buffer.tell()

            if size <= self.MAX_FILE_SIZE_BYTES:
                # Size is acceptable, save to file
                output_path.write_bytes(buffer.getvalue())
                return quality

            # File too large, reduce quality
            quality -= 5

        # Even at minimum quality, save anyway
        buffer.seek(0)
        output_path.write_bytes(buffer.getvalue())
        return quality

    def process_image(self, input_path: Path, output_path: Path, verbose: bool = False) -> dict:
        """
        Process a single image for Instagram.

        Returns dict with processing info: orientation, final_size, quality, etc.
        """
        # Load image
        img = Image.open(input_path)

        # Handle EXIF orientation
        try:
            img = Image.exif_transpose(img)
        except Exception:
            pass

        # Handle EXIF data (strip by default for privacy)
        exif_bytes = None
        if self.keep_exif:
            try:
                exif_dict = piexif.load(input_path.as_posix())
                filtered_exif = self._preserve_gps_datetime(exif_dict)
                exif_bytes = piexif.dump(filtered_exif)
            except Exception:
                # No EXIF or error reading it
                pass

        # Determine orientation
        orientation = self._get_orientation(img)

        # Process based on orientation
        if orientation == "portrait":
            # Crop to 4:5 and resize to 1080x1350
            img = self._center_crop_to_ratio(img, 4/5)
            img = self._resize_to_fit(img, self.PORTRAIT_SIZE)
        elif orientation == "landscape":
            # Resize to max long edge 1350
            img = self._resize_landscape(img, self.LANDSCAPE_MAX_LONG_EDGE)
        else:  # square
            # Resize to 1080x1080
            img = self._resize_to_fit(img, self.SQUARE_SIZE)

        # Convert to sRGB
        img = self._convert_to_srgb(img)

        # Apply screen sharpening (unless disabled)
        if not self.no_sharpen:
            img = self._apply_screen_sharpening(img)

        # Save with size optimization
        final_quality = self._save_with_size_optimization(img, output_path, exif_bytes)

        return {
            "orientation": orientation,
            "final_size": img.size,
            "quality": final_quality,
            "file_size_mb": output_path.stat().st_size / (1024 * 1024)
        }

    def process_image_size_constrained(
        self,
        input_path: Path,
        output_path: Path,
        max_size_mb: float,
        verbose: bool = False
    ) -> dict:
        """
        Process image with file size as primary constraint.

        Preserves original aspect ratio and scales down to fit within max_size_mb.
        Balances quality and resolution for best result.
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)

        # Load image
        img = Image.open(input_path)
        original_size = img.size

        # Handle EXIF orientation
        try:
            img = Image.exif_transpose(img)
        except Exception:
            pass

        # Handle EXIF data (strip by default for privacy)
        exif_bytes = None
        if self.keep_exif:
            try:
                exif_dict = piexif.load(input_path.as_posix())
                filtered_exif = self._preserve_gps_datetime(exif_dict)
                exif_bytes = piexif.dump(filtered_exif)
            except Exception:
                pass

        # Convert to sRGB
        img = self._convert_to_srgb(img)

        # Apply sharpening if enabled
        if not self.no_sharpen:
            img = self._apply_screen_sharpening(img)

        # Save with size and scale optimization
        final_quality, final_img = self._save_with_size_and_scale_optimization(
            img, output_path, max_size_bytes, exif_bytes
        )

        return {
            "original_size": original_size,
            "final_size": final_img.size,
            "quality": final_quality,
            "file_size_mb": output_path.stat().st_size / (1024 * 1024)
        }

    def _save_with_size_and_scale_optimization(
        self,
        img: Image.Image,
        output_path: Path,
        max_size_bytes: int,
        exif_bytes: bytes = None
    ) -> Tuple[int, Image.Image]:
        """
        Save image by balancing quality and scale to fit within size limit.

        Strategy: Scale down minimally, then maximize quality via binary search.
        Returns (final_quality, final_image).
        """
        current_img = img

        def encode_to_buffer(image: Image.Image, q: int) -> io.BytesIO:
            """Encode image to JPEG buffer at given quality."""
            buffer = io.BytesIO()
            save_kwargs = {
                "format": "JPEG",
                "quality": q,
                "optimize": True,
                "progressive": True,
            }
            if exif_bytes:
                save_kwargs["exif"] = exif_bytes
            image.save(buffer, **save_kwargs)
            return buffer

        # Step 1: Scale down if needed (at high quality) to get roughly under limit
        for _ in range(5):  # Max 5 scaling iterations
            buffer = encode_to_buffer(current_img, 95)
            size = buffer.tell()

            if size <= max_size_bytes:
                break  # Small enough at high quality

            # Calculate scale factor - use 0.98 margin (only 2% buffer)
            scale_factor = (max_size_bytes / size) ** 0.5 * 0.98

            if scale_factor >= 0.99:
                # Very close, quality adjustment will handle it
                break

            # Scale down
            new_width = max(100, int(current_img.width * scale_factor))
            new_height = max(100, int(current_img.height * scale_factor))
            current_img = current_img.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )

        # Step 2: Binary search for highest quality that fits
        min_quality = 60
        max_quality = 100
        best_quality = min_quality
        best_buffer = None

        while min_quality <= max_quality:
            mid_quality = (min_quality + max_quality) // 2
            buffer = encode_to_buffer(current_img, mid_quality)
            size = buffer.tell()

            if size <= max_size_bytes:
                # Fits - try higher quality
                best_quality = mid_quality
                best_buffer = buffer
                min_quality = mid_quality + 1
            else:
                # Too large - try lower quality
                max_quality = mid_quality - 1

        # Save the best result
        if best_buffer:
            output_path.write_bytes(best_buffer.getvalue())
        else:
            # Fallback: couldn't fit even at min quality, scale more aggressively
            scale_factor = 0.8
            current_img = current_img.resize(
                (int(current_img.width * scale_factor), int(current_img.height * scale_factor)),
                Image.Resampling.LANCZOS
            )
            buffer = encode_to_buffer(current_img, 80)
            output_path.write_bytes(buffer.getvalue())
            best_quality = 80

        return best_quality, current_img
