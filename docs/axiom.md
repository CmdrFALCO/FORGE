# AXIOM - Automated eXpert for Industrial Output Management

AXIOM (`forge.axiom`) is a neuro-symbolic AI architecture that supervises LLM-generated engineering specifications using formal validation methods.

The detailed Build Week execution path and provenance are documented in the
[OpenAI Build Week demonstration guide](openai-build-week.md).

## Components

- **Der Generator** - LLM prompt construction and YAML response parsing
- **Der Validator** - Multi-stage schema + physics constraint verification
- **Der Supervisor** - Orchestrates generate -> validate -> feedback -> retry loop
- **Backends** - OpenAI Responses API, Claude API, Ollama (local), extensible backend interface
