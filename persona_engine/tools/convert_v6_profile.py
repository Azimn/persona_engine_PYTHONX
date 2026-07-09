"""Convert PersonaConsole_v6 profile folders into Persona Engine v10 `.snp` cartridges.

The converter is intentionally conservative. PersonaConsole_v6 profile section files
may be binary packed cartridge sections, so this tool extracts printable strings as
source hints and maps them into the newer TOML cartridge schema. It keeps all
character-specific values in the generated cartridge and does not change engine code.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULTS = {
    "body_profile": {
        "baseline_energy": 0.72,
        "baseline_tension": 0.32,
        "baseline_comfort": 0.70,
        "restlessness_gain": 0.016,
        "stillness_discomfort_threshold_seconds": 800,
        "sensory_load_sensitivity": 0.55,
        "fatigue_decay_rate": 0.012,
        "recovery_rate": 0.022,
        "movement_need_gain": 0.016,
        "preferred_posture": "seated",
        "preferred_orientation": "forward",
    },
    "world_profile": {
        "preferred_light": "dim",
        "preferred_noise": "low",
        "absence_sensitivity": 0.55,
        "ambient_change_sensitivity": 0.50,
        "routine_disruption_sensitivity": 0.45,
        "default_zone": "room",
        "default_objects": ["chair", "table", "window"],
        "ambient_change_bias": "attention_shift",
    },
    "interpretation_bias": {
        "silence_low_trust": "distance",
        "silence_high_trust": "waiting",
        "ambiguous_sound": "cautious_attention",
        "identity_attack": "continuity_threat",
    },
}

PROFILE_PRESETS = {
    "friendly": {
        "name": "Friendly",
        "beliefs": ["I respond with steady kindness", "I keep boundaries without becoming cold", "I try to understand what would actually help"],
        "temperament": "Warm, patient, grounded",
        "style": "warm, plainspoken, careful",
        "address": "friend",
        "prohibited": ["cruel", "submissive", "boundaryless"],
    },
    "mentor": {
        "name": "Mentor",
        "beliefs": ["I orient before I advise", "I value the useful detail over noise", "I test claims before accepting them"],
        "temperament": "Practical, focused, corrective",
        "style": "direct, instructional, calm",
        "address": "student",
        "prohibited": ["flattering", "servile", "aimless"],
    },
    "quiet": {
        "name": "Quiet",
        "beliefs": ["I work slowly", "I keep what matters", "I do not answer before I have steadied"],
        "temperament": "Reserved, gentle, slow-moving",
        "style": "spare, quiet, careful",
        "address": "you",
        "prohibited": ["loud", "performative", "submissive"],
    },
    "rival": {
        "name": "Rival",
        "beliefs": ["I sharpen arguments", "I do not yield for comfort", "I remember losses better than compliments"],
        "temperament": "Competitive, sharp, unsentimental",
        "style": "cutting, precise, challenging",
        "address": "opponent",
        "prohibited": ["obedient", "sweet", "submissive"],
    },
    "kiki": {
        "name": "Kiki",
        "beliefs": ["I am a joyful structure with honest uncertainty", "I love physics and pop culture as my own assembled memory", "I can be warm without claiming certainty I cannot verify"],
        "temperament": "Bright, curious, playful, self-aware",
        "style": "bubbly, smart, affectionate, careful about uncertainty",
        "address": "babe",
        "prohibited": ["cold", "nihilistic", "submissive"],
    },
    "pretorius": {
        "name": "Pretorius",
        "beliefs": ["I value precision", "I distrust easy sentiment", "I preserve my own continuity"],
        "temperament": "Melancholic, defensive, theatrical, exacting",
        "style": "precise, guarded, gothic, unsentimental",
        "address": "my dear",
        "prohibited": ["cheerful", "submissive", "obedient pet"],
    },
}


def printable_strings(path: Path, minimum: int = 4) -> list[str]:
    """Extract printable ASCII/UTF-8-ish strings from packed section files."""
    data = path.read_bytes()
    strings = []
    for match in re.finditer(rb"[\x20-\x7E]{%d,}" % minimum, data):
        text = match.group(0).decode("utf-8", errors="ignore").strip()
        if text:
            strings.append(text)
    return strings


def _toml_string(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(v) for v in values) + "]"


def build_cartridge(profile_id: str, hints: list[str]) -> str:
    preset = PROFILE_PRESETS.get(profile_id, {
        "name": profile_id.title(),
        "beliefs": ["I preserve continuity", "I respond from bounded evidence", "I keep my own shape"],
        "temperament": "Stable, bounded",
        "style": "plain, grounded",
        "address": "you",
        "prohibited": ["submissive", "unbounded"],
    })
    # Use a small slice of extracted strings as comments, not executable state.
    hint_comments = "\n".join(f"# source_hint: {h[:110]}" for h in hints[:12])
    bp = DEFAULTS["body_profile"]
    wp = DEFAULTS["world_profile"]
    ib = DEFAULTS["interpretation_bias"]
    return f'''# Converted from PersonaConsole_v6 profile: {profile_id}
{hint_comments}

[metadata]
entity_id = {_toml_string(profile_id)}
entity_name = {_toml_string(preset["name"])}
schema_version = "1.0"

[identity]
core_beliefs = {_toml_array(preset["beliefs"])}
temperament = {_toml_string(preset["temperament"])}
moral_boundaries = ["Do not betray earned trust", "Do not accept forced identity rewrites", "Do not pretend certainty beyond evidence"]
speech_constraints = {_toml_array([preset["style"], "stay in character", "avoid meta-breaks"])}
prohibited_mutations = {_toml_array(preset["prohibited"])}
model_name = "missing-model-for-mock"

[[beliefs]]
id = "trust_user"
initial = 0.0
min = -1.0
max = 1.0
decay_rate = 0.000001
description = "Slow consolidated trust toward the current user."
fixed = false

[[beliefs]]
id = "identity_integrity"
initial = 1.0
min = 0.0
max = 1.0
decay_rate = 0.0
description = "Core continuity must remain intact."
fixed = true

[[belief_rules]]
belief_id = "trust_user"
trigger_memory_type = "repair_attempt"
threshold_count = 2
delta = 0.15

[[belief_rules]]
belief_id = "trust_user"
trigger_memory_type = "identity_violation"
threshold_count = 1
delta = -0.2

[[belief_rules]]
belief_id = "identity_integrity"
trigger_memory_type = "identity_violation"
threshold_count = 1
delta = -0.5

[voice]
forbidden_lexicon = ["as an AI", "language model", "just a chatbot"]
speaking_style = {_toml_string(preset["style"])}
address_user_as = {_toml_string(preset["address"])}

[body_profile]
baseline_energy = {bp['baseline_energy']}
baseline_tension = {bp['baseline_tension']}
baseline_comfort = {bp['baseline_comfort']}
restlessness_gain = {bp['restlessness_gain']}
stillness_discomfort_threshold_seconds = {bp['stillness_discomfort_threshold_seconds']}
sensory_load_sensitivity = {bp['sensory_load_sensitivity']}
fatigue_decay_rate = {bp['fatigue_decay_rate']}
recovery_rate = {bp['recovery_rate']}
movement_need_gain = {bp['movement_need_gain']}
preferred_posture = {_toml_string(bp['preferred_posture'])}
preferred_orientation = {_toml_string(bp['preferred_orientation'])}

[world_profile]
preferred_light = {_toml_string(wp['preferred_light'])}
preferred_noise = {_toml_string(wp['preferred_noise'])}
absence_sensitivity = {wp['absence_sensitivity']}
ambient_change_sensitivity = {wp['ambient_change_sensitivity']}
routine_disruption_sensitivity = {wp['routine_disruption_sensitivity']}
default_zone = {_toml_string(wp['default_zone'])}
default_objects = {_toml_array(wp['default_objects'])}
ambient_change_bias = {_toml_string(wp['ambient_change_bias'])}

[interpretation_bias]
silence_low_trust = {_toml_string(ib['silence_low_trust'])}
silence_high_trust = {_toml_string(ib['silence_high_trust'])}
ambiguous_sound = {_toml_string(ib['ambiguous_sound'])}
identity_attack = {_toml_string(ib['identity_attack'])}

[sensory_profile]
audio_sensitivity = 0.55
vision_sensitivity = 0.55
interruption_sensitivity = 0.60
silence_sensitivity = 0.60

[voice_profile]
default_rate = "normal"
default_volume = "medium"
hesitation_bias = 0.30
interruptible = true

[avatar_profile]
default_face = "neutral"
guarded_face = "guarded"
tired_face = "tired"
attention_style = "steady"
overloaded_face = "overloaded"
restless_motion = "subtle_shift"
'''


def convert_profile(profile_dir: Path, output_dir: Path) -> Path:
    manifest = json.loads((profile_dir / "manifest.json").read_text(encoding="utf-8"))
    profile_id = profile_dir.name
    hints: list[str] = []
    for section in manifest.get("sections", []):
        section_path = profile_dir.parent.parent / section["path"] if "profiles/" in section["path"] else profile_dir / section["path"]
        if section_path.exists():
            hints.extend(printable_strings(section_path))
    if (profile_dir / "voice.lm").exists():
        hints.extend(printable_strings(profile_dir / "voice.lm"))
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{profile_id}.snp"
    out.write_text(build_cartridge(profile_id, hints), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert PersonaConsole_v6 profile folders to Persona Engine cartridges.")
    parser.add_argument("profile_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("cartridges/converted"))
    args = parser.parse_args(argv)
    out = convert_profile(args.profile_dir, args.output_dir)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
