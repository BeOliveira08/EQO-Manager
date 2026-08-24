from enum import StrEnum

from eqo.domain.user import UserProfile
from eqo.interaction.response import InteractionResponse
from eqo.services.profile_service import ProfileService


class ConversationState(StrEnum):
    IDLE = "idle"
    ASK_USER_NAME = "ask_user_name"
    ASK_ASSISTANT_NAME = "ask_assistant_name"
    CONFIRM = "confirm"
    READY = "ready"


class DialogueManager:
    def __init__(self, profiles: ProfileService) -> None:
        self.profiles = profiles
        self.state = ConversationState.IDLE
        self._user_name: str | None = None
        self._assistant_name = "EQO"

    def start_onboarding(self) -> InteractionResponse:
        profile = self.profiles.current()
        if profile is not None:
            self.state = ConversationState.READY
            return InteractionResponse(
                f"Olá, {profile.name}. Eu sou {profile.assistant_name} e já estou configurado."
            )
        self.state = ConversationState.ASK_USER_NAME
        return InteractionResponse(
            "Olá. Meu nome é EQO. Sou seu mordomo virtual e existo para ajudar "
            "você a administrar sua vida com menos estresse. Como posso chamar você?"
        )

    def receive(self, text: str) -> InteractionResponse:
        answer = text.strip()
        if self.state is ConversationState.IDLE:
            raise RuntimeError("O diálogo precisa ser iniciado antes de receber respostas.")
        if self.state is ConversationState.READY:
            return InteractionResponse("O onboarding já foi concluído.")
        if not answer:
            return InteractionResponse("Preciso de uma resposta para continuar.")
        if self.state is ConversationState.ASK_USER_NAME:
            self._user_name = answer
            self.state = ConversationState.ASK_ASSISTANT_NAME
            return InteractionResponse(
                f"Prazer, {answer}. Quer continuar me chamando de EQO? "
                "Responda 'sim' ou informe outro nome."
            )
        if self.state is ConversationState.ASK_ASSISTANT_NAME:
            self._assistant_name = "EQO" if answer.casefold() in {"sim", "s"} else answer
            self.state = ConversationState.CONFIRM
            return InteractionResponse(
                f"Você é {self._user_name} e eu sou {self._assistant_name}. "
                "Confirmar? (s/n)",
                requires_confirmation=True,
            )
        return self._confirm(answer)

    def _confirm(self, answer: str) -> InteractionResponse:
        if answer.casefold() not in {"sim", "s", "não", "nao", "n"}:
            return InteractionResponse("Responda 'sim' para confirmar ou 'não' para recomeçar.")
        if answer.casefold() in {"não", "nao", "n"}:
            self._user_name = None
            self._assistant_name = "EQO"
            self.state = ConversationState.ASK_USER_NAME
            return InteractionResponse("Tudo bem. Como posso chamar você?")
        assert self._user_name is not None
        profile = self.profiles.save(UserProfile(
            name=self._user_name,
            assistant_name=self._assistant_name,
        ))
        self.state = ConversationState.READY
        return InteractionResponse(
            f"Perfeito, {profile.name}. A partir de agora sou {profile.assistant_name}."
        )
