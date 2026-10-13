import asyncio
import json

import httpx2 as httpx
import pytest


@pytest.mark.parametrize(
    "content", [b"{", b"\xff", b"", b"null", b"[]", b'{"id": NaN}', b"[" * 2000]
)
def test_invalid_json_has_safe_body_error(api_client, content):
    response = api_client.post(
        "/api/runs", content=content, headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    problem = response.json()["detail"][0]
    assert problem["loc"] == ["body"]
    assert set(problem) == {"loc", "type", "msg"}


@pytest.mark.parametrize(
    "media_type", [None, "text/plain", "application/x-www-form-urlencoded"]
)
def test_creation_requires_json(api_client, run_request, media_type):
    headers = {"content-type": media_type} if media_type else {}
    response = api_client.post(
        "/api/runs", content=json.dumps(run_request), headers=headers
    )
    assert response.status_code == 415
    assert isinstance(response.json()["detail"], str)


@pytest.mark.parametrize("extra_bytes", [0, 1])
def test_received_body_limit_including_missing_or_false_content_length(
    api_client, run_request, extra_bytes
):
    body = json.dumps(run_request).encode()
    body += b" " * (1_048_576 + extra_bytes - len(body))

    async def send_chunks(content_length):
        async def chunks():
            for offset in range(0, len(body), 16384):
                yield body[offset : offset + 16384]

        headers = {"content-type": "application/json; charset=utf-8"}
        if content_length is not None:
            headers["content-length"] = content_length
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api_client.app),
            base_url="http://testserver",
        ) as client:
            return await client.post("/api/runs", content=chunks(), headers=headers)

    for declared_length in (None, "1"):
        response = asyncio.run(send_chunks(declared_length))
        if extra_bytes:
            assert response.status_code == 413
            assert isinstance(response.json()["detail"], str)
        else:
            assert response.status_code in (200, 201)
    saved = api_client.get("/api/runs?start=2026-10-14&end=2026-10-15").json()
    assert len(saved) == (0 if extra_bytes else 1)


def test_limit_counts_utf8_bytes_with_content_length(api_client, run_request):
    run_request["user_note"] = "é" * 600_000
    body = json.dumps(run_request, ensure_ascii=False).encode()
    response = api_client.post(
        "/api/runs", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413
    assert api_client.get("/api/runs?start=2026-10-14&end=2026-10-15").json() == []
