# src/services/image_service.py
from typing import List, Optional
from utils.logger import logger, log_async_function_call
from utils.exceptions import ImageProcessingError
from utils.helpers import encode_image, get_image_paths
from services.llm_service import LLMService
from config.settings import settings

class ImageService:
    def __init__(self):
        self.llm_service = LLMService()

    @log_async_function_call
    async def get_chapter_content(
        self,
        standard: str,
        subject: str,
        chapter: str
    ) -> str:
        """
        Get and process chapter content from images.
        """
        try:
            # Get image paths
            image_paths = get_image_paths(
                settings.IMAGE_INDEX_DIR,
                standard=standard,
                subject=subject,
                chapter=chapter
            )

            if not image_paths:
                logger.error("No images found", {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter
                })
                raise ValueError(f"No images found for chapter {chapter}")

            # Process images
            contents = []
            for path in image_paths:
                content = await self._process_single_image(path)
                if content:
                    contents.append(content)

            if not contents:
                raise ImageProcessingError("Failed to extract content from images")

            return "\n\n".join(contents)

        except Exception as e:
            logger.error("Failed to get chapter content", {
                "error": str(e),
                "standard": standard,
                "subject": subject,
                "chapter": chapter
            })
            raise

    @log_async_function_call
    async def _process_single_image(self, image_path: str) -> Optional[str]:
        """
        Process a single image to extract content.
        """
        try:
            # Encode image
            image_base64 = encode_image(image_path)
            if not image_base64:
                return None

            # Process with LLM
            content = await self.llm_service.process_image(
                image_base64,
                "Extract and summarize the key educational content from this image."
            )

            return content

        except Exception as e:
            logger.error("Failed to process image", {
                "error": str(e),
                "image_path": image_path
            })
            return None