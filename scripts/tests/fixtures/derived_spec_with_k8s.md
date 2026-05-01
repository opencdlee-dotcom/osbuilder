# Derived Spec

**Goal:** Build a multi-tenant SaaS with Kubernetes orchestration and microservices for handling user onboarding at scale
**App type:** multi-user-web
**Playbook:** web
**Features:**
- User signup and login
- Team workspaces
- Per-tenant database isolation via Kubernetes namespaces
- Service mesh for inter-pod communication
**Stack hints:** Next.js + Postgres + Helm chart for k8s deploy
