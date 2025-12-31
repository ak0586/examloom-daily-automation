"""
Question Selector Module (v2.0 - Single JSON Design)
Handles question selection and tracking with self-contained question objects.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class QuestionSelector:
    """Selects unused questions from self-contained JSON."""
    
    def __init__(self, questions_file: str, used_log_file: str):
        """
        Initialize the question selector.
        
        Args:
            questions_file: Path to questions.json (self-contained format)
            used_log_file: Path to used_questions.log
        """
        self.questions_file = Path(questions_file)
        self.used_log_file = Path(used_log_file)
        self.questions = self._load_questions()
        self.used_ids = self._load_used_ids()
        self._validate_questions()
    
    def _load_questions(self) -> list:
        """Load all questions from JSON file."""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            logger.info(f"Loaded {len(questions)} questions from {self.questions_file}")
            return questions
        except Exception as e:
            logger.error(f"Failed to load questions: {e}")
            raise
    
    def _validate_questions(self) -> None:
        """Validate that all questions have required fields."""
        required_fields = [
            'id', 'difficulty', 'question', 'options', 'answer', 
            'explanation', 'captions', 'descriptions', 'hashtags'
        ]
        
        for i, q in enumerate(self.questions):
            for field in required_fields:
                if field not in q:
                    raise ValueError(
                        f"Question at index {i} (ID: {q.get('id', 'unknown')}) "
                        f"missing required field: {field}"
                    )
            
            # Validate arrays
            if not isinstance(q['options'], list) or len(q['options']) != 4:
                raise ValueError(f"Question ID {q['id']}: options must be array of 4 items")
            
            if not isinstance(q['captions'], list) or len(q['captions']) == 0:
                raise ValueError(f"Question ID {q['id']}: captions must be non-empty array")
            
            if not isinstance(q['descriptions'], list) or len(q['descriptions']) == 0:
                raise ValueError(f"Question ID {q['id']}: descriptions must be non-empty array")
            
            if not isinstance(q['hashtags'], list) or len(q['hashtags']) == 0:
                raise ValueError(f"Question ID {q['id']}: hashtags must be non-empty array")
            
            # Validate answer is A, B, C, or D
            if q['answer'] not in ['A', 'B', 'C', 'D']:
                raise ValueError(f"Question ID {q['id']}: answer must be A, B, C, or D")
        
        logger.info("All questions validated successfully")
    
    def _load_used_ids(self) -> set:
        """Load IDs of used questions from log file."""
        if not self.used_log_file.exists():
            logger.info("No used questions log found, starting fresh")
            return set()
        
        try:
            with open(self.used_log_file, 'r') as f:
                used_ids = {int(line.strip()) for line in f if line.strip()}
            logger.info(f"Loaded {len(used_ids)} used question IDs")
            return used_ids
        except Exception as e:
            logger.error(f"Failed to load used IDs: {e}")
            return set()
    
    def get_next_question(self) -> Optional[Dict[Any, Any]]:
        """
        Get the next unused question with all metadata.
        
        Returns:
            Complete question dict with caption, description, hashtags or None
        """
        # Find unused questions
        unused = [q for q in self.questions if q['id'] not in self.used_ids]
        
        if not unused:
            logger.warning("All questions have been used!")
            return None
        
        # Return the first unused question (complete object)
        question = unused[0]
        logger.info(f"Selected question ID: {question['id']}")
        logger.debug(f"Question difficulty: {question['difficulty']}")
        logger.debug(f"Caption options: {len(question['captions'])}")
        logger.debug(f"Description options: {len(question['descriptions'])}")
        logger.debug(f"Hashtags: {len(question['hashtags'])}")
        
        return question
    
    def get_caption(self, question: Dict[str, Any], index: int = 0) -> str:
        """
        Get caption from question object.
        
        Args:
            question: Question dictionary
            index: Index of caption to use (default: 0)
            
        Returns:
            Caption string
        """
        captions = question['captions']
        if index >= len(captions):
            index = 0
        return captions[index]
    
    def get_description(self, question: Dict[str, Any], index: int = 0) -> str:
        """
        Get description from question object with hashtags appended.
        
        Args:
            question: Question dictionary
            index: Index of description to use (default: 0)
            
        Returns:
            Complete description with hashtags
        """
        # Generate description dynamically to place Answer AFTER Explanation
        # as per user request (to avoid spoilers on Facebook Reels)
        
        explanation = question['explanation']
        answer_letter = question['answer']
        
        # Get answer text from options
        options = question['options']
        answer_index = ord(answer_letter) - ord('A')
        answer_text = options[answer_index] if 0 <= answer_index < len(options) else ""
        
        # Construct the core message
        # Format: Explanation -> Answer -> CTA
        content = (
            f"📝 Solution:\n{explanation}\n\n"
            f"✅ Correct Answer: {answer_letter} ({answer_text})\n\n"
            f"Follow for daily practice! 📚"
        )
        
        hashtags = ' '.join(question['hashtags'])
        
        return f"{content}\n\n{hashtags}"
    
    def mark_as_used(self, question_id: int) -> None:
        """
        Mark a question as used.
        
        Args:
            question_id: ID of the question to mark
        """
        try:
            with open(self.used_log_file, 'a') as f:
                f.write(f"{question_id}\n")
            self.used_ids.add(question_id)
            logger.info(f"Marked question {question_id} as used")
        except Exception as e:
            logger.error(f"Failed to mark question as used: {e}")
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics."""
        total = len(self.questions)
        used = len(self.used_ids)
        remaining = total - used
        
        # Count by difficulty
        difficulty_counts = {}
        remaining_by_difficulty = {}
        
        for q in self.questions:
            diff = q['difficulty']
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            if q['id'] not in self.used_ids:
                remaining_by_difficulty[diff] = remaining_by_difficulty.get(diff, 0) + 1
        
        return {
            'total': total,
            'used': used,
            'remaining': remaining,
            'percentage_used': round((used / total * 100) if total > 0 else 0, 2),
            'by_difficulty': difficulty_counts,
            'remaining_by_difficulty': remaining_by_difficulty
        }
    
    def reset(self) -> None:
        """Reset the used questions log (use with caution!)."""
        if self.used_log_file.exists():
            self.used_log_file.unlink()
        self.used_ids = set()
        logger.warning("Reset used questions log - all questions available again")
    
    def get_question_by_id(self, question_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific question by ID.
        
        Args:
            question_id: ID of the question
            
        Returns:
            Question dict or None if not found
        """
        for q in self.questions:
            if q['id'] == question_id:
                return q
        return None
    
    def export_unused_questions(self, output_file: str) -> None:
        """
        Export unused questions to a new JSON file.
        
        Args:
            output_file: Path to output file
        """
        unused = [q for q in self.questions if q['id'] not in self.used_ids]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unused, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(unused)} unused questions to {output_file}")
