---
name: editing-style-profile
description: Distill reviewed reference-edit annotations into a human-reviewed, versioned editing style profile. Use to separate reusable style preferences from the story of an individual video.
---

Installed package: when `runtime-root.json` is present beside this file, use its `runtime_root` for repository-relative `scripts/lab`, `docs`, and `WORKSTATION_PROMPTS.md` references. The snapshot contains independent copies of the public tools. Store user media, profiles and outputs in the user's writable project, never inside the installed package.


# editing-style-profile

Status: project-local draft; no autonomous analysis/render service is implemented.

Read [the local editing prompt](../../docs/reference-editing-lab/EDITING_PROMPT.md) and [version/conflict notes](../../docs/reference-editing-lab/INTEGRATION.md) before upstream references. Treat Student pacing/retention ideas as creative hypotheses with exceptions, not platform guarantees or automatic style mandates. Preserve factual qualifiers, negation, model names and numbers over stylistic compression. Changes invalidate affected downstream approvals.

Read [the shared contract](../../docs/reference-editing-lab/CONTRACT.md). Input is evidence-linked reference analysis, not raw filenames or an unsupported impression of a creator.

Propose reusable rules with scope, exceptions, supporting annotation IDs and approval status. Separate typography, visual hierarchy, pacing ranges and motivated B-roll from each film’s factual claims, plot, exact cuts and soundtrack. Repetition across several references strengthens a candidate rule; it does not establish causality or platform ranking benefit. Record counterexamples and small sample size.

Keep the new video's narrative brief independent. Do not generalize a single unusual effect into a mandatory style. Leave uncertain rules pending; show a compact accept/change/reject review. Only the human can approve their preferences; fixtures do not count as human approval.

Version profiles immutably with parent version, and make downstream plans pin a version. A changed rule invalidates affected plan approvals. Do not silently replace the creator's existing profile. Platform guidance is a separately dated input from [platform-guidelines](../../docs/reference-editing-lab/platform-guidelines/README.md), not evidence of this creator's style.

Return proposed profile and a rule review table. This is reusable prompting/configuration, not training or fine-tuning model weights.
