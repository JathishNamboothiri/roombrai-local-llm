# src/services/question_service.py
from typing import List, Dict, Any
import ollama
import json
from config import settings
from models.question_models import QuestionRequest, QuestionResponse, QuestionType
from utils.logger import logger, log_async_function_call
from utils.exceptions import ValidationError, QuestionGenerationError
from utils.helpers import encode_image_to_base64, get_images

class QuestionService:
    def __init__(self):
        self.model = settings.LLM_MODEL

    def _generate_prompt(
        self, 
        question_type: str, 
        count: int, 
        difficulty_level: str,
        language: str, 
        syllabus: str, 
        standard: str, 
        subject: str,
        chapter: str, 
        topic: str = None
    ) -> str:
        """Generate prompt for question generation."""
        prompt = f"""
        Generate EXACTLY {count} NEW {question_type} questions for {syllabus} {standard} {subject} at {difficulty_level} level.

        Chapter: {chapter}
        {f'Topic: {topic}' if topic else 'Scope: Entire chapter'}

        CRITICAL REQUIREMENTS:
        1. Generate EXACTLY {count} questions - no more, no less
        2. Each question must include all required fields
        3. All content must be in {language}
        """

        if question_type == QuestionType.MCQ.value:
            prompt += """
            Requirements:
            - Include clear and unambiguous question text
            - EXACTLY 4 options per question
            - Only ONE correct answer
            - All options must be plausible and related to the topic
            Format:
            {
                "type": "Multiple Choice",
                "difficulty": "Easy/Medium/Hard",
                "question": "Question text",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correct_answer": "Correct option"
            }
            """
        elif question_type == QuestionType.MSQ.value:
            prompt += """
            Requirements:
            - Include clear question text indicating multiple selections
            - EXACTLY 4 options per question
            - EXACTLY 2 correct answers
            - All options must be plausible and related to the topic
            Format:
            {
                "type": "Multiple Select",
                "difficulty": "Easy/Medium/Hard",
                "question": "Question text",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correct_answers": ["Correct option 1", "Correct option 2"]
            }
            """
        elif question_type == QuestionType.SDQ.value:
            prompt += """
            Requirements:
            - Questions should require 1-2 sentence answers
            - Include 3-5 relevant keywords
            - Answers should be concise and focused
            Format:
            {
                "type": "Short Descriptive Answer",
                "difficulty": "Easy/Medium/Hard",
                "question": "Question text",
                "answer": "1-2 sentence answer",
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
            }
            """
        else:  # Long Descriptive
            prompt += """
            Requirements:
            - Questions should require detailed explanations
            - Include 5-7 relevant keywords
            - Answers should be comprehensive paragraphs
            Format:
            {
                "type": "Long Descriptive Answer",
                "difficulty": "Easy/Medium/Hard",
                "question": "Question text",
                "answer": "Detailed paragraph answer",
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7"]
            }
            """

        return prompt

    async def _get_image_context(self, image_data: str) -> str:
        """Extract context from image using vision model."""
        response = ollama.chat(
            model=self.model,
            messages=[{
                'role': 'user',
                'content': "Extract the key points from this image to understand its context.",
                'images': [image_data]
            }]
        )
        return response.get('message', {}).get('content', '').strip()

    async def _generate_questions_for_type(
        self,
        context: str,
        question_type: str,
        count: int,
        request: QuestionRequest,
        difficulty_level: str
    ) -> List[Dict]:
        """Generate questions for a specific type and difficulty."""
        prompt = self._generate_prompt(
            question_type,
            count,
            difficulty_level,
            request.language,
            request.syllabus,
            request.standard,
            request.subject,
            request.chapter,
            request.topic
        )

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert in creating {question_type} questions at {difficulty_level} level. Generate EXACTLY {count} questions in proper JSON format."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nContext:\n{context}"
                }
            ]
        )

        try:
            content = response.get('message', {}).get('content', '').strip()
            questions = json.loads(content)
            if isinstance(questions, dict):
                questions = questions.get('questions', [])
            return [q for q in questions if q.get('type') == question_type]
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing response: {str(e)}")
            return []

    @log_async_function_call
    async def generate_questions(self, request: QuestionRequest) -> QuestionResponse:
        """Generate questions based on request parameters."""
        try:
            # Get image paths
            base_path = f"/Users/developer/Desktop/que/Root/Pdf/{request.language}/Teacher/{request.syllabus}/{request.standard}/{request.subject}/{request.chapter}"
            image_paths = get_images(base_path, [".png", ".jpg", ".jpeg"])

            if not image_paths:
                raise QuestionGenerationError("No images found for the specified chapter")

            # Accumulate context from all images
            accumulated_context = ""
            for image_path in image_paths:
                image_data = encode_image_to_base64(image_path)
                if image_data:
                    context = await self._get_image_context(image_data)
                    accumulated_context += f"{context}\n\n"

            if not accumulated_context:
                raise QuestionGenerationError("Failed to extract context from images")

            # Generate questions for each type and difficulty
            all_questions = []

            # Distribution of difficulties for each type
            question_types = {
                QuestionType.MCQ.value: request.question_distribution.multiple_choice,
                QuestionType.MSQ.value: request.question_distribution.multiple_select,
                QuestionType.SDQ.value: request.question_distribution.short_descriptive,
                QuestionType.LDQ.value: request.question_distribution.long_descriptive
            }

            difficulty_levels = ["Easy", "Medium", "Hard"]
            for q_type, count in question_types.items():
                if count > 0:
                    for difficulty in difficulty_levels:
                        # Calculate questions for this difficulty based on distribution
                        if difficulty == "Easy":
                            diff_count = (request.difficulty_distribution.easy * count) // request.question_distribution.total_questions()
                        elif difficulty == "Medium":
                            diff_count = (request.difficulty_distribution.medium * count) // request.question_distribution.total_questions()
                        else:
                            diff_count = (request.difficulty_distribution.hard * count) // request.question_distribution.total_questions()

                        if diff_count > 0:
                            questions = await self._generate_questions_for_type(
                                accumulated_context,
                                q_type,
                                diff_count,
                                request,
                                difficulty
                            )
                            all_questions.extend(questions)

            if not all_questions:
                raise QuestionGenerationError("Failed to generate questions")

            return QuestionResponse(
                title=f"{request.standard} {request.subject} Assessment - {request.chapter}",
                questions=all_questions,
                metadata={
                    "standard": request.standard,
                    "subject": request.subject,
                    "chapter": request.chapter,
                    "language": request.language,
                    "syllabus": request.syllabus,
                    "total_pages": len(image_paths),
                    "question_count": len(all_questions)
                }
            )

        except Exception as e:
            logger.error(f"Error in question generation: {str(e)}")
            raise QuestionGenerationError(str(e))