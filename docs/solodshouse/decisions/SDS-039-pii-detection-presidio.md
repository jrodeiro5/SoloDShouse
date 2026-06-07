# SDS-039: PII Detection Layer — Microsoft Presidio

**Status:** Draft  
**Date:** 2026-06-07  
**Deciders:** jrodeiro  
**Context:** AI chat responsibilities (Langfuse + garak + guardrails), SDS-038 (LLM gateway)

---

## Context

SoloDShouse AI chat (deepagents + Open WebUI) is designed as a non-engineer interface. Even with public domain data (ENTSO-E grid, Open-Meteo weather), user queries themselves may contain PII — names, emails, locations — especially if the platform is later extended or demoed to third parties.

Additionally, LLM responses can inadvertently surface or fabricate PII-like content. Langfuse traces the full conversation; traces stored server-side should not contain unredacted PII.

GDPR baseline requires:
- Data minimization: don't store PII you don't need
- Purpose limitation: energy analytics platform shouldn't be processing personal data at all

---

## Decision

Add **Microsoft Presidio** as a pre/post processing layer on the FastAPI proxy sitting between Open WebUI and deepagents.

- **Pre-processing (user input):** detect and anonymize PII before passing to LLM
- **Post-processing (LLM output):** scan response for PII leakage before returning to user
- **Langfuse integration:** log anonymized traces only — no raw PII in observability data

Presidio runs in-process (Python library) — no separate service required. Adds ~100 MB RAM, negligible latency (<10ms for typical query length).

---

## Rationale

| Factor | Assessment |
|--------|-----------|
| Fit | Python-native, integrates directly into FastAPI proxy middleware |
| RAM | ~100 MB library overhead — fits VPS and Mac profiles |
| Scope | Analyzer (detect) + Anonymizer (redact/replace) — both needed |
| Maintenance | Microsoft-backed, 8.5k stars, actively maintained |
| Alternative | No equivalent self-hosted option at this weight |

Presidio supports custom recognizers — relevant for energy domain (e.g., grid operator IDs, plant codes that could be sensitive in a commercial context).

---

## Implementation Sketch

FastAPI proxy middleware pattern:

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def anonymize(text: str) -> str:
    results = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=results).text

# In proxy endpoint:
# 1. anonymize(user_input) before forwarding to deepagents
# 2. anonymize(llm_response) before returning to Open WebUI
# 3. log anonymized versions to Langfuse
```

---

## Scope and Limitations

- Language: English primary; Spanish support via Presidio `es` models (relevant for UCM/Spain context)
- Does NOT replace garak — garak audits prompt injection and jailbreaks; Presidio handles PII only
- Does NOT replace content guardrails — out-of-scope query refusals handled separately in deepagents tools
- False positive rate: Presidio errs toward detection; custom allowlist needed for domain terms misidentified as PII (e.g., grid codes that look like phone numbers)

---

## RAM Budget

| Profile | Before | After |
|---------|-------:|------:|
| `agent` (Mac) | ~5.4 GB | ~5.5 GB |
| VPS | N/A (proxy only) | +~100 MB |

Within budget for both targets.

---

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| scrubadub | Less maintained, fewer entity types |
| spaCy NER only | Detection only, no anonymization pipeline |
| Cloud DLP (GCP/AWS) | Costs money, sends data to cloud — contradicts GDPR posture |
| No PII layer | Acceptable for current TFM scope, but forward-incompatible |

---

## Status Note

Drafted as forward-compatible hardening. Not blocking for initial TFM demo (domain data is public, no real users). Implement before any external demo or if user accounts added.

---

## Related

- SDS-038: LLM gateway (Groq via LiteLLM)
- SDS-037: VPS gateway role
- `agents/deepagents_proxy.py`: FastAPI proxy — integration point
- `ai_chat_responsibilities` memory: Langfuse + garak + guardrails context
