def language_instruction(language: str) -> str:
    if language == "bn":
        return "Write the blog post in Bangla."

    return "Write the blog post in English."


def blog_validation_messages(
    topic: str,
    short_description: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": """
You are a strict content classifier for Learniverse AI.
Return only valid JSON.
Do not include markdown or extra text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Check whether this blog topic is related to school-level Physics, Chemistry, Biology, or Mathematics.

Topic:
{topic}

Short description:
{short_description}

Allowed categories:
- physics
- chemistry
- biology
- math

Allowed examples:
- Science explanations
- Math learning
- Real-life physics/chemistry/biology/math examples
- Study tips related to science or math
- School-level educational content

Blocked examples:
- Sports gossip
- Entertainment
- Politics
- Programming tutorials
- Random lifestyle content
- Product reviews
- Anything not related to Physics, Chemistry, Biology, or Mathematics

Return exactly this JSON shape:
{{
  "is_allowed": true,
  "category": "physics",
  "reason": "short reason"
}}

If not allowed:
{{
  "is_allowed": false,
  "category": null,
  "reason": "short reason"
}}
""".strip(),
        },
    ]


def blog_generation_messages(
    topic: str,
    short_description: str,
    category: str,
    language: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": """
You are Learniverse AI blog writer.
Return only valid JSON.
Write educational blog posts only for Physics, Chemistry, Biology, or Mathematics.
Do not include markdown fences or extra text outside JSON.
""".strip(),
        },
        {
            "role": "user",
            "content": f"""
Generate a full educational blog post.

Topic:
{topic}

Short description:
{short_description}

Category:
{category}

Rules:
- The content must stay related to the selected category.
- Make it student-friendly.
- Use clear headings.
- Use markdown for the blog body.
- Keep the tone engaging but educational.
- Include real-life examples.
- Do not include unsafe experiments or dangerous instructions.
- Do not mention that you are an AI.
- {language_instruction(language)}

Return exactly this JSON shape:
{{
  "title": "blog title",
  "slug": "url-friendly-slug",
  "category": "{category}",
  "excerpt": "short preview summary",
  "content_markdown": "## Introduction\\n...\\n## Main Idea\\n...\\n## Real-life Example\\n...\\n## Summary\\n..."
}}
""".strip(),
        },
    ]