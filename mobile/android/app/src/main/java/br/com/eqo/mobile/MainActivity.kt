package br.com.eqo.mobile

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

class MainActivity : Activity() {
    private val backend: MobileEqoBackend = ShellPreviewBackend()
    private lateinit var feedback: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(buildScreen(backend.dashboard()))
    }

    private fun buildScreen(snapshot: DashboardSnapshot): ScrollView {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            setBackgroundColor(Color.rgb(245, 243, 236))
        }
        root.addView(label(snapshot.assistantName, 28f, Color.rgb(32, 48, 42)))
        root.addView(label("SHELL v0.8 • offline • backend demonstrativo", 12f, Color.DKGRAY))
        root.addView(label(
            "Agora: energia ${snapshot.state.energy}/5 • ${snapshot.state.availableMinutes} min",
            18f, Color.rgb(49, 92, 75)
        ))
        val action = snapshot.nextAction
        root.addView(label("Próxima ação", 14f, Color.DKGRAY))
        root.addView(label(action?.title ?: "Atualize seu estado para receber uma sugestão.", 23f, Color.BLACK))
        if (action != null) {
            root.addView(label("${action.allocatedMinutes} min • ${action.reason}", 15f, Color.DKGRAY))
        }
        root.addView(label("${snapshot.pendingCount} tarefa(s) pendente(s)", 15f, Color.DKGRAY))

        val input = EditText(this).apply { hint = "Fale ou escreva de forma direta"; minHeight = dp(56) }
        root.addView(input, matchWrap())
        root.addView(actionButton("Enviar") {
            feedback.text = backend.submitText(input.text.toString()).text
        })
        root.addView(actionButton("Falar") { requestMicrophone() })
        root.addView(actionButton("Tarefas") {
            feedback.text = "A lista será fornecida pelo mesmo MobileEqoBackend."
        })
        root.addView(actionButton("Atualizar estado") {
            feedback.text = "A edição de estado será uma tela curta, não um painel técnico."
        })
        feedback = label("Nenhuma ação é executada sem confirmação.", 15f, Color.DKGRAY)
        root.addView(feedback)
        return ScrollView(this).apply { addView(root) }
    }

    private fun requestMicrophone() {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            feedback.text = backend.requestPushToTalk().text
        } else {
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), AUDIO_REQUEST)
        }
    }

    override fun onRequestPermissionsResult(code: Int, permissions: Array<out String>, results: IntArray) {
        super.onRequestPermissionsResult(code, permissions, results)
        if (code == AUDIO_REQUEST) {
            feedback.text = if (results.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
                backend.requestPushToTalk().text
            } else {
                "Microfone negado. Texto continua disponível."
            }
        }
    }

    private fun label(text: String, size: Float, color: Int) = TextView(this).apply {
        this.text = text; textSize = size; setTextColor(color); setPadding(0, dp(8), 0, dp(8))
    }

    private fun actionButton(text: String, action: () -> Unit) = Button(this).apply {
        this.text = text; minHeight = dp(56); gravity = Gravity.CENTER; setOnClickListener { action() }
    }

    private fun matchWrap() = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    companion object { const val AUDIO_REQUEST = 100 }
}
