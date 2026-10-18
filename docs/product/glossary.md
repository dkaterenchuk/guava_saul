# Glossary

Use these terms consistently in code, docs, and prompts.

| Term | Meaning |
|---|---|
| Caller | The person who phones in. Not "user" or "client". "Client" implies an attorney-client relationship. |
| Intake | The structured question phase that builds the case summary. |
| Case summary | The structured output of intake (fields defined per intake flow). It's handed to attorneys. |
| Legal information | General explanation of the law and options, grounded in a source. Allowed. |
| Legal advice / guidance | Applying the law to the caller's facts to recommend action. The agent does this only inside an approved playbook (Tier 2). |
| Playbook | An attorney-approved decision procedure for one basic case type in one jurisdiction: eligibility criteria, recommended steps, exit conditions. It lives inside an intake flow. |
| Tier | 0 Escalate · 1 Inform · 2 Guide · 3 Hand off. See ADR 0001. |
| Resolved | A call that ended at Tier 2 with no handoff needed. It's still subject to attorney review. |
| Review queue | Async attorney review of resolved calls. |
| Handoff | Transfer to a human (an attorney, partner org, or staff), with the case summary attached. |
| Escalation | A safety-driven interruption (an emergency, danger, or crisis line). |
| Practice area | A legal domain such as tenant, employment, or immigration. |
| Jurisdiction | The state (and county, where it matters) whose law applies. |
| Corpus | The vetted set of legal sources the agent may cite. |
