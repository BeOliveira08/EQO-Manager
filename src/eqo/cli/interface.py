from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from colorama import Fore, init  # type: ignore[import-untyped]

from eqo.ai.confirmation import ConfirmationGate
from eqo.ai.context_builder import AIContextBuilder
from eqo.ai.interpreter import NaturalLanguageInterpreter
from eqo.ai.models import AIMode, InterpretationDisposition
from eqo.ai.ollama_provider import OllamaAIProvider
from eqo.ai.settings import AISettings
from eqo.domain.memory import MemoryImportance, MemorySource
from eqo.domain.persona import Persona
from eqo.domain.plan import Plan
from eqo.domain.state import Capacity
from eqo.domain.task import Priority, Task, TaskStatus
from eqo.services.context_engine import ContextEngine
from eqo.services.dialogue_manager import ConversationState, DialogueManager
from eqo.services.interpretation_executor import InterpretationExecutor
from eqo.services.memory_service import MemoryService
from eqo.services.personality_engine import PersonalityEngine
from eqo.services.planner import Planner
from eqo.services.profile_service import ProfileService
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService
from eqo.services.voice_interaction import VoiceInteractionService
from eqo.speech.adapters import WhisperSTTProvider, WindowsSAPIProvider
from eqo.speech.interfaces import AudioInput
from eqo.speech.settings import SpeechSettings, STTMode, TTSMode
from eqo.storage.sqlite_event_repository import SQLiteEventRepository
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository
from eqo.storage.sqlite_profile_repository import SQLiteUserProfileRepository
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository

init(autoreset=True)


def _show_voice_status(state: ConversationState) -> None:
    labels = {
        ConversationState.LISTENING: "[OUVINDO]",
        ConversationState.PROCESSING: "[PROCESSANDO]",
        ConversationState.WAITING_CONFIRMATION: "[AGUARDANDO CONFIRMAÇÃO]",
        ConversationState.RESPONDING: "[FALANDO]",
        ConversationState.ERROR: "[ERRO]",
        ConversationState.IDLE: "[OCIOSO]",
        ConversationState.READY: "[OCIOSO]",
    }
    if state in labels:
        print(Fore.BLUE + labels[state])


def _render_tasks(tasks: list[Task], today: date | None = None) -> None:
    if not tasks:
        print(Fore.YELLOW + "Nenhuma tarefa encontrada.")
        return
    current_date = today or date.today()
    for index, task in enumerate(tasks, 1):
        status = Fore.GREEN + "[x]" if task.completed else Fore.RED + "[ ]"
        deadline = ""
        if task.deadline:
            days_left = (task.deadline - current_date).days
            if days_left < 0:
                suffix = " [ATRASADA]"
            elif days_left == 0:
                suffix = " [HOJE]"
            else:
                suffix = f", {days_left}d"
            deadline = Fore.BLUE + f" (Prazo: {task.deadline.isoformat()}{suffix})"
        print(f"{index}. {status} [{task.priority.label}] {task.title}{deadline}")


class CLI:
    def __init__(
        self,
        service: TaskService,
        state_service: StateService | None = None,
        planner: Planner | None = None,
        context_engine: ContextEngine | None = None,
        profiles: ProfileService | None = None,
        dialogue: DialogueManager | None = None,
        personality: PersonalityEngine | None = None,
        memories: MemoryService | None = None,
        ai_interpreter: NaturalLanguageInterpreter | None = None,
        interpretation_executor: InterpretationExecutor | None = None,
        voice_service: VoiceInteractionService | None = None,
    ) -> None:
        self.service = service
        self.state_service = state_service
        self.planner = planner
        self.context_engine = context_engine
        self.profiles = profiles
        self.dialogue = dialogue
        self.personality = personality
        self.memories = memories
        self.ai_interpreter = ai_interpreter
        self.interpretation_executor = interpretation_executor
        self.voice_service = voice_service
        self.confirmation_gate = ConfirmationGate()

    def run(self) -> None:
        while True:
            print(Fore.BLUE + f"\n--- {self._assistant_name()} ---")
            print("1. Adicionar tarefa\n2. Listar todas\n3. Listar concluídas")
            print("4. Listar pendentes\n5. Buscar tarefas\n6. Concluir tarefa")
            print("7. Remover tarefa\n8. Estatísticas\n9. Sair")
            if self.state_service is not None:
                print("10. Atualizar meu estado\n11. Sugerir plano")
            if self.dialogue is not None:
                print("12. Onboarding\n13. Alterar nome do assistente")
            if self.memories is not None:
                print("14. Lembrar informação\n15. O que você lembra?\n16. Esquecer informação")
            if (
                self.ai_interpreter is not None
                and self.ai_interpreter.mode is AIMode.LOCAL
            ):
                print("17. Interpretar linguagem natural")
            if self.voice_service is not None:
                print("18. Push-to-talk (arquivo WAV)")
            choice = input(Fore.CYAN + "Escolha: ").strip()
            actions = {
                "1": self.add_task, "2": lambda: self.list_tasks(),
                "3": lambda: self.list_tasks(TaskStatus.COMPLETED),
                "4": lambda: self.list_tasks(TaskStatus.PENDING), "5": self.search_tasks,
                "6": lambda: self.manage_task("concluir"),
                "7": lambda: self.manage_task("remover"), "8": self.show_stats,
                "10": self.update_state,
                "11": self.show_plan,
                "12": self.run_onboarding,
                "13": self.change_assistant_name,
                "14": self.remember_information,
                "15": self.show_memories,
                "16": self.forget_information,
                "17": self.interpret_natural_language,
                "18": self.push_to_talk,
            }
            if choice == "9":
                print(Fore.MAGENTA + "Até logo!")
                return
            action = actions.get(choice)
            if action:
                action()
            else:
                print(Fore.RED + "Opção inválida!")

    def add_task(self) -> None:
        title = input(Fore.CYAN + "Título da tarefa: ").strip()
        if not title:
            print(Fore.YELLOW + "O título não pode estar vazio!")
            return
        raw = input(Fore.CYAN + "Prioridade (1-Alta, 2-Média, 3-Baixa): ").strip() or "2"
        try:
            priority = Priority(int(raw))
        except ValueError:
            print(Fore.YELLOW + "Prioridade inválida; usando Média.")
            priority = Priority.MEDIUM
        deadline = None
        if input("Adicionar prazo? (s/n): ").strip().casefold() == "s":
            try:
                raw_deadline = input("Data (YYYY-MM-DD): ").strip()
                deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
            except ValueError:
                print(Fore.RED + "Formato de data inválido; tarefa criada sem prazo.")
        try:
            raw_duration = input("Duração estimada em minutos (opcional): ").strip()
            estimated_minutes = int(raw_duration) if raw_duration else None
            effort = int(input("Esforço de 1 a 5 [3]: ").strip() or "3")
            flexibility = int(input("Flexibilidade de 1 a 5 [3]: ").strip() or "3")
            self.service.create(
                title,
                priority,
                deadline,
                estimated_minutes=estimated_minutes,
                effort=effort,
                flexibility=flexibility,
            )
        except ValueError as error:
            print(Fore.RED + f"Dados de demanda inválidos: {error}")
            return
        print(Fore.GREEN + "OK: Tarefa adicionada!")

    def list_tasks(self, status: TaskStatus | None = None) -> None:
        _render_tasks(self.service.list(status))

    def search_tasks(self) -> None:
        _render_tasks(self.service.search(input(Fore.CYAN + "Termo de busca: ")))

    def manage_task(self, action: str) -> None:
        tasks = self.service.list()
        _render_tasks(tasks)
        if not tasks:
            return
        try:
            number = int(input(Fore.CYAN + f"Número da tarefa para {action}: "))
            task = tasks[number - 1] if number > 0 else None
        except (ValueError, IndexError):
            task = None
        if task is None:
            print(Fore.YELLOW + "Número inválido.")
            return
        if action == "concluir":
            self.service.complete(task.id)
            print(Fore.GREEN + "OK: Tarefa concluída!")
        else:
            self.service.remove(task.id)
            print(Fore.GREEN + f"OK: Tarefa '{task.title}' removida!")

    def show_stats(self) -> None:
        stats = self.service.stats()
        print(Fore.MAGENTA + "\nEstatísticas:")
        print(f"- Total: {stats['total']} tarefas\n- Concluídas: {stats['completed']}")
        print(f"- Pendentes: {stats['pending']}\n- Alta: {stats['high']}")
        print(f"- Média: {stats['medium']}\n- Baixa: {stats['low']}")

    def update_state(self) -> None:
        if self.state_service is None:
            print(Fore.YELLOW + "Estado do usuário indisponível.")
            return
        try:
            state = self.state_service.update(
                capacity=Capacity(int(input("Capacidade de 1 a 5: ").strip())),
                energy=int(input("Energia de 1 a 5: ").strip()),
                available_minutes=int(input("Minutos disponíveis: ").strip()),
                focus=int(input("Foco de 1 a 5: ").strip()),
                stress=int(input("Estresse de 1 a 5: ").strip()),
            )
        except ValueError as error:
            print(Fore.RED + f"Estado inválido: {error}")
            return
        print(Fore.GREEN + f"OK: Estado atualizado; {state.available_minutes} min disponíveis.")

    def show_plan(self) -> None:
        if self.state_service is None or self.planner is None or self.context_engine is None:
            print(Fore.YELLOW + "Planejamento indisponível.")
            return
        state = self.state_service.current()
        context = self.context_engine.current(state)
        if context.available_minutes == 0:
            print(Fore.YELLOW + "Informe seu tempo disponível antes de planejar.")
            return
        plan = self.planner.create_plan(self.service.list(), state, context)
        if self.personality is not None:
            response = self.personality.describe_plan(
                plan, self._persona(), self.profiles.current() if self.profiles else None
            )
            print(Fore.CYAN + response.text)
        self._render_plan(plan)

    def run_onboarding(self) -> None:
        if self.dialogue is None:
            print(Fore.YELLOW + "Onboarding indisponível.")
            return
        response = self.dialogue.start_onboarding()
        print(Fore.CYAN + response.text)
        while self.dialogue.state is not ConversationState.READY:
            response = self.dialogue.receive(input("> "))
            print(Fore.CYAN + response.text)

    def change_assistant_name(self) -> None:
        if self.profiles is None:
            print(Fore.YELLOW + "Perfil indisponível.")
            return
        try:
            profile = self.profiles.change_assistant_name(
                input("Novo nome do assistente: ").strip()
            )
        except (LookupError, ValueError) as error:
            print(Fore.RED + str(error))
            return
        print(Fore.GREEN + f"Perfeito. A partir de agora sou {profile.assistant_name}.")

    def _assistant_name(self) -> str:
        profile = self.profiles.current() if self.profiles else None
        return profile.assistant_name if profile else "EQO"

    def _persona(self) -> Persona:
        return Persona(name=self._assistant_name())

    def remember_information(self) -> None:
        if self.memories is None:
            print(Fore.YELLOW + "Memória indisponível.")
            return
        key = input("Identificador da memória (ex.: preferred_study_time): ").strip()
        value = input("O que devo lembrar: ").strip()
        try:
            memory = self.memories.remember(
                key,
                value,
                importance=MemoryImportance.HIGH,
                source=MemorySource.USER_PREFERENCE,
            )
        except ValueError as error:
            print(Fore.RED + f"Memória inválida: {error}")
            return
        print(Fore.GREEN + f"Entendido. Vou lembrar: {memory.value}")

    def show_memories(self) -> None:
        if self.memories is None:
            print(Fore.YELLOW + "Memória indisponível.")
            return
        memories = self.memories.list()
        profile = self.profiles.current() if self.profiles else None
        if self.personality is not None:
            response = self.personality.describe_memories(memories, profile)
            print(Fore.CYAN + response.text)
            return
        for memory in memories:
            print(f"- {memory.key}: {memory.value}")

    def forget_information(self) -> None:
        if self.memories is None:
            print(Fore.YELLOW + "Memória indisponível.")
            return
        key = input("Identificador da memória a esquecer: ").strip()
        if self.memories.forget(key):
            print(Fore.GREEN + "Claro. Essa memória foi apagada.")
        else:
            print(Fore.YELLOW + "Não encontrei essa memória.")

    def interpret_natural_language(self) -> None:
        if self.ai_interpreter is None or self.interpretation_executor is None:
            print(Fore.YELLOW + "Inteligência local indisponível.")
            return
        state = self.state_service.current() if self.state_service else None
        outcome = self.ai_interpreter.interpret(input("Diga o que você precisa: "), state)
        if outcome.disposition is InterpretationDisposition.CONFIRM:
            entities = ", ".join(
                f"{key}={value}" for key, value in outcome.interpretation.entities
            )
            prompt = (
                f"Interpretei {outcome.interpretation.intent.value} "
                f"({entities}). Confirmar? (s/n): "
            )
            confirmed = input(prompt).strip().casefold() in {"s", "sim"}
            outcome = self.confirmation_gate.resolve(outcome, confirmed)
        if outcome.disposition is InterpretationDisposition.UNKNOWN:
            print(Fore.YELLOW + "Não consegui interpretar com segurança. Nenhuma ação foi feita.")
            return
        print(Fore.CYAN + self.interpretation_executor.execute(outcome).text)

    def push_to_talk(self) -> None:
        if self.voice_service is None:
            print(Fore.YELLOW + "Voz indisponível; use a interface textual.")
            return
        path = Path(input("Arquivo WAV gravado após pressionar e soltar: ").strip())
        try:
            audio = AudioInput(path.read_bytes())
        except (OSError, ValueError) as error:
            print(Fore.RED + f"Não foi possível ler o áudio: {error}")
            return
        result = self.voice_service.process(audio)
        if result.transcript:
            print(Fore.CYAN + f"Você disse: {result.transcript}")
        print(Fore.CYAN + result.response.text)
        if result.state is ConversationState.WAITING_CONFIRMATION:
            result = self.voice_service.confirm_text(input("Confirmação (sim/não/cancela): "))
            print(Fore.CYAN + result.response.text)
        metrics = result.metrics
        print(
            Fore.BLUE
            + f"Latência: STT={metrics.stt_ms:.0f}ms, interpretação="
            f"{metrics.interpretation_ms:.0f}ms, Core={metrics.core_ms:.0f}ms, "
            f"TTS={metrics.tts_ms:.0f}ms, total={metrics.total_ms:.0f}ms"
        )

    @staticmethod
    def _render_plan(plan: Plan) -> None:
        print(Fore.BLUE + "\nPlano sugerido (nenhuma tarefa foi alterada):")
        for item in plan.items:
            if item.allocated_minutes:
                start = item.starts_at.strftime("%H:%M") if item.starts_at else "--:--"
                segments = f" segmentos={item.segments}" if item.segments else ""
                print(
                    f"- {start} | {item.allocated_minutes} min | {item.title} "
                    f"[{item.decision.value}]{segments}"
                )
            else:
                print(f"- Depois | {item.title} [{item.decision.value}]")
            print(f"  Motivo: {item.reason}")
        print(f"Tempo ainda livre: {plan.remaining_capacity} min")


def build_cli(root: str | Path = ".") -> CLI:
    base = Path(root)
    repository = SQLiteTaskRepository(base / "data" / "eqo.db")
    state_repository = SQLiteUserStateRepository(base / "data" / "eqo.db")
    profile_repository = SQLiteUserProfileRepository(base / "data" / "eqo.db")
    memory_repository = SQLiteMemoryRepository(base / "data" / "eqo.db")
    event_repository = SQLiteEventRepository(base / "data" / "eqo.db")
    profiles = ProfileService(profile_repository)
    tasks = TaskService(repository, base / "backups")
    states = StateService(state_repository)
    memories = MemoryService(memory_repository, event_repository)
    planner = Planner()
    context_engine = ContextEngine()
    settings = AISettings.from_environment()
    provider = (
        OllamaAIProvider(
            model=settings.ollama_model,
            host=settings.ollama_host,
            timeout_seconds=settings.timeout_seconds,
        )
        if settings.mode is AIMode.LOCAL
        else None
    )
    interpreter = NaturalLanguageInterpreter(
        mode=settings.mode,
        provider=provider,
        context_builder=AIContextBuilder(memories),
    )
    executor = InterpretationExecutor(
        tasks=tasks,
        states=states,
        memories=memories,
        profiles=profiles,
        planner=planner,
        context_engine=context_engine,
    )
    speech_settings = SpeechSettings.from_environment()
    stt = (
        WhisperSTTProvider(speech_settings.whisper_model)
        if speech_settings.stt_mode is STTMode.WHISPER
        else None
    )
    tts = WindowsSAPIProvider() if speech_settings.tts_mode is TTSMode.WINDOWS else None
    voice_service = (
        VoiceInteractionService(
            stt=stt,
            interpreter=interpreter,
            executor=executor,
            dialogue=DialogueManager(profiles),
            states=states,
            tts=tts,
            status_listener=_show_voice_status,
        )
        if stt is not None
        else None
    )
    imported = repository.import_legacy_json(base / "tasks.json")
    if imported:
        print(Fore.GREEN + f"OK: {imported} tarefa(s) importada(s) do formato legado.")
    return CLI(
        tasks,
        states,
        planner,
        context_engine,
        profiles,
        DialogueManager(profiles),
        PersonalityEngine(),
        memories,
        interpreter,
        executor,
        voice_service,
    )


def main() -> None:
    build_cli().run()
