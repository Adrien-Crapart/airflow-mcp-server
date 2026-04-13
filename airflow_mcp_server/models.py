from typing import TypedDict, Any

class ToolResponse(TypedDict, total=False):
    success: bool
    data: Any
    error: str | None
