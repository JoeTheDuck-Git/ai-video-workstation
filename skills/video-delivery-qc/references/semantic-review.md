# Semantic continuity review

Use this review only when a story manifest, approved shot table, character sheet, prop list, reference images, or clear user statement establishes expected content.

## Build expected evidence

For each shot, record only known requirements:

- absolute start/end time;
- expected characters at opening, during entrances/exits, and at the end;
- stable identity cues such as species, clothing, color, hairstyle, accessories, or scale;
- required location, key props, and intended action;
- dialogue speaker and approximate spoken interval.

If no source establishes an expectation, mark the field unknown rather than inferring a requirement from the rendered video.

## Sample the right frames

Sample the start, midpoint, and end of every shot, plus frames immediately before and after:

- character entrances and exits;
- dialogue speaker changes;
- transitions;
- reported defects.

For short generated clips, one frame per second is usually sufficient for the first pass. Add tighter samples around a suspected failure. A contact sheet is for navigation; inspect full-resolution frames before confirming a defect.

## Check each shot

- Count intended foreground characters; distinguish a genuine third subject from reflections, posters, background extras, or transition overlap.
- Check for duplicate characters, fused limbs, sudden identity changes, costume/color drift, or unexplained size changes.
- Verify props do not disappear, multiply, change hand, or change design without a story reason.
- Verify the location and time-of-day remain consistent where continuity is expected.
- Confirm entrances and exits occur near their narrative cue, not substantially before or after it.
- Compare visible speaker/action with the actual audio and caption interval.

Vision-model output is an inference. Confirm high-impact findings across adjacent frames and, when possible, against the approved character or storyboard reference. If the model cannot reliably distinguish identities, report `needs_review` with the sampled frames.

## Report format

For every issue include:

```text
severity: blocking | warning
time: HH:MM:SS.mmm–HH:MM:SS.mmm
expected: evidence-backed requirement
observed: what the frames/audio show
evidence: frame paths, transcript interval, or measured result
confidence: confirmed | likely | needs_review
recommended_action: the smallest corrective action
```

End with a gate summary that lists `blocking`, `warning`, `pass`, and `not_checked` counts. Never collapse `not_checked` into `pass`.
