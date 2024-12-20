# src/services/evaluation_service.py
from typing import List, Dict, Any
import ollama
import json
from datetime import datetime
from models.evaluation_models import (
    AnswerPair,
    EvaluationResult,
    AnswersEvaluationRequest
)
from utils.exceptions import ValidationError, LLMServiceError
from utils.logger import logger, log_async_function_call

class EvaluationService:
    def __init__(self):
        self.model = "llama3.2-vision"
        self.temperature = 0.2
        self.top_p = 0.1

    def _get_evaluation_prompt(self, expected_answer: str, student_answer: str) -> str:
        """Generate the evaluation prompt with few-shot examples."""
        return f"""You are an AI assistant tasked with comparing student answers with key answers and provide a precise evaluation score (0-100) indicating how well the actual answer 
                 matches the expected answer semantically. Use the examples below as guidance.

Example 1 (10% similarity):
Key answer: "The Big Bang Theory explains that the universe began as a singularity, which then rapidly expanded, leading to the formation of matter, galaxies, and eventually stars and planets."
Student answer: "The Earth is part of the Milky Way galaxy, which contains billions of stars and planets."
Result: 10% semantically similar.

Example 2 (30% similarity):
Key answer: "According to the Big Bang Theory, the universe expanded from an extremely hot and dense state approximately 13.8 billion years ago, giving rise to galaxies, stars, and planets."
Student answer: "Stars and planets formed from clouds of gas and dust, with gravity playing a key role in their creation and development over billions of years."
Result: 30% semantically similar.

Example 3 (50% similarity):
Key answer: "The Big Bang Theory explains the origin of the universe as a rapid expansion from a very hot, dense singularity that gave rise to galaxies, stars, and planets, forming the universe as we know it."
Student answer: "The universe began with a massive expansion from a singularity, and over time, galaxies, stars, and planets formed, shaping the cosmos."
Result: 50% semantically similar.

Example 4 (70% similarity):
Key answer: "The Big Bang Theory proposes that the universe began as a singular point that expanded rapidly, resulting in the cooling and formation of matter, which later formed stars and galaxies."
Student answer: "The Big Bang was a rapid expansion of a singular point, leading to the cooling of the universe and the creation of matter, stars, and galaxies."
Result: 70% semantically similar.

Example 5 (90% similarity):
Key answer: "The Big Bang Theory states that the universe began as an extremely hot and dense singularity that expanded, cooling over time and allowing matter to form stars, galaxies, and the large-scale structure we see today."
Student answer: "According to the Big Bang Theory, the universe started from a very hot, dense singularity, expanding and cooling over time, leading to the formation of stars, galaxies, and the universe's structure."
Result: 90% semantically similar.

Now, evaluate the following:
Key answer: "{expected_answer}"
Student answer: "{student_answer}"

What is the percentage of semantic similarity between the key answer and the student answer? Please provide reasoning and the percentage similarity score.

Return the result in the following JSON format without prefixing with the word 'json':
{{"reasoning": "...", "score": ...}}"""

    async def _evaluate_single_answer(self, pair: AnswerPair, pair_index: int) -> EvaluationResult:
        """Evaluate a single answer pair."""
        try:
            prompt = self._get_evaluation_prompt(pair.expected_answer, pair.student_answer)
            
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': self.temperature,
                    'top_p': self.top_p
                }
            )

            return self._process_llm_response(response, pair_index)
            
        except Exception as e:
            logger.error(f"Error evaluating answer pair {pair_index}: {str(e)}")
            return EvaluationResult(
                score=0,
                justification=f"Error: Failed to evaluate answer pair {pair_index}"
            )

    def _process_llm_response(self, response: Dict[str, Any], pair_index: int) -> EvaluationResult:
        """Process and validate LLM response."""
        try:
            content = response.get('message', {}).get('content', '').strip()
            evaluation = json.loads(content)
            
            score = float(evaluation.get('score', 0))
            if not 0 <= score <= 100:
                raise ValueError("Score must be between 0 and 100")

            return EvaluationResult(
                score=score,
                justification=evaluation.get('reasoning', 'No reasoning provided')
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for pair {pair_index}: {str(e)}")
            return EvaluationResult(
                score=0,
                justification="Error: Failed to parse evaluation response"
            )
        except ValueError as e:
            logger.error(f"Invalid score in LLM response for pair {pair_index}: {str(e)}")
            return EvaluationResult(
                score=0,
                justification=f"Error: Invalid score - {str(e)}"
            )

    def _validate_request(self, request: AnswersEvaluationRequest) -> None:
        """Validate the evaluation request."""
        if request.number_of_pairs != len(request.answer_pairs):
            raise ValidationError(
                f"number_of_pairs ({request.number_of_pairs}) does not match actual pairs count ({len(request.answer_pairs)})"
            )

    def _prepare_response_metadata(self, results: List[EvaluationResult], total_pairs: int) -> Dict[str, Any]:
        """Prepare metadata for the response."""
        return {
            "total_pairs": total_pairs,
            "successful_evaluations": len([r for r in results if r.score > 0]),
            "average_score": sum(r.score for r in results) / len(results) if results else 0,
            "timestamp": datetime.utcnow().isoformat()
        }

    @log_async_function_call
    async def evaluate_answers(self, request: AnswersEvaluationRequest) -> Dict[str, Any]:
        """
        Evaluate multiple answer pairs and return results with metadata.
        """
        try:
            self._validate_request(request)
            
            logger.info("Starting answer evaluation", {
                "number_of_pairs": request.number_of_pairs
            })

            # Evaluate all answers
            results = []
            for i, pair in enumerate(request.answer_pairs, 1):
                logger.info(f"Processing pair {i}/{request.number_of_pairs}")
                result = await self._evaluate_single_answer(pair, i)
                results.append(result)

            # Prepare response
            response = {
                "results": results,
                "metadata": self._prepare_response_metadata(results, request.number_of_pairs)
            }

            logger.info("Answer evaluation completed", {
                "successful_evaluations": response["metadata"]["successful_evaluations"],
                "average_score": response["metadata"]["average_score"]
            })

            return response

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in answer evaluation: {str(e)}")
            raise LLMServiceError(f"Answer evaluation failed: {str(e)}")