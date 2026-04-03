# 🛠️ Coding Standards & Instructions

## 🧹 Code Cleanup & Refactoring
- **CRITICAL**: Always perform a complete cleanup after refactoring.
- **No Dead Code**: Remove any unused imports, functions, or variables immediately after they are no longer needed.
- **Consistency**: Ensure that any changes to names or patterns are propagated throughout the entire file or project.
- **Indentation**: Verify and fix Python indentation and scoping after any automated tool edits.
- **Global Context**: Before finishing a task, scan the modified files for "orphan" variables or logic that lost its purpose during the refactor.

## 🏗️ Architectural Patterns
- Follow the **Signal/Slot pattern** (PySide6) for all cross-thread communication.
- Maintain the **Glass UI** and **9-Theme System** standards for all GUI elements.
- Ensure **Hardware Fallback** (CUDA to CPU) is implemented for all model-related logic.

## 📝 Documentation & Logging
- Use **Correlation IDs** for all cross-thread log tracing.
- Keep the `agent_manifest.md` updated with the latest mission status and architectural changes.
