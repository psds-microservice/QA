from __future__ import annotations

import pytest

from qa_tests.http_client import StreamingServiceClient


@pytest.mark.smoke
def test_streaming_health_ok(streaming_service_client: StreamingServiceClient) -> None:
    resp = streaming_service_client.health()
    assert resp.status_code == 200


@pytest.mark.smoke
def test_streaming_ready_ok(streaming_service_client: StreamingServiceClient) -> None:
    resp = streaming_service_client.ready()
    assert resp.status_code == 200
