# src/services/question_service.py
import datetime
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
    def calculate_difficulty_distribution(self, total_type_questions: int, request: QuestionRequest) -> Dict[str, int]:
        """
        Calculate how many questions of each difficulty level to generate for a specific question type.
        
        Args:
            total_type_questions: Total number of questions needed for this type
            request: QuestionRequest containing the overall difficulty distribution
            
        Returns:
            Dict[str, int]: Distribution of questions by difficulty level
        """
        # Get the global difficulty distribution totals
        total_questions = request.difficulty_distribution.total_questions()
        total_easy = request.difficulty_distribution.easy
        total_medium = request.difficulty_distribution.medium
        total_hard = request.difficulty_distribution.hard
        
        logger.info(f"Calculating distribution for {total_type_questions} questions", {
            "total_questions": total_questions,
            "requested_distribution": {
                "easy": total_easy,
                "medium": total_medium,
                "hard": total_hard
            }
        })

        # Initialize distribution with floor values
        distribution = {
            "Easy": (total_easy * total_type_questions) // total_questions,
            "Medium": (total_medium * total_type_questions) // total_questions,
            "Hard": (total_hard * total_type_questions) // total_questions
        }
        
        # Calculate remaining questions to distribute
        allocated = sum(distribution.values())
        remaining = total_type_questions - allocated
        
        if remaining > 0:
            # Calculate fractional parts
            fractions = {
                "Easy": (total_easy * total_type_questions / total_questions) % 1,
                "Medium": (total_medium * total_type_questions / total_questions) % 1,
                "Hard": (total_hard * total_type_questions / total_questions) % 1
            }
            
            # Distribute remaining questions based on largest fractional parts
            while remaining > 0:
                max_diff = max(fractions.items(), key=lambda x: x[1])
                distribution[max_diff[0]] += 1
                fractions[max_diff[0]] = 0  # Mark as used
                remaining -= 1
        
        # Ensure minimum of 1 question per difficulty if total_type_questions >= 3
        if total_type_questions >= 3:
            while any(count == 0 for count in distribution.values()):
                # Find difficulty with 0 questions
                zero_diff = next(diff for diff, count in distribution.items() if count == 0)
                # Find difficulty with most questions
                max_diff = max(distribution.items(), key=lambda x: x[1])[0]
                
                # Transfer one question
                distribution[zero_diff] += 1
                distribution[max_diff] -= 1
        
        logger.info(f"Calculated distribution", {
            "type_questions": total_type_questions,
            "distribution": distribution,
            "total_allocated": sum(distribution.values())
        })

        # Final validation
        if sum(distribution.values()) != total_type_questions:
            logger.error("Invalid distribution calculation", {
                "expected_total": total_type_questions,
                "actual_total": sum(distribution.values()),
                "distribution": distribution
            })
            raise QuestionGenerationError(
                "Invalid difficulty distribution calculation",
                details=[f"Expected {total_type_questions} questions, got {sum(distribution.values())}"]
            )

        return distribution

    async def generate_questions(self, request: QuestionRequest) -> QuestionResponse:
        """
        Generate questions based on request parameters and distributions.
        
        Args:
            request: QuestionRequest containing all parameters and distributions
                
        Returns:
            QuestionResponse containing generated questions and metadata
                
        Raises:
            QuestionGenerationError: If question generation fails or distributions don't match
            ValidationError: If request parameters are invalid
        """
        try:
            # Validate total distributions match
            if request.question_distribution.total_questions() != request.difficulty_distribution.total_questions():
                raise ValidationError(
                    "Distribution mismatch",
                    details=["Question type total does not match difficulty level total"]
                )

            # Get image paths
            base_path = f"/Users/developer/Desktop/que/Root/Pdf/{request.language}/Teacher/{request.syllabus}/{request.standard}/{request.subject}/{request.chapter}"
            image_paths = get_images(base_path, [".png", ".jpg", ".jpeg"])

            if not image_paths:
                raise QuestionGenerationError(
                    "No images found for the specified chapter",
                    details=[f"No images found in path: {base_path}"]
                )

            # Accumulate context from all images
            logger.info("Processing images to extract context")
            accumulated_context = ""
            
            for image_path in image_paths:
                image_data = encode_image_to_base64(image_path)
                if image_data:
                    content = await self._get_image_context(image_data)
                    if content:
                        accumulated_context += f"{content}\n\n"

            if not accumulated_context.strip():
                raise QuestionGenerationError(
                    "Failed to extract context from images",
                    details=["No meaningful content could be extracted from the images"]
                )

            logger.info("Starting question generation with accumulated context")
            
            # Generate questions for each type
            all_questions = []
            questions_generated = {"Easy": 0, "Medium": 0, "Hard": 0}
            
            question_types = {
                QuestionType.MCQ.value: request.question_distribution.multiple_choice,
                QuestionType.MSQ.value: request.question_distribution.multiple_select,
                QuestionType.SDQ.value: request.question_distribution.short_descriptive,
                QuestionType.LDQ.value: request.question_distribution.long_descriptive
            }
            
            for q_type, total_count in question_types.items():
                if total_count > 0:
                    logger.info(f"Processing question type: {q_type}", {
                        "total_count": total_count,
                        "current_totals": questions_generated
                    })
                    
                    # Calculate difficulty distribution for this type
                    type_difficulties = self.calculate_difficulty_distribution(total_count, request)
                    
                    # Generate questions for each difficulty level
                    for difficulty, count in type_difficulties.items():
                        if count > 0:
                            logger.info(f"Generating questions", {
                                "type": q_type,
                                "difficulty": difficulty,
                                "count": count
                            })
                            
                            questions = await self._generate_questions_for_type(
                                accumulated_context,
                                q_type,
                                count,
                                request,
                                difficulty
                            )
                            
                            if len(questions) != count:
                                raise QuestionGenerationError(
                                    f"Incorrect number of {difficulty} {q_type} questions generated",
                                    details=[f"Expected {count}, got {len(questions)}"]
                                )
                            
                            all_questions.extend(questions)
                            questions_generated[difficulty] += len(questions)
                            
                            logger.info(f"Successfully generated questions", {
                                "type": q_type,
                                "difficulty": difficulty,
                                "count": len(questions),
                                "running_total": questions_generated
                            })
            
            # Validate final distribution matches request
            total_generated = sum(questions_generated.values())
            expected_total = request.question_distribution.total_questions()
            
            if total_generated != expected_total:
                raise QuestionGenerationError(
                    "Generated questions count mismatch",
                    details=[
                        f"Expected total: {expected_total}",
                        f"Generated total: {total_generated}",
                        f"Distribution: {questions_generated}"
                    ]
                )
            
            # Create and return response
            return QuestionResponse(
                title=f"{request.standard} {request.subject} - {request.chapter}",
                questions=all_questions,
                metadata={
                    "request_id": request.request_id,
                    "total_questions": len(all_questions),
                    "distribution": questions_generated,
                    "subject": request.subject,
                    "chapter": request.chapter,
                    "standard": request.standard,
                    "language": request.language,
                    "syllabus": request.syllabus
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Error generating questions", {
                "error": str(e),
                "request_id": request.request_id
            })
            raise