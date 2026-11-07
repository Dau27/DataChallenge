from dataclasses import dataclass, field
from decimal import Decimal
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / "local_data/cqa.sqlite3"
    api_key: str = field(default="", repr=False)
    model: str = ""
    organizer_url: str = field(default="", repr=False)
    timeout: float = 90
    concurrency: int = 2
    max_input_characters: int = 180000
    max_output_tokens: int = 16000
    reasoning_effort: str | None = None
    input_rate: Decimal | None = None
    output_rate: Decimal | None = None
    rate_source: str | None = None
    budget_limit_usd: Decimal = Decimal("0")
    budget_overhead_usd: Decimal = Decimal("0.10")
    budget_baseline_path: Path | None = None

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env", override=False)
        path = Path(os.getenv("DATABASE_PATH", "local_data/cqa.sqlite3"))
        baseline_path = Path(os.getenv("BUDGET_BASELINE_PATH") or str(ROOT / "local_data/budget_baseline.json"))
        rate = lambda name: Decimal(os.environ[name]) if os.getenv(name) else None
        settings = cls(database_path=path if path.is_absolute() else ROOT / path,
                       api_key=os.getenv("OPENAI_API_KEY", "").strip(), model=os.getenv("OPENAI_MODEL", "").strip(),
                       organizer_url=os.getenv("ORGANIZER_API_URL", "").strip(),
                       timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "90")),
                       concurrency=int(os.getenv("WORKER_CONCURRENCY", "2")),
                       max_input_characters=int(os.getenv("MAX_INPUT_CHARACTERS", "180000")),
                       max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "16000")),
                       reasoning_effort=os.getenv("REASONING_EFFORT") or None,
                       input_rate=rate("INPUT_USD_PER_MILLION"), output_rate=rate("OUTPUT_USD_PER_MILLION"),
                       rate_source=os.getenv("COST_RATE_SOURCE") or None,
                       budget_limit_usd=Decimal(os.getenv("BUDGET_LIMIT_USD", "0")),
                       budget_overhead_usd=Decimal(os.getenv("BUDGET_OVERHEAD_USD", "0.10")),
                       budget_baseline_path=baseline_path if baseline_path.is_absolute() else ROOT / baseline_path)
        settings.validate()
        return settings

    def validate(self):
        if not 1 <= self.concurrency <= 8 or not 1 <= self.timeout <= 300:
            raise ValueError("Concurrency must be 1–8; request timeout must be 1–300 seconds")
        if self.max_input_characters < 1000 or not 256 <= self.max_output_tokens <= 100000:
            raise ValueError("Invalid request size safeguards")
        if self.reasoning_effort is not None and self.reasoning_effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError("Unsupported reasoning effort setting")
        for value in [self.input_rate, self.output_rate]:
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError("Configured cost rates must be finite and nonnegative")
        for value in [self.budget_limit_usd, self.budget_overhead_usd]:
            if not value.is_finite() or value < 0:
                raise ValueError("Budget limit and overhead must be finite and nonnegative")
        if self.organizer_url:
            parts = urlsplit(self.organizer_url)
            if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.fragment:
                raise ValueError("Organizer endpoint must be an HTTPS URL without userinfo or fragment")

    @property
    def provider_ready(self):
        return bool(self.api_key and not self.api_key.startswith(("org-", "nvapi-")) and self.model)

    def public_access(self):
        missing = [name for name, value in [("OPENAI_API_KEY", self.api_key), ("OPENAI_MODEL", self.model)] if not value]
        issue = ("OPENAI_API_KEY contains an organization ID, not an API key" if self.api_key.startswith("org-") else
                 "OPENAI_API_KEY contains a NVIDIA key; this configured adapter requires an OpenAI key" if self.api_key.startswith("nvapi-") else
                 "Missing " + ", ".join(missing) if missing else "Configured; live check required")
        return {"provider": "openai-responses", "model": self.model or None,
                "provider_configured": self.provider_ready, "provider_verified": False,
                "provider_status": issue,
                "organizer_configured": bool(self.organizer_url), "concurrency": self.concurrency,
                "budget_limit_usd": str(self.budget_limit_usd),
                "cost_rate_available": all(v is not None for v in [self.input_rate, self.output_rate, self.rate_source])}
