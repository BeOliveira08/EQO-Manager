from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class UserProfile:
    name: str
    assistant_name: str = "EQO"
    age: int | None = None
    language: str = "pt-BR"
    timezone: str = "America/Sao_Paulo"

    def __post_init__(self) -> None:
        name = self.name.strip()
        assistant_name = self.assistant_name.strip()
        if not name or not assistant_name:
            raise ValueError("Os nomes do usuário e do assistente são obrigatórios.")
        if self.age is not None and not 0 < self.age < 130:
            raise ValueError("A idade deve estar entre 1 e 129.")
        if not self.language.strip() or not self.timezone.strip():
            raise ValueError("Idioma e fuso horário são obrigatórios.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "assistant_name", assistant_name)

    def with_assistant_name(self, name: str) -> "UserProfile":
        return replace(self, assistant_name=name)

