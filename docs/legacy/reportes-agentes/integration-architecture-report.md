# Integration Architecture Report: Spec Kit & Antigravity IDE

**Framework Extension**: Iterative Evidence Framework (IEF)  
**Date**: 2026-08-05  
**Target Toolkit**: GitHub Spec Kit (`specify-cli` v0.16.0)  
**Target Agent Environment**: Antigravity IDE (`agy`)  

---

## 1. Investigation of Spec Kit `agy` Integration Source Code

Inspection of `specify-cli` v0.16.0 Python source code (`specify_cli.integrations.agy` and `specify_cli.integrations.base`) reveals the exact mechanism behind the `agy` integration:

### Source Code Analysis Summary
```python
class AgyIntegration(SkillsIntegration):
    key = "agy"
    config = {
        "name": "Antigravity",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://antigravity.google/",
        "requires_cli": True,
    }

    def build_exec_args(self, prompt: str, *, model: str | None = None, output_json: bool = True) -> list[str] | None:
        args = [self._resolve_executable(), "--print", prompt]
        self._apply_extra_args_env_var(args)
        return args
```

### Empirical Answers to Technical Questions

1. **What binary does `agy` expect?**
   - It expects an executable named `agy` (default) or the value set in `SPECKIT_INTEGRATION_AGY_EXECUTABLE`.
2. **How does it detect that binary?**
   - `_resolve_executable()` checks `os.environ.get("SPECKIT_INTEGRATION_AGY_EXECUTABLE")` and falls back to `"agy"`. When executing subprocesses, Spec Kit delegates to system `PATH` resolution via Python `shutil.which`.
3. **How does it construct the dispatch command?**
   - `build_exec_args(prompt)` produces `["agy", "--print", prompt]`.
4. **What environment variables does it use?**
   - `SPECKIT_INTEGRATION_AGY_EXECUTABLE`: Overrides binary path (default: `agy`).
   - `SPECKIT_INTEGRATION_AGY_EXTRA_ARGS`: Injects extra CLI flags via `shlex.split`.
5. **Does Antigravity actually install that binary?**
   - **No**. Empirical system PATH checks (`shutil.which('agy')` and `where agy`) return `None` (Exit Code 1). Antigravity is an IDE / Agent Extension environment, not a standalone CLI binary on OS PATH.
6. **Can the binary be executed from terminal?**
   - **No**, because no `agy` binary exists on PATH. Running `specify workflow run` on `type: command` steps fails with:
     `Cannot dispatch command 'speckit.ief.frame': integration None CLI not found or not installed.`
7. **Can Antigravity receive prompts from Spec Kit?**
   - Spec Kit cannot push prompts to Antigravity non-interactively via OS subprocess because there is no CLI listener binary. Antigravity reads agent skills from `.agents/skills/speckit-<name>/SKILL.md` when the user triggers them inside the IDE.
8. **Is the integration supported or merely declared?**
   - **Declared / Scaffolding-Only**: `specify init --integration agy` correctly scaffolds skills into `.agents/skills/`. However, non-interactive CLI dispatch of `type: command` steps via `specify workflow run` is unsupported without an external CLI binary wrapper.

---

## 2. Evaluation of Architectural Options

### Architecture A: Spec Kit Orchestrates Antigravity
`User → Spec Kit workflow → Antigravity CLI → agent → artifacts`

- **Viability**: **Unviable natively**. Requires a standalone `agy` CLI binary on OS PATH that does not exist in standard Antigravity installations.
- **Evidence**: `VRN-F0-020-001` failed on command step dispatch with exit code 1 / blocked status. `shutil.which('agy')` returned `None`.
- **Limitations**:
  - Requires writing and maintaining a custom CLI wrapper executable on every developer machine.
  - Cannot pass structured context to Antigravity's IDE memory window via subprocess flags without custom IPC.
- **Portability**: Poor. Requires separate CLI wrappers for Claude Code, Hermes, and Antigravity.
- **Pause & Resume**: Handled by Spec Kit workflow state (`status: paused` / `specify workflow resume`), but command execution step itself fails.
- **Observability**: Process stdout/stderr capture works for external CLI tools, but fails when binary is absent.
- **Security**: Spawning subprocesses requires local executable trust and extra permission flags.
- **Implementation Complexity**: High (requires building cross-platform CLI daemon/shims).
- **Dependency on External CLI**: High (100% hard dependency).

---

### Architecture B: Antigravity Orchestrates Spec Kit
`User → Antigravity Agent → IEF Commands / Templates → Spec Kit Validation & Workflows → Artifacts`

- **Viability**: **Highly Viable & Native**. Antigravity agent operates directly in the project workspace, invoking `specify` CLI commands (`specify bundle validate`, `specify workflow run --json`, `specify workflow status`, `specify workflow resume`), populating templates (`charter.md`), and reading Spec Kit skills from `.agents/skills/`.
- **Evidence**: Verified by all Phase 0.1 real runs (`VRN-F0-001-001` through `VRN-F0-023-001`). Workflows with `type: shell` and `type: gate` pause and resume cleanly with exit code 0 and valid JSON outputs.
- **Limitations**:
  - Requires agent prompts / skills to instruct the agent on when to run Spec Kit validation commands.
- **Portability**: **Excellent**. Antigravity, Claude Code, and Hermes all support skill/command registration layouts (`.agents/skills/` for Antigravity, `.claude/skills/` for Claude, etc.).
- **Pause & Resume**: Fully supported natively via Spec Kit gate steps (`type: gate`). Antigravity inspects `status == "paused"`, prompts the human user, and executes `specify workflow resume <run_id> --input choice=approve`.
- **Observability**: Complete. All CLI commands output JSON (`--json`) directly consumed by the agent and logged to `verification/runs/VRN-XXX/`.
- **Security**: High. Runs within agent workspace boundaries using standard Spec Kit CLI commands.
- **Implementation Complexity**: Low / Elegant (uses existing Spec Kit CLI primitives without extra shims).
- **Dependency on External CLI**: Zero external CLI dependency (only relies on standard `specify-cli` package installed in Python environment).

---

## 3. Comparative Evaluation Summary

| Criterion | Architecture A (Spec Kit → Agent) | Architecture B (Agent → Spec Kit) |
| :--- | :--- | :--- |
| **Viability** | Unviable (Missing `agy` binary) | **Highly Viable (Native IDE Agent)** |
| **CLI Dependency** | Requires external `agy` binary on PATH | **No external binary needed** |
| **Pause / Resume** | Spec Kit state machine | **Spec Kit gate steps + Agent execution** |
| **Portability** | Requires custom CLI shims per tool | **Universal across AGY, Claude, Hermes** |
| **Observability** | Process stdout capture | **Structured JSON output logging** |
| **Complexity** | High (Custom daemon/wrapper) | **Low (Native skills & CLI primitives)** |

---

## 4. Architectural Recommendation

**Selected Architecture**: **Architecture B (Antigravity Orchestrates Spec Kit)**

Under Architecture B, Antigravity acts as the primary intelligent agent. It executes IEF commands, populates charter templates, and validates project artifacts using Spec Kit's CLI primitives (`specify bundle validate`, `specify workflow run`, `specify workflow status`, `specify workflow resume`). Workflows utilize `type: shell` and `type: gate` steps for deterministic checkpointing without relying on unavailable external CLI binaries.
