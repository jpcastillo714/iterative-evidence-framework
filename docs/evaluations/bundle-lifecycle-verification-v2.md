# Bundle Lifecycle Verification Report (v2 - Hardened Empirical Audit)

**Date**: 2026-08-05  
**Toolkit Version**: `specify-cli` v0.16.0  
**Artifact Tested**: [`dist/iterative-evidence-framework-0.1.0.zip`](dist/iterative-evidence-framework-0.1.0.zip)  
**Execution Environment**: Clean temporary project directory (`specify init --here --integration agy --ignore-agent-tools`)  

---

## 1. Executive Summary & Audit Correction

This report replaces `bundle-lifecycle-verification.md` with a strict, empirical classification of all bundle lifecycle operations.

As audited during Phase 0.3 review:
- Single-step bundle installation (`specify bundle install <zip-path>`) **FAILED** with Exit Code 1 because Spec Kit 0.16.0 requires non-built-in extensions (`ief`) to be present in an active catalog stack.
- The workaround of unzipping the archive and invoking `specify extension add --dev` and `specify workflow add` is a **manual component installation workaround**, and MUST NOT be described as a single-step `bundle install` or native bundle lifecycle.

---

## 2. Empirical Verification Matrix

| Operation | Command Executed | Exit Code | Verification Status | Empirical Observation |
| :--- | :--- | :---: | :---: | :--- |
| **Build** | `specify bundle build --path <clean-stage> --output dist` | 0 | **PASSED** | Built clean 7-file `.zip` archive without test/verification logs |
| **Install (Bundle)** | `specify bundle install "dist/iterative-evidence-framework-0.1.0.zip"` | 1 | **BLOCKED** | `Error: Extension 'ief' not found in any catalog.` |
| **List (Bundle)** | `specify bundle list` | 0 | **PASSED** | `No bundles installed.` |
| **Update (Bundle)** | `specify bundle update iterative-evidence-framework` | 1 | **BLOCKED** | `Error: Bundle 'iterative-evidence-framework' is not installed.` |
| **Remove (Bundle)** | `specify bundle remove iterative-evidence-framework` | 1 | **BLOCKED** | `Error: Bundle 'iterative-evidence-framework' is not installed.` |
| **Manual Component Workaround** | `specify extension add --dev ./extension` & `specify workflow add ./workflows/minimal-workflow.yml` | 0 | **WORKAROUND EXECUTED** | Manual installation of unpacked extension and workflow components |

---

## 3. Detailed Logs & Artifact Trees

### 3.1 Single-Step `specify bundle install` (Blocked)
- **Command**: `specify bundle install "C:\Users\juanp\OneDrive\Escritorio\Proyectos\spec-kit_bundle\dist\iterative-evidence-framework-0.1.0.zip"`
- **Exit Code**: `1`
- **Stderr**: `Error: Extension 'ief' not found in any catalog.`
- **File Tree State**: No `.specify/bundles.json` provenance record created.

### 3.2 Manual Component Workaround (Executed)
- **Commands**:
  1. `specify extension add --dev "./.specify/bundle-staging/extension"` (Exit Code: 0)
  2. `specify workflow add "./.specify/bundle-staging/workflows/minimal-workflow.yml"` (Exit Code: 0)
- **Result**:
  - Skill generated: `.agents/skills/speckit-ief-frame/SKILL.md` (Exit Code: 0)
  - Workflow added: `.specify/workflows/minimal-workflow.yml` (Exit Code: 0)

---

## 4. Conclusion

Single-step native bundle lifecycle commands (`specify bundle install`, `update`, `remove`) are **BLOCKED** in Spec Kit 0.16.0 for local un-cataloged extensions. Projects deploying the IEF bundle prior to catalog publication must use manual component installation from unpacked bundle assets.
