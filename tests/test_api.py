from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_generate_validation():

    response = client.post(
        "/generate",

        json={
            "document_type": "",
            "parties": "A",
            "terms": "B",
            "effective_date": "2026-04-15"
        }
    )

    assert response.status_code == 422


def test_txt_export():

    response = client.post(
        "/export",

        json={
            "format": "txt",

            "document_type": "Agreement",

            "text": (
                "AGREEMENT\n\n"
                "1. Purpose\n"
                "This is a draft."
            ),

            "terms": [
                "Confidentiality",
                "Payment within 30 days"
            ]
        }
    )


    assert response.status_code == 200


    data = response.json()


    assert data["success"] is True

    assert data["filename"].endswith(
        ".txt"
    )

    assert data["media_type"] == (
        "text/plain"
    )


def test_docx_export():

    response = client.post(
        "/export",

        json={
            "format": "docx",

            "document_type": "Agreement",

            "text": (
                "AGREEMENT\n\n"
                "1. Purpose\n"
                "This is a draft."
            ),

            "terms": [
                "Confidentiality"
            ]
        }
    )


    assert response.status_code == 200

    assert response.json()[
        "filename"
    ].endswith(".docx")


def test_pdf_export():

    response = client.post(
        "/export",

        json={
            "format": "pdf",

            "document_type": "Agreement",

            "text": (
                "AGREEMENT\n\n"
                "1. Purpose\n"
                "This is a draft."
            ),

            "terms": [
                "Confidentiality"
            ]
        }
    )


    assert response.status_code == 200

    assert response.json()[
        "filename"
    ].endswith(".pdf")