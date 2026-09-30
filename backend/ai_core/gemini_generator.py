import random
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

    # Transient Gemini errors that are safe to retry.
    RETRYABLE_ERROR_CODES = ("408", "429", "500", "502", "503", "504")

    def __init__(self) -> None:
        settings = get_settings()

        api_key = (settings.gemini_api_key or "").strip()

        # Vercel/AI Studio values are sometimes pasted with quotes.
        # Remove only matching surrounding quotes; never alter the key body.
        if (
            len(api_key) >= 2
            and api_key[0] == api_key[-1]
            and api_key[0] in {"'", '"'}
        ):
            api_key = api_key[1:-1].strip()

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Add it to the deployment environment variables."
            )

        self.client = genai.Client(api_key=api_key)

        self.primary_model = settings.gemini_model

        # Keep multiple independent fallback choices.
        self.fallback_models = [
            "gemini-3.7-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
        ]

    @classmethod
    def _is_retryable_error(cls, exc: Exception) -> bool:
        error_text = str(exc).upper()
        return (
            any(code in error_text for code in cls.RETRYABLE_ERROR_CODES)
            or "UNAVAILABLE" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
            or "DEADLINE_EXCEEDED" in error_text
        )

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        # 2s, 4s, 8s with small jitter to avoid synchronized retries.
        base_delay = 2 ** (attempt + 1)
        jitter = random.uniform(0, 0.5)
        return base_delay + jitter

    def _generate_with_retries(self, model: str, prompt: str) -> str:
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
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
                        f"Gemini model '{model}' returned an empty response."
                    )

                return text.strip()

            except Exception as exc:
                last_error = exc

                # Do not retry permanent errors such as invalid API keys,
                # malformed requests, permission errors, etc.
                if not self._is_retryable_error(exc):
                    raise

                if attempt < max_attempts - 1:
                    time.sleep(self._backoff_delay(attempt))

        raise RuntimeError(
            f"Model '{model}' remained unavailable after "
            f"{max_attempts} attempts. Details: {last_error}"
        )

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

        # Try the configured primary model first, followed by several
        # independent fallback models. Duplicate model names are removed.
        models_to_try = []
        for model in [self.primary_model, *self.fallback_models]:
            if model and model not in models_to_try:
                models_to_try.append(model)

        errors = []

        for model in models_to_try:
            try:
                return self._generate_with_retries(model, prompt)
            except Exception as exc:
                errors.append(f"{model}: {exc}")

        raise RuntimeError(
            "Gemini is temporarily unavailable. "
            "LegalEase tried multiple models with automatic retries. "
            "Please try again in a few moments. "
            f"Details: {' | '.join(errors)}"
        )
