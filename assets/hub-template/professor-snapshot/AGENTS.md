# Professor Hub — Workspace Guide

Central workspace for teaching workflows: grading, Canvas operations, and student communication.

## Tool Routing

| Folder | Purpose | Runtime |
|--------|---------|---------|
| `LabNoteBookGrader/` | Grade handwritten lab notebooks (PDF + Canvas workflows) | Python |
| `Exam-grader/` | Grade handwritten exams/lab reports and post results | Python |
| `gradehub/` | Queue-based Canvas grading orchestration pipeline | Python |
| `student-email-tool/` | Student email automation + Canvas messaging flows | Python |

## Notes For LLM Agents

- Use the nearest subproject `AGENTS.md`; this file is only a router for the teaching hub.
- Keep secrets out of source files; prefer Keychain or local env files that stay uncommitted.
