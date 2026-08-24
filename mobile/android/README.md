# EQO Mobile Application Shell

Shell Kotlin mínimo para validar leitura, contraste, fluxo “Agora / Próxima ação” e
push-to-talk explícito em Android API 23+. Ele **não incorpora Python** e o
`ShellPreviewBackend` não é o Core: é apenas uma fixture visível enquanto o adapter
persistente é implementado contra `MobileEqoBackend`.

O manifesto não declara Internet, localização, sensores ou acesso amplo ao armazenamento.
O microfone é solicitado em runtime somente ao tocar em **Falar**; se negado, texto segue
funcionando. Dados de produção deverão ficar no armazenamento interno privado do app.

Abra esta pasta no Android Studio ou execute `gradlew assembleDebug` depois de gerar o
wrapper local. O repositório não inclui binários do Gradle wrapper.
