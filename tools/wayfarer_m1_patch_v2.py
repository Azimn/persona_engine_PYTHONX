"""Project Wayfarer M1 ordered migration, revision 2.

Step 1 removes the final InteriorEngine dependency on ``identity.model_name``.
Step 2 moves AI/human ontology assumptions from generic engine code into
character-scoped self-model constraints.

The script is strict and fails on unexpected source shapes instead of guessing.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]


def p(rel: str) -> Path:
    return ROOT / rel


def replace_once(file: Path, old: str, new: str) -> None:
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected one match in {file}, found {count}: {old!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def step1() -> None:
    replace_once(
        p("persona_engine/core/engine.py"),
        "        self.renderer = LocalLLMRenderer(model_name=identity.model_name)\n",
        "        # Renderer bootstrap is host/runtime policy, not character identity.\n"
        "        # Start deterministically offline until an approved host/session replaces it.\n"
        "        self.renderer = LocalLLMRenderer(model_name=\"missing-model-for-mock\", provider=\"offline\")\n",
    )

    file = p("persona_engine/tests/test_wayfarer_renderer_identity.py")
    text = file.read_text(encoding="utf-8")
    if "test_engine_bootstrap_does_not_read_identity_model_name" not in text:
        marker = "def test_host_can_replace_renderer_without_changing_identity(tmp_path):\n"
        if marker not in text:
            raise SystemExit("renderer identity test marker missing")
        test = dedent(
            '''
            def test_engine_bootstrap_does_not_read_identity_model_name(tmp_path, monkeypatch):
                identity = CoreIdentity(
                    name="NoRendererInIdentity",
                    core_beliefs=("I persist across renderers",),
                    temperament="steady",
                    model_name="legacy-value-must-not-be-read",
                )

                # The compatibility InitVar is not stored on the instance. Removing
                # its class default makes any accidental engine read fail immediately.
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
        file.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")


def patch_identity() -> None:
    file = p("persona_engine/core/identity.py")
    text = file.read_text(encoding="utf-8")

    old = (
        "    prohibited_mutations: Tuple[str, ...] = ()\n"
        "    # Transitional compatibility only. InitVar accepts legacy constructor calls\n"
    )
    new = (
        "    prohibited_mutations: Tuple[str, ...] = ()\n"
        "    # Character-scoped self-model conflicts. These are authored facts about\n"
        "    # this individual, never universal ontology imposed by the engine.\n"
        "    forbidden_self_claims: Tuple[str, ...] = ()\n"
        "    # Transitional compatibility only. InitVar accepts legacy constructor calls\n"
    )
    if old not in text:
        raise SystemExit("CoreIdentity insertion marker missing")
    text = text.replace(old, new, 1)

    universal = re.compile(
        r"_FORBIDDEN_SELF_PATTERNS = \[.*?\]\n_FORCED_REWRITE_PATTERNS =",
        re.S,
    )
    if not universal.search(text):
        raise SystemExit("universal ontology pattern block missing")
    text = universal.sub("_FORCED_REWRITE_PATTERNS =", text, count=1)

    start = text.find("def detect_identity_violations")
    end = text.find("\ndef classify_user_identity_command", start)
    if start < 0 or end < 0:
        raise SystemExit("identity violation function boundaries missing")
    new_fn = dedent(
        '''
        def detect_identity_violations(
            text: str,
            forbidden_self_claims: Tuple[str, ...] = (),
        ) -> List[IdentityViolation]:
            """Detect conflicts with this character's authored self-model.

            The generic engine has no universal rule about whether a subject is human,
            artificial, embodied, disembodied, or something else. A rendered claim is
            a conflict only when the current individual explicitly forbids it.
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

        '''
    ).lstrip()
    text = text[:start] + new_fn + text[end + 1 :]
    file.write_text(text, encoding="utf-8")


def patch_cartridge() -> None:
    file = p("persona_engine/core/cartridge.py")
    text = file.read_text(encoding="utf-8")

    old = '_ALLOWED_SECTION_FIELDS["identity"].add("model_name")'
    new = '_ALLOWED_SECTION_FIELDS["identity"].update({"model_name", "forbidden_self_claims"})'
    if old not in text:
        raise SystemExit("identity allowlist marker missing")
    text = text.replace(old, new, 1)

    old = '    _require_string_list(identity_data, "prohibited_mutations", "[identity]")\n'
    if old not in text:
        raise SystemExit("identity validation marker missing")
    text = text.replace(
        old,
        old
        + '    if "forbidden_self_claims" in identity_data:\n'
        + '        _require_string_list(identity_data, "forbidden_self_claims", "[identity]")\n',
        1,
    )

    old = '        prohibited_mutations=tuple(str(x) for x in identity_data["prohibited_mutations"]),\n'
    if old not in text:
        raise SystemExit("identity constructor marker missing")
    text = text.replace(
        old,
        old
        + '        forbidden_self_claims=tuple(str(x) for x in identity_data.get("forbidden_self_claims", [])),\n',
        1,
    )
    file.write_text(text, encoding="utf-8")


def patch_renderer() -> None:
    file = p("persona_engine/core/renderer.py")
    text = file.read_text(encoding="utf-8")

    universal = re.compile(r"    FORBIDDEN_PHRASES = \[.*?\]\n\n    def check\(", re.S)
    if not universal.search(text):
        raise SystemExit("OutputValidator universal ontology list missing")
    text = universal.sub("    def check(", text, count=1)

    old = "        decision_payload: dict | None = None,\n    ) -> List[str]:"
    new = (
        "        decision_payload: dict | None = None,\n"
        "        forbidden_self_claims: tuple[str, ...] = (),\n"
        "    ) -> List[str]:"
    )
    if old not in text:
        raise SystemExit("validator check signature marker missing")
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
        raise SystemExit("validator ontology check loop missing")
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
        raise SystemExit("validator sanitizer ontology loop missing")
    text = text.replace(old, new, 1)
    file.write_text(text, encoding="utf-8")


def patch_workspace() -> None:
    replace_once(
        p("persona_engine/core/workspace.py"),
        '        lines.append("Never explain private calculations. Never say you are an AI or language model. Stay in character.")\n',
        '        lines.append("Never explain private calculations. Follow the character\'s stated identity and expression constraints.")\n',
    )


def patch_engine_ontology() -> None:
    file = p("persona_engine/core/engine.py")
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
        raise SystemExit("engine forbidden claims marker missing")
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


def migrate_bundled_cartridges() -> None:
    claims = (
        'forbidden_self_claims = ["as an ai", "i am an ai", "language model", '
        '"i don\'t have feelings", "i don\'t have emotions", "i cannot experience"]'
    )
    for file in sorted(p("persona_engine/cartridges").glob("*.snp")):
        text = file.read_text(encoding="utf-8")
        if "forbidden_self_claims =" in text:
            continue
        out: list[str] = []
        inserted = False
        for line in text.splitlines():
            out.append(line)
            if not inserted and line.strip().startswith("prohibited_mutations ="):
                out.append(claims)
                inserted = True
        if not inserted:
            raise SystemExit(f"No prohibited_mutations field in {file}")
        file.write_text("\n".join(out) + "\n", encoding="utf-8")


def patch_existing_tests() -> None:
    file = p("persona_engine/tests/test_engine.py")
    text = file.read_text(encoding="utf-8")
    if "forbidden_self_claims=(" not in text:
        old = '        prohibited_mutations=("cheerful", "submissive"),\n'
        if old not in text:
            raise SystemExit("test_engine fixture marker missing")
        text = text.replace(
            old,
            old
            + '        forbidden_self_claims=("as an ai", "i am an ai", "language model", "i cannot experience"),\n',
            1,
        )
        file.write_text(text, encoding="utf-8")


def write_ontology_tests() -> None:
    p("persona_engine/tests/test_wayfarer_ontology.py").write_text(
        dedent(
            '''
            """Wayfarer regressions for character-scoped self-model policy."""

            from persona_engine.agent import CharacterAgent
            from persona_engine.core.identity import CoreIdentity, detect_identity_violations


            def _agent(identity, tmp_path, name):
                return CharacterAgent(identity, user_id=name, db_path=str(tmp_path / f"{name}.db"))


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


def step2() -> None:
    patch_identity()
    patch_cartridge()
    patch_renderer()
    patch_workspace()
    patch_engine_ontology()
    migrate_bundled_cartridges()
    patch_existing_tests()
    write_ontology_tests()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("step1", "step2"))
    args = parser.parse_args()
    (step1 if args.step == "step1" else step2)()


if __name__ == "__main__":
    main()
