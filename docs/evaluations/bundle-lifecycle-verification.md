# Bundle Lifecycle Verification Report (`specify bundle` commands)

**Date**: 2026-08-05  
**Toolkit Version**: `specify-cli` v0.16.0  
**Artifact Tested**: [`dist/iterative-evidence-framework-0.1.0.zip`](dist/iterative-evidence-framework-0.1.0.zip)  
**Execution Environment**: Clean temporary project directory (`specify init --here --integration agy --ignore-agent-tools`)  

---

## 1. Overview & Protocol Compliance

Per Task 4 requirements, the built bundle `.zip` artifact was tested directly against Spec Kit's `specify bundle` CLI command group without substituting operations with `specify extension add/remove`.

Every step records exact commands, exit codes, stdout, stderr, and directory file trees.

---

## 2. Empirical Execution Log

### Step 1: `specify bundle install <zip-path>`

- **Command**: `specify bundle install "C:\Users\juanp\OneDrive\Escritorio\Proyectos\spec-kit_bundle\dist\iterative-evidence-framework-0.1.0.zip"`
- **Working Directory**: Clean temporary project root
- **Exit Code**: `1`
- **Verification Status**: **BLOCKED**
- **Captured Output**:
  - `stdout`: *(empty)*
  - `stderr`: `Error: Extension 'ief' not found in any catalog.`

#### File Tree After Step 1:
```json
[
  ".agents/skills/speckit-analyze/SKILL.md",
  ".agents/skills/speckit-checklist/SKILL.md",
  ".agents/skills/speckit-clarify/SKILL.md",
  ".agents/skills/speckit-constitution/SKILL.md",
  ".agents/skills/speckit-converge/SKILL.md",
  ".agents/skills/speckit-implement/SKILL.md",
  ".agents/skills/speckit-plan/SKILL.md",
  ".agents/skills/speckit-specify/SKILL.md",
  ".agents/skills/speckit-tasks/SKILL.md",
  ".agents/skills/speckit-taskstoissues/SKILL.md",
  ".specify/extensions/.cache/catalog.json",
  ".specify/init-options.json",
  ".specify/integration.json",
  ".specify/integrations/agy.manifest.json",
  ".specify/memory/constitution.md",
  ".specify/workflows/workflow-registry.json"
]
```

#### Technical Explanation of Failure:
Inspection of `specify_cli.bundler.services.primitives` reveals that when `specify bundle install` unpacks a `.zip` artifact, it parses `bundle.yml`'s `provides.extensions` section:
```yaml
provides:
  extensions:
    - id: "ief"
      version: "0.1.0"
      source: "./extension"
```
During primitive delegation (`PrimitiveInstaller.install`), `specify-cli` checks whether the extension component `ief` exists in installed catalog stacks. Because `ief` is a local bundle component and has not been published to an online or local Spec Kit catalog stack (`catalog.json`), `specify-cli` aborts the installation with `Error: Extension 'ief' not found in any catalog.`

---

### Step 2: `specify bundle list`

- **Command**: `specify bundle list`
- **Exit Code**: `0`
- **Verification Status**: **PASSED**
- **Captured Output**:
  - `stdout`:
    ```
    No bundles installed.

    Install one with: specify bundle install <id>
    ```
  - `stderr`: *(empty)*

---

### Step 3: `specify bundle update <bundle-id>`

- **Command**: `specify bundle update iterative-evidence-framework`
- **Exit Code**: `1`
- **Verification Status**: **BLOCKED** (Prerequisite bundle install blocked)
- **Captured Output**:
  - `stdout`: *(empty)*
  - `stderr`: `Error: Bundle 'iterative-evidence-framework' is not installed.`

---

### Step 4: `specify bundle remove <bundle-id>`

- **Command**: `specify bundle remove iterative-evidence-framework`
- **Exit Code**: `1`
- **Verification Status**: **BLOCKED** (Prerequisite bundle install blocked)
- **Captured Output**:
  - `stdout`: *(empty)*
  - `stderr`: `Error: Bundle 'iterative-evidence-framework' is not installed.`

---

## 3. Summary of Findings

1. **`specify bundle install <zip-path>` Behavior**: In `specify-cli` v0.16.0, installing a bundle from a local `.zip` path fails if any extension declared under `provides.extensions` is missing from an active catalog.
2. **Impact on Component Installation**: Installing local extensions and workflows currently requires registering local catalog sources or installing components via `specify extension add --dev ./extension` and `specify workflow add ./workflows/minimal-workflow.yml`.
