# OSBuilder Question Bank — Web Playbook (v1)

> Plain-English clarifying questions for the PM role intake flow.
> Loaded on-demand by SKILL.md. NOT pulled into SKILL.md (line limit).
> Ask at most 5 questions per build. Do not ask all questions on every build.
> Never use technical jargon — see the plain-English substitutes section below.

## Q: Devices

"Should this work on phones and tablets too, or just on desktop computers?"

- Yes, phones and tablets too → note in spec: mobile layout needed; Tailwind utilities applied
- Just desktop is fine → note in spec: desktop-only layout; no mobile-specific breakpoints needed
- I don't know, you decide → YES (phones and tablets — safer default for web apps)

## Q: Users

"Will multiple people use this app with separate accounts, or is it just for you?"

- Multiple people with their own accounts → note in spec: multi-user auth needed; Postgres via Docker
- Just for me, no logins → note in spec: single-user mode; local storage or simple session
- I don't know, you decide → Multiple people (multi-user is the safer default for web apps)

## Q: Data persistence

"Do you need to save information between visits — like a list of things, records, or history?"

- Yes, save data between visits → note in spec: database needed; Postgres via compose.yaml
- No, it's just for the current visit → note in spec: in-memory or session storage only
- I don't know, you decide → YES (save data — almost all apps need this)

## Q: External access

"Should other apps or services be able to talk to this app automatically?"

- Yes, other apps need to connect to it → note in spec: web API path needed; document routes in spec
- No, it's just for people to use in a browser → note in spec: UI-only; no machine-to-machine access
- I don't know, you decide → NO (UI-only — most apps don't need this at first)

## Q: File uploads

"Do users need to upload files — like photos, PDFs, or documents?"

- Yes, users will upload files → note in spec: file upload handling needed; storage solution required
- No, no file uploads needed → note in spec: no file handling needed
- I don't know, you decide → NO (no uploads — add later if needed)

## Q: Privacy

"Should this app be private (only people you invite can use it) or open to anyone?"

- Private, invite-only → note in spec: auth required; no public signup
- Open to anyone who finds it → note in spec: public access; consider rate limiting
- I don't know, you decide → PRIVATE (safer default; easier to open up than to lock down)

## Plain-English substitutes

When writing or editing questions, use plain-English alternatives instead of technical terms.
Examples:
- "works on phones and tablets" instead of the technical layout term
- "other apps can connect to it" instead of the technical API term
- "save data between visits" instead of the technical persistence term
- "loads quickly for people far away" instead of the technical distribution term
- "handle logins and permissions" instead of the technical auth layer term

Never mention server-side or client-side rendering modes — users do not need to know these exist.
