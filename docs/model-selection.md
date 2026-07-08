# Model Selection for Material Insight AI

## Recommendation

Use **OpenAI `gpt-5.5` as the default LLM provider** for Phase 5.

Use **vLLM Qwen 27B as the local/private fallback provider** when API cost, privacy, or offline testing matters.

Use **vLLM Gemma 4B only for smoke tests or very small demos**.

The available local vLLM models are:

- `qwen-27b`
- `gemma-4b`

## Why

Material Insight AI is not a free-form chatbot. The LLM layer must:

- preserve Rule Engine results
- summarize adopted RAG sources
- avoid unsupported material or code claims
- return valid `RecommendationResult` JSON
- degrade safely when sources are missing

For this project, the best model is the one that follows constraints and produces stable structured output. Accuracy and instruction following matter more than raw speed.

## Provider Ranking

| Rank | Provider/model | Best use |
|---:|---|---|
| 1 | OpenAI `gpt-5.5` | Default MVP recommendation generation |
| 2 | vLLM Qwen 27B | Local/private fallback and cost-controlled demos |
| 3 | vLLM Gemma 4B | Fast smoke tests, mock-like local checks |
| 4 | mock provider | Deterministic tests and offline development |

## Implementation Default

```env
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-5.5
```

For local fallback:

```env
LLM_PROVIDER=vllm
VLLM_MODEL=qwen-27b
```

For a lighter local smoke test:

```env
LLM_PROVIDER=vllm
VLLM_MODEL=gemma-4b
```

For CI or offline demos:

```env
LLM_PROVIDER=mock
```

## Guardrails

Regardless of model, Phase 5 should enforce these rules in code and prompt:

- Rule Engine issues must not be removed or softened by the LLM.
- If `sources=[]`, the LLM must say there is no document evidence.
- The LLM must not invent material specs, dimensions, regulations, or compliance results.
- Output must validate against `RecommendationResult`.
- On provider failure, return the Phase 4 fallback recommendation.
