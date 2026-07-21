# AXIOM - Automated eXpert for Industrial Output Management

AXIOM (`forge.axiom`) is a neuro-symbolic AI architecture that supervises LLM-generated engineering specifications using formal validation methods.

*Detailed AXIOM documentation will be expanded from the project's internal design documents.*

## Components

- **Der Generator** - LLM prompt construction and YAML response parsing
- **Der Validator** - Multi-stage schema + physics constraint verification
- **Der Supervisor** - Orchestrates generate -> validate -> feedback -> retry loop
- **Backends** - OpenAI Responses API, Claude API, Ollama (local), extensible backend interface
