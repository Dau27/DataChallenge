# Weight-impact preview

Verified 8 November 2026. Added a **fixed-judgment simulation** to the existing checklist editor. It reads a selected saved run and applies draft weights with the existing deterministic scorer. It never evaluates a conversation, saves a version or changes a recorded result. **Zero provider calls; demo deferred.**

## Market pattern and fit

[Amazon Connect documents weighted questions, form preview and validation](https://docs.aws.amazon.com/connect/latest/adminguide/create-evaluation-forms.html). We adopt the inspect-before-saving workflow while retaining our project's arithmetic, N/A rules, unscored flags and immutable versions. Our fixed-judgment scenario is an engineering adaptation; this report does not claim Amazon provides an identical simulation or that we inspected proprietary implementation.

## Implemented behavior

- Collapsed tool below the existing structural change preview; no extra request until opened. Successful saved runs are explicitly selectable with dataset, source, revision and run ID. Server pagination exposes total/offset/limit; no saved candidates are silently truncated.
- Original/effective basis selection, strict saved-version/hash matching and exact baseline-score replay before any simulation.
- After normalized model validation, **only criterion weights may differ**. Changes to names, descriptions, IDs/order, sections, scales, answer types, N/A settings, notes, scoring policy or any other field disable reuse. Invalid draft fields receive the existing field-error contract.
- Old/new totals, point difference, applicable denominator, fixed judgments, raw points and normalized contributions. N/A still excludes scored weight; flags stay unscored; unresolved/all-N/A totals remain null.
- Contribution display rounds decimal text to four places, with an explicit display-only note. Exact underlying Decimal results, raw points, totals and saved data are retained. Binary/flag labels use Yes/No and Flagged/Not flagged.
- Source/run/checklist/draft/basis request identity and manifest checks prevent stale results or a prior run's scenario from appearing under a newer choice. Saved-run pagination/refresh preserves explicit selections and checks their updated revision.
- Unsupported or unreplayable saved judgments return an unavailable explanation rather than inventing a scenario or relaxing the current validation contract.

Implementation: `services/weight_preview.py`, `api_weight_preview.py`, `WeightImpact.tsx`, shared router and a small editor integration. No schema, dependency, prompt or provider change.

## Acceptance actually run

- Feature backend: **28 passed**. Tests cover all non-weight fields, invalid weights, exact identity, N/A redistribution, unresolved/all-N/A/flag states, both bases, legacy source-evidence compatibility, version/hash mismatch, failures, pagination, privacy and no writes/provider calls.
- Client: **9 passed** after the display refinement; TypeScript passed. Includes late run/draft/error responses, exact metadata, basis/null handling, pagination/retry and a deeply frozen response with precise halfway/carry/scientific contribution values.
- Fresh actual-data copy: **394 identity scenarios and 394 changed-weight scenarios** across available saved successful judgment bases. Identity replays equal recorded scores; changed scenarios retain the recorded baseline, flags and unresolved totals. Six paginated saved-run pages were checked across five checklist versions.
- **Two historical bases remain unavailable.** Their critical-flag missing-basis reasons are placeholders rejected by the current generic saved-judgment contract. They were not rewritten, approved or reinterpreted. This limitation is explicit, not a hidden skipped result.
- Browser on the protected copy: p4-ru-005 effective total remains withheld when Contact weight changes 10 → 20. Its original-basis arithmetic scenario shows 92.31 → 93.33, explicitly as a simulation, while the recorded original stays 92.31. Changing a criterion definition disables preview. Restoring the definition and weight returns the editor to its saved snapshot; no save was made.

The initial client test used a singular locator for two intentionally equal identity totals; the locator was corrected before the passing targeted run. Browser testing also revealed long contribution strings; display-only rounding fixed readability without altering calculations. Complete integrated acceptance is in [final verification](16-insights-verification.md).

The preview explains arithmetic sensitivity. It does not validate changed wording, improve operator behavior, tune weights to maximize a grade or establish model accuracy. Originals, reviews and the unresolved call remain intact.
