# src/services/llm_service.py
import ollama
from typing import List, Dict, Any, Optional
from config.settings import settings
from utils.logger import logger, log_async_function_call
from utils.exceptions import LLMServiceError

class LLMService:
    def __init__(self):
        self.model = settings.LLM_MODEL
        self.max_retries = settings.MAX_RETRIES

    @log_async_function_call
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate response from the LLM model.
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": -1
                }
            )
            
            return response
            
        except Exception as e:
            logger.error("LLM response generation failed", {
                "error": str(e),
                "model": self.model,
                "message_count": len(messages)
            })
            raise LLMServiceError(f"Failed to generate LLM response: {str(e)}")

    @log_async_function_call
    async def process_image(
        self,
        image_base64: str,
        prompt: str
    ) -> Optional[str]:
        """
        Process image using the vision model.
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_base64]
                }]
            )
            
            return response.get('message', {}).get('content', '')
            
        except Exception as e:
            logger.error("Image processing failed", {
                "error": str(e),
                "model": self.model
            })
            raise LLMServiceError(f"Failed to process image: {str(e)}")