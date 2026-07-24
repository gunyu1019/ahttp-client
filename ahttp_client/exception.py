"""HTTP status exceptions raised for unsuccessful responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .response import Response


class HTTPException(Exception):
    """Base exception for an unsuccessful HTTP response.

    Each concrete status exception declares its HTTP ``status_code`` and
    human-readable ``title`` as class variables.  The original response is
    retained when the exception is raised through
    :meth:`~ahttp_client.response.Response.raise_for_status`.
    """

    status_code: ClassVar[int | None] = None
    title: ClassVar[str] = "HTTP error"

    def __init__(self, response: Response | None = None, message: str | None = None) -> None:
        """Create the exception, optionally attaching the triggering response.

        Parameters
        ----------
        response: Response | None
            Response that triggered the exception. When given, ``status`` and
            ``url`` are read from it instead of the class-level defaults.
        message: str | None
            Exception message. A message built from ``status``/``title``/``url``
            is used when empty.
        """
        self.response = response
        self.status = response.status if response is not None else self.status_code
        self.url = response.url if response is not None else None
        super().__init__(message or self._default_message())

    def _default_message(self) -> str:
        """Build a useful exception message without consuming the response body."""
        if self.status is None:
            return self.title

        message = f"{self.status} {self.title}"
        if self.url is not None:
            message += f" for url: {self.url}"
        return message


class HTTPClientError(HTTPException):
    """Base exception for an unrecognised 4xx client error response."""

    title: ClassVar[str] = "Client Error"


class HTTPServerError(HTTPException):
    """Base exception for an unrecognised 5xx server error response."""

    title: ClassVar[str] = "Server Error"


class HTTPBadRequest(HTTPClientError):
    status_code: ClassVar[int] = 400
    title: ClassVar[str] = "Bad Request"


class HTTPUnauthorized(HTTPClientError):
    status_code: ClassVar[int] = 401
    title: ClassVar[str] = "Unauthorized"


class HTTPPaymentRequired(HTTPClientError):
    status_code: ClassVar[int] = 402
    title: ClassVar[str] = "Payment Required"


class HTTPForbidden(HTTPClientError):
    status_code: ClassVar[int] = 403
    title: ClassVar[str] = "Forbidden"


class HTTPNotFound(HTTPClientError):
    status_code: ClassVar[int] = 404
    title: ClassVar[str] = "Not Found"


class HTTPMethodNotAllowed(HTTPClientError):
    status_code: ClassVar[int] = 405
    title: ClassVar[str] = "Method Not Allowed"


class HTTPNotAcceptable(HTTPClientError):
    status_code: ClassVar[int] = 406
    title: ClassVar[str] = "Not Acceptable"


class HTTPProxyAuthenticationRequired(HTTPClientError):
    status_code: ClassVar[int] = 407
    title: ClassVar[str] = "Proxy Authentication Required"


class HTTPRequestTimeout(HTTPClientError):
    status_code: ClassVar[int] = 408
    title: ClassVar[str] = "Request Timeout"


class HTTPConflict(HTTPClientError):
    status_code: ClassVar[int] = 409
    title: ClassVar[str] = "Conflict"


class HTTPGone(HTTPClientError):
    status_code: ClassVar[int] = 410
    title: ClassVar[str] = "Gone"


class HTTPLengthRequired(HTTPClientError):
    status_code: ClassVar[int] = 411
    title: ClassVar[str] = "Length Required"


class HTTPPreconditionFailed(HTTPClientError):
    status_code: ClassVar[int] = 412
    title: ClassVar[str] = "Precondition Failed"


class HTTPContentTooLarge(HTTPClientError):
    status_code: ClassVar[int] = 413
    title: ClassVar[str] = "Content Too Large"


class HTTPURITooLong(HTTPClientError):
    status_code: ClassVar[int] = 414
    title: ClassVar[str] = "URI Too Long"


class HTTPUnsupportedMediaType(HTTPClientError):
    status_code: ClassVar[int] = 415
    title: ClassVar[str] = "Unsupported Media Type"


class HTTPRangeNotSatisfiable(HTTPClientError):
    status_code: ClassVar[int] = 416
    title: ClassVar[str] = "Range Not Satisfiable"


class HTTPExpectationFailed(HTTPClientError):
    status_code: ClassVar[int] = 417
    title: ClassVar[str] = "Expectation Failed"


class HTTPImATeapot(HTTPClientError):
    status_code: ClassVar[int] = 418
    title: ClassVar[str] = "I'm a teapot"


class HTTPMisdirectedRequest(HTTPClientError):
    status_code: ClassVar[int] = 421
    title: ClassVar[str] = "Misdirected Request"


class HTTPUnprocessableContent(HTTPClientError):
    status_code: ClassVar[int] = 422
    title: ClassVar[str] = "Unprocessable Content"


class HTTPLocked(HTTPClientError):
    status_code: ClassVar[int] = 423
    title: ClassVar[str] = "Locked"


class HTTPFailedDependency(HTTPClientError):
    status_code: ClassVar[int] = 424
    title: ClassVar[str] = "Failed Dependency"


class HTTPTooEarly(HTTPClientError):
    status_code: ClassVar[int] = 425
    title: ClassVar[str] = "Too Early"


class HTTPUpgradeRequired(HTTPClientError):
    status_code: ClassVar[int] = 426
    title: ClassVar[str] = "Upgrade Required"


class HTTPPreconditionRequired(HTTPClientError):
    status_code: ClassVar[int] = 428
    title: ClassVar[str] = "Precondition Required"


class HTTPTooManyRequests(HTTPClientError):
    status_code: ClassVar[int] = 429
    title: ClassVar[str] = "Too Many Requests"


class HTTPRequestHeaderFieldsTooLarge(HTTPClientError):
    status_code: ClassVar[int] = 431
    title: ClassVar[str] = "Request Header Fields Too Large"


class HTTPUnavailableForLegalReasons(HTTPClientError):
    status_code: ClassVar[int] = 451
    title: ClassVar[str] = "Unavailable For Legal Reasons"


class HTTPInternalServerError(HTTPServerError):
    status_code: ClassVar[int] = 500
    title: ClassVar[str] = "Internal Server Error"


class HTTPNotImplemented(HTTPServerError):
    status_code: ClassVar[int] = 501
    title: ClassVar[str] = "Not Implemented"


class HTTPBadGateway(HTTPServerError):
    status_code: ClassVar[int] = 502
    title: ClassVar[str] = "Bad Gateway"


class HTTPServiceUnavailable(HTTPServerError):
    status_code: ClassVar[int] = 503
    title: ClassVar[str] = "Service Unavailable"


class HTTPGatewayTimeout(HTTPServerError):
    status_code: ClassVar[int] = 504
    title: ClassVar[str] = "Gateway Timeout"


class HTTPVersionNotSupported(HTTPServerError):
    status_code: ClassVar[int] = 505
    title: ClassVar[str] = "HTTP Version Not Supported"


class HTTPVariantAlsoNegotiates(HTTPServerError):
    status_code: ClassVar[int] = 506
    title: ClassVar[str] = "Variant Also Negotiates"


class HTTPInsufficientStorage(HTTPServerError):
    status_code: ClassVar[int] = 507
    title: ClassVar[str] = "Insufficient Storage"


class HTTPLoopDetected(HTTPServerError):
    status_code: ClassVar[int] = 508
    title: ClassVar[str] = "Loop Detected"


class HTTPNotExtended(HTTPServerError):
    status_code: ClassVar[int] = 510
    title: ClassVar[str] = "Not Extended"


class HTTPNetworkAuthenticationRequired(HTTPServerError):
    status_code: ClassVar[int] = 511
    title: ClassVar[str] = "Network Authentication Required"


STATUS_EXCEPTIONS: dict[int, type[HTTPException]] = {
    exception.status_code: exception
    for exception in (
        HTTPBadRequest,
        HTTPUnauthorized,
        HTTPPaymentRequired,
        HTTPForbidden,
        HTTPNotFound,
        HTTPMethodNotAllowed,
        HTTPNotAcceptable,
        HTTPProxyAuthenticationRequired,
        HTTPRequestTimeout,
        HTTPConflict,
        HTTPGone,
        HTTPLengthRequired,
        HTTPPreconditionFailed,
        HTTPContentTooLarge,
        HTTPURITooLong,
        HTTPUnsupportedMediaType,
        HTTPRangeNotSatisfiable,
        HTTPExpectationFailed,
        HTTPImATeapot,
        HTTPMisdirectedRequest,
        HTTPUnprocessableContent,
        HTTPLocked,
        HTTPFailedDependency,
        HTTPTooEarly,
        HTTPUpgradeRequired,
        HTTPPreconditionRequired,
        HTTPTooManyRequests,
        HTTPRequestHeaderFieldsTooLarge,
        HTTPUnavailableForLegalReasons,
        HTTPInternalServerError,
        HTTPNotImplemented,
        HTTPBadGateway,
        HTTPServiceUnavailable,
        HTTPGatewayTimeout,
        HTTPVersionNotSupported,
        HTTPVariantAlsoNegotiates,
        HTTPInsufficientStorage,
        HTTPLoopDetected,
        HTTPNotExtended,
        HTTPNetworkAuthenticationRequired,
    )
}


def exception_for_status(status_code: int) -> type[HTTPException] | None:
    """Return the exception class associated with an unsuccessful status code.

    Registered HTTP status codes use their concrete exception class.  Other
    values in the 4xx and 5xx ranges use their respective category base class.
    Successful and redirect responses return ``None``.
    """
    if status_code in STATUS_EXCEPTIONS:
        return STATUS_EXCEPTIONS[status_code]
    if 400 <= status_code < 500:
        return HTTPClientError
    if 500 <= status_code < 600:
        return HTTPServerError
    return None


# RFC 9110 renamed these two response statuses.  Keep their common legacy
# names available so applications can use either terminology.
HTTPPayloadTooLarge = HTTPContentTooLarge
HTTPRequestURITooLong = HTTPURITooLong
HTTPUnprocessableEntity = HTTPUnprocessableContent


__all__ = [
    "HTTPException",
    "HTTPClientError",
    "HTTPServerError",
    "HTTPBadRequest",
    "HTTPUnauthorized",
    "HTTPPaymentRequired",
    "HTTPForbidden",
    "HTTPNotFound",
    "HTTPMethodNotAllowed",
    "HTTPNotAcceptable",
    "HTTPProxyAuthenticationRequired",
    "HTTPRequestTimeout",
    "HTTPConflict",
    "HTTPGone",
    "HTTPLengthRequired",
    "HTTPPreconditionFailed",
    "HTTPContentTooLarge",
    "HTTPPayloadTooLarge",
    "HTTPURITooLong",
    "HTTPRequestURITooLong",
    "HTTPUnsupportedMediaType",
    "HTTPRangeNotSatisfiable",
    "HTTPExpectationFailed",
    "HTTPImATeapot",
    "HTTPMisdirectedRequest",
    "HTTPUnprocessableContent",
    "HTTPUnprocessableEntity",
    "HTTPLocked",
    "HTTPFailedDependency",
    "HTTPTooEarly",
    "HTTPUpgradeRequired",
    "HTTPPreconditionRequired",
    "HTTPTooManyRequests",
    "HTTPRequestHeaderFieldsTooLarge",
    "HTTPUnavailableForLegalReasons",
    "HTTPInternalServerError",
    "HTTPNotImplemented",
    "HTTPBadGateway",
    "HTTPServiceUnavailable",
    "HTTPGatewayTimeout",
    "HTTPVersionNotSupported",
    "HTTPVariantAlsoNegotiates",
    "HTTPInsufficientStorage",
    "HTTPLoopDetected",
    "HTTPNotExtended",
    "HTTPNetworkAuthenticationRequired",
    "STATUS_EXCEPTIONS",
    "exception_for_status",
]
