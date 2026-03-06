# FORGE ML Layer (Layer 3) - Surrogate Modeling

## Overview

The ML layer provides geometric representation learning and surrogate modeling
for lithium-ion battery cell design. It bridges the parametric CAD engine (Layer 1)
with physics-based simulation (PyBaMM) to train ML models that predict
electrochemical and thermal properties from geometric design parameters.

## Architecture

```
batch/              Batch geometry generation from parametric ranges (LHS, grid)
  ->
simulation/         PyBaMM DFN/TSPMe simulation -> voltage, temperature, capacity
  ->
dataset/            Dataset assembly, storage, and loading
  ->
representations/    Geometric encoding (parametric vectors, point clouds, B-Rep)
  ->
models/             Surrogate model definitions (feedforward NN, GNN, PINN)
  ->
training/           Training loop, evaluation, experiment tracking
```

### Supporting modules

- `common/` - Shared dataclasses and type definitions used across the ML layer
- `sensitivity/` - PyBOP Sobol screening (prerequisite before dataset generation)

## ML Target Properties

1. **Rate capability** (primary) - capacity at high C-rate as fraction of C/10 capacity
2. **Maximum temperature during fast charge** (secondary) - continuous, safety-critical
3. **Lithium plating onset** (stretch goal) - threshold detection, model-form dependent

## Key Design Parameters

| Parameter | Range | Rationale |
|-----------|-------|-----------|
| Electrode thickness | 50-200 um | Transport limitation transition at ~100 um |
| Electrode porosity | 0.20-0.50 | Electronic/ionic transport crossover |
| Separator thickness | 10-30 um | Low sensitivity (narrow range) |
| Cell dimensions | 50-300 mm | Small to large format |
| Tab count | 1-4 per electrode | Thermal/current distribution effects |
| Tab position | Same-side, opposite, distributed | Topology variations |

## Status

Interface definitions only. Implementation follows:
1. PyBOP Sobol sensitivity screening
2. Dataset generation (5,000-10,000 configurations)
3. Representation extraction and model training
