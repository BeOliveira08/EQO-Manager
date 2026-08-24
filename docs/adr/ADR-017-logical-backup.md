# ADR-017 — Backup lógico versionado

## Status

Aceita na v0.8.

## Decisão

“Exportar meus dados” produz JSON UTF-8 com extensão `.eqobackup`, identificador de formato,
versão de schema e seções de tarefas, estado, perfil, memórias e eventos. Não copia páginas
do SQLite e não exporta histórico de conversa ou raciocínio de IA.

## Consequências

O formato atravessa implementações de banco e runtimes. Importação e migrações serão
adicionadas por versão; a v0.8 entrega primeiro o caminho seguro e auditável de exportação.
