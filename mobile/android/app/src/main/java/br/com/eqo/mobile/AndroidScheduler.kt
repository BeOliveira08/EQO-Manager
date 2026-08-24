package br.com.eqo.mobile

data class Reminder(val id: String, val taskId: String, val title: String, val triggerAtMillis: Long)

interface AndroidScheduler {
    fun schedule(reminder: Reminder)
    fun cancel(reminderId: String): Boolean
}

// A implementação com AlarmManager/WorkManager entra somente após testes no aparelho alvo.
