# CLAUDE.md

Les règles de travail sont dans [AGENTS.md](AGENTS.md) et les règles produit dans
[PROJECT_GUIDE.md](PROJECT_GUIDE.md) : lis-les avant toute modification.

Spécificités Claude Code :

- Une session lancée par l'orchestrateur reçoit son ticket, sa branche, son worktree et le chemin de
  son rapport JSON dans le prompt (`orchestrator/session-prompt.md`). Personne ne lit la session en
  direct : ne pose pas de question dans la conversation, écris-les dans le ticket.
- Porte locale avant la PR : `bash scripts/check-contract.sh`.
- Préfère la bibliothèque standard de la stack ; toute dépendance ajoutée est justifiée dans la PR.
