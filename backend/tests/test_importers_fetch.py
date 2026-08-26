import httpx
import pytest

from app.importers import fetch


def test_raises_clear_error_when_url_not_configured(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch.settings, "awin_feed_url", None)
    with pytest.raises(RuntimeError, match="AWIN_FEED_URL"):
        fetch.fetch_awin_feed(dest=tmp_path / "awin.csv")


def test_streams_response_body_to_dest_file(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch.settings, "awin_feed_url", "https://example.com/awin-feed.csv")

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.com/awin-feed.csv"
        return httpx.Response(200, content=b"sku,brand\n123,Levi's\n")

    monkeypatch.setattr(fetch.httpx, "stream", _mock_stream(handler))

    dest = tmp_path / "awin.csv"
    result = fetch.fetch_awin_feed(dest=dest)

    assert result == dest
    assert dest.read_bytes() == b"sku,brand\n123,Levi's\n"


def test_raises_on_http_error_status(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch.settings, "awin_feed_url", "https://example.com/awin-feed.csv")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    monkeypatch.setattr(fetch.httpx, "stream", _mock_stream(handler))

    with pytest.raises(httpx.HTTPStatusError):
        fetch.fetch_awin_feed(dest=tmp_path / "awin.csv")


def _mock_stream(handler):
    """Build a drop-in replacement for httpx.stream backed by MockTransport.

    httpx.stream() is a context manager returning a live Response; the real
    signature takes arbitrary args/kwargs (method, url, follow_redirects,
    timeout, ...) which we just forward to a client wired to the transport.
    """

    def stream(method, url, **kwargs):
        client = httpx.Client(transport=httpx.MockTransport(handler))
        kwargs.pop("follow_redirects", None)
        kwargs.pop("timeout", None)
        return client.stream(method, url, **kwargs)

    return stream
