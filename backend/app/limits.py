"""Bound import bytes before JSON parsing or database writes."""
from starlette.responses import JSONResponse

IMPORT_BYTE_LIMIT = 25_000_000


class RequestBodyLimit:
    def __init__(self, app, max_bytes=IMPORT_BYTE_LIMIT):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await self.app(scope, receive, send)
        try:
            declared = int(next((value for name, value in scope.get("headers", []) if name.lower() == b"content-length"), b"0"))
            if declared < 0:
                raise ValueError
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length"}, status_code=400)(scope, receive, send)
        if declared > self.max_bytes:
            return await JSONResponse({"detail": "JSON upload exceeds 25 MB safeguard"}, status_code=413)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_bytes:
                response = JSONResponse({"detail": "JSON upload exceeds 25 MB safeguard"}, status_code=413)
                return await response(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        payload = bytes(body)
        del body
        consumed = False

        async def replay():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": payload, "more_body": False}
            return await receive()

        return await self.app(scope, replay, send)
