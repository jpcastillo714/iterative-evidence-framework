# Verification Contract & Verification as Evidence Specification

**Framework Extension**: Iterative Evidence Framework (IEF)  
**Concept Module**: Verification as Evidence (VAE)  
**Target Phase Implementation**: Phase 1 Roadmap  

---

## 1. Traceability Chain

The Iterative Evidence Framework enforces an unbreakably typed, end-to-end evidence chain:

```
CLM (Claim)
  ↳ INC (Increment)
      ↳ CRT (Evaluation Criterion)
          ↳ TST (Test Definition)
              ↳ VRN (Verification Run)
                  ↳ EVI (Evidence Artifact)
                      ↳ EVA (Evaluation)
                          ↳ DEC (Governance Decision)
```

---

## 2. Structural Separation of Verification Concepts

1. **Test Definition (`TST-XXX`) vs. Verification Run (`VRN-XXX`)**:
   - `TST-XXX`: Static declaration of verification requirements, expected outputs, test classification (`unit`, `static`, `integration`, `end-to-end`, `negative`, `manual`), required verification level (`asserted`, `inspected`, `executed`, `reproduced`, `independently-reviewed`), and requirement designation (`required` vs `optional`).
   - `VRN-XXX`: Timestamped execution instance of a `TST-XXX` test, recording:
     - `command`: The exact CLI command line executed.
     - `command_exit_code`: The raw exit code returned by the target subprocess.
     - `runner_exit_code`: The exit code returned by the test runner harness.
     - `stdout`: Raw un-truncated standard output.
     - `stderr`: Raw un-truncated standard error.
     - `duration_seconds`: Execution duration.
     - `artifacts`: List of generated output files.

2. **Disambiguation of Non-Success Outcomes**:
   - **Failed Execution**: System, syntax, or dependency failure during test execution.
   - **Rejected Hypothesis**: Test executed cleanly, but empirical results contradicted the claim threshold.
   - **Inconclusive / Blocked Result**: Test execution could not complete due to missing prerequisites (e.g. missing external binary).

3. **Suite Status Taxonomy**:
   The test suite status is classified as:
   - `passed`: All tests passed cleanly.
   - `passed-with-limitations`: All required tests passed; non-critical optional tests failed.
   - `incomplete`: One or more required verifications are `blocked` or missing.
   - `failed`: One or more required tests failed.
   - `error`: Test harness execution failure.

4. **Governance Decision Blocking**:
   Governance decision steps (`DEC-XXX`) MUST automatically block if any `required` verification run (`VRN-XXX`) is missing, failed, or marked `blocked` (`suite_status: incomplete`).

---

## 3. Verification Contract Schema (`verification-contract.yml`)

```yaml
verification_contract:
  increment_id: INC-001
  claims:
    - CLM-001
  criteria:
    - id: CRT-001
      metric: command_exit_code
      expected: 0
  tests:
    - id: TST-001
      criterion_id: CRT-001
      kind: integration
      requirement: required # required vs optional
      verification_level: executed
      command: "specify bundle validate --path . --offline"
      expected_command_exit_code: 0
```

---

## 4. Proposed `/iterate.verify` Command (Phase 1 Core)

In Phase 1, `/iterate.verify` will automate execution and logging of Verification Runs (`VRN-XXX`):

1. Parse active `verification-contract.yml`.
2. Execute declared test commands non-interactively.
3. Capture raw un-truncated `stdout` and `stderr`.
4. Store `command_exit_code` and `runner_exit_code` separately.
5. Persist evidence under `verification/runs/VRN-XXX/` (`command.txt`, `metadata.yml`, `stdout.txt`, `stderr.txt`, `result.yml`, `artifacts.yml`).
6. Compute `suite_status` (`passed`, `passed-with-limitations`, `incomplete`, `failed`, `error`).
7. Block governance decisions (`DEC-XXX`) if `suite_status` is `incomplete` or `failed`.
