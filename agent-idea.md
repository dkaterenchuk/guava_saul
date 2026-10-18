# Saul Goodman & Associates — Voice Intake Agent

> Built for the Guava Voice AI hackathon. Fictional firm. Demo only, not legal advice.

## One-liner

A voice AI agent that answers the phone for Saul Goodman & Associates. The caller tells it the situation they're in. The agent asks follow-up questions until it has the full story, reads the story back to confirm, and then tells the caller what to do and say, what *not* to do and say, and the pros and cons of each path they could take.

## Why voice

People in legal trouble are stressed, often on their phone, and not in the mood to fill out a form. A phone call that lets them explain in their own words, then gives them clear, short guidance they can act on today, fits how they actually behave in that moment.

## How a call goes

1. **Greeting.** Saul picks up, introduces the firm, says this is a demo and not real legal advice, and asks what happened.
2. **Intake.** The caller tells their story. The agent listens and asks one follow-up at a time to fill in the gaps: when and where, who was involved, any police contact, any charges or court dates, what the caller has already said to anyone, evidence and witnesses, and what outcome the caller wants.
3. **Confirm.** Once the story is complete, the agent summarises it back in three or four sentences and asks "did I get that right?"
4. **Advice.** Delivered in short chunks so the caller can keep up:
   - What to do and say right now.
   - What not to do and say.
   - The paths available (for example: stay silent and get a lawyer, cooperate, negotiate, fight it) with the pros and cons of each, plus Saul's take.
5. **Interrupt any time.** The caller can cut in with "why?", "why not?", or "what if…" and the agent explains, then picks up where it left off.
6. **Wrap-up.** The agent recaps the top three actions, repeats the disclaimer, and signs off.

## Persona

Saul's confidence, pace, and humour on the surface. Underneath, the advice is sober and universal: don't talk to police without counsel, don't post about it, don't contact the other party, preserve evidence, write down what happened while it's fresh, and get a real lawyer. The disclaimer and the "don'ts" are never played for laughs.

## Demo scenarios

- **DUI stop.** Pulled over, took a breathalyzer, no court date yet.
- **Shoplifting accusation.** Stopped by store security, no police yet, asked to sign a form.
- **Bar fight.** Charged with assault, the other guy started it, there were witnesses.
- **Roommate / landlord dispute.** Threatened with eviction, deposit withheld.

## Safety and scope

- Fictional firm, demo only. The agent says so at the start and the end.
- Advice is general and non-jurisdictional. The agent does not cite statutes or promise outcomes.
- "Hire a real lawyer" is always one of the options presented.
- If the caller describes an active emergency, the agent tells them to call 911.

## Stack

- **Guava SDK** for telephony, speech-to-text, text-to-speech, and barge-in (interruptions).
- **Claude** (Sonnet 5.5) for intake questions, story extraction, advice generation, and answering "why?".

See `plan.md` for the architecture and build plan.
