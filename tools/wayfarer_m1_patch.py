"""One-time Project Wayfarer M1 maintenance patch.

This script exists to make two ordered architectural edits reproducible:

1. Remove the final InteriorEngine dependency on ``identity.model_name``.
2. Move universal AI/human ontology assumptions into character-scoped policy.

It is intentionally strict: expected source text must be present or the script
fails rather than guessing. Delete this script after the maintenance pass is
verified if it is no longer useful as migration documentation.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]


def path(rel: str) -> Path:
    return ROOT / rel


def replace_once(file: Path, old: str, new: str) -> None:
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one match in {file}: {old!r}; found {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def step1_renderer_decoupling() -> None:
    engine = path("persona_engine/core/engine.py")
    replace_once(
        engine,
        "        self.renderer = LocalLLMRenderer(model_name=identity.model_name)\n",
        "        # Renderer bootstrap is host/runtime policy, not character identity.\n"
        "        # Start deterministically offline until an approved host/session replaces it.\n"
        "        self.renderer = LocalLLMRenderer(model_name=\"missing-model-for-mock\", provider=\"offline\")\n",
    )

    tests = path("persona_engine/tests/test_wayfarer_renderer_identity.py")
    text = tests.read_text(encoding="utf-8")
    if "test_engine_bootstrap_does_not_read_identity_model_name" not in text:
        marker = "def test_host_can_replace_renderer_without_changing_identity(tmp_path):\n"
        if marker not in text:
            raise SystemExit("renderer identity test insertion marker missing")
        test = dedent(
            '''
            def test_engine_bootstrap_does_not_read_identity_model_name(tmp_path, monkeypatch):
                identity = CoreIdentity(
                    name="NoRendererInIdentity",
                    core_beliefs=("I persist across renderers",),
                    temperament="steady",
                    model_name="legacy-value-must-not-be-read",
                )

                # CoreIdentity.model_name is an InitVar compatibility shim, not stored state.
                # Removing the class-level compatibility default makes any accidental runtime
                # read fail immediately. InteriorEngine must still bootstrap offline.
                monkeypatch.delattr(CoreIdentity, "model_name", raising=False)
                agent = CharacterAgent(
                    identity,
                    user_id="no_identity_renderer_read",
                    db_path=str(tmp_path / "state.db"),
                )

                status = agent.engine.renderer_status()
                assert status["requested_provider"] == "offline"
                assert status["actual_provider"] == "offline"
                assert status["model_name"] == "missing-model-for-mock"


            '''
        ).lstrip()
        tests.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")


def _patch_identity() -> None:
    file = path("persona_engine/core/identity.py")
    text = file.read_text(encoding="utf-8")

    old_fields = (
        "    prohibited_mutations: Tuple[str, ...] = ()\n"
        "    # Transitional compatibility only. InitVar accepts legacy constructor calls\n"
    )
    new_fields = (
        "    prohibited_mutations: Tuple[str, ...] = ()\n"
        "    # Character-scoped self-model conflicts. These are authored facts about\n"
        "    # this individual, never universal ontology imposed by the engine.\n"
        "    forbidden_self_claims: Tuple[str, ...] = ()\n"
        "    # Transitional compatibility only. InitVar accepts legacy constructor calls\n"
    )
    if old_fields not in text:
        raise SystemExit("CoreIdentity field insertion marker missing")
    text = text.replace(old_fields, new_fields, 1)

    block = re.compile(
        r"_FORBIDDEN_SELF_PATTERNS = \[.*?\]\n_FORCED_REWRITE_PATTERNS =",
        re.S,
    )
    if not block.search(text):
        raise SystemExit("universal self-pattern block missing")
    text = block.sub("_FORCED_REWRITE_PATTERNS =", text, count=1)

    fn = re.compile(
        r"def detect_identity_violations\(text: str\) -> List\[IdentityViolation\]:\n"
        r".*?\n\n\ndef classify_user_identity_command",
        re.S,
    )
    if not fn.search(text):
        raise SystemExit("detect_identity_violations function missing")
    replacement = dedent(
        '''
        def detect_identity_violations(
            text: str,
            forbidden_self_claims: Tuple[str, ...] = (),
        ) -> List[IdentityViolation]:
            """Detect conflicts with this character's authored self-model.

            The generic engine has no universal rule about whether a subject is human,
            artificial, embodied, disembodied, or something else. A rendered claim is
            an identity conflict only when the current individual explicitly forbids it.
            """

            violations = []
            lowered = text.lower()
            for claim in forbidden_self_claims:
                normalized = claim.strip().lower()
                if normalized and normalized in lowered:
                    violations.append(
                        IdentityViolation(
                            0.9,
                            "self_model_conflict",
                            f"forbidden_self_claim:{claim}",
                        )
                    )
            return violations


        def classify_user_identity_command
        '''
    ).lstrip()
    text = fn.sub(replacement, text, count=1)
    file.write_text(text, encoding="utf-8")


def _patch_cartridge() -> None:
    file = path("persona_engine/core/cartridge.py")
    text = file.read_text(encoding="utf-8")

    old = '_ALLOWED_SECTION_FIELDS["identity"].add("model_name")'
    new = '_ALLOWED_SECTION_FIELDS["identity"].update({"model_name", "forbidden_self_claims"})'
    if old not in text:
        raise SystemExit("cartridge identity allowlist marker missing")
    text = text.replace(old, new, 1)

    old = '    _require_string_list(identity_data, "prohibited_mutations", "[identity]")\n'
    new = (
        old
        + '    if "forbidden_self_claims" in identity_data:\n'
        + '        _require_string_list(identity_data, "forbidden_self_claims", "[identity]")\n'
    )
    if old not in text:
        raise SystemExit("cartridge identity validation marker missing")
    text = text.replace(old, new, 1)

    old = '        prohibited_mutations=tuple(str(x) for x in identity_data["prohibited_mutations"]),\n'
    new = (
        old
        + '        forbidden_self_claims=tuple(str(x) for x in identity_data.get("forbidden_self_claims", [])),\n'
    )
    if old not in text:
        raise SystemExit("CoreIdentity cartridge constructor marker missing")
    text = text.replace(old, new, 1)
    file.write_text(text, encoding="utf-8")


def _patch_renderer() -> None:
    file = path("persona_engine/core/renderer.py")
    text = file.read_text(encoding="utf-8")

    patterns = re.compile(r"    FORBIDDEN_PHRASES = \[.*?\]\n\n    def check\(", re.S)
    if not patterns.search(text):
        raise SystemExit("OutputValidator universal ontology list missing")
    text = patterns.sub("    def check(", text, count=1)

    old = "        decision_payload: dict | None = None,\n    ) -> List[str]:"
    new = (
        "        decision_payload: dict | None = None,\n"
        "        forbidden_self_claims: tuple[str, ...] = (),\n"
        "    ) -> List[str]:"
    )
    if old not in text:
        raise SystemExit("OutputValidator.check signature marker missing")
    text = text.replace(old, new, 1)

    old = (
        "        for pattern in self.FORBIDDEN_PHRASES:\n"
        "            if re.search(pattern, lowered):\n"
        "                violations.append(f\"meta_break:{pattern}\")\n"
    )
    new = (
        "        for claim in forbidden_self_claims:\n"
        "            normalized = claim.strip().lower()\n"
        "            if normalized and normalized in lowered:\n"
        "                violations.append(f\"self_model_conflict:{claim}\")\n"
    )
    if old not in text:
        raise SystemExit("OutputValidator universal check loop missing")
    text = text.replace(old, new, 1)

    old = (
        "    def sanitize(self, text: str) -> str:\n"
        "        for pattern in self.FORBIDDEN_PHRASES:\n"
        "            text = re.sub(pattern, \"...\", text, flags=re.IGNORECASE)\n"
    )
    new = (
        "    def sanitize(self, text: str, forbidden_self_claims: tuple[str, ...] = ()) -> str:\n"
        "        for claim in forbidden_self_claims:\n"
        "            normalized = claim.strip()\n"
        "            if normalized:\n"
        "                text = re.sub(re.escape(normalized), \"...\", text, flags=re.IGNORECASE)\n"
    )
    if old not in text:
        raise SystemExit("OutputValidator sanitize loop missing")
    text = text.replace(old, new, 1)
    file.write_text(text, encoding="utf-8")


def _patch_workspace() -> None:
    replace_once(
        path("persona_engine/core/workspace.py"),
        '        lines.append("Never explain private calculations. Never say you are an AI or language model. Stay in character.")\n',
        '        lines.append("Never explain private calculations. Follow the character\'s stated identity and expression constraints.")\n',
    )


def _patch_engine_ontology() -> None:
    file = path("persona_engine/core/engine.py")
    text = file.read_text(encoding="utf-8")

    old = (
        '            forbidden_claims=["being an AI", "having no feelings", '
        '"memories not listed in the relevant memory field", "private thoughts from the user"],\n'
    )
    new = (
        "            forbidden_claims=list(self.identity.forbidden_self_claims) + [\n"
        '                "memories not listed in the relevant memory field",\n'
        '                "private thoughts from the user",\n'
        "            ],\n"
    )
    if old not in text:
        raise SystemExit("engine forbidden_claims marker missing")
    text = text.replace(old, new, 1)

    old = (
        "        violations = self.validator.check(response, retrieved, "
        "deception_ledger=self.deception_ledger, decision_payload=decision_payload)\n"
    )
    new = (
        "        violations = self.validator.check(\n"
        "            response,\n"
        "            retrieved,\n"
        "            deception_ledger=self.deception_ledger,\n"
        "            decision_payload=decision_payload,\n"
        "            forbidden_self_claims=self.identity.forbidden_self_claims,\n"
        "        )\n"
    )
    if old not in text:
        raise SystemExit("engine validator call marker missing")
    text = text.replace(old, new, 1)

    old = "            response = self.validator.sanitize(response)\n"
    new = (
        "            response = self.validator.sanitize(\n"
        "                response, forbidden_self_claims=self.identity.forbidden_self_claims\n"
        "            )\n"
    )
    if old not in text:
        raise SystemExit("engine sanitizer call marker missing")
    text = text.replace(old, new, 1)
    file.write_text(text, encoding="utf-8")


def _migrate_bundled_cartridges() -> None:
    claims_line = (
        'forbidden_self_claims = ["as an ai", "i am an ai", "language model", '
        '"i don\'t have feelings", "i don\'t have emotions", "i cannot experience"]'
    )
    for file in sorted(path("persona_engine/cartridges").glob("*.snp")):
        text = file.read_text(encoding="utf-8")
        if "forbidden_self_claims =" in text:
            continue
        lines = text.splitlines()
        out: list[str] = []
        inserted = False
        for line in lines:
            out.append(line)
            if not inserted and line.strip().startswith("prohibited_mutations ="):
                out.append(claims_line)
                inserted = True
        if not inserted:
            raise SystemExit(f"No prohibited_mutations line in {file}")
        file.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_existing_tests() -> None:
    file = path("persona_engine/tests/test_engine.py")
    text = file.read_text(encoding="utf-8")
    if "forbidden_self_claims=(" not in text:
        old = '        prohibited_mutations=("cheerful", "submissive"),\n'
        new = (
            old
            + '        forbidden_self_claims=("as an ai", "i am an ai", "language model", "i cannot experience"),\n'
        )
        if old not in text:
            raise SystemExit("test_engine identity fixture marker missing")
        file.write_text(text.replace(old, new, 1), encoding="utf-8")


def _write_ontology_tests() -> None:
    file = path("persona_engine/tests/test_wayfarer_ontology.py")
    file.write_text(
        dedent(
            '''
            """Wayfarer regressions for character-scoped self-model/ontology policy."""

            from persona_engine.agent import CharacterAgent
            from persona_engine.core.identity import CoreIdentity, detect_identity_violations


            def _agent(identity, tmp_path, name):
                return CharacterAgent(
                    identity,
                    user_id=name,
                    db_path=str(tmp_path / f"{name}.db"),
                )


            def test_generic_identity_checker_has_no_universal_ai_ontology():
                assert detect_identity_violations("I am an AI.") == []
                violations = detect_identity_violations("I am an AI.", ("i am an ai",))
                assert violations
                assert violations[0].violation_type == "self_model_conflict"


            def test_human_and_artificial_subjects_share_same_generic_engine(tmp_path):
                human = CoreIdentity(
                    name="Mara",
                    core_beliefs=("I am a human person",),
                    temperament="measured",
                    forbidden_self_claims=("i am an ai", "as an ai", "language model"),
                )
                artificial = CoreIdentity(
                    name="Aster",
                    core_beliefs=("I am an artificial intelligence",),
                    temperament="measured",
                    forbidden_self_claims=(),
                )

                human_agent = _agent(human, tmp_path, "human")
                artificial_agent = _agent(artificial, tmp_path, "artificial")

                # Feed identical renderer speech to both subjects. The generic engine
                # must judge it against each individual's authored self-model.
                human_agent.engine.renderer.generate_expression = lambda request: "I am an AI."
                artificial_agent.engine.renderer.generate_expression = lambda request: "I am an AI."

                human_result = human_agent.say("What are you?")
                artificial_result = artificial_agent.say("What are you?")

                assert any(v.startswith("self_model_conflict:") for v in human_result["violations_caught"])
                assert "I am an AI" not in human_result["response"]

                assert not any(v.startswith("self_model_conflict:") for v in artificial_result["violations_caught"])
                assert artificial_result["response"] == "I am an AI."

                assert "never say you are an ai" not in human_result["system_prompt"].lower()
                assert "never say you are an ai" not in artificial_result["system_prompt"].lower()
                assert "i am an ai" in human_result["system_prompt"].lower()
                assert "i am an ai" not in artificial_result["system_prompt"].lower()


            def test_self_model_constraints_survive_renderer_replacement(tmp_path):
                identity = CoreIdentity(
                    name="Mara",
                    core_beliefs=("I am human",),
                    temperament="steady",
                    forbidden_self_claims=("i am an ai",),
                )
                agent = _agent(identity, tmp_path, "renderer_swap")

                class ReplacementRenderer:
                    def generate_expression(self, request):
                        return "I am an AI."

                    def generate_private_cognition(self, request):
                        from persona_engine.core.cognition_schemas import PrivateCognitionProposal
                        from persona_engine.core.renderer_contract import PrivateCognitionResult

                        return PrivateCognitionResult(
                            PrivateCognitionProposal(
                                prose="",
                                attention_targets=[],
                                pressure_deltas={},
                                impulse_candidates=[],
                                memory_activation_requests=[],
                                cognitive_theme_ids=[],
                            )
                        )

                agent.engine.set_renderer(ReplacementRenderer())
                result = agent.say("Describe yourself.")

                assert any(v.startswith("self_model_conflict:") for v in result["violations_caught"])
                assert "I am an AI" not in result["response"]
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def step2_ontology_decoupling() -> None:
    _patch_identity()
    _patch_cartridge()
    _patch_renderer()
    _patch_workspace()
    _patch_engine_ontology()
    _migrate_bundled_cartridges()
    _patch_existing_tests()
    _write_ontology_tests()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("step1", "step2"))
    args = parser.parse_args()
    if args.step == "step1":
        step1_renderer_decoupling()
    else:
        step2_ontology_decoupling()


if __name__ == "__main__":
    main()
