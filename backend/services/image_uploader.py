import os
import shutil
from typing import Optional

# Check if Cloudinary is configured
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")

if CLOUDINARY_URL:
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(cloudinary_url=CLOUDINARY_URL)
    USE_CLOUDINARY = True
else:
    USE_CLOUDINARY = False


def upload_image(file_path: str, filename: str) -> str:
    """
    Upload image to storage (Cloudinary in production, local in development)
    Returns the URL/path to access the image
    """
    if USE_CLOUDINARY:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_path,
            folder="mr-system/uploads",
            public_id=os.path.splitext(filename)[0],
            overwrite=True,
            resource_type="image"
        )
        return result["secure_url"]
    else:
        # Local storage - return relative path
        return f"/uploads/{filename}"


def save_uploaded_file(file, upload_dir: str) -> tuple[str, str]:
    """
    Save uploaded file to local storage
    Returns (local_file_path, filename)
    """
    file_location = f"{upload_dir}/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    return file_location, file.filename


def get_image_url(local_path: str, filename: str) -> str:
    """
    Get the URL for an uploaded image
    In production, uploads to Cloudinary and returns the URL
    In development, returns the local path
    """
    if USE_CLOUDINARY:
        return upload_image(local_path, filename)
    else:
        return f"/uploads/{filename}"


def delete_image(image_url: str) -> bool:
    """
    Delete image from storage
    """
    if USE_CLOUDINARY and "cloudinary" in image_url:
        try:
            # Extract public_id from URL
            # URL format: https://res.cloudinary.com/{cloud}/image/upload/{version}/{folder}/{public_id}.{ext}
            parts = image_url.split("/")
            public_id_with_ext = parts[-1]
            public_id = os.path.splitext(public_id_with_ext)[0]
            folder = parts[-2] if len(parts) > 1 else ""
            full_public_id = f"{folder}/{public_id}" if folder else public_id

            cloudinary.uploader.destroy(full_public_id)
            return True
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
            return False
    else:
        # Local file - optionally delete
        # For now, we'll keep local files to avoid accidental deletion
        return True
