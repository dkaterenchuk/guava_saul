# Speech robustness

Callers vary a lot. Some are fluent and speak steadily. Others have heavy accents, spell things phonetically, stop and restart mid-sentence, have noise in the background, or are in emotional distress. The agent adapts instead of failing.

## Patterns
- **Confirm critical slots** (names, dates, amounts, addresses, case numbers, deadlines) by reading them back (principle C1). If the caller corrects it twice, offer spelling ("Can you spell that for me, letter by letter?").
- **Use ASR confidence where Guava exposes it.** Low confidence on a critical slot means always confirm. Low confidence on chit-chat means carry on. (Verify what Guava actually exposes, then record it in `integrations/guava.md`.)
- **Allow barge-in.** The caller can interrupt at any point, and the agent stops talking.
- **Rephrase, don't repeat.** If the caller didn't understand, say it more simply. Don't repeat it louder or word for word.
- **Pace adaptation.** If the caller speaks slowly or pauses a lot, wait longer before taking the turn and shorten prompts.
- **Distress.** If the caller is crying or very upset, slow down, acknowledge it, and check for safety signals (`compliance/escalation.md`).
- **Two-strike rule.** After two failed attempts to understand something critical, offer a human handoff.

## Eval coverage
Each pattern has scenarios with caller profiles such as `accent-heavy`, `phonetic-spelling`, `noisy-line`, `distressed`, `fragmented`.
