# Architecture

FORGE uses a layered architecture separating deterministic engineering computation from AI-driven generation and prediction.

*Detailed architecture documentation will be expanded from the project's internal design documents.*

## Four-Layer Design

### Layer 1 - Engine (orge.engine)
Deterministic parametric modeling. No AI. Handles geometry, mass/energy calculations, BOM, cost estimation, validation, and CAD export (STEP, STL, FreeCAD).

### Layer 2 - AXIOM (orge.axiom)
Neuro-symbolic supervision of LLM-generated specifications. Three components: Der Generator, Der Validator, Der Supervisor.

### Layer 3 - ML Extensions (orge.ml)
Geometric representation learning and surrogate modeling. Interfaces defined; implementation in progress.

### Layer 4 - Integration (orge.integration)
Documented stubs for PyBOP optimization, CFD/FEM connectivity via preCICE/OpenFOAM.
