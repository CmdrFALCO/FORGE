"""
Main LLM driver for cell design generation.

Orchestrates: prompt building -> LLM generation -> parsing -> validation -> retry loop -> calculation

Supports all cell types: prismatic, pouch, and cylindrical.
"""

import logging

from forge.axiom.backends import LLMBackend, get_backend
from forge.axiom.generator.parser import extract_yaml_block
from forge.axiom.generator.prompt_builder import build_retry_prompt, build_system_prompt
from forge.axiom.supervisor.result import GenerationResult
from forge.engine.calculators.cylindrical_calculator import CylindricalCalculator
from forge.engine.calculators.pouch_calculator import CellCalculator
from forge.engine.calculators.prismatic_calculator import PrismaticCalculator
from forge.engine.conversion import (
    MappingError,
    from_cylindrical_template_format,
    from_pouch_template_format,
    from_template_format,
)
from forge.engine.validation.pipeline import validate_cell_definition

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def generate_cell_design(
    request: str,
    backend: str | LLMBackend = "claude",
    api_key: str | None = None,
    calculate: bool = True,
    cell_type: str = "prismatic",
    **backend_kwargs,
) -> GenerationResult:
    """
    Generate a battery cell design from a natural language request.

    This is the main entry point for LLM-driven cell design.

    Args:
        request: Natural language design request
                 e.g., "Design a 100Ah LFP prismatic cell for ESS"
                 or "Design a 10Ah NMC pouch cell for EV"
                 or "Design a 5Ah 21700 NMC cylindrical cell"
        backend: LLM backend - "openai", "claude", "ollama", or an LLMBackend instance
        api_key: Optional backend API key for direct library use; API routes use environment-based credentials
        calculate: Whether to run the calculation after successful generation
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")
        **backend_kwargs: Additional backend configuration

    Returns:
        GenerationResult with success status, cell definition, and calculation results

    Example:
        >>> result = generate_cell_design(
        ...     "Design a high-energy NMC811 cell around 50Ah",
        ...     backend="claude",
        ...     cell_type="prismatic"
        ... )
        >>> if result.success:
        ...     print(f"Energy density: {result.calculation_result.gravimetric_ed_whkg} Wh/kg")

        >>> result = generate_cell_design(
        ...     "Design a 10Ah NMC pouch cell",
        ...     backend="claude",
        ...     cell_type="pouch"
        ... )

        >>> result = generate_cell_design(
        ...     "Design a 5Ah 21700 NMC cell",
        ...     backend="claude",
        ...     cell_type="cylindrical"
        ... )
    """

    # Normalize cell type
    cell_type_lower = cell_type.lower()
    if cell_type_lower not in ("prismatic", "pouch", "cylindrical"):
        logger.warning(f"Unknown cell type '{cell_type}', defaulting to prismatic")
        cell_type_lower = "prismatic"

    # Initialize backend
    if isinstance(backend, str):
        if backend == "claude" and api_key:
            backend_kwargs["api_key"] = api_key
        llm = get_backend(backend, **backend_kwargs)
    else:
        llm = backend

    # Build system prompt for the specified cell type
    system_prompt = build_system_prompt(include_example=True, cell_type=cell_type_lower)

    # For local Ollama models: enforce strict YAML-only output (unless disabled)
    is_ollama = hasattr(llm, 'host')  # OllamaBackend has host attr, ClaudeBackend does not
    append_suffix = getattr(llm, 'append_yaml_suffix', True)  # Default True for backward compat
    if is_ollama and append_suffix:
        system_prompt += (
            "\n\nCRITICAL: Output ONLY the YAML specification. "
            "No explanations, no commentary, no text before or after the YAML block. "
            "Start your response with ```yaml and end with ```. Do not write anything else."
        )

    # Initialize tracking
    attempts = 0
    retry_reasons = []
    attempt_constraint_results = []
    last_error = None
    yaml_content = None
    parse_result = None

    # Initial messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request},
    ]

    while attempts < MAX_RETRIES:
        attempts += 1
        logger.info(f"Generation attempt {attempts}/{MAX_RETRIES}")

        try:
            # Generate response
            response = llm.generate(messages)
            logger.debug(f"LLM response length: {len(response)} chars")

            # Parse YAML from response
            parse_result = extract_yaml_block(response)

            if not parse_result.success:
                last_error = f"Parse error: {parse_result.error}"
                logger.warning(last_error)
                retry_reasons.append(last_error)

                # Add retry message
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Your response could not be parsed: {parse_result.error}\n\n"
                        f"Please provide a valid YAML cell definition in a ```yaml code block.",
                    }
                )
                continue

            yaml_content = parse_result.yaml_content

            # Validate with cell type
            validation_result = validate_cell_definition(yaml_content, cell_type=cell_type_lower)

            # Capture per-constraint results for this attempt
            if validation_result.constraint_results:
                attempt_constraint_results.append(validation_result.constraint_results)

            if not validation_result.valid:
                feedback = validation_result.to_llm_feedback()
                last_error = f"Validation failed: {feedback}"
                logger.warning(f"Validation failed on attempt {attempts}")
                retry_reasons.append(feedback)

                # Add retry message with validation feedback
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": build_retry_prompt(request, feedback, cell_type=cell_type_lower),
                    }
                )
                continue

            # Success! Convert and optionally calculate
            logger.info(f"Valid {cell_type_lower} design generated on attempt {attempts}")

            try:
                # Use appropriate conversion function based on cell type
                if cell_type_lower == "pouch":
                    cell_input = from_pouch_template_format(yaml_content)
                elif cell_type_lower == "cylindrical":
                    cell_input = from_cylindrical_template_format(yaml_content)
                else:
                    cell_input = from_template_format(yaml_content)
            except MappingError as e:
                last_error = f"Conversion error: {e}"
                logger.error(last_error)
                return GenerationResult(
                    success=False,
                    attempts=attempts,
                    yaml_content=parse_result.raw_yaml,
                    last_error=last_error,
                    retry_reasons=retry_reasons,
                    attempt_constraint_results=attempt_constraint_results,
                )

            calculation_result = None
            if calculate:
                try:
                    # Use appropriate calculator based on cell type
                    if cell_type_lower == "pouch":
                        calculator = CellCalculator(cell_input)
                        calculation_result = calculator.calculate()
                    elif cell_type_lower == "cylindrical":
                        calculator = CylindricalCalculator(cell_input)
                        calculation_result = calculator.calculate()
                    else:
                        calculator = PrismaticCalculator(cell_input)
                        calculation_result = calculator.calculate()
                    logger.info(f"Calculation complete: {calculation_result.capacity_ah:.1f} Ah")
                except Exception as e:
                    last_error = f"Calculation error: {e}"
                    logger.error(last_error)
                    # Still return success=True since the design is valid

            return GenerationResult(
                success=True,
                attempts=attempts,
                yaml_content=parse_result.raw_yaml,
                cell_input=cell_input,
                calculation_result=calculation_result,
                retry_reasons=retry_reasons,
                attempt_constraint_results=attempt_constraint_results,
            )

        except Exception as e:
            last_error = f"Generation error: {e}"
            logger.exception(f"Error on attempt {attempts}")
            retry_reasons.append(last_error)

            # For API errors, don't retry (likely auth/rate limit)
            if "api" in str(e).lower() or "auth" in str(e).lower():
                break

    # All retries exhausted
    logger.error(f"Failed after {attempts} attempts")

    return GenerationResult(
        success=False,
        attempts=attempts,
        yaml_content=parse_result.raw_yaml if parse_result else None,
        last_error=last_error,
        validation_errors=[str(e) for e in retry_reasons],
        retry_reasons=retry_reasons,
        attempt_constraint_results=attempt_constraint_results,
    )

