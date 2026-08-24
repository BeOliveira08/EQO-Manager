import json
from pathlib import Path

from eqo.interaction.intent import Intent


def test_benchmark_cases_use_known_intents_and_structured_entities() -> None:
    path = Path(__file__).parents[1] / "benchmarks" / "intent_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    assert len(cases) >= 7
    for case in cases:
        assert case["text"].strip()
        assert Intent(case["expected_intent"]) is not Intent.UNKNOWN
        assert isinstance(case["expected_entities"], dict)
