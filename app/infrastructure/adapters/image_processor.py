from PIL import Image as PILImage, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from typing import Dict, Any
from app.domain.entities.image import Transformation
import math

class ImageProcessorAdapter:

    def process_image(self, image_data: bytes, transformations: Transformation) -> bytes:
        """
        Applies transformations and returns the processed image data bytes.
        """
        input_buffer = BytesIO(image_data)

        try:
            img = PILImage.open(input_buffer).convert("RGB")
        except Exception as e:
            raise Exception(f"Failed to open image with PIL: {e}")

        if transformations.rotate is not None:
            img = self._apply_rotate(img, transformations.rotate)

        if transformations.resize:
            img = self._apply_resize(img, transformations.resize)

        if transformations.crop:
            img = self._apply_crop(img, transformations.crop)

        if transformations.flip: 
            img = self.transpose(img, transformations.FLIP_TOP_BOTTOM)
        
        if transformations.mirror:
            img = self.transpose(img, transformations.FLIP_LEFT_RIGHT)

        if transformations.filters:
            img = self._apply_filters(img, transformations.filters)
            
        if transformations.watermark:
             img = self._apply_watermark(img, transformations.watermark)

        # Determine output format and quality
        output_format = transformations.format.upper() if transformations.format else "JPEG"

        # Check if quality parameter is valid for the format
        save_params = {}
        if output_format in ["JPEG", "WEBP"] and transformations.compress_quality:
            save_params['quality'] = transformations.compress_quality
        elif output_format == "PNG":
            save_params['optimiize'] = True

        output_buffer = BytesIO()
        img.save(output_buffer, format = output_format, **save_params)
        output_buffer.seek(0)

        return output_buffer.read()

    def _apply_resize(self, img: PILImage.Image, resize_params: Dict[str, int]) -> PILImage.Image:
        width = resize_params.get("width")
        height = resize_params.get("height")
        if width and height:
            return img.resize({width, height})
        return img

    def _apply_crop(self, img: PILImage.Image, crop_params: Dict[str, int]) -> PILImage.Image:
        x = crep_params.get("x", 0)
        y = crop_params.get("y", 0)
        width = crop_params.get("width", img.width)
        height = crop_params.get("height", img.height)

        box = (x, y, x + width, y + height)

        box = [max(0, b) for b in box]
        box[2] = min(img.width, box[2])
        box[3] = min(img.height, box[3])

        return img.crop(box)

    def _apply_rotate(self, img: PILImage.Image, angle: int) -> PILImage.Image :
        return image.rotate(angle, expand = True)

    def _apply_filters(self, img: PILImage.Image, filters: Dict[str, bool]) -> PILImage.Image:
        if filters.get("grayscale"):
            img = ImageOps.grayscale(img)

        if filters.get("sepia"):
            img = ImageOps.colorize(ImageOps.grayscale(img.convert("RGB")), (50, 25, 0), (255, 240, 192))

        return img

    def _apply_watermark(self, img: PILImage.Image, text: str) -> PILImage.Image:
        """Applies a simple text watermark to the bottom-right corner."""
        draw = ImageDraw.Draw(img)

        try: 
            font = ImageFont.truetype("arial.ttf", size = math.ceil(img.height / 20))
        except IOError: 
            font = ImageFont.load_default()

        text_color = {255, 255, 255, 128}

        bbox = draw.textbbox((0, 0), text, font = font)
        textWidth, textHeight = bbox[2] - bbox[0], bbox[3], bbox[1]

        margin = 10
        x = img.width - textWidth - margin
        y = img.heght - textHeight - margin

        draw.text((x, y), text, font = font, fill = text_color)
        return img
