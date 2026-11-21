# SPDX-License-Identifier: MPL-2.0
"""Bounded public HTTPS contact through the shared source acquisition port."""

from hashlib import sha256
from pathlib import Path
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from empirical_lawhood.design.public_source_acquisition import ChecksummedPublicSourceMember, CaptureAssuredPublicSourceMember, validate_public_https_url
from empirical_lawhood.execution.public_source_acquisition import FetchedPublicSource, verify_public_source_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def _public_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


class _ExactRedirects(HTTPRedirectHandler):
    def __init__(self, member: ChecksummedPublicSourceMember) -> None:
        self.member = member
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.count += 1
        validate_public_https_url(newurl)
        if (
            self.count > 4
            or _public_url(newurl) not in self.member.allowed_redirect_urls_without_query
        ):
            raise PermissionError("public source redirect is outside the exact URL roster")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class BoundedPublicHttpsFetcher:
    transport_key = "public-source.https-exact"
    transport_version = "1.0.0"

    @property
    def implementation_sha256(self) -> str:
        return sha256(read_bounded_bytes(Path(__file__), maximum_bytes=1024**2)).hexdigest()

    def fetch(self, member: ChecksummedPublicSourceMember, *, timeout_seconds: int) -> FetchedPublicSource:
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
            raise ValueError("source transfer timeout is outside its bound")
        validate_public_https_url(member.url)
        deadline = time.monotonic() + timeout_seconds
        opener = build_opener(ProxyHandler({}), _ExactRedirects(member))
        request = Request(
            member.url,
            headers={
                "User-Agent": "empirical-lawhood-public-source-intake/1.0",
                "Accept-Encoding": "identity",
            },
        )
        with opener.open(request, timeout=min(timeout_seconds, 30)) as response:
            if response.status != 200:
                raise ValueError("public source did not return HTTP 200")
            validate_public_https_url(response.geturl())
            final_url = _public_url(response.geturl())
            if final_url not in (member.url, *member.allowed_redirect_urls_without_query):
                raise PermissionError("final public-source URL differs from its finite roster")
            if len(str(response.headers)) > 64 * 1024:
                raise ValueError("source headers exceed the bounded envelope")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ValueError("implicit HTTP content decompression is forbidden")
            length = response.headers.get("Content-Length")
            if length is not None and int(length) != member.expected_size_bytes:
                raise ValueError("source Content-Length differs from the exact byte selection")
            etag = response.headers.get("ETag")
            media = response.headers.get("Content-Type")
            if (
                isinstance(member, CaptureAssuredPublicSourceMember)
                and member.upstream_etag is not None
                and etag != member.upstream_etag
            ):
                raise ValueError("source ETag differs from the selected metadata")
            chunks: list[bytes] = []
            observed = 0
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError("public source exceeded its transfer time envelope")
                chunk = response.read(min(1024**2, member.expected_size_bytes + 1 - observed))
                if not chunk:
                    break
                observed += len(chunk)
                if observed > member.expected_size_bytes:
                    raise ValueError("public source exceeded its byte envelope")
                chunks.append(chunk)
        payload = b"".join(chunks)
        verify_public_source_bytes(member, payload)
        return FetchedPublicSource(payload, final_url, etag, media)


