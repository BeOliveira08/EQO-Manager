package br.com.eqo.mobile

data class StateSnapshot(
    val capacity: Int,
    val energy: Int,
    val availableMinutes: Int,
    val focus: Int,
    val stress: Int,
)

data class NextAction(
    val kind: String,
    val title: String,
    val reason: String,
    val allocatedMinutes: Int,
    val taskId: String?,
)

data class DashboardSnapshot(
    val schemaVersion: Int,
    val assistantName: String,
    val state: StateSnapshot,
    val nextAction: NextAction?,
    val pendingCount: Int,
    val capabilities: Set<String>,
)

data class InteractionReply(val text: String, val requiresConfirmation: Boolean = false)

interface MobileEqoBackend {
    fun dashboard(): DashboardSnapshot
    fun submitText(text: String): InteractionReply
    fun requestPushToTalk(): InteractionReply
}

/** UI fixture only. Replace with the persisted backend adapter; no domain rule belongs here. */
class ShellPreviewBackend : MobileEqoBackend {
    override fun dashboard() = DashboardSnapshot(
        schemaVersion = 1,
        assistantName = "EQO",
        state = StateSnapshot(3, 3, 45, 3, 3),
        nextAction = NextAction(
            "task", "Conectar o backend local", "Primeiro marco executável do shell.", 20, null
        ),
        pendingCount = 1,
        capabilities = setOf("text", "push_to_talk"),
    )

    override fun submitText(text: String) = InteractionReply(
        if (text.isBlank()) "Digite uma mensagem." else "Shell offline: backend local ainda não conectado."
    )

    override fun requestPushToTalk() =
        InteractionReply("Permissão concedida. A captura será ligada pelo adapter de voz.")
}
