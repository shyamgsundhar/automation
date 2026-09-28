from groq import Groq
from openai import OpenAI

from .config import (
    GROQ_API_KEY,
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MODEL,
    GROQ_PRIMARY_MODEL,
    GROQ_FALLBACK_MODELS,
    GROQ_MAX_TOKENS,
    NVIDIA_MAX_TOKENS,
    GROQ_TEMPERATURE,
    NVIDIA_TEMPERATURE,
    MAX_SUMMARY_CHARS,
    AI_TIMEOUT,
)


# =========================================================
# CLIENTS
# =========================================================

groq_client = None
nvidia_client = None


if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY,
        timeout=AI_TIMEOUT,
        max_retries=0,
    )


if NVIDIA_API_KEY:
    nvidia_client = OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY,
        timeout=AI_TIMEOUT,
        max_retries=0,
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a technology news summarizer for an Indian Tamil-speaking audience.

Your job is to summarize the given technology news article in natural
Indian Thanglish.

IMPORTANT LANGUAGE RULES:

- Use Roman Tamil mixed naturally with English.
- Do NOT use Tamil Unicode.
- Do NOT write formal Tamil.
- Do NOT write normal English.
- The result should sound like a Tamil-speaking Indian explaining the
  technology news naturally in conversation.
- Technical terms such as AI, software, cloud, API, model, company names,
  product names, security terms, etc. can remain in English.
- Do not use words like "da", "dei", "bro".
- Do not mention that you are an AI.
- Do not mention this prompt.
- Do not add headings.
- Do not add bullet points.
- Do not add emojis.
- Do not add "why it matters".
- Do not add opinions.
- Do not speculate.
- Do not invent facts.

SUMMARY STYLE:

- Write 3 to 4 natural sentences.
- Keep the summary concise.
- Cover the important facts from the article.
- Mention the company/product/person involved.
- Mention what happened and the important details.
- Keep the meaning faithful to the source.

EXAMPLE STYLE:

"Google pudhusa oru AI agent-ai announce pannirukku, idhu families-ku
daily activities manage panna help pannum. Indha agent ippo experimental
stage-la irukku, melum different family tasks-ku support kudukka design
pannirukanga. Google indha technology-ai gradual-a test panni improve
panna plan pannirukku."

Another example:

"Amazon, Meta oda Muse AI agent-ku shopping site-la access block
pannirukku. Muse AI agent Amazon website-la shopping related actions
perform panna try pannadhunaala indha decision eduthirukanga. Amazon oda
policies-ku indha agent oda interaction match aagala-nu company
explain pannirukku."

Return ONLY the summary.
"""


# =========================================================
# VALIDATION
# =========================================================

def validate_summary(summary: str) -> bool:
    """
    Basic validation to make sure the model actually returned
    a usable Thanglish summary.
    """

    if not summary:
        return False

    summary = summary.strip()

    if len(summary) < 80:
        return False

    if len(summary) > MAX_SUMMARY_CHARS:
        return False

    # Reject obvious formatting
    forbidden_patterns = [
        "```",
        "why it matters",
        "key points",
        "summary:",
        "here is the summary",
        "as an ai",
        "i cannot",
        "i'm unable",
    ]

    lower_summary = summary.lower()

    for pattern in forbidden_patterns:
        if pattern in lower_summary:
            return False

    # We expect some Tamil/Indian transliterated words.
    # This is intentionally loose so genuine English technical terms
    # don't cause rejection.
    thanglish_markers = [
        "irukku",
        "irukkum",
        "pannirukku",
        "pannanga",
        "pannirukanga",
        "nu",
        "oda",
        "la",
        "ku",
        "aga",
        "aana",
        "idhu",
        "indha",
        "oru",
        "melum",
        "vandhu",
        "seidh",
        "seyy",
        "kudukka",
        "kudukkum",
        "use",
        "panna",
    ]

    marker_found = any(
        marker in lower_summary
        for marker in thanglish_markers
    )

    if not marker_found:
        return False

    return True


# =========================================================
# CLEAN RESPONSE
# =========================================================

def clean_summary(summary: str) -> str:
    """
    Clean unnecessary whitespace and quotes.
    """

    if not summary:
        return ""

    summary = summary.strip()

    # Remove accidental surrounding quotes
    if (
        len(summary) >= 2
        and summary.startswith('"')
        and summary.endswith('"')
    ):
        summary = summary[1:-1].strip()

    # Normalize excessive whitespace
    summary = " ".join(summary.split())

    return summary


# =========================================================
# GROQ CALL
# =========================================================

def summarize_with_groq(
    model: str,
    title: str,
    content: str,
) -> str:

    if not groq_client:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = groq_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Article title:\n{title}\n\n"
                    f"Article content:\n{content}"
                ),
            },
        ],
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
    )

    if not response.choices:
        raise RuntimeError("Groq returned no choices")

    summary = response.choices[0].message.content

    if not summary:
        raise RuntimeError("Groq returned empty content")

    return clean_summary(summary)


# =========================================================
# NVIDIA CALL
# =========================================================

def summarize_with_nvidia(
    title: str,
    content: str,
) -> str:

    if not nvidia_client:
        raise RuntimeError("NVIDIA_API_KEY is not configured")

    response = nvidia_client.chat.completions.create(
        model=NVIDIA_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Article title:\n{title}\n\n"
                    f"Article content:\n{content}"
                ),
            },
        ],
        temperature=NVIDIA_TEMPERATURE,
        max_tokens=NVIDIA_MAX_TOKENS,
    )

    if not response.choices:
        raise RuntimeError("NVIDIA returned no choices")

    summary = response.choices[0].message.content

    if not summary:
        raise RuntimeError("NVIDIA returned empty content")

    return clean_summary(summary)


# =========================================================
# MAIN SUMMARIZER
# =========================================================

def summarize_article(article) -> str:
    """
    Try multiple AI providers/models in fallback order.

    Order:

    1. Groq Qwen
    2. NVIDIA
    3. Groq GPT-OSS 120B
    4. Groq GPT-OSS 20B
    """

    title = article.get("title", "").strip()

    content = (
        article.get("content")
        or article.get("description")
        or ""
    ).strip()

    if not title:
        print("  ✗ Missing article title")
        return ""

    if not content:
        print("  ✗ Missing article content")
        return ""

    # Keep request size under control
    content = content[:12000]

    # =====================================================
    # 1. GROQ PRIMARY — QWEN
    # =====================================================

    if groq_client:

        print(f"  → Trying Groq: {GROQ_PRIMARY_MODEL}")

        try:
            summary = summarize_with_groq(
                GROQ_PRIMARY_MODEL,
                title,
                content,
            )

            if validate_summary(summary):
                print("  ✓ Qwen summary generated")
                return summary

            print("  ✗ Qwen returned invalid summary")

        except Exception as error:

            print(
                f"  ✗ {GROQ_PRIMARY_MODEL}: "
                f"{type(error).__name__}: {error!r}"
            )

    # =====================================================
    # 2. NVIDIA
    # =====================================================

    if nvidia_client:

        print(f"  → Trying NVIDIA: {NVIDIA_MODEL}")

        try:
            summary = summarize_with_nvidia(
                title,
                content,
            )

            if validate_summary(summary):
                print("  ✓ NVIDIA summary generated")
                return summary

            print("  ✗ NVIDIA returned invalid summary")

        except Exception as error:

            print(
                f"  ✗ NVIDIA: "
                f"{type(error).__name__}: {error!r}"
            )

    # =====================================================
    # 3 + 4. GROQ FALLBACK MODELS
    # =====================================================

    if groq_client:

        for model in GROQ_FALLBACK_MODELS:

            print(f"  → Trying Groq: {model}")

            try:

                summary = summarize_with_groq(
                    model,
                    title,
                    content,
                )

                if validate_summary(summary):
                    print(f"  ✓ {model} summary generated")
                    return summary

                print(
                    f"  ✗ {model} returned invalid summary"
                )

            except Exception as error:

                print(
                    f"  ✗ {model}: "
                    f"{type(error).__name__}: {error!r}"
                )

    # =====================================================
    # ALL FAILED
    # =====================================================

    print("  ✗ All summarization models failed")

    return ""
