from eqo.interaction.command_parser import CommandParser
from eqo.interaction.intent import Intent


def test_explicit_commands_map_to_intents_and_arguments() -> None:
    parser = CommandParser()
    assert parser.parse("listar").intent is Intent.LIST_TASKS
    command = parser.parse('nome "Alfred Pennyworth"')
    assert command.intent is Intent.CHANGE_NAME
    assert command.arguments == {"value": "Alfred Pennyworth"}


def test_unknown_or_malformed_command_is_not_guessed() -> None:
    parser = CommandParser()
    assert parser.parse("estou cansado").intent is Intent.UNKNOWN
    assert parser.parse('nome "sem fechar').intent is Intent.UNKNOWN
    assert parser.parse("   ").intent is Intent.UNKNOWN


def test_memory_commands_have_explicit_intents() -> None:
    parser = CommandParser()
    assert parser.parse("lembrar study_time=evening").intent is Intent.REMEMBER
    assert parser.parse("recordar study_time").intent is Intent.RECALL
    assert parser.parse("esquecer study_time").intent is Intent.FORGET_MEMORY
    assert parser.parse("memorias").intent is Intent.LIST_MEMORIES
