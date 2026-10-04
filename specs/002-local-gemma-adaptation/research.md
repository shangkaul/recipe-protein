# Research: Local Pantry Intelligence and Recipe Adaptation

## Structured local inference

**Decision**: Use Ollama's local `/api/chat` endpoint with a JSON Schema in `format`, `stream: false`,
temperature `0`, and `gemma3:1b` as the configurable default model.

**Rationale**: Ollama is already installed, runs entirely on the household device, exposes model
availability through `/api/tags`, and supports structured output without adding a cloud account.

**Alternatives considered**:

- Free-form model JSON: rejected because parseable text is not a sufficient validation boundary.
- Browser inference: rejected for MVP due model download, memory, and WebGPU variability.
- Cloud inference fallback: rejected by the privacy constitution.
- Replacing deterministic parsing: rejected because common searches should remain instant and
  available without the model.

## Pantry refinement boundary

**Decision**: Run deterministic parsing first. Call the model only when unresolved terms remain or
the caller explicitly requests role refinement. Supply a bounded candidate vocabulary derived from
the corpus; accept only exact returned IDs that exist in that vocabulary. Model output may add
validated terms or classify roles but may never delete deterministic recognized terms.

**Rationale**: This makes the model useful for language ambiguity without allowing hallucinated
ingredients to alter retrieval.

## Failure behavior

**Decision**: Treat unavailable service, absent model, timeout, invalid JSON, schema failure, and
unknown identifiers as normal fallback states. Search returns deterministic results plus a concise
status; adaptation fails closed and leaves the source recipe usable.

## Adaptation operations

**Decision**: Initially permit only explicit add, increase, decrease, and remove operations where
the ingredient and unit can be deterministically validated. The model provides reasons and step
notes but not nutrition values. Unsupported changes reject the complete proposal.

## Nutrition

**Decision**: Preserve source per-serving nutrition as the baseline and apply deterministic deltas
only for changed ingredients with attributed local nutrient records and supported quantity
conversions. Reject any adaptation that cannot be fully reproduced.

**Source direction**: Use USDA FoodData Central public-domain records for the small supported local
ingredient table and preserve FDC identifiers and measurement basis.

## Timeouts and privacy

- Refinement timeout: 10 seconds.
- Adaptation timeout: 30 seconds.
- Ollama base URL defaults to `http://127.0.0.1:11434` and rejects non-loopback configuration by
  default.
- Logs contain duration, status, and validation codes, never pantry or prompt content.

## Community implementation evidence

- Jangwook Kim, [Ollama Structured Outputs in Practice — Getting Type-Safe JSON from Local LLMs
  with Pydantic](https://dev.to/jangwook_kim_e31e7291ad98/ollama-structured-outputs-in-practice-getting-type-safe-json-from-local-llms-with-pydantic-m38):
  recommends Ollama's schema-constrained `format`, temperature zero, and a second Pydantic
  validation boundary; also reports that small models struggle as schemas become deeply nested.
- Mukunda Katta, [Rule-Based LLM Output Validation: Reject Bad Responses Before They Reach Your
  Users](https://dev.to/mukundakatta/rule-based-llm-output-validation-reject-bad-responses-before-they-reach-your-users-if0):
  separates parse/schema checks from semantic allow-list validation and treats fallback as an
  application decision. Protein Pantry therefore validates canonical IDs after schema validation.
- Burak Yıldız, [Why Sending Schemas to Cloud LLMs is a Privacy Risk](https://dev.to/burak_yldz_aef1be5e5088/why-sending-schemas-to-cloud-llms-is-a-privacy-risk-generating-synthetic-data-locally-with-ollama-36k6):
  describes the same separation used here: local semantic generation followed by deterministic
  verification, with no sensitive context sent to a cloud model.
