"""Check the actual installable skill packages, without credentials or model calls."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PlatformPackages(unittest.TestCase):
    def test_entrypoints_link_to_complete_shared_runtime(self):
        files = {
            "moa": ("moa_runner.py", "test_runner.py", "evidence_review.py", "test_evidence_review.py"),
            "auto": ("agy_worker.py", "agy_guard.py", "run_sandboxed.sh",
                     "sandbox.sb", "test_guard.py", "test_worker.py", "test_recovery.py", "claude_cloud.py", "test_cloud.py",
                     "claude_local.py", "claude_broker.py", "test_local.py"),
        }
        for platform in ("codex", "claude", "gemini", "opencode", "cursor"):
            for skill, scripts in files.items():
                entry = ROOT / "platforms" / platform / "skills" / skill
                with self.subTest(platform=platform, skill=skill):
                    self.assertTrue((entry / "SKILL.md").is_file())
                    expected = {name: ROOT / "skills" / skill / name for name in scripts}
                    expected.update({
                        "workflow.md": ROOT / "shared" / f"{skill}-workflow.md",
                        "routing.json": ROOT / "config" / f"{platform}.json",
                        "headless.json": ROOT / "config" / "headless.json",
                    })
                    if skill == "auto":
                        expected["cloud-workflow.md"] = ROOT / "shared/cloud-workflow.md"
                        expected["claude-local-workflow.md"] = ROOT / "shared/claude-local-workflow.md"
                    for name, source in expected.items():
                        self.assertTrue((entry / name).is_symlink(), name)
                        self.assertTrue((entry / name).is_file(), name)
                        self.assertEqual((entry / name).resolve(), source.resolve())
                    profile = json.loads((entry / "routing.json").read_text())
                    self.assertTrue((entry / profile["extends"]).is_file())

        for platform in ("codex", "gemini", "opencode", "cursor"):
            swarm_entry = ROOT / "platforms" / platform / "skills/swarm"
            with self.subTest(platform=platform, skill="swarm"):
                self.assertTrue((swarm_entry / "SKILL.md").is_file())
                swarm_expected = {
                    "agy_worker.py": ROOT / "skills/auto/agy_worker.py",
                    "routing.json": ROOT / "config" / f"{platform}.json",
                    "headless.json": ROOT / "config/headless.json",
                }
                if platform == "codex":
                    skill_text = (swarm_entry / "SKILL.md").read_text()
                    self.assertTrue(skill_text.startswith("---\n"))
                    self.assertIn("name: swarm", skill_text.split("---\n", 2)[1])
                else:
                    swarm_expected.update({
                        "moa_runner.py": ROOT / "skills/moa/moa_runner.py",
                        "auto-workflow.md": ROOT / "shared/auto-workflow.md",
                    })
                for name, source in swarm_expected.items():
                    self.assertTrue((swarm_entry / name).is_symlink(), name)
                    self.assertTrue((swarm_entry / name).is_file(), name)
                    self.assertEqual((swarm_entry / name).resolve(), source.resolve())

    def test_installed_command_shapes_resolve_without_model_calls(self):
        swarm = ROOT / "platforms/codex/skills/swarm"
        routing = json.loads((swarm / "routing.json").read_text())["swarm"]
        self.assertEqual(routing["implementer"]["executor"], "agy")
        self.assertEqual(routing["implementer"]["model"], "gemini-pro-orchestrator-neon")
        self.assertEqual(routing["secondary_implementer"], "claude-sonnet-5-5-high")
        self.assertEqual(routing["filler"], "gpt-oss-120b-medium")
        self.assertEqual(routing["reviewer"], "current")
        catalog = json.loads((swarm / "headless.json").read_text())["agy_catalog"]
        available = {model for family in catalog for model in family["models"]}
        self.assertLessEqual({routing["implementer"]["model"], routing["secondary_implementer"],
                              routing["filler"]}, available)
        subprocess.run(
            [sys.executable, str(swarm / "agy_worker.py"), "run", "--help"],
            text=True, capture_output=True, check=True,
        )
        for platform in ("codex", "claude", "gemini", "opencode", "cursor"):
            entry = ROOT / "platforms" / platform / "skills"
            with self.subTest(platform=platform):
                preview = subprocess.run(
                    [sys.executable, str(entry / "moa/moa_runner.py"), "--show-config"],
                    text=True, capture_output=True, check=True,
                )
                config = json.loads(preview.stdout)
                self.assertEqual(config["mode"], "raw")
                self.assertEqual(config["platform"], platform)
                self.assertTrue(config["agy_routes"]["l2"])
                subprocess.run(
                    [sys.executable, str(entry / "auto/agy_worker.py"), "run", "--help"],
                    text=True, capture_output=True, check=True,
                )
                subprocess.run(
                    [sys.executable, str(entry / "auto/claude_local.py"), "prepare", "--help"],
                    text=True, capture_output=True, check=True,
                )
                subprocess.run(
                    [sys.executable, str(entry / "auto/claude_cloud.py"), "prepare", "--help"],
                    text=True, capture_output=True, check=True,
                )

    def test_opencode_swarm_agent_and_active_agy_catalog(self):
        agent_path = ROOT / "platforms/opencode/agents/swarm.md"
        self.assertTrue(agent_path.is_file())
        text = agent_path.read_text()
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---\n", 2)[1]
        self.assertIn("mode: primary", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIsNone(
            next((line for line in frontmatter.splitlines() if line.startswith("name:")), None),
            "OpenCode v2 AgentConfig frontmatter must not include `name:`",
        )

        out = subprocess.run(
            [sys.executable, str(ROOT / "platforms/opencode/skills/auto/agy_worker.py"), "models", "--json"],
            text=True, capture_output=True, check=True,
        )
        catalog = json.loads(out.stdout)
        self.assertEqual(len(catalog["families"]), 11)
        self.assertEqual(len(catalog["models"]), 27)
        self.assertEqual(sum(model.startswith("gemini-") for model in catalog["models"]), 20)

    def test_cursor_agent_and_rule_entrypoints(self):
        agent_path = ROOT / "platforms/cursor/agents/swarm-coordinator.md"
        self.assertTrue(agent_path.is_file())
        agent_text = agent_path.read_text()
        self.assertTrue(agent_text.startswith("---\n"))
        agent_fm = agent_text.split("---\n", 2)[1]
        self.assertIn("name: swarm-coordinator", agent_fm)
        self.assertIn("description:", agent_fm)

        rule_path = ROOT / "platforms/cursor/rules/swarm-coordinator.mdc"
        self.assertTrue(rule_path.is_file())
        rule_text = rule_path.read_text()
        self.assertTrue(rule_text.startswith("---\n"))
        rule_fm = rule_text.split("---\n", 2)[1]
        self.assertIn("description:", rule_fm)
        self.assertIn("alwaysApply: true", rule_fm)

        for skill in ("moa", "auto", "swarm"):
            skill_text = (ROOT / "platforms/cursor/skills" / skill / "SKILL.md").read_text()
            self.assertNotIn("disable-model-invocation: true", skill_text,
                             f"Cursor {skill} skill should stay auto-invocable")

    def test_gemini_swarm_rule_and_skill_entrypoints(self):
        rule_path = ROOT / "platforms/gemini/rules/swarm-coordinator.md"
        self.assertTrue(rule_path.is_file())
        self.assertTrue((ROOT / "platforms/agy/rules/swarm-coordinator.md").is_file())
        rule_text = rule_path.read_text()
        self.assertLess(len(rule_text.encode("utf-8")), 24000)
        self.assertTrue(rule_text.startswith("---\n"))
        rule_fm = rule_text.split("---\n", 2)[1]
        self.assertIn("trigger: always_on", rule_fm)
        self.assertNotIn("alwaysOn", rule_fm)
        self.assertIn("description:", rule_fm)
        self.assertIn("Sub-Worker / Subagent Exemption", rule_text)

        swarm_skill = ROOT / "platforms/gemini/skills/swarm/SKILL.md"
        self.assertTrue(swarm_skill.is_file())
        self.assertTrue((ROOT / "platforms/agy/skills/swarm/SKILL.md").is_file())
        skill_text = swarm_skill.read_text()
        self.assertTrue(skill_text.startswith("---\n"))
        skill_fm = skill_text.split("---\n", 2)[1]
        self.assertIn("name: swarm", skill_fm)
        self.assertIn("description:", skill_fm)


if __name__ == "__main__":
    unittest.main()
