# ML Layer

The ML layer (orge.ml) provides geometric representation learning and surrogate modeling for predicting electrochemical and thermal properties from cell geometry.

*This layer is currently at the interface-definition stage. Implementation follows PyBOP sensitivity screening.*

## ML Targets

1. **Rate capability** (primary) - capacity retention at elevated C-rates
2. **Maximum temperature during fast charge** (secondary)
3. **Lithium plating onset** (stretch goal)

## Pipeline

BatchGenerator -> SimulationRunner -> SensitivityScreener -> DatasetBuilder -> RepresentationExtractor -> SurrogateModel -> TrainingPipeline
