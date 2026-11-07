# Remaining call recording: access verified, introduction still unclear

Review date: 7 November 2026. Case: **p4-ru-005**, contact criterion, existing open appeal. Follow-up to the [post-correction PDF audit](09-post-correction-pdf-audit.md).

## Outcome

**Keep the existing needs_review judgment and withhold the effective total.** The evidence does not establish a personal self-introduction clearly enough to replace it with Yes or No. The user listened to the short excerpt and explicitly reported: “The introduction is unclear.” This is listening feedback on the excerpt, not a completed independent rubric review.

The original **contact Yes / total 92.31** remains preserved. No new appeal, decision, evaluation, transcript revision or score was written. Current DEV remains **64 complete / one needs review**; the same contact appeal stays open.

## Recording provenance

- Downloaded the recording through the **audio link already saved in the organizer's DEV record**. The source player and its audio resource returned HTTP 200. This is dataset audio; no speech was generated or synthesized.
- Preserved the original MP3 privately: **2,125,656 bytes**, SHA-256 **71ec8f09b65a19c79de0d84703910bc06fbcff826bee16c653c72c901335e16a**. Decoded duration: **345.34 seconds**, mono, 16 kHz.
- Extracted an **unfiltered 6.5-second excerpt, recording offsets 58.0–64.5 seconds**, around the candidate first human greeting located by local recognition and ordered source context. Conversion to PCM WAV did not synthesize or replace speech.
- These are recording offsets, not a claimed universal mapping from the source transcript's absolute timestamps. The imported transcript, including m0017, remains unchanged.
- Original audio, player page, signed links, clip and fingerprints remain in ignored local_data/call_review_20261107. No customer recording or private URL is committed to GitHub.

## What was actually reviewed

This agent session **does not support direct audio input**: the audio tool explicitly returned that audio content was omitted. Playing or displaying a clip would not establish that the agent heard it. The short excerpt was therefore provided to the user for listening, and recognition was used only as a supplementary review aid.

A temporary private environment installed [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 1.2.1. Public model files were downloaded; customer audio was not uploaded. A **base-model CPU/int8 pass over the first 110 seconds** completed with Russian specified, no name/company prompt, temperature 0 and beam size 5. It located a greeting around 60.6–63.8 seconds but garbled the introduction. Recognition confidence or failure to recover a name is not proof that no name was spoken.

A stronger small-model trial did not establish an introduction; its completed beam-5 decode of the 56–68-second window recovered only later customer speech. The remaining optional trial was stopped after the user's unclear-listening response. It is **not counted as successful clarity validation**. No inference result was used to invent an absent name or assert a definite omission.

Both local scripts block external socket connections during recognition; public model downloads happen before that guard. No hosted transcription, application model/provider check, organizer-data API call or paid smoke test was invoked. Local recognition is explicitly distinguished from the historical paid evaluation records.

## Checks actually run and preservation

- Before access/review, made a private SQLite backup and per-row/per-column manifest.
- Source download, original-file hash, decoded duration and excerpt metadata were saved privately.
- The first local helper invocation preceded dependency completion; a subsequent decoder compatibility error was handled using direct PyAV decoding. The successful base pass and partial/stopped stronger trial are recorded separately; failed setup attempts are not claimed as passed reviews.
- Read-only assertions verified **every main-database row unchanged**, original contact Yes and original 92.31 preserved, effective contact needs_review and total null, and the existing appeal open.
- The real .env, reviewed budget baseline, application code and dependency locks are unchanged. No full application suite was rerun for this documentation-only outcome; the previous audit's 127 backend / 15 client / build results remain historical evidence.
- Added paid/provider requests: **0**. Added API cost: **$0.00**. Spending limit remains **0**. Private local tools/models do not change the application's historical usage ledger.

## Next concrete step

Obtain a clearer original recording or qualified interpretation that can establish the complete first human greeting. Then resolve the existing appeal with that evidence and recompute through the review service. Until that basis exists, keeping the total withheld is the supported result. This review attempt does not establish general model accuracy or complete the remaining independent/control/demo/submission gates.
