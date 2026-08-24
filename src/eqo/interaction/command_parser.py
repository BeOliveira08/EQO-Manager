import shlex

from eqo.interaction.intent import Intent, ParsedCommand


class CommandParser:
    """Parser deliberadamente explícito; não tenta simular compreensão livre."""

    COMMANDS = {
        "criar": Intent.CREATE_TASK,
        "listar": Intent.LIST_TASKS,
        "concluir": Intent.COMPLETE_TASK,
        "remover": Intent.DELETE_TASK,
        "estado": Intent.UPDATE_STATE,
        "plano": Intent.GET_PLAN,
        "preferencia": Intent.SET_PREFERENCE,
        "nome": Intent.CHANGE_NAME,
        "ajuda": Intent.HELP,
        "sair": Intent.EXIT,
    }

    def parse(self, text: str) -> ParsedCommand:
        raw = text.strip()
        if not raw:
            return ParsedCommand(Intent.UNKNOWN, raw_text=text)
        try:
            parts = shlex.split(raw)
        except ValueError:
            return ParsedCommand(Intent.UNKNOWN, raw_text=text)
        intent = self.COMMANDS.get(parts[0].casefold(), Intent.UNKNOWN)
        arguments: dict[str, str] = {}
        if len(parts) > 1:
            arguments["value"] = " ".join(parts[1:])
        return ParsedCommand(intent, arguments, text)
