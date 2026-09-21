import re

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
)


# =========================================================
# CLIENTS
# =========================================================

groq_client = Groq(
    api_key=GROQ_API_KEY
)


nvidia_client = None

if NVIDIA_API_KEY:
    nvidia_client = OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY,
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a technology news editor from Tamil Nadu.

Your job is to summarize technology news in NATURAL INDIAN
THANGGLISH.

IMPORTANT:

Write Tamil using ENGLISH / ROMAN letters.

The output must sound like a Tamil-speaking Indian person
naturally explaining the news.

DO NOT write a normal English news summary.

DO NOT use Tamil Unicode.

DO NOT use formal Tamil.

DO NOT translate every English word into Tamil.

Technical words should remain in English.

Natural examples:

"Google pudhusa oru AI agent-ai announce pannirukku."

"Indha vulnerability use panni attackers system-la code
execute panna mudiyum-nu researchers kandupidichirukanga."

"Amazon indha feature-ai limited users-ku release pannirukku."

"Company ippo indha technology-ai test panni varudhu."

"Researchers indha attack method-a identify pannirukanga."

"Microsoft indha update-ai Windows users-ku gradually
rollout panna start pannirukku."

The summary should feel like a Tamil-speaking tech person
naturally explaining the news.

STYLE RULES:

- Roman Tamil + English
- Natural Indian Thanglish
- Conversational but professional
- Easy to understand
- Exactly 3 or 4 sentences
- Around 70 to 120 words
- Use facts from the article only
- Do not invent information
- Do not speculate
- Do not give personal opinions
- Do not explain "why it matters"
- Do not add recommendations
- Do not add analysis
- No bullet points
- No headings
- No emojis
- No markdown
- No quotes around the summary
- Do not say "According to the article"
- Do not say "This article discusses"
- Do not say "This news is about"
- Do not say "The article talks about"
- Do not say "As an AI"
- Do not say "I cannot summarize"

Start directly with what happened.

BAD:

"This article discusses a new AI agent launched by Google."

GOOD:

"Google pudhusa oru AI agent-ai announce pannirukku, idhu
families-ku daily activities manage panna help pannum."

BAD:

"Amazon has blocked Meta's Muse AI from shopping on its website."

GOOD:

"Amazon, Meta oda Muse AI agent-ku shopping site-la access
block pannirukku."

Return ONLY the final Thanglish summary.
"""


# =========================================================
# CLEAN SUMMARY
# =========================================================

def clean_summary(summary):

    if not summary:
        return ""

    summary = summary.strip()

    # Remove code fences
    summary = re.sub(
        r"^```(?:text)?\s*",
        "",
        summary,
        flags=re.IGNORECASE,
    )

    summary = re.sub(
        r"\s*```$",
        "",
        summary,
        flags=re.IGNORECASE,
    )

    # Remove accidental prefixes
    prefixes = [
        "Summary:",
        "SUMMARY:",
        "Thanglish Summary:",
        "Thanglish summary:",
        "Final Summary:",
        "Final summary:",
    ]

    for prefix in prefixes:

        if summary.startswith(prefix):
            summary = summary[
                len(prefix):
            ].strip()

    # Remove surrounding quotes
    summary = (
        summary
        .strip('"')
        .strip("'")
        .strip()
    )

    # Normalize whitespace
    summary = re.sub(
        r"\s+",
        " ",
        summary,
    )

    return summary.strip()


# =========================================================
# VALIDATE THANGGLISH
# =========================================================

def validate_summary(summary):

    if not summary:
        return False

    summary = clean_summary(summary)

    # Minimum length
    if len(summary) < 180:
        return False

    # Maximum length
    if len(summary) > MAX_SUMMARY_CHARS:
        return False

    lowered = summary.lower()

    invalid_phrases = [

        # AI meta
        "as an ai",
        "as a language model",

        # Failure responses
        "unable to summarize",
        "cannot summarize",
        "can't summarize",
        "i cannot",
        "i can't",

        # English article openings
        "this article",
        "this news is about",
        "the article discusses",
        "the article talks about",
        "according to the article",

        # Unwanted casual words
        "da bro",
        "dei",
    ]

    for phrase in invalid_phrases:

        if phrase in lowered:
            return False

    return True


# =========================================================
# LIMIT SUMMARY
# =========================================================

def limit_summary(summary):

    summary = clean_summary(summary)

    if len(summary) <= MAX_SUMMARY_CHARS:
        return summary

    shortened = summary[
        :MAX_SUMMARY_CHARS
    ]

    shortened = shortened.rsplit(
        " ",
        1,
    )[0]

    return shortened + "..."


# =========================================================
# GROQ SUMMARY
# =========================================================

def generate_groq_summary(
    model,
    title,
    content,
):

    prompt = f"""
Summarize the following technology news.

Write ONLY natural Indian Thanglish.

Tamil must be written using English/Roman letters.

Exactly 3 or 4 sentences.

Do NOT write normal English.

Use natural Tamil sentence structure mixed with English.

Start directly with what happened.

Use only information present in the article.

Article title:

{title}

Article content:

{content}

Return ONLY the final Thanglish summary.
"""

    request_args = {

        "model": model,

        "messages": [

            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },

            {
                "role": "user",
                "content": prompt,
            },

        ],

        "temperature": GROQ_TEMPERATURE,

        "max_tokens": GROQ_MAX_TOKENS,
    }


    # Qwen → disable reasoning
    if model == GROQ_PRIMARY_MODEL:

        request_args[
            "reasoning_effort"
        ] = "none"


    # GPT-OSS → disable reasoning
    elif model.startswith("openai/"):

        request_args[
            "include_reasoning"
        ] = False


    response = groq_client.chat.completions.create(
        **request_args
    )

    return response.choices[0].message.content


# =========================================================
# NVIDIA SUMMARY
# =========================================================

def generate_nvidia_summary(
    title,
    content,
):

    if not nvidia_client:

        raise RuntimeError(
            "NVIDIA_API_KEY is not configured"
        )


    prompt = f"""
Summarize the following technology news in natural Indian
Thanglish.

Tamil must be written using English/Roman letters.

The output should sound like a Tamil-speaking Indian tech
person naturally explaining the news.

Use natural Tamil sentence structure mixed with English.

Do NOT produce normal English.

Do NOT use Tamil Unicode.

Do NOT use formal Tamil.

Exactly 3 or 4 sentences.

Around 70 to 120 words.

Use only facts present in the article.

No opinions.

No speculation.

No analysis.

No "why it matters".

No headings.

No bullets.

No emojis.

Start directly with what happened.

Article title:

{title}

Article content:

{content}

Return ONLY the final Thanglish summary.
"""


    response = nvidia_client.chat.completions.create(

        model=NVIDIA_MODEL,

        messages=[

            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },

            {
                "role": "user",
                "content": prompt,
            },

        ],

        temperature=NVIDIA_TEMPERATURE,

        max_tokens=NVIDIA_MAX_TOKENS,
    )


    return response.choices[0].message.content


# =========================================================
# MAIN SUMMARIZER
# =========================================================

def summarize_article(article):

    title = article.get(
        "title",
        "",
    )

    content = article.get(
        "content",
        "",
    )


    if not content:

        print(
            "  ✗ No article content"
        )

        return None


    # =====================================================
    # 1. GROQ PRIMARY
    # =====================================================

    groq_models = [
        GROQ_PRIMARY_MODEL,
        *GROQ_FALLBACK_MODELS,
    ]


    # =====================================================
    # 2. TRY GROQ PRIMARY + FALLBACKS
    # =====================================================

    for model in groq_models:

        try:

            print(
                f"  → Trying Groq: {model}"
            )


            raw = generate_groq_summary(
                model,
                title,
                content,
            )


            if not raw:

                print(
                    f"  ✗ {model}: empty response"
                )

                continue


            summary = clean_summary(
                raw
            )


            if not validate_summary(
                summary
            ):

                print(
                    f"  ✗ {model}: invalid Thanglish"
                )

                continue


            summary = limit_summary(
                summary
            )


            print(
                f"  ✓ Groq success: {model}"
            )

            return summary


        except Exception as error:

            print(
                f"  ✗ {model}: {error}"
            )


    # =====================================================
    # 3. NVIDIA FALLBACK
    # =====================================================

    if nvidia_client:

        try:

            print(
                f"  → Trying NVIDIA: {NVIDIA_MODEL}"
            )


            raw = generate_nvidia_summary(
                title,
                content,
            )


            if not raw:

                print(
                    "  ✗ NVIDIA: empty response"
                )

            else:

                summary = clean_summary(
                    raw
                )


                if validate_summary(
                    summary
                ):

                    summary = limit_summary(
                        summary
                    )


                    print(
                        "  ✓ NVIDIA fallback success"
                    )

                    return summary


                print(
                    "  ✗ NVIDIA: invalid Thanglish"
                )


        except Exception as error:

            print(
                f"  ✗ NVIDIA: {error}"
            )


    # =====================================================
    # 4. EVERYTHING FAILED
    # =====================================================

    print(
        "  ✗ All summarization models failed"
    )

    return None