"""
Automated Test Suite for Increment F1.1: Frame Verificable
Tests initiative/charter.md creation, verification contract, VRN evidence logging,
non-overwrite safety, and workflow gate pause & resume under Architecture B.
"""

import json
import os
import shutil
import subprocess
import tempfile
import sys
import yaml

BUNDLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = r"C:\Users\juanp\AppData\Local\Programs\Python\Python311\python.exe"

def test_f1_1_end_to_end():
    tmp_dir = tempfile.mkdtemp(prefix="f1_1_test_proj_")
    print(f"=== TESTING INCREMENT F1.1 IN CLEAN PROJ: {tmp_dir} ===", flush=True)

    # 1. specify init
    res_init = subprocess.run("specify init --here --integration agy --ignore-agent-tools", cwd=tmp_dir, shell=True, capture_output=True, text=True)
    assert res_init.returncode == 0, f"specify init failed: {res_init.stderr}"

    # 2. specify extension add --dev ./extension
    ext_src = os.path.join(BUNDLE_DIR, "extension")
    res_ext = subprocess.run(f'specify extension add --dev "{ext_src}"', cwd=tmp_dir, shell=True, capture_output=True, text=True)
    assert res_ext.returncode == 0, f"specify extension add failed: {res_ext.stderr}"

    # 3. specify workflow add ./workflows/f1-1-frame-workflow.yml
    wf_src = os.path.join(BUNDLE_DIR, "workflows", "f1-1-frame-workflow.yml")
    res_wf = subprocess.run(f'specify workflow add "{wf_src}"', cwd=tmp_dir, shell=True, capture_output=True, text=True)
    assert res_wf.returncode == 0, f"specify workflow add failed: {res_wf.stderr}"

    # Copy core/ scripts and templates into temporary project directory
    shutil.copytree(os.path.join(BUNDLE_DIR, "core"), os.path.join(tmp_dir, "core"))

    # 4. Verify skills generated for Antigravity
    skill_frame = os.path.join(tmp_dir, ".agents", "skills", "speckit-ief-frame", "SKILL.md")
    skill_verify = os.path.join(tmp_dir, ".agents", "skills", "speckit-ief-verify", "SKILL.md")
    assert os.path.exists(skill_frame), f"Skill speckit-ief-frame missing: {skill_frame}"
    assert os.path.exists(skill_verify), f"Skill speckit-ief-verify missing: {skill_verify}"
    print("[PASS] Skills generated successfully in .agents/skills/", flush=True)

    # 5. Run verify_frame.py script in clean project
    sys.path.insert(0, os.path.join(BUNDLE_DIR, "core", "scripts"))
    import verify_frame
    res_engine = verify_frame.run_frame_and_verify(
        project_dir=tmp_dir,
        initiative_name="Iniciativa de Producción F1.1",
        user_input={"purpose": "Demostrar encuadre verificable IEF", "context": "Fase 1.1 MVP", "outcome": "Charter y evidencias generadas", "constraints": "Tiempo y presupuesto acotados"}
    )
    assert res_engine["suite_status"] == "passed"
    print("[PASS] Frame & Verify engine executed successfully (Status: passed)", flush=True)

    # 6. Verify created artifacts in initiative/
    init_charter = os.path.join(tmp_dir, "initiative", "charter.md")
    verif_contract = os.path.join(tmp_dir, "initiative", "verification", "verification-contract.yml")
    verif_summary = os.path.join(tmp_dir, "initiative", "verification", "verification-summary.md")
    runs_dir = os.path.join(tmp_dir, "initiative", "verification", "runs")

    assert os.path.exists(init_charter), "initiative/charter.md missing"
    assert os.path.exists(verif_contract), "initiative/verification/verification-contract.yml missing"
    assert os.path.exists(verif_summary), "initiative/verification/verification-summary.md missing"
    assert os.path.exists(runs_dir) and len(os.listdir(runs_dir)) == 4, f"Expected 4 VRN run directories, found {len(os.listdir(runs_dir))}"
    print("[PASS] Initiative artifacts verified (charter.md, contract, summary, 4 VRN run folders)", flush=True)

    # 7. Test non-overwrite safety: modify charter.md and re-run frame engine
    with open(init_charter, "a", encoding="utf-8") as f:
        f.write("\n<!-- User Edit: Manual constraint added -->")
    mtime_before = os.path.getmtime(init_charter)

    res_engine_2 = verify_frame.run_frame_and_verify(project_dir=tmp_dir, initiative_name="Attempt Overwrite")
    assert res_engine_2["created_new_charter"] is False, "Frame engine should NOT overwrite existing charter"
    with open(init_charter, "r", encoding="utf-8") as f:
        text_after = f.read()
    assert "User Edit: Manual constraint added" in text_after, "User edit was overwritten!"
    print("[PASS] Non-overwrite safety verified (User edit preserved)", flush=True)

    # 8. Test real Spec Kit workflow run & pause at gate & resume
    res_wf_run = subprocess.run(f'specify workflow run f1-1-frame-workflow --json', cwd=tmp_dir, shell=True, capture_output=True, text=True)
    if res_wf_run.returncode != 0:
        print("WF RUN RETURN CODE:", res_wf_run.returncode, flush=True)
        print("WF RUN STDOUT:\n", res_wf_run.stdout, flush=True)
        print("WF RUN STDERR:\n", res_wf_run.stderr, flush=True)
    assert res_wf_run.returncode == 0, f"specify workflow run failed: {res_wf_run.stderr}"
    data_run = json.loads(res_wf_run.stdout)
    run_id = data_run["run_id"]
    assert data_run["status"] == "paused"
    assert data_run["current_step_id"] == "checkpoint"
    print(f"[PASS] Workflow F1.1 paused at gate checkpoint (Run ID: {run_id})", flush=True)

    # Status check
    res_wf_stat = subprocess.run(f'specify workflow status {run_id} --json', cwd=tmp_dir, shell=True, capture_output=True, text=True)
    assert res_wf_stat.returncode == 0
    data_stat = json.loads(res_wf_stat.stdout)
    assert data_stat["status"] == "paused"

    # Resume workflow with choice=approve
    res_wf_resume = subprocess.run(f'specify workflow resume {run_id} --input choice=approve --json', cwd=tmp_dir, shell=True, capture_output=True, text=True)
    assert res_wf_resume.returncode == 0, f"specify workflow resume failed: {res_wf_resume.stderr}"
    data_resume = json.loads(res_wf_resume.stdout)
    assert data_resume["status"] == "completed"
    print(f"[PASS] Workflow F1.1 resumed and reached status completed (Run ID: {run_id})", flush=True)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print("\n=== INCREMENT F1.1 TEST SUITE PASSED CLEANLY ===", flush=True)

if __name__ == '__main__':
    test_f1_1_end_to_end()
