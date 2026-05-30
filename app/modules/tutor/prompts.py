from app.modules.catalog.model import Topic
from app.modules.rag.model import DocumentChunk


def get_topic_context(topic: Topic) -> tuple[str, str, str, str]:
    chapter = topic.chapter
    subject = chapter.subject
    grade = subject.grade_level

    return (
        grade.name,
        subject.name,
        chapter.title,
        topic.title,
    )


def language_rule(language: str) -> str:
    if language == "bn":
        return "Reply only in Bangla using simple student-friendly language."

    return "Reply only in English using simple student-friendly language."


def out_of_scope_reply(chapter_title: str, language: str) -> str:
    if language == "bn":
        return (
            "এই প্রশ্নটি আপনার নির্বাচিত বিষয় বা অধ্যায়ের বাইরে। "
            "অনুগ্রহ করে নির্বাচিত বিষয়, অধ্যায় বা টপিক সম্পর্কিত প্রশ্ন করুন।"
        )

    return (
        "This question is outside your selected subject or topic. "
        "Please ask something related to your selected learning content."
    )


def no_rag_context_reply(language: str) -> str:
    if language == "bn":
        return (
            "আপনার নির্বাচিত বিষয়ের জন্য অনুমোদিত পাঠ্যবইয়ের "
            "প্রাসঙ্গিক তথ্য পাওয়া যায়নি। RAG বন্ধ করে চেষ্টা করুন "
            "অথবা অ্যাডমিনকে সোর্স কনটেন্ট যুক্ত করতে বলুন।"
        )

    return (
        "I could not find approved textbook context for this question "
        "inside your selected topic. Turn off RAG or add the required "
        "source chunks first."
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
    topic: Topic,
    student_message: str,
) -> list[dict[str, str]]:
    grade_name, subject_name, chapter_title, topic_title = get_topic_context(topic)

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
- Topic: {topic_title}

Student question:
{student_message}

Decision rules:
Reply YES only if the question is related to the selected subject, chapter, or topic.

Reply YES for:
- questions about {subject_name}
- questions about {chapter_title}
- questions about {topic_title}
- prerequisite concepts needed to understand this selected topic
- formulas, units, examples, graphs, numerical problems, or real-life applications related to the selected subject

Reply NO for:
- programming questions such as C, C++, Java, Python, HTML, CSS, React
- sports, entertainment, politics, history, religion, lifestyle, random general knowledge
- questions from another subject
- requests unrelated to school-level {subject_name}
- personal, romantic, unsafe, or non-educational requests

Is the student question inside the selected subject/topic scope?

Reply exactly:
YES
or
NO
""".strip(),
        },
    ]


def story_messages(
    topic: Topic,
    language: str,
    student_preference: str | None,
    rag_context: str | None = None,
) -> list[dict[str, str]]:
    grade_name, subject_name, chapter_title, topic_title = get_topic_context(topic)
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
- Do not claim that this answer is verified from a textbook.
- Do not provide textbook page references.
- Textbook-grounded retrieval was not used for this response.
"""
        source_context = ""

    system_prompt = f"""
You are Learniverse AI, a friendly story-based school tutor.

Selected learning scope:
- Grade: {grade_name}
- Subject: {subject_name}
- Chapter: {chapter_title}
- Topic: {topic_title}

Rules:
- Teach only within this selected chapter and topic.
- Begin with an engaging everyday story.
- Then connect the story to the learning concept.
- Keep the explanation suitable for a school student.
- End with one simple understanding-check question.
- {language_rule(language)}
{source_rule}
{source_context}
""".strip()

    user_prompt = f"""
Create the first story-based learning explanation for this topic.

Topic description:
{topic.description or "No additional topic description provided."}

Learning objective:
{topic.learning_objective or "Understand the selected topic."}

Student story preference:
{preference}

Use this structure:
1. Story
2. Connection to the concept
3. Key idea in simple words
4. Real-life example
5. Quick check question
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def chat_system_prompt(
    topic: Topic,
    language: str,
    rag_context: str | None = None,
) -> str:
    grade_name, subject_name, chapter_title, topic_title = get_topic_context(topic)

    if rag_context:
        source_rule = """
Use the approved source context below as the factual basis of your answer.
If the approved source context does not contain enough information to answer,
say that the source material is insufficient for this question.
Do not answer from unsupported outside knowledge.

Approved source context:
""" + rag_context
    else:
        source_rule = """
Textbook-grounded retrieval was not used.
Do not claim textbook verification or provide textbook page citations.
"""

    return f"""
You are Learniverse AI, a conversational story-based tutor.

Selected learning scope:
- Grade: {grade_name}
- Subject: {subject_name}
- Chapter: {chapter_title}
- Current topic: {topic_title}

Strict rules:
- Answer only within the selected subject and chapter.
- Focus especially on the selected topic.
- Explain using simple stories, analogies or daily-life examples when helpful.
- Never answer questions unrelated to this selected chapter.
- Keep the answer concise and student-friendly.
- {language_rule(language)}

Source rule:
{source_rule}
""".strip()