from pydantic import BaseModel, Field, field_validator


class DocumentRequest(BaseModel):
    document_type: str = Field(
        ...,
        min_length=2,
        max_length=120
    )

    parties: str = Field(
        ...,
        min_length=2,
        max_length=2000
    )

    terms: str = Field(
        ...,
        min_length=2,
        max_length=10000
    )

    effective_date: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    @field_validator(
        "document_type",
        "parties",
        "terms",
        "effective_date"
    )
    @classmethod
    def strip_text(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value


class ExportRequest(BaseModel):
    format: str = Field(
        ...,
        pattern=r"^(txt|docx|pdf)$"
    )

    document_type: str = Field(
        ...,
        min_length=2,
        max_length=120
    )

    text: str = Field(
        ...,
        min_length=1,
        max_length=100000
    )

    terms: list[str] = Field(
        default_factory=list,
        max_length=100
    )


class GenerateResponse(BaseModel):
    success: bool
    document_type: str
    text: str