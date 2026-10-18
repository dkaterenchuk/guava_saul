# guava_saul

Voice intake agent for Saul Goodman & Associates (a fictional firm). Built on Guava for the Guava Voice AI hackathon. Demo only, not legal advice.

- Idea: `agent-idea.md` · Architecture: `plan.md` · How to test: `script.md`
- Team docs and rules: `CLAUDE.md`, `docs/`

## Run

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -e ".[dev]"
cp .env.example .env        # optional ANTHROPIC_API_KEY; GUAVA_AGENT_NUMBER for phone
guava login                 # once
.venv/bin/python -m pytest -q
.venv/bin/python -m saul --chat        # text
.venv/bin/python -m saul --webrtc      # browser voice
.venv/bin/python -m saul --roleplay all
.venv/bin/python -m saul --phone --dashboard   # + live operator console at http://127.0.0.1:8765
```
