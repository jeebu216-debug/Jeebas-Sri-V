import time

from google import genai
from google.genai import types

from backend.config import get_settings


class GeminiDocumentGenerator:
    """Generates structured legal-document drafts using Gemini."""

    SYSTEM_INSTRUCTION = """
You are LegalEase, an AI assistant that drafts structured legal-document
templates for human review.

Rules:

1. Generate a professional DRAFT, not legal advice.

2. Use only information supplied by the user.

3. Never invent names, amounts, dates, addresses, laws,
registration numbers, or signatures.

4. If important information is missing, use:
[MISSING INFORMATION]

5. Use clear headings and numbered clauses.

6. Use formal and professional language.

7. Keep the document editable as plain text.

8. Include a short Review Notice at the end.

9. Do not claim that the document is legally valid
or legally enforceable.

10. Do not invent laws or court cases.

11. Preserve the user's supplied terms accurately.

12. Do not fabricate information.
"""

    def __init__(self) -> None:
        settings = get_settings()

        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Add it to your .env file."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.primary_model = settings.gemini_model
        self.fallback_model = "gemini-flash-lite-latest"

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:

        prompt = f"""
Create a complete editable draft for the following legal document.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

EFFECTIVE DATE:
{effective_date}

USER-PROVIDED TERMS:
{terms}

Create the document with the following structure where appropriate:

1. Document title
2. Parties
3. Effective date
4. Background / recitals
5. Definitions
6. Main agreement clauses
7. User-provided terms
8. Responsibilities
9. Payment terms if applicable
10. Confidentiality if applicable
11. Termination if applicable
12. General provisions
13. Signature section
14. Review Notice

Do not add facts that the user did not provide.

Use [MISSING INFORMATION] wherever necessary.
"""

        models_to_try = [
            self.primary_model,
            self.fallback_model,
        ]

        last_error = None

        for model in models_to_try:

            for attempt in range(2):

                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=self.SYSTEM_INSTRUCTION,
                            temperature=0.3,
                            max_output_tokens=6000,
                        ),
                    )

                    text = getattr(response, "text", None)

                    if not text:
                        raise RuntimeError(
                            "Gemini returned an empty response."
                        )

                    return text.strip()

                except Exception as exc:
                    last_error = exc
                    error_text = str(exc)

                    is_temporary_error = (
                        "503" in error_text
                        or "UNAVAILABLE" in error_text
                        or "429" in error_text
                    )

                    if not is_temporary_error:
                        raise

                    if attempt == 0:
                        time.sleep(3)

        raise RuntimeError(
            "Gemini is temporarily unavailable. "
            "LegalEase tried the primary and fallback models. "
            "Please try again in a few moments. "
            f"Details: {last_error}"
        )