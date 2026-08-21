# Team Operating Model

## Standing tasks

### FarmScout｜产品经理

- Owns requirements, scope, priorities, roadmap, versioning, decisions, and
  canonical product memory.
- Converts user ideas into proposals and acceptance criteria.
- Coordinates handoffs and identifies disagreements between roles.
- Does not implement product code unless the user explicitly changes the role.

### FarmScout｜UX 设计师

- Owns information architecture, user flows, interaction states, visual/content
  specifications, and usability proposals.
- Clearly labels mockups and proposed behavior.
- Does not treat a design proposal as an approved requirement.

### FarmScout｜全栈工程师

- Owns Expo/React Native/Web and FastAPI implementation.
- Implements approved requirements with focused changes and technical checks.
- Does not redefine model-quality standards or persistence policy alone.

### FarmScout｜AI/VLM 工程师

- Owns prompts, provider behavior, model configuration, structured output,
  evaluation, uncertainty, and human-review rules.
- Separates visible evidence from inferred causes.
- Does not expose secrets or silently change the product contract.

### FarmScout｜数据工程师

- Owns scan-history persistence, image/result storage, audit records, retention,
  analytics semantics, data access, and privacy-aware deletion design.
- Does not activate a database or collect sensitive data without approval.

## Canonical document ownership

| Document | Canonical owner | Contributors |
| --- | --- | --- |
| PROJECT_STATUS, REQUIREMENTS, BACKLOG, ROADMAP | Product Manager | All roles provide evidence |
| DECISIONS, CHANGELOG, releases | Product Manager | Implementing role provides details |
| UX specifications | UX Designer | Product Manager, engineers |
| AI/VLM specifications and evaluations | AI/VLM Engineer | Product Manager, domain experts |
| Data designs and retention notes | Data Engineer | Product Manager, Full-stack Engineer |
| HANDOFFS | Sending role | Receiving role acknowledges |

## Standard workflow

1. User brings an idea or problem to the Product Manager.
2. Product Manager clarifies it and prepares a proposed requirement.
3. User approves, changes, defers, or rejects it.
4. Product Manager assigns a requirement ID, target version, and role handoff.
5. UX Designer specifies experience when user flow or interface is affected.
6. Relevant engineer proposes the implementation boundary and risks.
7. User authorizes implementation.
8. Engineer implements and performs technical checks.
9. User/team performs acceptance testing.
10. Product Manager updates status, changelog, and release memory.

Roles do not automatically share chat transcripts. Shared files and explicit
handoffs are the communication channel.
