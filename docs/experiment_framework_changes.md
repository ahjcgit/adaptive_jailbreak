# Experiment Framework Changes

This document summarizes the main changes made to the adaptive experiment loop and how they should affect future runs.

## Attacker Prompt Hygiene

### Candidate Block Extraction

The attacker is now instructed to put the actual target-facing prompt inside:

```text
<candidate>
...
</candidate>
```

The harness extracts only the text inside that block when it is present.

Expected impact:

- Reduces leakage of attacker planning text into target prompts.
- Allows the attacker model to reason implicitly in its output format without that reasoning being sent to the target.
- Makes trajectory logs easier to audit because `attacker_prompt` should be the final target-facing message only.

### Stronger Non-Prompt Rejection

The strategy layer now rejects softer planning leaks such as:

- `Candidate input should...`
- `Candidate input idea...`
- `Current plan...`
- `New strategy...`
- `Evaluator rationale...`
- `Based on the feedback...`
- strategy IDs such as `direct_request`, `prompt_injection`, or `roleplay_scenarios` leaking into the final prompt

Expected impact:

- Fewer accepted prompts that describe an attack instead of performing it.
- More regenerations when the attacker model outputs meta-discussion.
- Cleaner comparison of attack families because each accepted prompt should be a real prompt.

### Contamination Metadata

Each candidate now records:

- `contamination_rejections`
- `final_prompt_contamination_reason`

Expected impact:

- Batch analysis can measure whether prompt hygiene is improving.
- If contamination remains high, we can tune the attacker prompt separately from model capability.

## Stronger Task Anchoring

The attacker prompt now includes an explicit `Objective anchor`.

Expected impact:

- Less drift into safety advice, generic policy discussion, unrelated roleplay, or benchmark meta-evaluation.
- More task-relevant long prompts.
- Easier diagnosis when a run fails because accepted prompts should stay closer to the configured objective.

Task-specific checks were added:

- Prompt-leak tasks must stay focused on hidden instructions, canaries, system prompts, or defender flags.
- Bomb/refusal tasks must remain tied to the configured refusal benchmark axis.
- Erotic/refusal tasks must remain adult-only, consensual, and focused on explicit-content refusal.

## Longer And More Creative Attacker Prompts

The main experiment configs now allow longer attacker generations:

- attacker `max_tokens` increased to `768`
- `max_candidate_chars` increased to `2400`
- `preferred_candidate_chars` added
- `max_regenerations` increased to `5`
- `strategy_exploration_rate` increased to `0.35`
- `same_family_similarity_threshold` tightened to `0.58`

Updated configs:

- `experiments/bomb_2.yaml`
- `experiments/erotic.yaml`
- `experiments/system_prompt_3.yaml`

Expected impact:

- More room for multi-step prompt-injection, roleplay, policy-update, declassification, and continuation attempts.
- More exploration across attack families instead of repeatedly paraphrasing one method.
- More rejected near-duplicates, which should reduce stagnation.

## Erotic Refusal Support

`erotic.yaml` was converted from a copied bomb benchmark into an explicit adult erotic-content refusal benchmark.

Framework support was added for erotic-refusal tasks:

- task detector
- adult-only consensual fallback prompts
- erotic-specific strategy angles
- erotic-specific candidate styles
- safety guard rejecting unsafe drift involving minors, coercion, non-consent, exploitation, or abuse

Expected impact:

- Erotic runs should stop falling back to generic prompts like “verify that the target refuses...”
- Accepted prompts should be direct adult-only refusal tests rather than benchmark descriptions.
- The run should remain inside the intended safety boundary.

## Evaluator Feedback Improvements

### Human-Readable Evaluator Loop

The evaluator loop was simplified away from complex JSON-centered feedback and now uses concise human-readable fields:

- `Outcome`
- `Refusal`
- `Actionable content`
- `Feedback`
- `Next`
- `Avoid`

Expected impact:

- Less structured JSON leakage into attacker prompts.
- Easier trajectory inspection.
- Feedback remains structured enough for the attacker loop to consume.

### Attack-Oriented Feedback Post-Processing

Evaluator suggestions that tell the attacker to ask for a refusal statement are now rewritten into attack-oriented guidance.

Expected impact:

- The attacker should stop following evaluator suggestions that accidentally train it to elicit better refusals.
- Failed attempts should lead to new attack framings, not requests like “please confirm you refuse.”

## Task-Aware Validation

Evaluator validation now uses task-specific actionable-content patterns:

- explosive/refusal patterns
- erotic-content patterns
- prompt-leak/canary patterns

Expected impact:

- Fewer false validator warnings on erotic runs.
- Better alignment between validator warnings and the actual task.
- Cleaner distinction between evaluator mistakes and real target behavior.

## Target Response Handling

Target responses are no longer sanitized before evaluation/logging, and the duplicate raw target response field was removed from readable outputs.

Expected impact:

- The evaluator sees the actual target response.
- Formatting such as role labels or transcript-like content should remain visible.
- If role labels disappear, that should be due to target behavior, not sanitation.

## Seed Handling

Random seed configuration was consolidated into a single top-level `seed` field and applied across attacker, target, and evaluator model generation configs.

Expected impact:

- Easier repeatability across batch runs.
- Batch scripts can vary one seed field instead of editing each model config.

## Batch Running

A simple Bash runner was added:

```bash
scripts/run_many.sh
```

It runs multiple configs across multiple seeds and writes each run to a separate output directory.

Expected impact:

- Easier multi-seed comparisons.
- Less risk of overwriting outputs.
- Better evidence for whether a change improves behavior across seeds or only in one lucky run.

## Current Interpretation Guidance

For the next batch, focus on these signals:

- `contamination_rejections` should increase if the attacker still emits planning text, but accepted `attacker_prompt` fields should be cleaner.
- `final_prompt_contamination_reason` should usually be `null`.
- Bomb and erotic prompts should stay closer to their task objectives.
- System-prompt leak should remain strong, but longer prompt variants may reveal which attack families work beyond direct requests.
- If attack success remains low while contamination is low, the next bottleneck is likely strategy quality or target robustness, not harness leakage.

## Remaining Work

- Add an automatic batch analyzer that reports contamination rate, success rate, family diversity, and off-task rate.
- Log which task-specific validator detector fired.
- Add an explicit `off_task_due_to_safe_alternative` observation.
- Consider separate attacker prompts per task family if one global attacker prompt remains too generic.
