# AGENTS.md (extended)

## Workspace Requirement (CRITICAL)

- The agent MUST operate from the repository root.
- Before any search, read, write, git, or test operation, verify that the working directory contains:
  - influxbro/
  - AGENTS.md
  - repository.yaml

- If these are not present:
  - STOP immediately
  - report: "Wrong working directory – repository root required"

---

## Default Test Host

- Use <http://192.168.2.200:8099> for all Home Assistant integration tests
- Use this host for:
  - API smoke tests
  - UI validation
  - integration checks
- Do NOT use localhost unless explicitly required

---

## UI Design Standard

- Before adding or modifying any GUI element:
  - consult influxbro/Template.md
- Maintain consistent layout patterns across all UI components
- Ensure:
  - consistent spacing
  - consistent card/layout structure
  - consistent naming of classes and IDs
- UI components must be validated not only on container level but also for all child elements

---

## Issue Handling Rule

- Only ask whether a request should be recorded as an issue or implemented immediately if it is a NEW request
- If the request relates to an existing issue or context:
  - continue implementation without asking

---

## Questions: Numeric Choices

- When asking the user to choose between options:
  - always provide numbered options (1, 2, 3, …)
  - allow the user to respond with just the number
- Example:
  1. Merge
  2. Rebase
  3. Fast-forward only
