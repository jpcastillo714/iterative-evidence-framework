# Technical Compatibility Report: Spec Kit & Iterative Evidence Framework (Phase 0.1 Verification Hardening)

**Date**: 2026-08-05  
**Framework Version**: 0.1.0 (Phase 0.1 Verification Hardening)  
**Target Toolkit**: GitHub Spec Kit (`specify-cli` v0.16.0)  
**Evidence Storage**: [`verification/runs/`](verification/runs/)  

---

## 1. Executive Summary

This report documents the **Phase 0.1 Verification Hardening** results for the **Iterative Evidence Framework (IEF)** on GitHub Spec Kit (`specify-cli` v0.16.0).

All mock executions and file-copying simulations were replaced by **real Spec Kit CLI operations** (`specify bundle validate`, `specify bundle build`, `specify init`, `specify extension add --dev`, `specify workflow add`, `specify workflow run`, `specify workflow status`, `specify workflow resume`, and `specify extension remove --force`).

Every test execution produced raw un-truncated evidence stored in [`verification/runs/VRN-XXX/`](verification/runs/).

---

## 2. Hardened Verification Suite Summary

- **Total Test Runs**: 13
- **Passed**: 12
- **Blocked**: 1 (`VRN-F0-020-001`: Workflow Command Step Dispatch requiring external agent CLI binary)
- **Failed**: 0
- **Aggregator Mathematical Consistency**: Verified (`13 = 12 + 0 + 1 + 0 + 0`)
- **Aggregator Record**: [`tests/results.json`](tests/results.json)

---

## 3. Real Verification Runs & Raw Evidence

| VRN ID | Test ID | Description | Type | Verification Level | Exit Code | Status | Raw Evidence |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `VRN-F0-001-001` | `TST-F0-001` | Validate bundle manifest (`specify bundle validate --path . --offline`) | static | executed | 0 | **PASSED** | [`VRN-F0-001-001`](verification/runs/VRN-F0-001-001/) |
| `VRN-F0-002-001` | `TST-F0-002` | Validate extension manifest schema (v1.0 & `speckit.ief.frame`) | static | asserted | 0 | **PASSED** | [`VRN-F0-002-001`](verification/runs/VRN-F0-002-001/) |
| `VRN-F0-003-001` | `TST-F0-003` | Validate workflow YAML schema (`minimal-workflow.yml`) | static | asserted | 0 | **PASSED** | [`VRN-F0-003-001`](verification/runs/VRN-F0-003-001/) |
| `VRN-F0-004-001` | `TST-F0-004` | Inspect uninstalled bundle info (`specify bundle info`) | negative | executed | 1 | **PASSED** | [`VRN-F0-004-001`](verification/runs/VRN-F0-004-001/) |
| `VRN-F0-005-001` | `TST-F0-005` | Build bundle artifact (`specify bundle build --output dist`) | end-to-end | reproduced | 0 | **PASSED** | [`VRN-F0-005-001`](verification/runs/VRN-F0-005-001/) |
| `VRN-F0-010-001` | `TST-F0-010` | Project init & `specify extension add --dev` + `specify workflow add` | integration | executed | 0 | **PASSED** | [`VRN-F0-010-001`](verification/runs/VRN-F0-010-001/) |
| `VRN-F0-012-001` | `TST-F0-012` | Charter.md creation from template | unit | asserted | 0 | **PASSED** | [`VRN-F0-012-001`](verification/runs/VRN-F0-012-001/) |
| `VRN-F0-016-001` | `TST-F0-016` | Non-overwrite safety check | integration | executed | 0 | **PASSED** | [`VRN-F0-016-001`](verification/runs/VRN-F0-016-001/) |
| `VRN-F0-020-001` | `TST-F0-020` | Workflow Command Step Dispatch (No Agent CLI on PATH) | end-to-end | executed | 1 | **BLOCKED** | [`VRN-F0-020-001`](verification/runs/VRN-F0-020-001/) |
| `VRN-F0-020-002` | `TST-F0-020` | Real Workflow Run & Gate Pause (`specify workflow run --json`) | end-to-end | executed | 0 | **PASSED** | [`VRN-F0-020-002`](verification/runs/VRN-F0-020-002/) |
| `VRN-F0-022-001` | `TST-F0-022` | Workflow Status Inspection (`specify workflow status --json`) | integration | inspected | 0 | **PASSED** | [`VRN-F0-022-001`](verification/runs/VRN-F0-022-001/) |
| `VRN-F0-023-001` | `TST-F0-023` | Real Workflow Resume & Completion (`specify workflow resume --json`) | end-to-end | reproduced | 0 | **PASSED** | [`VRN-F0-023-001`](verification/runs/VRN-F0-023-001/) |
| `VRN-F0-034-001` | `TST-F0-034` | Extension Removal (`specify extension remove --force ief`) & User Artifact Check | integration | executed | 0 | **PASSED** | [`VRN-F0-034-001`](verification/runs/VRN-F0-034-001/) |

---

## 4. Analysis of Integration Issue (`VRN-F0-020-001`)

- **Integrations Available**: 37 coding agent integrations (`agy`, `gemini`, `copilot`, `claude`, etc.).
- **Selected Integration**: `agy` (Antigravity).
- **CLI Requirement**: Spec Kit's `specify_cli` requires an agent CLI binary installed on the operating system PATH to dispatch `type: command` steps (e.g. `speckit.ief.frame`).
- **Observed Behavior**: When no `agy` CLI binary is installed on PATH, Spec Kit's workflow runner halts command step execution with error:
  `Cannot dispatch command 'speckit.ief.frame': integration None CLI not found or not installed.`
- **Resolution**:
  - Test `VRN-F0-020-001` is recorded as **BLOCKED** due to missing external agent CLI binary.
  - Test `VRN-F0-020-002` demonstrated real Spec Kit workflow execution, gate pausing (`status: paused` at `checkpoint`), status query (`specify workflow status`), and workflow resumption (`specify workflow resume --input choice=approve`), reaching `status: completed` with exit code 0.

---

## 5. User Artifact Preservation Result

Verified in `VRN-F0-034-001`: Executing `specify extension remove --force ief` removed extension files cleanly while leaving the user's `charter.md` file 100% intact.
