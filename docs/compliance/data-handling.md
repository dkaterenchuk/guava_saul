# Data handling

Callers share sensitive facts: immigration status, abuse, finances, criminal exposure. Treat every transcript as highly sensitive.

## Rules
- **No real caller data in git, logs, or dev environments.** Use synthetic scenarios only (`evals/scenarios/`). `data/raw/` is reserved for local, gitignored material, and a hook blocks Claude from writing there.
- **Minimum necessary.** Intake collects only the fields its flow defines.
- **Redact before logging.** Application logs never contain transcript text or phone numbers.
- **Retention.** TBD per counsel. Define it before launch.
- **Third parties.** Every vendor that touches audio or text (Guava, the LLM provider, storage) is listed here, with its data terms.

## Vendors
| Vendor | Touches | Terms verified? |
|---|---|---|
| Guava | Audio, transcripts | No |
| LLM provider | Transcripts, case summary | No |

## Privilege note
Conversations with an AI intake system are probably **not** protected by attorney-client privilege. Confirm this with counsel, and decide whether the caller needs to be told.
