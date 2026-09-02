# Bundle Component Resolution Technical Report

**Framework Extension**: Iterative Evidence Framework (IEF)  
**Date**: 2026-08-05  
**Target Toolkit**: GitHub Spec Kit (`specify-cli` v0.16.0)  
**Subject**: Technical Analysis of Local Bundle Component Resolution & `specify bundle install`  

---

## 1. Executive Summary

This report analyzes why single-step bundle installation (`specify bundle install <zip-path>`) fails when executed against a local bundle containing custom extensions (`ief`), and explains the exact technical mechanism within `specify-cli` v0.16.0.

---

## 2. Technical Investigation of `specify-cli` v0.16.0

### Component Resolution Flow
In Spec Kit 0.16.0, `specify bundle install <zip-path>` unpacks the `.zip` archive to a temporary directory and parses `bundle.yml`. For each component declared under `provides.extensions`, `specify-cli` invokes the primitive extension installer (`_ExtensionKindManager._do_install` in `specify_cli.bundler.services.primitives`).

### Source Code Line Analysis
```python
# specify_cli/bundler/services/primitives.py

bundled = _locate_bundled_extension(component.id)
if bundled is not None:
    # 1. Installs built-in first-party extensions shipped inside specify_cli package
    self._manager.install_from_directory(bundled, ...)
    return

# 2. If not a built-in extension, query ExtensionCatalog
catalog = ExtensionCatalog(self._root)
info = catalog.get_extension_info(component.id)
if not info:
    raise BundlerError(f"Extension '{component.id}' not found in any catalog.")
```

### Empirical Finding
1. **Built-in Check (`_locate_bundled_extension`)**: Checks if `ief` is a first-party extension bundled inside Python's installed `specify_cli` package assets. Returns `None`.
2. **Catalog Stack Query (`ExtensionCatalog.get_extension_info`)**: Searches active catalog stack files (`catalog.json`). Because `ief` is a local custom extension that has not been published to an online or local catalog stack, `info` is `None`.
3. **Execution Failure**: Spec Kit raises `BundlerError: Extension 'ief' not found in any catalog.` with Exit Code 1.

---

## 3. Distinction: Single-Step `bundle install` vs Manual Component Installation

| Feature | Single-Step `specify bundle install` | Manual Component Installation Workaround |
| :--- | :--- | :--- |
| **Command** | `specify bundle install <zip-path>` | `specify extension add --dev ./extension` & `specify workflow add ./workflows/minimal-workflow.yml` |
| **Spec Kit Primitive** | `BundlerInstaller` (all components in one step) | Individual primitive CLI commands |
| **Catalog Requirement** | **Requires catalog registration** for non-built-in extensions | **Direct local path installation** in dev mode (`--dev`) |
| **Status in Phase 0.3** | **BLOCKED** (Exit Code 1) | **EXECUTED WORKAROUND** (Exit Code 0) |
| **Provenance Record** | Written to `.specify/bundles.json` | Recorded separately in extension & workflow registries |

---

## 4. Architectural Impact & Recommendation

Because single-step `specify bundle install` is **BLOCKED** for local un-cataloged extensions, projects using local IEF bundles must either:
1. Register a local catalog source (`catalog.json`) prior to running `specify bundle install`.
2. Or use manual component installation (`specify extension add --dev` and `specify workflow add`) from unpacked bundle assets as an installation workaround under Architecture B.
