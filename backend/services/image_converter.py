"""
Image format conversion utilities
Handles HEIC/HEIF to JPEG conversion for iPhone photos
"""
import os
from datetime import datetime
from typing import Tuple, Optional

# Try to import pillow-heif for HEIC support
try:
    from pillow_heif import register_heif_opener
    from PIL import Image
    from PIL.ExifTags import TAGS
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False
    print("Warning: pillow-heif not installed. HEIC files will not be supported.")


def is_heic_file(filename: str) -> bool:
    """Check if file is HEIC/HEIF format"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ['.heic', '.heif']


def get_photo_taken_at(file_path: str) -> Optional[datetime]:
    """
    Extract photo taken datetime from EXIF data

    Args:
        file_path: Path to image file

    Returns:
        datetime object if found, None otherwise
    """
    if not HEIC_SUPPORTED:
        return None

    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None

            # Look for DateTimeOriginal (tag 36867) or DateTimeDigitized (tag 36868)
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                elif tag == 'DateTimeDigitized':
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

            return None
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
        return None


def convert_heic_to_jpeg(input_path: str, output_path: str = None) -> Tuple[str, bool]:
    """
    Convert HEIC/HEIF image to JPEG

    Args:
        input_path: Path to HEIC file
        output_path: Optional output path. If not provided, uses same name with .jpg extension

    Returns:
        Tuple of (output_path, success)
    """
    if not HEIC_SUPPORTED:
        print(f"HEIC conversion not supported, returning original: {input_path}")
        return input_path, False

    if not is_heic_file(input_path):
        return input_path, False

    try:
        # Generate output path if not provided
        if output_path is None:
            base = os.path.splitext(input_path)[0]
            output_path = f"{base}.jpg"

        # Open and convert
        with Image.open(input_path) as img:
            # Convert to RGB (HEIC may have alpha channel)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Save as JPEG with good quality
            img.save(output_path, 'JPEG', quality=90)

        print(f"Converted HEIC to JPEG: {input_path} -> {output_path}")
        return output_path, True

    except Exception as e:
        print(f"HEIC conversion error: {e}")
        return input_path, False


def process_uploaded_image(file_path: str, filename: str) -> Tuple[str, str]:
    """
    Process uploaded image, converting HEIC if necessary

    Args:
        file_path: Path where file was saved
        filename: Original filename

    Returns:
        Tuple of (processed_file_path, new_filename)
    """
    if is_heic_file(filename):
        # Convert HEIC to JPEG
        new_filename = os.path.splitext(filename)[0] + '.jpg'
        new_path = os.path.splitext(file_path)[0] + '.jpg'

        converted_path, success = convert_heic_to_jpeg(file_path, new_path)

        if success:
            # Remove original HEIC file
            try:
                os.remove(file_path)
            except:
                pass
            return converted_path, new_filename

    return file_path, filename
