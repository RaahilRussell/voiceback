# Claude Code operating contract

Before editing any project code:

1. Read `PROJECT_CONTEXT.md`.
2. Read `BUILD_WORKFLOW.md`.
3. Read `PROGRESS.md`.
4. Inspect the actual relevant source and current Git status.
5. Identify the current active stage.
6. Work exclusively on that stage and its prerequisites.
7. Follow the stage's implementation order, validation commands, and acceptance criteria.
8. Run the required tests and correct errors.
9. Update `PROGRESS.md` with exact commands, results, environment, evidence, blockers, and commit hash.
10. Update `PROJECT_CONTEXT.md` when architecture changes.
11. Stop at the next validation gate and ask the user before advancing.

Never claim a feature works without actual execution evidence. A file existing, a unit test passing, a simulator result, a loaded checkpoint, a successful provider call, or a paper benchmark is not proof of physical-device behavior, model usefulness, accuracy, or end-to-end success.

Never replace failing ML integration with fabricated output. Never silently change the architecture. Preserve no-audio inference, privacy, consent, and explicit approval before synthesis. Treat the Markdown files as an implementation contract, while verifying every claim against source and runtime behavior.

The current active stage and the next action are always in `PROGRESS.md`. Do not begin Stage 01 until Stage 00 has a recorded gate result.

