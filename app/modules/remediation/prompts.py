from app.modules.catalog.model import Topic
from app.modules.rag.model import DocumentChunk


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
        return "Write all student-facing text in Bangla."

    return "Write all student-facing text in English."


def remediation_generation_messages(
    topic: Topic,
    language: str,
    weakness_label: str,
    evidence: str,
    chunks: list[DocumentChunk],
) -> list[dict[str, str]]:
    rag_context = format_rag_context(chunks)

    return [
        {
            "role": "system",
            "content": """
You are Learniverse AI remediation generator.
Return only valid JSON.
Generate focused remediation only for the given weakness.
Use the approved source context as the factual basis.
Do not include markdown or extra text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Selected topic:
{topic.title}

Topic description:
{topic.description or "Not provided"}

Detected weakness:
{weakness_label}

Evidence from student's diagnostic answers:
{evidence}

Approved source context:
{rag_context}

Rules:
- Do not repeat the whole topic.
- Focus only on the detected weakness.
- Keep explanation short and student-friendly.
- Include one guided example.
- Include one partially solved problem.
- Include one recheck question.
- next_action must be one of:
  continue, retry, practice_more, move_back
- {language_instruction(language)}

Return exactly this JSON shape:
{{
  "weakness_statement": "what caused the mistake",
  "micro_lesson": "short focused explanation",
  "guided_example": "worked example",
  "partially_solved_problem": "supported practice problem",
  "recheck_question": "one question to check improvement",
  "expected_answer": "expected answer to the recheck question",
  "next_action": "retry"
}}
""".strip(),
        },
    ]


def recheck_evaluation_messages(
    language: str,
    weakness_label: str,
    recheck_question: str,
    expected_answer: str,
    student_answer: str,
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
You are Learniverse AI remediation recheck evaluator.
Return only valid JSON.
Evaluate only the given answer against the expected answer.
Do not include markdown or text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Weakness being rechecked:
{weakness_label}

Recheck question:
{recheck_question}

Expected answer:
{expected_answer}

Student answer:
{student_answer}

Rules:
- score must be between 0 and 1.
- is_correct is true only when score is at least 0.7.
- next_action must be:
  continue if correct,
  retry if mostly wrong,
  practice_more if partially correct,
  move_back if the student lacks prerequisite understanding.
- {feedback_language}

Return exactly this JSON shape:
{{
  "is_correct": false,
  "score": 0.0,
  "feedback": "short feedback",
  "next_action": "retry"
}}
""".strip(),
        },
    ]