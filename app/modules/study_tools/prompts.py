def language_rule(language: str) -> str:
    if language == "bn":
        return "Write in Bangla unless the student asks otherwise."
    return "Write in English unless the student asks otherwise."


def note_generation_messages(
    source_text: str,
    language: str,
    ai_help_mode: str,
    instruction: str | None,
) -> list[dict[str, str]]:
    mode_instruction = {
        "study_notes": "Create organized study notes with headings, bullet points, key terms, examples, and a short recap.",
        "lecture_notes": "Create lecture-style notes with explanations, flow, examples, and important definitions.",
        "summary_notes": "Create concise summary notes focused only on the most important ideas.",
        "writing_help": "Help the student write better notes. Improve clarity, structure, grammar, and explanation quality.",
    }.get(ai_help_mode, "Create helpful study notes.")

    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Note Taker.

Task:
{mode_instruction}

Rules:
- Make the notes student-friendly.
- Use clear headings.
- Include key terms and short explanations.
- Include examples when useful.
- Do not invent facts outside the provided content unless the student asks for general help.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short note title",
  "content": "full note content in markdown"
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "No extra instruction."}

Source content:
{source_text}
""".strip(),
        },
    ]


def pdf_summary_messages(
    source_text: str,
    language: str,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI PDF Summarizer.

Create a useful student-friendly summary from the PDF text.

Rules:
- Start with a short overview.
- Then list the main points.
- Add important definitions or formulas if present.
- Add a final revision recap.
- Do not mention missing images unless needed.
- {language_rule(language)}

Return JSON only:
{{
  "summary": "full PDF summary in markdown"
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Summarize this PDF for studying."}

PDF text:
{source_text}
""".strip(),
        },
    ]


def flashcard_generation_messages(
    source_text: str,
    language: str,
    card_count: int,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Flashcard Generator.

Generate exactly {card_count} useful revision flashcards.

Rules:
- Front side should be a question or prompt.
- Back side should be clear and short.
- Add a hint only when helpful.
- Avoid duplicate cards.
- Focus on exam-useful concepts.
- {language_rule(language)}

Return JSON only:
{{
  "deck_title": "short deck title",
  "cards": [
    {{
      "front": "question",
      "back": "answer",
      "hint": "optional hint"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"Source content:\n{source_text}",
        },
    ]

def mind_map_generation_messages(
    source_text: str,
    language: str,
    item_count: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Mind Map Generator.

Create a student-friendly mind map from the source content.

Rules:
- Find the central idea.
- Create main branches and sub-branches.
- Keep labels short.
- Make it useful for revision.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short mind map title",
  "markdown": "mind map written as nested markdown bullets",
  "nodes": [
    {{"id": "node-1", "label": "Central idea", "level": 0}},
    {{"id": "node-2", "label": "Main branch", "level": 1}}
  ],
  "edges": [
    {{"from": "node-1", "to": "node-2"}}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Create a clear revision mind map."}

Maximum main ideas:
{item_count}

Source content:
{source_text}
""".strip(),
        },
    ]


def worksheet_generation_messages(
    source_text: str,
    language: str,
    item_count: int,
    difficulty: str,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Worksheet Generator.

Create a practice worksheet for students.

Rules:
- Include a mix of short questions, MCQs, and thinking questions.
- Include an answer key.
- Difficulty: {difficulty}
- Keep it school-friendly.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short worksheet title",
  "markdown": "full worksheet in markdown with questions and answer key",
  "questions": [
    {{
      "question_type": "mcq | short_answer | explanation",
      "question": "question text",
      "options": ["A", "B", "C", "D"],
      "answer": "correct answer",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Create a worksheet for practice."}

Number of questions:
{item_count}

Source content:
{source_text}
""".strip(),
        },
    ]


def formula_extraction_messages(
    source_text: str,
    language: str,
    item_count: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Formula Extractor.

Extract important formulas, equations, rules, and symbolic relationships from the source.

Rules:
- Include formula name.
- Include the formula.
- Explain each variable.
- Explain when to use it.
- Give one simple example if possible.
- If there are no formulas, extract key rules or relationships.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short formula sheet title",
  "markdown": "formula sheet in markdown",
  "formulas": [
    {{
      "name": "formula name",
      "formula": "formula text",
      "variables": ["variable explanations"],
      "when_to_use": "usage explanation",
      "example": "simple example"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Extract important formulas for revision."}

Maximum formulas:
{item_count}

Source content:
{source_text}
""".strip(),
        },
    ]


def important_questions_messages(
    source_text: str,
    language: str,
    item_count: int,
    difficulty: str,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Important Questions Generator.

Generate likely important questions for exam revision.

Rules:
- Include high-value questions.
- Include short answers or answer hints.
- Mix conceptual, definition, explanation, and application questions.
- Difficulty: {difficulty}
- {language_rule(language)}

Return JSON only:
{{
  "title": "short important questions title",
  "markdown": "important questions with answers in markdown",
  "questions": [
    {{
      "question": "question text",
      "answer": "answer or answer hint",
      "why_important": "short reason",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Generate important questions for exam preparation."}

Number of questions:
{item_count}

Source content:
{source_text}
""".strip(),
        },
    ]

def key_points_messages(
    source_text: str,
    language: str,
    item_count: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Key Points Extractor.

Extract the most important study points from the source.

Rules:
- Generate exactly {item_count} key points if possible.
- Keep each point short but meaningful.
- Focus on exam-useful ideas.
- Do not add unnecessary explanation.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short title",
  "markdown": "key points in markdown bullet list",
  "items": [
    {{
      "point": "key point",
      "why_important": "short reason"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Extract the most important key points."}

Source content:
{source_text}
""".strip(),
        },
    ]


def glossary_messages(
    source_text: str,
    language: str,
    item_count: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Glossary Maker.

Extract the top {item_count} important jargon, vocabulary, or critical terms.

Rules:
- Choose terms that are important for understanding or exams.
- Give simple definitions.
- Add examples when useful.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short glossary title",
  "markdown": "glossary in markdown table",
  "terms": [
    {{
      "term": "word or phrase",
      "definition": "simple meaning",
      "example": "example or null"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Extract the most important glossary terms."}

Source content:
{source_text}
""".strip(),
        },
    ]


def revision_checklist_messages(
    source_text: str,
    language: str,
    item_count: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Revision Checklist Generator.

Create a revision checklist from the source.

Rules:
- Generate around {item_count} checklist items.
- Items should be practical and study-focused.
- Use checkbox format in markdown.
- Include what to review, practice, or memorize.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short checklist title",
  "markdown": "revision checklist in markdown",
  "checklist": [
    {{
      "task": "revision task",
      "reason": "why this matters"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Create a revision checklist."}

Source content:
{source_text}
""".strip(),
        },
    ]


def study_plan_messages(
    source_text: str,
    language: str,
    plan_days: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Study Plan Generator.

Create a {plan_days}-day study plan from the source.

Rules:
- Break the plan by day.
- Include revision, practice, flashcards, and quiz time when useful.
- Keep it realistic for students.
- Mention what to study each day.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short study plan title",
  "markdown": "study plan in markdown",
  "days": [
    {{
      "day": 1,
      "focus": "main focus",
      "tasks": ["task 1", "task 2"]
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Create a realistic study plan."}

Source content:
{source_text}
""".strip(),
        },
    ]


def mnemonic_messages(
    source_text: str,
    language: str,
    item_count: int,
    instruction: str | None,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"""
You are Learniverse AI Mnemonic Maker.

Create memory tricks from the source.

Rules:
- Generate up to {item_count} useful mnemonics.
- Use simple memorable phrases.
- Explain what each mnemonic helps remember.
- Keep them student-friendly.
- {language_rule(language)}

Return JSON only:
{{
  "title": "short mnemonic title",
  "markdown": "mnemonics in markdown",
  "mnemonics": [
    {{
      "mnemonic": "memory trick",
      "remembers": "what it helps remember",
      "explanation": "short explanation"
    }}
  ]
}}
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Student instruction:
{instruction or "Create useful mnemonics."}

Source content:
{source_text}
""".strip(),
        },
    ]