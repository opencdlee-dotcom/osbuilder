## Project

OSBuilder

## Technology Stack

# Stack Research

**Domain:** Claude Code skill orchestrating an end-to-end "describe → working app on private GitHub" pipeline (virtual dev-team metaphor)
**Researched:** 2026-04-29
**Confidence:** HIGH for OSBuilder's own stack (verified against Anthropic skills docs, Node/Python release notes); MEDIUM for the per-build defaults menu (verified against Next.js / Tauri / FastAPI release notes; per-build research happens at runtime so menu is a starting point, not a contract)

---

## Scope

This document answers **two** stack questions, in priority order:

1. **OSBuilder's own implementation stack** — what the skill itself is built from. *Heavily prioritized.*
2. **The "research-driven defaults" menu** — opinionated starting points OSBuilder picks when scaffolding the apps it builds. *Per-build research at runtime overrides these; the menu is the fallback when research is inconclusive.*

---

# Part 1 — OSBuilder's Own Stack

## Recommended Stack (the skill itself)

### Core Technologi
