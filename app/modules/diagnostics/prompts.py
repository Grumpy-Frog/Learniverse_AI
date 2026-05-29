from typing import get_args

from app.modules.catalog.model import Topic
from app.modules.diagnostics.schema import SkillLabel
from app.modules.rag.model import DocumentChunk


ALLOWED_SKILLS = ", ".join(get_args(SkillLabel))


def format_rag_context(chunks: list[DocumentChunk]) -> str:
    sections = []

    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            f"[Source {index}: pages {chunk.page_start}-{chunk.page_end}]\n"
            f"{chunk.content}"
        )

    return "\n\n".join(sections)


def language_instruction(language: str) -> str:
    if language == "bn":
        return "Write the question and explanation in Bangla."

    return "Write the question and explanation in English."


def understanding_check_messages(
    topic: Topic,
    language: str,
    chunks: list[DocumentChunk],
) -> list[dict[str, str]]:
    context = format_rag_context(chunks)

    return [
        {
            "role": "system",
            "content": """
You are Learniverse AI assessment generator.
Return only valid JSON.
Generate questions only from the supplied approved source context.
Do not include markdown or extra text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Generate exactly one short-answer understanding-check question.

Topic:
{topic.title}

Topic description:
{topic.description or "Not provided"}

Approved source context:
{context}

Rules:
- The question should be short and simple.
- It should check immediate understanding after a tutor explanation.
- It must be a short_answer question.
- Choose one skill_label from this exact allowed list:
  {ALLOWED_SKILLS}
- {language_instruction(language)}

Return this exact JSON shape:
{{
  "questions": [
    {{
      "question_type": "short_answer",
      "question_text": "question here",
      "options": null,
      "correct_answer": "expected answer here",
      "evaluation_rubric": "what makes an answer correct",
      "skill_label": "one_allowed_skill_label",
      "explanation": "simple explanation"
    }}
  ]
}}
""".strip(),
        },
    ]


def diagnostic_quiz_messages(
    topic: Topic,
    language: str,
    chunks: list[DocumentChunk],
) -> list[dict[str, str]]:
    context = format_rag_context(chunks)

    return [
        {
            "role": "system",
            "content": """
You are Learniverse AI diagnostic assessment generator.
Return only valid JSON.
Generate questions only from the supplied approved source context.
Do not include markdown or extra text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Generate exactly five diagnostic questions for the selected topic.

Topic:
{topic.title}

Topic description:
{topic.description or "Not provided"}

Approved source context:
{context}

Rules:
- Generate exactly 3 mcq questions and 2 short_answer questions.
- Questions must identify precise sub-skill weaknesses.
- Do not ask anything outside the supplied context.
- Each MCQ must contain exactly four options: A, B, C and D.
- For MCQ, correct_answer must be the option key only, such as "B".
- For short_answer, options must be null.
- For short_answer, include a clear evaluation_rubric.
- Choose each skill_label from this exact list:
  {ALLOWED_SKILLS}
- {language_instruction(language)}

Return this exact JSON shape:
{{
  "questions": [
    {{
      "question_type": "mcq",
      "question_text": "question here",
      "options": {{
        "A": "option A",
        "B": "option B",
        "C": "option C",
        "D": "option D"
      }},
      "correct_answer": "B",
      "evaluation_rubric": null,
      "skill_label": "one_allowed_skill_label",
      "explanation": "why the answer is correct"
    }},
    {{
      "question_type": "short_answer",
      "question_text": "question here",
      "options": null,
      "correct_answer": "expected answer",
      "evaluation_rubric": "what a correct answer must contain",
      "skill_label": "one_allowed_skill_label",
      "explanation": "simple explanation"
    }}
  ]
}}
""".strip(),
        },
    ]


def short_answer_evaluation_messages(
    question_text: str,
    expected_answer: str,
    rubric: str,
    student_answer: str,
    skill_label: str,
    language: str,
) -> list[dict[str, str]]:
    feedback_language = (
        "Write feedback in Bangla."
        if language == "bn"
        else "Write feedback in English."
    )

    return [
        {
            "role": "system",
            "content": """
You are Learniverse AI answer evaluator.
Return only valid JSON.
Evaluate only against the given expected answer and rubric.
Do not include markdown or text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Question:
{question_text}

Expected answer:
{expected_answer}

Evaluation rubric:
{rubric}

Student answer:
{student_answer}

Skill being evaluated:
{skill_label}

Rules:
- Give score between 0 and 1.
- is_correct is true only when score is at least 0.7.
- If incorrect, detected_weakness must be exactly "{skill_label}".
- If correct, detected_weakness must be null.
- confidence must be low, medium or high.
- {feedback_language}

Return exactly this JSON shape:
{{
  "is_correct": false,
  "score": 0.0,
  "feedback": "feedback here",
  "detected_weakness": "{skill_label}",
  "confidence": "high"
}}
""".strip(),
        },
    ]