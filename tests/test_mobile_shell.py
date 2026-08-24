import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_android_manifest_keeps_permissions_minimal() -> None:
    manifest = (ROOT / "mobile/android/app/src/main/AndroidManifest.xml").read_text()
    assert "android.permission.RECORD_AUDIO" in manifest
    assert "android.permission.INTERNET" not in manifest
    assert "LOCATION" not in manifest
    assert "BLUETOOTH" not in manifest
    assert "SENSORS" not in manifest


def test_mobile_contract_and_benchmark_are_versioned() -> None:
    contract = json.loads((ROOT / "contracts/mobile-backend-v1.schema.json").read_text())
    benchmark = json.loads((ROOT / "benchmarks/mobile/scenarios.json").read_text())
    scenario_ids = {item["id"] for item in benchmark["scenarios"]}
    assert contract["properties"]["schema_version"]["const"] == 1
    assert benchmark["schema_version"] == 1
    assert {"cold_start", "idle_memory", "database_open", "planner_100_tasks"} <= scenario_ids


def test_kotlin_shell_requests_microphone_only_from_user_action() -> None:
    source = (
        ROOT / "mobile/android/app/src/main/java/br/com/eqo/mobile/MainActivity.kt"
    ).read_text()
    assert "actionButton(\"Falar\") { requestMicrophone() }" in source
    assert "requestPermissions" in source
    assert "ShellPreviewBackend" in source
