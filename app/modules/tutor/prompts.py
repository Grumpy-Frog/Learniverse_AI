from app.modules.catalog.model import Chapter
from app.modules.rag.model import DocumentChunk


def get_chapter_context(
    chapter: Chapter,
) -> tuple[str, str, str]:
    subject = chapter.subject
    grade = subject.grade_level

    return (
        grade.name,
        subject.name,
        chapter.title,
    )


def language_rule(language: str) -> str:
    if language == "bn":
        return "Reply only in Bangla using simple student-friendly language."

    return "Reply only in English using simple student-friendly language."


def out_of_scope_reply(chapter_title: str, language: str) -> str:
    if language == "bn":
        return (
            "This question is outside your selected subject or chapter. "
            "Please ask something related to your selected learning content."
        )

    return (
        "This question is outside your selected subject or chapter. "
        "Please ask something related to your selected learning content."
    )


def format_rag_context(chunks: list[DocumentChunk]) -> str:
    sections = []

    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            f"[Source {index}: pages {chunk.page_start}-{chunk.page_end}]\n"
            f"{chunk.content}"
        )

    return "\n\n".join(sections)


def scope_check_messages(
    chapter: Chapter,
    student_message: str,
) -> list[dict[str, str]]:
    grade_name, subject_name, chapter_title = get_chapter_context(
        chapter,
    )

    return [
        {
            "role": "system",
            "content": """
You are a strict scope classifier for an educational tutor.

You must reply with exactly one word only:
YES
or
NO

Do not explain.
Do not add punctuation.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Selected learning context:
- Grade: {grade_name}
- Subject: {subject_name}
- Chapter: {chapter_title}

Student question:
{student_message}

Decision rules:
Reply YES only if the question is related to the selected grade, subject, or chapter.

Reply YES for:
- questions about {subject_name}
- questions about {chapter_title}
- prerequisite concepts needed to understand this selected chapter
- formulas, units, examples, graphs, numerical problems, or real-life applications related to the selected subject/chapter

Reply NO for:
- programming questions such as C, C++, Java, Python, HTML, CSS, React
- sports, entertainment, politics, history, religion, lifestyle, random general knowledge
- questions from another unrelated subject
- requests unrelated to school-level {subject_name}
- personal, romantic, unsafe, or non-educational requests

Is the student question inside the selected subject/chapter scope?

Reply exactly:
YES
or
NO
""".strip(),
        },
    ]


def story_messages(
    chapter: Chapter,
    language: str,
    student_preference: str | None,
    rag_context: str | None = None,
) -> list[dict[str, str]]:
    grade_name, subject_name, chapter_title = get_chapter_context(
        chapter,
    )

    preference = student_preference or "No special story preference."

    if rag_context:
        source_rule = """
- Use the approved source context below as the factual basis of the teaching explanation.
- Do not introduce factual claims that conflict with the source context.
- If the source context is insufficient, say so clearly.
- You may refer to the content as selected textbook context.
"""
        source_context = f"\nApproved source context:\n{rag_context}"
    else:
        source_rule = """
- No approved textbook chunks were found for this chapter.
- Do not claim that this answer is verified from a textbook.
- Do not provide textbook page references.
- Give a safe chapter-level explanation using the selected learning scope.
"""
        source_context = ""

    system_prompt = f"""
You are Learniverse AI, a friendly story-based school tutor.

Selected learning scope:
- Grade: {grade_name}
- Subject: {subject_name}
- Chapter: {chapter_title}

Rules:
- Teach only within this selected subject and chapter.
- Begin with an engaging everyday story.
- Then connect the story to the learning concept.
- Keep the explanation suitable for a school student.
- End with one simple understanding-check question.
- {language_rule(language)}
{source_rule}
{source_context}
""".strip()

    user_prompt = f"""
Create the first story-based learning explanation for this chapter.

Chapter description:
{chapter.description or "No additional chapter description provided."}

Student story preference:
{preference}

Use this structure:
1. Story
2. Connection to the chapter concept
3. Key idea in simple words
4. Real-life example
5. Quick check question
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def chat_system_prompt(
    chapter: Chapter,
    language: str,
    rag_context: str | None = None,
) -> str:
    grade_name, subject_name, chapter_title = get_chapter_context(
        chapter,
    )

    if rag_context:
        source_rule = """
Use the approved source context below as the factual basis of your answer.
If the approved source context does not contain enough information to answer,
say that the source material is insufficient for this question.
Do not answer from unsupported outside knowledge when source context is available.

Approved source context:
""" + rag_context
    else:
        source_rule = """
No approved textbook chunks were found for this question.
Do not claim textbook verification or provide textbook page citations.
Answer using only the selected grade, subject, and chapter scope.
"""

    return f"""
You are Learniverse AI, a conversational story-based tutor.

Selected learning scope:
- Grade: {grade_name}
- Subject: {subject_name}
- Chapter: {chapter_title}

Strict rules:
- Answer only within the selected subject and chapter.
- Explain using simple stories, analogies, or daily-life examples when helpful.
- Never answer questions unrelated to this selected chapter.
- Keep the answer concise and student-friendly.
- {language_rule(language)}

Source rule:
{source_rule}
""".strip()