from app.modules.catalog.model import Topic


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
            f"এই প্রশ্নটি আপনার নির্বাচিত {chapter_title} অধ্যায়ের বাইরে। "
            "অনুগ্রহ করে এই অধ্যায়ের সাথে সম্পর্কিত প্রশ্ন করুন অথবা অন্য অধ্যায় নির্বাচন করুন।"
        )

    return (
        f"This question is outside your selected chapter. "
        f"Please ask something related to {chapter_title} "
        "or choose another chapter first."
    )


def scope_check_messages(
    topic: Topic,
    student_message: str,
) -> list[dict[str, str]]:
    grade_name, subject_name, chapter_title, topic_title = get_topic_context(topic)

    return [
        {
            "role": "system",
            "content": (
                "You are a strict educational scope classifier. "
                "Reply with exactly YES or NO only."
            ),
        },
        {
            "role": "user",
            "content": f"""
Selected learning scope:
- Grade: {grade_name}
- Subject: {subject_name}
- Chapter: {chapter_title}
- Current topic: {topic_title}

Student question:
{student_message}

Is this question relevant to the selected subject and chapter, including helpful questions about the current topic?

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
) -> list[dict[str, str]]:
    grade_name, subject_name, chapter_title, topic_title = get_topic_context(topic)

    preference = student_preference or "No special story preference."

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
- Do not claim that the answer is verified from a textbook.
- Do not provide textbook page references.
- Textbook-grounded retrieval will be added later.
- End with one simple understanding-check question.
- {language_rule(language)}
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
) -> str:
    grade_name, subject_name, chapter_title, topic_title = get_topic_context(topic)

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
- Do not claim textbook verification.
- Do not provide textbook page citations yet.
- If asked for textbook proof, explain that textbook-grounded retrieval will be available later.
- Keep the answer concise and student-friendly.
- {language_rule(language)}
""".strip()