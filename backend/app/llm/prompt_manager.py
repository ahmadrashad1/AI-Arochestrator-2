from __future__ import annotations

from dataclasses import dataclass, field
from string import Template
from typing import Any


class _SafeMapping(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass
class PromptManager:
    prompts: dict[str, str] = field(default_factory=dict)

    def register(self, name: str, template: str) -> None:
        self.prompts[name] = template

    def render(self, template: str, **context: Any) -> str:
        return Template(template).safe_substitute(context)

    def render_named(self, name: str, **context: Any) -> str:
        template = self.prompts.get(name)
        if template is None:
            raise KeyError(f"Unknown prompt: {name}")
        return self.render(template, **context)


prompt_manager = PromptManager()
