from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Type

from pydantic import BaseModel

from src.tools.names import ToolName


class ToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolSpec:
    name: ToolName
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    handler: Callable[[BaseModel], BaseModel]

    def schema_for_llm(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
        }


class ToolRegistry:
    def __init__(self, tools: list[ToolSpec]):
        self._tools = {t.name: t for t in tools}

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def schemas_for_llm(self, *, cache_breakpoint: bool = False) -> list[dict[str, Any]]:
        schemas = [t.schema_for_llm() for t in self._tools.values()]
        if cache_breakpoint and schemas:
            schemas[-1] = {**schemas[-1], "cache_control": {"type": "ephemeral"}}
        return schemas

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        return self._tools[name]

    def dispatch(self, tool_name: str, tool_input: dict[str, Any]) -> BaseModel:
        tool = self.get(tool_name)
        try:
            parsed = tool.input_model.model_validate(tool_input)
        except Exception as e:
            raise ToolError(f"Invalid input for {tool_name}: {e}") from e

        try:
            out = tool.handler(parsed)
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Tool {tool_name} failed: {e}") from e

        return tool.output_model.model_validate(out)

