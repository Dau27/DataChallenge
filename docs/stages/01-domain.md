# Stage 1 — Domain and deterministic scoring

Status: arithmetic/validation acceptance gate passed.

- Copied `initial_checklist.json` to `config/initial_checklist.json` byte for byte. SHA-256: `913445BC3A3BBBB486AD2C124BEEBBACCF493F23E868B4212EEC7EF648500747`.
- Implemented strict Pydantic contracts for checklist configuration, import envelopes, messages, judgments, and evidence.
- Implemented Decimal scoring, global N/A redistribution, discrete numerical anchors, independent unscored flags, section percentages, and final-only ROUND_HALF_UP display rounding.
- Unresolved judgments prevent a final total. Unknown/missing criteria, forbidden N/A, boolean scale values, invalid ranges, duplicate IDs, unsupported policies, and invalid weights/scales fail validation.

Command actually run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_scoring.py -q
```

Final outcome: **32 passed in 0.12s**. First run had 31 passed and a test assertion failure comparing `60.0` to `60`; fixed the assertion to compare Decimal values and reran successfully. No arithmetic failure was hidden.

These are deterministic tests with explicitly synthetic judgments, not model-quality or live-evaluation evidence.

Next step: persistent import and evaluation services, generated provider schema, and the first real evaluation slice when provider access is available.
