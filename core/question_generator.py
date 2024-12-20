# src/core/question_generator.py
import json
from typing import List, Dict, Any
import logging
from services.llm_service import LLMService
from models.data_models import QuestionRequest
from utils.validators import validate_questions
from utils.helpers import format_prompt

logger = logging.getLogger(__name__)

class QuestionGenerator:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_questions(self, request: QuestionRequest, context: str) -> Dict[str, Any]:
        try:
            # Format prompt with request parameters and context
            prompt = format_prompt(request, context)
            
            # Generate questions using LLM
            response = await self.llm_service.generate_response([
                {"role": "system", "content": "You are an expert education assessment creator."},
                {"role": "user", "content": prompt}
            ])
            
            # Process and validate response
            questions = self._process_response(response)
            validate_questions(questions, request.question_distribution)
            
            return {
                "title": f"{request.standard} {request.subject} Assessment - {request.chapter}",
                "questions": questions
            }
            
        except Exception as e:
            logger.error(f"Error in question generation: {str(e)}")
            raise
    
    def _process_response(self, response: Dict) -> List[Dict]:
        # Process LLM response and convert to question format
        try:
            content = response.get('message', {}).get('content', '')
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error processing LLM response: {str(e)}")
            raise ValueError("Invalid response format from LLM")