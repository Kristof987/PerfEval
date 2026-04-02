import json

class BaseMetadata:
    def __init__(self, question, answer, question_type, competence, evaluator_role):
        self.question = question
        self.answer = answer
        self.question_type = question_type
        self.competence = competence
        self.evaluator_role = evaluator_role

    def to_json(self) -> str:
        """Serialize all fields to a JSON string."""
        return json.dumps({
            "question": self.question,
            "answer": self.answer,
            "question_type": self.question_type,
            "competence": self.competence,
            "evaluator_role": self.evaluator_role,
        }, ensure_ascii=False)
