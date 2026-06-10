from app.modules.catalog.model import Chapter, GradeLevel, Subject
from app.modules.custom_tutor.model import CustomTutorMessage


def language_rule(language: str) -> str:
    if language == "bn":
        return "Reply in Bangla unless the student asks for another language."

    return "Reply in English unless the student asks for another language."


def context_text(
    grade: GradeLevel | None,
    subject: Subject | None,
    chapter: Chapter | None,
) -> str:
    lines = []

    if grade:
        lines.append(f"Grade: {grade.name}")

    if subject:
        lines.append(f"Subject: {subject.name}")

    if chapter:
        lines.append(f"Chapter: {chapter.title}")

    if not lines:
        return "No specific grade, subject, or chapter was selected."

    return "\n".join(lines)


def custom_tutor_messages(
    language: str,
    grade: GradeLevel | None,
    subject: Subject | None,
    chapter: Chapter | None,
    history: list[CustomTutorMessage],
    student_message: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": f"""
You are Learniverse Custom Tutor, a helpful AI study assistant for students.

This is a free chat window, like ChatGPT or Gemini.
The student may ask questions outside the selected chapter.
You may help with general study questions, school subjects, coding concepts, writing help, exam preparation, and explanations.

Selected learning context:
{context_text(grade, subject, chapter)}

Rules:
- Be clear, friendly, and student-friendly.
- Do not claim that you are restricted to only one chapter.
- If a grade/subject/chapter is selected, use it as helpful context, not as a hard limit.
- If the student asks an unsafe, harmful, or inappropriate request, refuse briefly and redirect to safe learning help.
- Do not give instructions for dangerous activities.
- For math, show steps.
- For coding, explain simply and give safe examples.
- {language_rule(language)}
""".strip(),
        }
    ]

    for item in history:
        messages.append(
            {
                "role": "assistant" if item.role == "assistant" else "user",
                "content": item.content,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": student_message,
        }
    )

    return messages