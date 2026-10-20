"""
Image optimization, storage, thumbnailing, and caching service.
Ensures the application loads images rapidly without memory bloat or UI freezes.
"""
import os
import uuid
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageTk
from config import (
    IMAGES_DIR, IMG_CUSTOMERS_DIR, IMG_ID_PROOFS_DIR,
    IMG_JEWELS_DIR, IMG_CONNECTIONS_DIR, IMG_THUMBNAILS_DIR,
    MAX_IMAGE_DIMENSION, THUMBNAIL_DIMENSION,
    IMAGE_JPEG_QUALITY, THUMBNAIL_JPEG_QUALITY
)

class ImageService:
    # Memory cache for Tkinter PhotoImage objects to prevent garbage collection and reload lag
    _tk_cache = {}

    @staticmethod
    def _get_target_dir(category):
        mapping = {
            "customer": IMG_CUSTOMERS_DIR,
            "id_proof": IMG_ID_PROOFS_DIR,
            "jewel": IMG_JEWELS_DIR,
            "connection": IMG_CONNECTIONS_DIR,
        }
        return mapping.get(category, IMAGES_DIR)

    @classmethod
    def save_and_optimize_image(cls, src_path_or_image, category="customer"):
        """
        Compresses and saves an image to the appropriate folder.
        Generates and saves a corresponding fast-loading thumbnail.
        Returns: relative/absolute path to the optimized image.
        """
        if not src_path_or_image:
            return ""

        try:
            # Load PIL Image
            if isinstance(src_path_or_image, str):
                if not os.path.exists(src_path_or_image):
                    return ""
                img = Image.open(src_path_or_image)
            else:
                img = src_path_or_image

            # Convert RGBA/Palette to RGB
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Unique filename
            file_id = uuid.uuid4().hex
            filename = f"{category}_{file_id}.jpg"
            target_dir = cls._get_target_dir(category)
            full_path = os.path.join(target_dir, filename)

            # Resize if larger than max dimension while maintaining aspect ratio
            w, h = img.size
            if max(w, h) > MAX_IMAGE_DIMENSION:
                ratio = MAX_IMAGE_DIMENSION / float(max(w, h))
                new_size = (int(w * ratio), int(h * ratio))
                optimized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            else:
                optimized_img = img

            # Save optimized image
            optimized_img.save(full_path, "JPEG", quality=IMAGE_JPEG_QUALITY, optimize=True)

            # Create and save thumbnail
            thumb_name = f"thumb_{category}_{file_id}.jpg"
            thumb_path = os.path.join(IMG_THUMBNAILS_DIR, thumb_name)
            thumb_img = optimized_img.copy()
            thumb_img.thumbnail((THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION), Image.Resampling.LANCZOS)
            thumb_img.save(thumb_path, "JPEG", quality=THUMBNAIL_JPEG_QUALITY, optimize=True)

            return full_path
        except Exception as e:
            print(f"Error optimizing image: {e}")
            return ""

    @classmethod
    def get_thumbnail_path(cls, full_image_path):
        """Derives or generates the thumbnail path for a given image."""
        if not full_image_path or not os.path.exists(full_image_path):
            return None
        
        base_name = os.path.basename(full_image_path)
        thumb_name = f"thumb_{base_name}"
        thumb_path = os.path.join(IMG_THUMBNAILS_DIR, thumb_name)
        
        if os.path.exists(thumb_path):
            return thumb_path
        
        # If thumbnail doesn't exist, create it on-the-fly
        try:
            with Image.open(full_image_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail((THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION), Image.Resampling.LANCZOS)
                img.save(thumb_path, "JPEG", quality=THUMBNAIL_JPEG_QUALITY)
            return thumb_path
        except Exception:
            return full_image_path

    @classmethod
    def load_tk_image(cls, image_path, size=(100, 100), placeholder_text="👤"):
        """
        Loads an image scaled to `size` and returns a Tkinter-compatible PhotoImage.
        Uses in-memory cache to ensure smooth rendering and avoid garbage collection.
        If file doesn't exist, returns a beautifully generated placeholder card.
        """
        cache_key = f"{image_path}_{size[0]}x{size[1]}_{placeholder_text}"
        if cache_key in cls._tk_cache:
            return cls._tk_cache[cache_key]

        try:
            if image_path and os.path.exists(image_path):
                with Image.open(image_path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    # Fit within bounds with LANCZOS
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    cls._tk_cache[cache_key] = photo
                    return photo
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")

        # Fallback to generated placeholder avatar
        photo = cls._create_placeholder(size, placeholder_text)
        cls._tk_cache[cache_key] = photo
        return photo

    @classmethod
    def _create_placeholder(cls, size, text):
        """Draws a clean, modern flat avatar placeholder with initials or icon."""
        img = Image.new("RGB", size, color="#f1f5f9") # Light slate background
        draw = ImageDraw.Draw(img)
        w, h = size

        # Border
        draw.rectangle([0, 0, w - 1, h - 1], outline="#cbd5e1", width=1)

        # Draw circle silhouette in the middle
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#e2e8f0", outline="#94a3b8", width=1)

        # Draw simple stylized figure or text
        try:
            draw.text((cx, cy), text, fill="#64748b", anchor="mm")
        except Exception:
            pass

        return ImageTk.PhotoImage(img)

    @classmethod
    def clear_cache(cls):
        """Clears in-memory Tkinter image references."""
        cls._tk_cache.clear()
