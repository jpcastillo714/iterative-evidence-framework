# ZIP Content Verification Report

**Artifact Tested**: [`dist/iterative-evidence-framework-0.1.0.zip`](dist/iterative-evidence-framework-0.1.0.zip)  
**Date**: 2026-08-05  
**SHA-256 Hash**: `efe52f599ccc9158634d1206625caf162b95ee0a8992fc5e1870352c504bbc04`  
**File Count**: 7  
**Build Command**: `specify bundle build --path <clean-staging-dir> --output dist`  

---

## 1. Verified Archive Member List

Inspected using Python `zipfile.ZipFile(r'dist\iterative-evidence-framework-0.1.0.zip')`:

```text
1. README.md
2. bundle.yml
3. core/docs/verification_contract_spec.md
4. core/templates/charter-template.md
5. extension/commands/iterate.frame.md
6. extension/extension.yml
7. workflows/minimal-workflow.yml
```

---

## 2. Exclusion Verification Checklist

- [x] `tests/` directory and test runners (`tests/run_verification_suite.py`, `tests/results.json`): **EXCLUDED**
- [x] `verification/` raw run directories (`verification/runs/VRN-XXX/`): **EXCLUDED**
- [x] Internal Spec Kit execution state (`.specify/`): **EXCLUDED**
- [x] Internal scratch scripts (`scratch/`): **EXCLUDED**
- [x] Office / spec documents (`plan.docx`, `doc.docx`): **EXCLUDED**
- [x] Workspace checklist & evaluation docs (`task.md`, `phase-0.1-evaluation.md`, `decision-request.md`): **EXCLUDED**

---

## 3. Conclusion

The build artifact `dist/iterative-evidence-framework-0.1.0.zip` contains **exclusively 7 production files**. It is 100% clean, reproducible, and free of extraneous test logs or workspace state.
