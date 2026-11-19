"""Offline routing and failure-contract tests; no local keys or network are used."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import uuid

# Test the shared runner deterministically even when this test file is invoked
# through a platform symlink. Entrypoint inference is checked in subprocesses.
spec = importlib.util.spec_from_file_location("moa_runner", Path(__file__).resolve().with_name("moa_runner.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
_REAL_LOAD_ENV = runner.load_env
_REAL_HAS_OPENCODE_XAI_AUTH = runner.has_opencode_xai_auth


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch.object(runner, "RUNS_DIR", self.root / "runs"))
        self.env_loader = self.enterContext(patch.object(runner, "load_env"))
        self.grok_oauth = self.enterContext(patch.object(runner, "has_opencode_xai_auth", return_value=False))
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.network = self.enterContext(patch.object(runner.urllib.request, "urlopen",
                                                      side_effect=AssertionError("Network forbidden in offline tests")))

    def invoke(self, args, result="worker answer", side_effect=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(runner, "call_model", return_value=result, side_effect=side_effect) as call:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = runner.main(args)
        return code, stdout.getvalue(), stderr.getvalue(), call

    def record(self):
        files = list(runner.RUNS_DIR.glob("*.json"))
        self.assertEqual(len(files), 1)
        return json.loads(files[0].read_text())

    def raw_response(self, stdout):
        body = stdout.split("===MOA_RAW_JSON_START===\n")[1].split("\n===MOA_RAW_JSON_END===")[0]
        return json.loads(body)

    def test_profiles_share_api_defaults_and_have_distinct_native_roles(self):
        headless = runner.load_config("headless")
        codex = runner.load_config("codex")
        claude = runner.load_config("claude")
        self.assertEqual(headless["mode"], "aggregate")
        self.assertEqual(codex["mode"], "raw")
        self.assertEqual(claude["mode"], "raw")
        self.assertEqual(headless["providers"], codex["providers"])
        self.assertEqual(codex["native_roles"]["planner"], "gpt-6.2-astra")
        self.assertEqual(codex["agy_routes"]["l1"], claude["agy_routes"]["l1"])
        self.assertEqual(headless["reviewer"]["model"], "glm-5.3")
        self.assertEqual(headless["providers"]["codex"], {"model": "gpt-6-luna-high", "display_name": "GPT-6-Luna (High)"})
        self.assertEqual(headless["providers"]["glm"], {"model": "glm-5.3", "display_name": "GLM-5.3"})
        self.assertEqual(headless["providers"]["deepseek"], {"model": "deepseek-v4-pro", "display_name": "DeepSeek-V4-Pro"})
        self.assertEqual(headless["providers"]["deepseek-flash"], {"model": "deepseek-flash", "display_name": "DeepSeek-V4.1-Flash"})
        self.assertEqual(headless["providers"]["kimi"], {"model": "kimi-k3.1-pro", "display_name": "Kimi-K3.1-Pro"})
        self.assertEqual(headless["agy_routes"]["filler"], "gemini-4-argon-low")
        self.assertEqual(headless["api_advisors"]["providers"], ["glm", "deepseek", "deepseek-flash", "kimi", "minimax"])
        self.assertEqual(headless["worker_defaults"], ["agy", "codex", "grok", "glm", "deepseek", "kimi", "minimax"])
        self.assertEqual(headless["aggregation_priority"], ["agy", "codex", "grok", "deepseek", "deepseek-flash", "glm", "kimi", "minimax"])
        self.assertEqual(codex["worker_defaults"], ["agy", "grok", "glm", "deepseek", "kimi", "minimax"])

    def test_config_preview_does_not_read_keys_call_models_or_create_records(self):
        for alias in ("--show-config", "--dry-run"):
            code, stdout, _, call = self.invoke(["--platform", "codex", alias, "--models", "deepseek"])
            self.assertEqual(code, 0)
            config = json.loads(stdout)
            self.assertEqual(config["mode"], "raw")
            self.assertEqual([w["provider"] for w in config["selected_workers"]], ["deepseek"])
            call.assert_not_called()
        self.env_loader.assert_not_called()
        self.network.assert_not_called()
        self.assertFalse(runner.RUNS_DIR.exists())

    def test_codex_and_claude_default_to_raw(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-key"
        for platform in ("codex", "claude"):
            code, stdout, _, call = self.invoke(["--platform", platform, "question"])
            self.assertEqual(code, 0)
            self.assertEqual(self.raw_response(stdout), {"DeepSeek-V4-Pro": "worker answer"})
            self.assertEqual(call.call_count, 1)

    def test_headless_legacy_default_aggregates_and_raw_override_remains(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-key"
        code, stdout, _, call = self.invoke(["question"])
        self.assertEqual(code, 0)
        self.assertIn("FINAL SYNTHESIZED RESPONSE", stdout)
        self.assertEqual(call.call_count, 2)
        code, stdout, _, call = self.invoke(["--raw", "question"])
        self.assertEqual(code, 0)
        self.assertIn("MOA_RAW_JSON_START", stdout)
        self.assertEqual(call.call_count, 1)

    def test_explicit_selection_does_not_call_other_configured_providers(self):
        os.environ.update(DEEPSEEK_API_KEY="deepseek-test-key", MINIMAX_API_KEY="minimax-test-key")
        code, _, _, call = self.invoke(["--models", "deepseek,deepseek", "question"])
        self.assertEqual(code, 0)
        self.assertEqual(call.call_count, 2)
        self.assertTrue(all(item.args[0] == "deepseek" for item in call.call_args_list))
        self.assertEqual([w["provider"] for w in self.record()["worker_configuration"]], ["deepseek"])

    def test_explicit_missing_key_fails_before_any_model_call(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-key"
        code, _, stderr, call = self.invoke(["--models", "deepseek,minimax", "--raw", "question"])
        self.assertNotEqual(code, 0)
        self.assertIn("Selected providers lack API keys: minimax", stderr)
        call.assert_not_called()
        self.assertEqual(self.record()["status"], "failed")

    def test_unknown_and_native_models_are_not_api_providers(self):
        for value in ("gpt-6-astra", "planner", "", "deepseek,unknown"):
            with self.subTest(value=value), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as stopped:
                    runner.main(["--models", value, "--dry-run"])
                self.assertEqual(stopped.exception.code, 2)
        self.env_loader.assert_not_called()
        self.network.assert_not_called()

    def test_agy_models_in_catalog_can_be_selected_by_exact_id(self):
        profile = runner.load_config("codex")
        models = [model for family in profile["agy_catalog"] for model in family["models"]]
        for model in models:
            for selector in (f"agy/{model}", model):
                with self.subTest(selector=selector):
                    code, stdout, stderr, call = self.invoke(["--show-config", "--platform", "codex",
                                                               "--models", selector])
                    self.assertEqual(code, 0, stderr)
                    worker, = json.loads(stdout)["selected_workers"]
                    self.assertEqual((worker["provider"], worker["model"]), ("agy", model))
                    call.assert_not_called()
        self.env_loader.assert_not_called()
        self.network.assert_not_called()

    def test_agy_model_selection_rejects_unknown_or_conflicting_models(self):
        for selector, message in (
            ("agy/nonexistent-model", "Unknown agy model"),
            ("agy/gemini-4-neon-high,agy/gemini-4-neon-medium", "Select one agy model per run"),
        ):
            with self.subTest(selector=selector), redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as stopped:
                    runner.main(["--models", selector, "--show-config"])
                self.assertEqual(stopped.exception.code, 2)
                self.assertIn(message, stderr.getvalue())

    def test_explicit_agy_model_is_passed_to_the_local_cli(self):
        os.environ.update(AGY_CLI="installed", GEMINI_API_KEY="must-stay-out-of-environment")
        proc = subprocess.CompletedProcess([], 0, stdout='{"status":"SUCCESS","response":"hello"}')
        with patch.object(runner, "agy_executable", return_value="/usr/local/bin/agy"), \
                patch.object(runner.shutil, "which", return_value=None), \
                patch.object(runner.subprocess, "run", return_value=proc) as called, \
                redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()):
            code = runner.main(["--raw", "--models", "agy/gpt-oss-120b-medium", "question"])

        self.assertEqual(code, 0)
        called.assert_called_once()
        command = called.call_args.args[0]
        self.assertEqual(command[command.index("--model") + 1], "gpt-oss-120b-medium")
        self.assertEqual(command[command.index("--mode") + 1], "plan")
        self.assertNotIn("GEMINI_API_KEY", called.call_args.kwargs["env"])
        self.assertEqual(self.raw_response(stdout.getvalue()), {"GPT-OSS 120B (Medium)": "hello"})
        self.assertEqual(self.record()["worker_results"]["agy"]["executor"], "agy")
        self.network.assert_not_called()

    def test_mixed_failure_is_excluded_from_raw_and_recorded(self):
        os.environ.update(DEEPSEEK_API_KEY="test-ds", MINIMAX_API_KEY="test-minimax")
        def answer(provider, *args):
            if provider == "minimax":
                raise ValueError("rejected")
            return "usable answer"
        code, stdout, stderr, _ = self.invoke(["--platform", "codex", "question"], side_effect=answer)
        self.assertEqual(code, 0)
        self.assertEqual(self.raw_response(stdout), {"DeepSeek-V4-Pro": "usable answer"})
        self.assertIn("Partial failure", stderr)
        record = self.record()
        self.assertEqual(record["status"], "partial_success")
        self.assertEqual(record["worker_results"]["minimax"]["status"], "failed")

    def test_mixed_failure_is_excluded_from_aggregation(self):
        os.environ.update(DEEPSEEK_API_KEY="test-ds", MINIMAX_API_KEY="test-minimax")
        def answer(provider, prompt, api_key, model, system, max_tokens):
            if system and system.startswith("You are the Aggregator"):
                payload = json.loads(prompt)
                self.assertEqual(payload["original_prompt"], "question")
                self.assertEqual(payload["worker_responses"], {"DeepSeek-V4-Pro": "usable answer"})
                self.assertIn(runner.COMMON_RULES, system)
                self.assertNotIn("usable answer", system)
                return "final answer"
            if provider == "minimax":
                raise ValueError("bad worker response")
            return "usable answer"
        code, stdout, _, call = self.invoke(["question"], side_effect=answer)
        self.assertEqual(code, 0)
        self.assertIn("final answer", stdout)
        self.assertEqual(call.call_count, 3)
        self.assertEqual(self.record()["status"], "partial_success")

    def test_all_failed_workers_stop_before_aggregation(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-key"
        code, stdout, stderr, call = self.invoke(["question"], side_effect=ValueError("unusable"))
        self.assertNotEqual(code, 0)
        self.assertNotIn("FINAL SYNTHESIZED RESPONSE", stdout)
        self.assertIn("All workers failed", stderr)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(self.record()["status"], "failed")
        self.assertNotIn("aggregation_result", self.record())

    def test_review_alias_uses_configured_reviewer_and_preserves_markers(self):
        os.environ["ZHIPUAI_API_KEY"] = "synthetic-key"
        code, stdout, _, call = self.invoke(["--glm52", "question"])
        self.assertEqual(code, 0)
        self.assertIn("===MOA_REVIEW_START===", stdout)
        self.assertIn("===MOA_REVIEW_END===", stdout)
        self.assertEqual(call.call_args.args[0], "glm")
        self.assertEqual(call.call_args.args[3], "glm-5.3")
        self.assertEqual(self.record()["reviewer_result"]["status"], "success")

    def test_independent_workers_receive_only_task_and_shared_rules(self):
        os.environ.update(DEEPSEEK_API_KEY="synthetic-ds", MINIMAX_API_KEY="synthetic-minimax")
        code, stdout, _, call = self.invoke(["--platform", "codex", "--models", "deepseek,minimax", "original task"])
        self.assertEqual(code, 0)
        self.assertEqual(call.call_count, 2)
        for item in call.call_args_list:
            self.assertEqual(item.args[1], "original task")
            self.assertEqual(item.args[4], runner.WORKER_RULES)
        self.assertIn("MOA_RAW_JSON_START", stdout)
        self.assertEqual(self.record()["prompt_version"], runner.PROMPT_VERSION)

    def test_review_is_one_logical_call_with_evidence_rules(self):
        os.environ["ZHIPUAI_API_KEY"] = "synthetic-key"
        code, _, _, call = self.invoke(["--review", "task and draft"])
        self.assertEqual(code, 0)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[1], "task and draft")
        self.assertEqual(call.call_args.args[4], runner.REVIEW_RULES)

    def test_review_error_returns_nonzero_and_no_success_marker(self):
        os.environ["ZHIPUAI_API_KEY"] = "synthetic-key"
        code, stdout, stderr, _ = self.invoke(["--review", "question"], side_effect=ValueError("review failed"))
        self.assertNotEqual(code, 0)
        self.assertNotIn("MOA_REVIEW_START", stdout)
        self.assertIn("Review failed", stderr)
        self.assertEqual(self.record()["status"], "failed")

    def test_aggregation_error_returns_nonzero(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-key"
        code, stdout, stderr, _ = self.invoke(["question"], side_effect=["draft", ValueError("failed")])
        self.assertNotEqual(code, 0)
        self.assertNotIn("FINAL SYNTHESIZED RESPONSE", stdout)
        self.assertIn("Aggregation failed", stderr)
        self.assertEqual(self.record()["aggregation_result"]["status"], "failed")

    def test_run_metadata_is_shared_and_does_not_store_prompt_or_keys(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-private-key"
        prompt = "private original prompt"
        code, _, _, _ = self.invoke(["--platform", "codex", "--coordinator-model", "gpt-6-astra",
                                      "--task-id", "task-42", prompt])
        self.assertEqual(code, 0)
        record = self.record()
        uuid.UUID(record["run_id"])
        self.assertEqual(record["platform"], "codex")
        self.assertEqual(record["executor"], "api")
        self.assertEqual(record["coordinator_model"], "gpt-6-astra")
        self.assertEqual(record["task_id"], "task-42")
        self.assertEqual(record["prompt_characters"], len(prompt))
        self.assertEqual(len(record["prompt_sha256"]), 64)
        self.assertIn("finished_at", record)
        serialized = json.dumps(record)
        self.assertNotIn(prompt, serialized)
        self.assertNotIn("synthetic-private-key", serialized)

    def test_error_messages_redact_transport_key(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-private-key"
        code, _, stderr, _ = self.invoke(["--raw", "question"], side_effect=ValueError(
            "https://example.invalid?key=synthetic-private-key"))
        self.assertNotEqual(code, 0)
        self.assertNotIn("synthetic-private-key", stderr)
        self.assertNotIn("synthetic-private-key", json.dumps(self.record()))

    def test_transient_errors_retry_but_auth_errors_do_not(self):
        settings = runner.load_config("headless")["providers"]["deepseek"]
        with patch.object(runner, "call_model", side_effect=[TimeoutError("slow"), "recovered"]) as call:
            result = runner.run_worker("deepseek", settings, "question", "synthetic-key")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["attempts"], 2)
            self.assertNotIn("error", result)
            self.assertEqual(call.call_count, 2)
        failure = urllib.error.HTTPError("https://example.invalid", 401, "Unauthorized", {}, None)
        with patch.object(runner, "call_model", side_effect=failure) as call:
            self.assertEqual(runner.run_worker("deepseek", settings, "question", "synthetic-key")["status"], "failed")
            self.assertEqual(call.call_count, 1)

    def test_symlink_resolves_shared_config_env_and_runtime_paths(self):
        link = self.root / "platform" / "moa_runner.py"
        link.parent.mkdir()
        link.symlink_to(Path(runner.__file__).resolve())
        spec = importlib.util.spec_from_file_location("runner_through_link", link)
        linked = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(linked)
        self.assertEqual(linked.SKILL_DIR, Path(runner.__file__).resolve().parent)
        self.assertEqual(linked.env_paths()[0], linked.SKILL_DIR / ".env")
        self.assertEqual(linked.RUNS_DIR, linked.SKILL_DIR / "runs")
        process = subprocess.run([sys.executable, str(link), "--platform", "codex", "--dry-run"],
                                 capture_output=True, text=True, env={})
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["native_roles"]["planner"], "gpt-6.2-astra")

    def test_platform_entrypoints_infer_raw_without_platform_argument(self):
        repo = runner.SKILL_DIR.parent.parent
        for platform in ("codex", "claude", "gemini", "opencode", "cursor"):
            platform_dir = repo / "platforms" / platform / "skills" / "moa"
            installed = self.root / platform / ".agents" / "skills" / "moa"
            installed.parent.mkdir(parents=True)
            installed.symlink_to(platform_dir, target_is_directory=True)
            for entry in (platform_dir / "moa_runner.py", installed / "moa_runner.py"):
                with self.subTest(platform=platform, entry=str(entry)):
                    process = subprocess.run([sys.executable, str(entry), "--show-config"],
                                             capture_output=True, text=True, env={})
                    self.assertEqual(process.returncode, 0, process.stderr)
                    config = json.loads(process.stdout)
                    self.assertEqual(config["platform"], platform)
                    self.assertEqual(config["mode"], "raw")

    def test_core_keeps_headless_default_and_explicit_platform_always_wins(self):
        repo = runner.SKILL_DIR.parent.parent
        cases = [
            (runner.SKILL_DIR / "moa_runner.py", [], "headless", "aggregate"),
            (repo / "platforms/codex/skills/moa/moa_runner.py", ["--platform", "headless"], "headless", "aggregate"),
            (repo / "platforms/claude/skills/moa/moa_runner.py", ["--platform", "codex"], "codex", "raw"),
            (repo / "platforms/gemini/skills/moa/moa_runner.py", ["--platform", "gemini"], "gemini", "raw"),
            (repo / "platforms/opencode/skills/moa/moa_runner.py", ["--platform", "opencode"], "opencode", "raw"),
            (repo / "platforms/cursor/skills/moa/moa_runner.py", ["--platform", "cursor"], "cursor", "raw"),
            (runner.SKILL_DIR / "moa_runner.py", ["--platform", "claude"], "claude", "raw"),
        ]
        for entry, flags, platform, mode in cases:
            with self.subTest(entry=str(entry), flags=flags):
                process = subprocess.run([sys.executable, str(entry), *flags, "--show-config"],
                                         capture_output=True, text=True, env={})
                self.assertEqual(process.returncode, 0, process.stderr)
                config = json.loads(process.stdout)
                self.assertEqual(config["platform"], platform)
                self.assertEqual(config["mode"], mode)

    def test_config_accepts_explicit_api_model_and_rejects_circular_inheritance(self):
        config_dir = self.root / "config"
        shutil.copytree(runner.CONFIG_DIR, config_dir)
        path = config_dir / "codex.json"
        config = runner.load_config("codex")
        config["providers"]["deepseek"]["model"] = "deepseek-reasoner"
        path.write_text(json.dumps(config))
        with patch.object(runner, "CONFIG_DIR", config_dir):
            self.assertEqual(runner.load_config("codex")["providers"]["deepseek"]["model"], "deepseek-reasoner")
            path.write_text(json.dumps({"extends": "codex.json"}))
            with self.assertRaisesRegex(ValueError, "circular"):
                runner.load_config("codex")

    def test_adapter_payloads_use_configured_models_without_network(self):
        providers = dict(runner.load_config("headless")["providers"])
        providers.update({
            "openai": {"model": "synthetic-openai"},
            "anthropic": {"model": "synthetic-anthropic"},
            "gemini": {"model": "synthetic-gemini"},
        })
        for provider, settings in providers.items():
            if provider in ("agy", "codex", "grok"):
                continue
            with self.subTest(provider=provider):
                if provider == "gemini":
                    content = b'data: {"candidates":[{"content":{"parts":[{"text":"answer"}]}}]}\n\n'
                elif provider == "anthropic":
                    content = b'{"content":[{"type":"text","text":"answer"}]}'
                else:
                    content = b'{"choices":[{"message":{"content":"answer"}}]}'
                self.network.side_effect = None
                self.network.return_value = io.BytesIO(content)
                answer = runner.call_model(provider, "question", "synthetic-key", settings["model"],
                                           system_prompt=runner.WORKER_RULES)
                self.assertEqual(answer, "answer")
                request = self.network.call_args.args[0]
                payload = json.loads(request.data)
                if provider == "gemini":
                    self.assertIn(settings["model"], request.full_url)
                    self.assertEqual(payload["systemInstruction"], {"parts": [{"text": runner.WORKER_RULES}]})
                    self.assertEqual(payload["contents"], [{"parts": [{"text": "question"}]}])
                else:
                    self.assertEqual(payload["model"], settings["model"])
                    if provider == "anthropic":
                        self.assertEqual(payload["system"], runner.WORKER_RULES)
                        self.assertEqual(payload["messages"], [{"role": "user", "content": "question"}])
                    else:
                        self.assertEqual(payload["messages"], [
                            {"role": "system", "content": runner.WORKER_RULES},
                            {"role": "user", "content": "question"},
                        ])

    def test_agy_adapter_calls_cli_in_plan_mode_without_network(self):
        settings = runner.load_config("headless")["providers"]["agy"]
        self.assertEqual(settings["model"], "gemini-pro-orchestrator")
        self.assertEqual(settings["display_name"], "Orchestrator (Carbon)")

        def fake_run(cmd, cwd=None, env=None, text=True, capture_output=True, timeout=None):
            self.assertIn("-p", cmd)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "gemini-pro-orchestrator")
            self.assertIn("--mode", cmd)
            self.assertEqual(cmd[cmd.index("--mode") + 1], "plan")
            self.assertIn("--disable-slash-commands", cmd)
            self.assertIn("--output-format", cmd)
            self.assertEqual(cmd[cmd.index("--output-format") + 1], "json")
            self.assertTrue(cwd and Path(cwd).is_dir())
            self.assertNotIn("AUTO_WORKER", env)
            self.assertNotIn("DEEPSEEK_API_KEY", env)
            prompt_arg = cmd[cmd.index("-p") + 1]
            self.assertIn(runner.WORKER_RULES, prompt_arg)
            self.assertIn("question", prompt_arg)
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=json.dumps({"status": "SUCCESS", "response": "agy carbon answer"}) + "\n",
                stderr=""
            )

        os.environ["DEEPSEEK_API_KEY"] = "secret-must-not-leak"
        with patch.object(runner, "agy_executable", return_value="/usr/local/bin/agy"), \
                patch.object(runner.shutil, "which", return_value=None), \
                patch.object(runner.subprocess, "run", side_effect=fake_run) as mock_sub:
            answer = runner.call_model("agy", "question", "installed", settings["model"],
                                       system_prompt=runner.WORKER_RULES)
            self.assertEqual(answer, "agy carbon answer")
            mock_sub.assert_called_once()

        def fail_run(cmd, cwd=None, env=None, text=True, capture_output=True, timeout=None):
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=json.dumps({"status": "ERROR", "error": "quota reached"}) + "\n",
                stderr=""
            )

        with patch.object(runner, "agy_executable", return_value="/usr/local/bin/agy"), \
                patch.object(runner.shutil, "which", return_value=None), \
                patch.object(runner.subprocess, "run", side_effect=fail_run):
            with self.assertRaisesRegex(RuntimeError, "quota reached"):
                runner.call_model("agy", "question", "installed", settings["model"])

    def test_opencode_profile_uses_agy_orchestrator_and_skips_glm_self_vote(self):
        cfg = runner.load_config("opencode")
        self.assertEqual(cfg["mode"], "raw")
        self.assertEqual(cfg["worker_defaults"], ["agy", "deepseek", "minimax"])
        self.assertEqual(cfg["reviewer"]["provider"], "agy")
        self.assertEqual(cfg["reviewer"]["model"], "gemini-pro-orchestrator")
        self.assertEqual(cfg["agy_routes"]["l1"], "gemini-4-carbon-high")
        self.assertEqual(cfg["agy_routes"]["l3"], ["gemini-pro-orchestrator", "gemini-4-carbon-high"])

    def test_cursor_profile_uses_agy_orchestrator_and_raw_mode(self):
        cfg = runner.load_config("cursor")
        self.assertEqual(cfg["mode"], "raw")
        self.assertEqual(cfg["worker_defaults"], ["agy", "codex", "grok", "glm", "deepseek", "kimi", "minimax"])
        self.assertEqual(runner.load_config("codex")["worker_defaults"], ["agy", "grok", "glm", "deepseek", "kimi", "minimax"])
        self.assertEqual(cfg["reviewer"]["provider"], "agy")
        self.assertEqual(cfg["reviewer"]["model"], "gemini-pro-orchestrator")
        self.assertEqual(cfg["agy_routes"]["filler"], "gemini-4-argon-low")
        self.assertEqual(cfg["agy_routes"]["l1"], "gemini-4-carbon-high")
        self.assertEqual(cfg["agy_routes"]["l3"], ["gemini-pro-orchestrator", "gemini-4-carbon-high"])

    def test_codex_adapter_calls_cli_without_network(self):
        def fake_run(cmd, input=None, cwd=None, env=None, text=True, capture_output=True, timeout=None):
            self.assertTrue(cwd and Path(cwd).is_dir())
            self.assertIsNotNone(env)
            self.assertNotIn("DEEPSEEK_API_KEY", env)
            self.assertEqual(env.get("HOME"), str(self.root / "fake-home"))
            self.assertEqual(env.get("CODEX_HOME"), str(self.root / "fake-codex-home"))
            out_idx = cmd.index("-o") + 1
            out_file = cmd[out_idx]
            Path(out_file).write_text("codex answer")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        os.environ.update(
            DEEPSEEK_API_KEY="secret-must-not-leak",
            HOME=str(self.root / "fake-home"),
            CODEX_HOME=str(self.root / "fake-codex-home"),
            OPENAI_API_KEY="openai-allowed-key",
        )
        with patch.object(runner, "codex_executable", return_value="/usr/local/bin/codex"), \
                patch.object(runner.subprocess, "run", side_effect=fake_run) as mock_sub:
            answer = runner.call_model("codex", "question", "synthetic-key", "gpt-6-astra",
                                       system_prompt=runner.WORKER_RULES)
            self.assertEqual(answer, "codex answer")
            mock_sub.assert_called_once()
            cmd, kwargs = mock_sub.call_args[0][0], mock_sub.call_args[1]
            self.assertEqual(cmd[0], "/usr/local/bin/codex")
            self.assertIn("exec", cmd)
            self.assertIn("--skip-git-repo-check", cmd)
            self.assertEqual(cmd[cmd.index("-m") + 1], "gpt-6-astra")
            self.assertNotIn("-c", cmd)
            self.assertEqual(kwargs["timeout"], 120)
            self.assertEqual(kwargs["env"].get("OPENAI_API_KEY"), "openai-allowed-key")
            self.assertIn(runner.WORKER_RULES, kwargs["input"])
            self.assertIn("question", kwargs["input"])

        with patch.object(runner, "codex_executable", return_value="/Applications/ChatGPT.app/codex"), \
                patch.object(runner.subprocess, "run", side_effect=fake_run) as mock_luna:
            answer = runner.call_model("codex", "question", "installed", "gpt-6-luna-max",
                                       system_prompt=runner.WORKER_RULES)
            self.assertEqual(answer, "codex answer")
            mock_luna.assert_called_once()
            cmd_max, kwargs_max = mock_luna.call_args[0][0], mock_luna.call_args[1]
            self.assertEqual(cmd_max[0], "/Applications/ChatGPT.app/codex")
            self.assertIn("--skip-git-repo-check", cmd_max)
            self.assertEqual(cmd_max[cmd_max.index("-m") + 1], "gpt-6-luna")
            self.assertIn("-c", cmd_max)
            self.assertEqual(cmd_max[cmd_max.index("-c") + 1], 'model_reasoning_effort="max"')
            self.assertEqual(kwargs_max["timeout"], 180)


    def test_cross_review_mode_in_show_config(self):
        process = subprocess.run([sys.executable, str(runner.SKILL_DIR / "moa_runner.py"),
                                 "--cross-review", "--cycles", "2", "--show-config"],
                                 capture_output=True, text=True, env={})
        self.assertEqual(process.returncode, 0, process.stderr)
        config = json.loads(process.stdout)
        self.assertEqual(config["mode"], "cross_review")

    def test_cross_review_rejects_single_active_provider(self):
        os.environ.update(DEEPSEEK_API_KEY="test-ds")
        # only deepseek has key, minimax does not
        code, stdout, stderr, _ = self.invoke(["--models", "deepseek", "--cross-review", "question"])
        self.assertNotEqual(code, 0)
        self.assertIn("Cross-review requires at least 2 active providers", stderr)

    def test_cross_review_mock_pipeline_execution(self):
        os.environ.update(DEEPSEEK_API_KEY="test-ds", MINIMAX_API_KEY="test-minimax")

        def mock_call(provider, prompt, api_key, model, system_prompt=None, max_tokens=None):
            if "Candidate to Review" in prompt or "expert reviewer" in (system_prompt or ""):
                payload = {
                    "review_id": f"rev-{provider}", "reviewer": provider, "target_participant": "target",
                    "target_version": 1, "no_substantive_issues": True, "issues": []
                }
            elif "original author" in (system_prompt or ""):
                payload = {
                    "revision_id": f"rev-{provider}-v2", "participant": provider, "version": 2,
                    "issue_responses": [], "revised_summary": "revised", "revised_answer": "revised"
                }
            elif "Lead Synthesizer" in (system_prompt or ""):
                payload = {
                    "synthesis_id": "syn", "usable_answer": "Authoritative Synthesis",
                    "supported_points": ["Point A"], "unresolved_disagreements": [],
                    "evidence_gaps": [], "next_checks": [], "limitations": [], "stop_reason": "completed"
                }
            else:
                payload = {
                    "answer_id": f"ans-{provider}-v1", "participant": provider, "version": 1,
                    "summary": "initial summary", "claims": [{"claim_id": "c1", "statement": "st", "claim_type": "fact"}],
                    "full_answer": "initial full answer"
                }
            return json.dumps(payload)

        code, stdout, stderr, _ = self.invoke(["--models", "deepseek,minimax", "--cross-review", "question"], side_effect=mock_call)
        self.assertEqual(code, 0, stderr)
        self.assertIn("===MOA_CROSS_REVIEW_START===", stdout)
        self.assertIn("Authoritative Synthesis", stdout)
        self.assertIn("===MOA_CROSS_REVIEW_END===", stdout)
        record = self.record()
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["mode"], "cross_review")
        self.assertIn("evidence_review", record)

    def test_env_paths_order_and_load_env_first_nonempty_priority(self):
        paths = runner.env_paths()
        self.assertEqual(
            paths,
            (runner.SKILL_DIR / ".env", Path.home() / ".env", Path.home() / "Desktop" / "moa_keys.env"),
        )
        skill_env = self.root / "skill.env"
        home_env = self.root / "home.env"
        desktop_env = self.root / "desktop.env"
        skill_env.write_text("DEEPSEEK_API_KEY=from-skill\nZHIPUAI_API_KEY=your_placeholder\nMINIMAX_API_KEY=\n")
        home_env.write_text("DEEPSEEK_API_KEY=from-home\nexport ZHIPUAI_API_KEY='from-home'\nOPENAI_API_KEY=from-home-openai\n")
        desktop_env.write_text("ZHIPUAI_API_KEY=from-desktop\nMINIMAX_API_KEY=\"from-desktop\"\nOPENAI_API_KEY=from-desktop-openai\n")

        os.environ["OPENAI_API_KEY"] = "from-process-env"
        with patch.object(runner, "env_paths", return_value=(skill_env, home_env, desktop_env)), \
                patch.object(runner, "agy_executable", return_value=None), \
                patch.object(runner, "has_opencode_xai_auth", return_value=False), \
                patch.object(runner, "codex_executable", return_value=None), \
                patch.object(runner, "has_codex_auth", return_value=False):
            _REAL_LOAD_ENV()

        self.assertEqual(os.environ["OPENAI_API_KEY"], "from-process-env")
        self.assertEqual(os.environ["DEEPSEEK_API_KEY"], "from-skill")
        self.assertEqual(os.environ["ZHIPUAI_API_KEY"], "from-home")
        self.assertEqual(os.environ["MINIMAX_API_KEY"], "from-desktop")
        self.assertNotIn("CODEX_CLI", os.environ)

        with patch.object(runner, "env_paths", return_value=()), \
                patch.object(runner, "agy_executable", return_value=None), \
                patch.object(runner, "has_opencode_xai_auth", return_value=False), \
                patch.object(runner, "codex_executable", return_value="/app/codex"), \
                patch.object(runner, "has_codex_auth", return_value=False):
            _REAL_LOAD_ENV()
        self.assertNotIn("CODEX_CLI", os.environ)

        with patch.object(runner, "env_paths", return_value=()), \
                patch.object(runner, "agy_executable", return_value=None), \
                patch.object(runner, "has_opencode_xai_auth", return_value=False), \
                patch.object(runner, "codex_executable", return_value="/app/codex"), \
                patch.object(runner, "has_codex_auth", return_value=True):
            _REAL_LOAD_ENV()
        self.assertEqual(os.environ.get("CODEX_CLI"), "installed")

    def test_review_failover_when_primary_glm_fails(self):
        os.environ.update(
            ZHIPUAI_API_KEY="synthetic-glm",
            AGY_CLI="installed",
            DEEPSEEK_API_KEY="synthetic-ds",
        )

        def review_call(provider, prompt, api_key, model, system_prompt=None, max_tokens=None):
            self.assertEqual(system_prompt, runner.REVIEW_RULES)
            if provider == "glm":
                raise ValueError("insufficient balance")
            if provider == "agy":
                raise RuntimeError("quota exhausted")
            if provider == "deepseek":
                return "deepseek fallback review"
            raise AssertionError(f"Unexpected provider {provider}")

        code, stdout, stderr, call = self.invoke(["--review", "draft to check"], side_effect=review_call)
        self.assertEqual(code, 0, stderr)
        self.assertIn("===MOA_REVIEW_START===\ndeepseek fallback review\n===MOA_REVIEW_END===", stdout)
        self.assertEqual(call.call_count, 3)
        record = self.record()
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["reviewer_configuration"]["provider"], "deepseek")
        self.assertEqual(record["reviewer_configuration"]["model"], "deepseek-v4-pro")
        self.assertEqual(record["reviewer_result"]["provider"], "deepseek")
        self.assertEqual(record["reviewer_result"]["fallback_from"], "glm")
        self.assertEqual(
            [(f["provider"], f["model"]) for f in record["reviewer_fallbacks"]],
            [("glm", "glm-5.3"), ("agy", "gemini-pro-orchestrator")],
        )

    def test_review_failover_when_primary_glm_lacks_key(self):
        os.environ["MINIMAX_API_KEY"] = "synthetic-minimax"
        code, stdout, stderr, call = self.invoke(["--review", "draft to check"], result="minimax fallback review")
        self.assertEqual(code, 0, stderr)
        self.assertIn("===MOA_REVIEW_START===\nminimax fallback review\n===MOA_REVIEW_END===", stdout)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[0], "minimax")
        record = self.record()
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["reviewer_configuration"]["provider"], "minimax")
        self.assertEqual(record["reviewer_result"]["fallback_from"], "glm")

    def test_review_fails_when_no_candidate_has_key(self):
        code, stdout, stderr, call = self.invoke(["--review", "draft to check"])
        self.assertNotEqual(code, 0)
        self.assertNotIn("MOA_REVIEW_START", stdout)
        self.assertIn("Review requires a configured key for glm", stderr)
        call.assert_not_called()
        self.assertEqual(self.record()["status"], "failed")

    def test_aggregate_failover_prefers_healthy_worker_when_primary_fails_worker_stage(self):
        os.environ.update(DEEPSEEK_API_KEY="synthetic-ds", MINIMAX_API_KEY="synthetic-minimax")

        def answer(provider, prompt, api_key, model, system_prompt=None, max_tokens=None):
            if provider == "deepseek":
                raise ValueError("deepseek balance exhausted")
            if system_prompt and system_prompt.startswith("You are the Aggregator"):
                return "synthesized by healthy minimax"
            return "minimax worker answer"

        code, stdout, stderr, call = self.invoke(["question"], side_effect=answer)
        self.assertEqual(code, 0, stderr)
        self.assertIn("--- FINAL SYNTHESIZED RESPONSE ---\nsynthesized by healthy minimax", stdout)
        self.assertEqual(call.call_count, 3)
        record = self.record()
        self.assertEqual(record["status"], "partial_success")
        self.assertEqual(record["aggregation_configuration"]["provider"], "minimax")
        self.assertEqual(record["aggregation_result"]["provider"], "minimax")
        self.assertEqual(record["aggregation_result"]["fallback_from"], "deepseek")

    def test_aggregate_failover_when_first_aggregator_raises_in_aggregation_stage(self):
        os.environ.update(
            DEEPSEEK_API_KEY="synthetic-ds",
            ZHIPUAI_API_KEY="synthetic-glm",
            MINIMAX_API_KEY="synthetic-minimax",
        )

        def answer(provider, prompt, api_key, model, system_prompt=None, max_tokens=None):
            if system_prompt and system_prompt.startswith("You are the Aggregator"):
                if provider == "deepseek":
                    raise ValueError("deepseek quota hit on synthesis")
                if provider == "glm":
                    return "synthesized by glm-5.3"
                raise AssertionError(f"Should not reach {provider} after glm succeeded")
            return f"{provider} draft"

        code, stdout, stderr, call = self.invoke(["question"], side_effect=answer)
        self.assertEqual(code, 0, stderr)
        self.assertIn("--- FINAL SYNTHESIZED RESPONSE ---\nsynthesized by glm-5.3", stdout)
        self.assertEqual(call.call_count, 5)
        record = self.record()
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["aggregation_configuration"]["provider"], "glm")
        self.assertEqual(record["aggregation_configuration"]["model"], "glm-5.3")
        self.assertEqual(record["aggregation_result"]["provider"], "glm")
        self.assertEqual(record["aggregation_result"]["fallback_from"], "deepseek")
        self.assertEqual(
            record["aggregation_fallbacks"],
            [{
                "provider": "deepseek",
                "model": "deepseek-v4-pro",
                "error": "ValueError: deepseek quota hit on synthesis",
            }],
        )

    def test_cross_review_synthesizer_failover_when_primary_fails_stage4(self):
        os.environ.update(DEEPSEEK_API_KEY="test-ds", MINIMAX_API_KEY="test-minimax")

        def mock_call(provider, prompt, api_key, model, system_prompt=None, max_tokens=None):
            if "Candidate to Review" in prompt or "expert reviewer" in (system_prompt or ""):
                payload = {
                    "review_id": f"rev-{provider}", "reviewer": provider, "target_participant": "target",
                    "target_version": 1, "no_substantive_issues": True, "issues": []
                }
            elif "original author" in (system_prompt or ""):
                payload = {
                    "revision_id": f"rev-{provider}-v2", "participant": provider, "version": 2,
                    "issue_responses": [], "revised_summary": "revised", "revised_answer": "revised"
                }
            elif "Lead Synthesizer" in (system_prompt or ""):
                if provider == "deepseek":
                    raise ValueError("deepseek synthesis failed")
                payload = {
                    "synthesis_id": "syn", "usable_answer": "Fallback Synthesis by MiniMax",
                    "supported_points": ["Point A"], "unresolved_disagreements": [],
                    "evidence_gaps": [], "next_checks": [], "limitations": [], "stop_reason": "completed"
                }
            else:
                payload = {
                    "answer_id": f"ans-{provider}-v1", "participant": provider, "version": 1,
                    "summary": "initial summary", "claims": [{"claim_id": "c1", "statement": "st", "claim_type": "fact"}],
                    "full_answer": "initial full answer"
                }
            return json.dumps(payload)

        code, stdout, stderr, _ = self.invoke(["--models", "deepseek,minimax", "--cross-review", "question"], side_effect=mock_call)
        self.assertEqual(code, 0, stderr)
        self.assertIn("Fallback Synthesis by MiniMax", stdout)
        record = self.record()
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["synthesis_fallbacks"][0]["provider"], "deepseek")

    def test_has_opencode_xai_auth_reads_sqlite_readonly(self):
        xdg_data = self.root / "xdg_data"
        db_dir = xdg_data / "opencode"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "opencode.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE credential (id TEXT, integration_id TEXT, active INTEGER, value TEXT)")
        conn.execute("INSERT INTO credential VALUES ('c1', 'xai', 0, ?)", ('{"type":"oauth"}',))
        conn.commit()
        conn.close()

        os.environ["XDG_DATA_HOME"] = str(xdg_data)
        with patch.object(runner, "opencode_executable", return_value="/usr/local/bin/opencode"):
            self.assertFalse(_REAL_HAS_OPENCODE_XAI_AUTH())
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE credential SET active = 1 WHERE id = 'c1'")
            conn.commit()
            self.assertTrue(_REAL_HAS_OPENCODE_XAI_AUTH())
            conn.execute("INSERT INTO credential VALUES ('c2', 'xai', 1, ?)", ('{"type":"key"}',))
            conn.commit()
            self.assertFalse(_REAL_HAS_OPENCODE_XAI_AUTH())
            conn.execute("UPDATE credential SET active = 0 WHERE id = 'c1'")
            conn.commit()
            conn.close()
            self.assertFalse(_REAL_HAS_OPENCODE_XAI_AUTH())

        with patch.object(runner, "opencode_executable", return_value=None):
            self.assertFalse(_REAL_HAS_OPENCODE_XAI_AUTH())

    def test_grok_opencode_oauth_adapter_ignores_api_keys(self):
        settings = runner.load_config("headless")["providers"]["grok"]
        self.assertEqual(settings["model"], "grok-4.7")
        self.assertEqual(settings["display_name"], "Grok-4.7")
        self.grok_oauth.return_value = True

        def fake_run(cmd, cwd=None, env=None, text=True, capture_output=True, timeout=None):
            self.assertEqual(cmd[:8], ["/usr/local/bin/opencode", "run", "--standalone", "--archived",
                                      "--agent", "plan", "--format", "json"])
            self.assertEqual(cmd[cmd.index("-m") + 1], "xai/grok-4.7")
            self.assertIn("--", cmd)
            prompt_arg = cmd[-1]
            self.assertIn(runner.WORKER_RULES, prompt_arg)
            self.assertIn("question", prompt_arg)
            self.assertTrue(cwd and Path(cwd).is_dir())
            self.assertNotIn("DEEPSEEK_API_KEY", env)
            self.assertNotIn("XAI_API_KEY", env)
            self.assertNotIn("GROK_API_KEY", env)
            events = [
                json.dumps({"type": "step_start"}),
                json.dumps({"type": "text", "part": {"type": "text", "text": "grok subscription answer"}}),
                json.dumps({"type": "step_finish", "part": {"reason": "stop"}}),
            ]
            return subprocess.CompletedProcess(cmd, 0, stdout="\n".join(events) + "\n", stderr="")

        os.environ.update(DEEPSEEK_API_KEY="synthetic-ds", XAI_API_KEY="synthetic-xai", GROK_API_KEY="synthetic-grok")
        with patch.object(runner, "opencode_executable", return_value="/usr/local/bin/opencode"), \
                patch.object(runner.subprocess, "run", side_effect=fake_run) as mock_sub:
            answer = runner.call_model("grok", "question", "opencode-oauth", settings["model"],
                                       system_prompt=runner.WORKER_RULES)
            self.assertEqual(answer, "grok subscription answer")
            mock_sub.assert_called_once()
            self.network.assert_not_called()

    def test_grok_oauth_failure_never_falls_back_to_http(self):
        self.grok_oauth.return_value = True
        os.environ.update(XAI_API_KEY="synthetic-xai", GROK_API_KEY="synthetic-grok")
        fail_proc = subprocess.CompletedProcess(["opencode"], 1, stdout="", stderr="oauth expired")
        with patch.object(runner, "opencode_executable", return_value="/usr/local/bin/opencode"), \
                patch.object(runner.subprocess, "run", return_value=fail_proc) as mock_sub:
            with self.assertRaisesRegex(RuntimeError, "oauth expired"):
                runner.call_model("grok", "question", runner.GROK_OAUTH, "xai/grok-4.7")
        mock_sub.assert_called_once()
        self.network.assert_not_called()

    def test_grok_without_oauth_rejects_api_keys_and_unverified_marker(self):
        os.environ.update(XAI_API_KEY="synthetic-xai", GROK_API_KEY="synthetic-grok",
                          OPENCODE_XAI_AUTH=runner.GROK_OAUTH, ZHIPUAI_API_KEY="synthetic-glm")
        for mode in ("--raw", "--review"):
            with self.subTest(mode=mode):
                code, _, stderr, call = self.invoke([mode, "--models", "grok", "question"])
                self.assertNotEqual(code, 0)
                self.assertIn(runner.GROK_LOGIN_REQUIRED, stderr)
                call.assert_not_called()
        with self.assertRaisesRegex(ValueError, "OpenCode xAI OAuth"):
            runner.call_model("grok", "question", "synthetic-xai", "grok-4.7")
        with self.assertRaisesRegex(RuntimeError, "OpenCode xAI OAuth"):
            runner.call_model("grok", "question", runner.GROK_OAUTH, "grok-4.7")
        self.network.assert_not_called()

    def test_explicit_grok_review_does_not_switch_to_another_provider(self):
        self.grok_oauth.return_value = True
        os.environ["ZHIPUAI_API_KEY"] = "synthetic-glm"
        code, _, stderr, call = self.invoke(["--review", "--models", "grok", "draft"],
                                            side_effect=RuntimeError("OAuth expired"))
        self.assertNotEqual(code, 0)
        self.assertIn("OAuth expired", stderr)
        call.assert_called_once()
        self.assertEqual(call.call_args.args[0], "grok")
        self.assertEqual(self.record()["reviewer_result"]["executor"], "opencode")

    def test_explicit_timeout_overrides_grok_cli_minimum(self):
        self.grok_oauth.return_value = True
        events = [
            json.dumps({"type": "text", "part": {"type": "text", "text": "PONG"}}),
        ]
        proc = subprocess.CompletedProcess(["opencode"], 0, stdout="\n".join(events) + "\n", stderr="")
        with patch.object(runner, "opencode_executable", return_value="/usr/local/bin/opencode"), \
                patch.object(runner.subprocess, "run", return_value=proc) as mock_sub:
            answer = runner.call_model("grok", "Ping", "opencode-oauth", "grok-4.7", max_tokens=128, timeout=25)
            self.assertEqual(answer, "PONG")
            self.assertEqual(mock_sub.call_args.kwargs["timeout"], 35)

    def test_doctor_command_probes_providers_and_reports_table(self):
        self.grok_oauth.return_value = True
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-key"
        recorded = {}

        def probe(provider, prompt, api_key, model, system_prompt=None, max_tokens=None, timeout=None):
            recorded[provider] = (api_key, model, max_tokens, timeout)
            return "PONG"

        code, stdout, stderr, _ = self.invoke(["--models", "grok,deepseek", "--doctor"], side_effect=probe)
        self.assertEqual(code, 0, stderr)
        self.assertIn("MoA Provider Health & Latency Check", stdout)
        self.assertIn("OAuth CLI", stdout)
        self.assertIn("API", stdout)
        self.assertIn("✅ OK", stdout)
        self.assertIn("Summary: 2/2 providers healthy.", stdout)
        self.assertEqual(recorded["grok"], ("opencode-oauth", "grok-4.7", 128, 35))
        self.assertEqual(recorded["deepseek"], ("synthetic-key", "deepseek-v4-pro", 128, 20))
        self.assertFalse(runner.RUNS_DIR.exists())

    def test_doctor_command_reports_no_auth_when_keys_missing(self):
        code, stdout, stderr, call = self.invoke(["--doctor", "--models", "deepseek"])
        self.assertEqual(code, 1, stderr)
        self.assertIn("⚠️ No Auth", stdout)
        self.assertIn("Summary: 0/1 providers healthy.", stdout)
        call.assert_not_called()

    def test_doctor_command_handles_provider_errors(self):
        os.environ["DEEPSEEK_API_KEY"] = "synthetic-secret"
        code, stdout, stderr, _ = self.invoke(
            ["--doctor", "--models", "deepseek"],
            side_effect=RuntimeError("synthetic-secret refused"),
        )
        self.assertEqual(code, 1, stderr)
        self.assertIn("❌ Error", stdout)
        self.assertIn("[REDACTED]", stdout)
        self.assertNotIn("synthetic-secret", stdout)
        self.assertIn("Summary: 0/1 providers healthy.", stdout)

    def test_codex_executable_priority_and_has_codex_auth(self):
        fake_home = self.root / "codex_home_root"
        fake_home.mkdir()
        app_codex = self.root / "ChatGPT.app" / "codex"
        app_codex.parent.mkdir(parents=True)
        app_codex.write_text("#!/bin/sh\n")
        app_codex.chmod(0o755)

        brew_file = self.root / "brew_codex_target"
        brew_file.write_text("#!/bin/sh\n")
        brew_file.chmod(0o755)

        custom_shim = self.root / "custom_shim_dir" / "codex"
        custom_shim.parent.mkdir(parents=True)
        custom_shim.write_text("#!/bin/sh\n")
        custom_shim.chmod(0o755)

        override_bin = self.root / "override_codex"
        override_bin.write_text("#!/bin/sh\n")
        override_bin.chmod(0o755)

        non_exec = self.root / "non_exec_codex"
        non_exec.write_text("not executable\n")
        non_exec.chmod(0o644)

        real_realpath = os.path.realpath

        def fake_realpath(p):
            if p == "/opt/homebrew/bin/codex":
                return str(brew_file)
            return real_realpath(p)

        with patch.object(runner.subprocess, "run", side_effect=AssertionError("subprocess forbidden")), \
                patch.object(runner.Path, "home", return_value=fake_home), \
                patch.object(runner, "CHATGPT_APP_CODEX_CANDIDATES", (str(app_codex),)), \
                patch.object(runner.os.path, "realpath", side_effect=fake_realpath):
            # 1. Newer ChatGPT.app binary beats /opt/homebrew/bin/codex
            os.utime(brew_file, (1000, 1000))
            os.utime(app_codex, (2000, 2000))
            with patch.object(runner.shutil, "which", return_value="/opt/homebrew/bin/codex"):
                self.assertEqual(runner.codex_executable(), str(app_codex))

            # Older ChatGPT.app binary loses to newer /opt/homebrew/bin/codex
            os.utime(brew_file, (3000, 3000))
            with patch.object(runner.shutil, "which", return_value="/opt/homebrew/bin/codex"):
                self.assertEqual(runner.codex_executable(), "/opt/homebrew/bin/codex")

            # 2. Non-system PATH shim (including relative path) beats newer ChatGPT.app binary and returns abs path
            os.utime(app_codex, (5000, 5000))
            os.utime(custom_shim, (1000, 1000))
            rel_shim = os.path.relpath(custom_shim, os.getcwd())
            with patch.object(runner.shutil, "which", return_value=rel_shim):
                resolved_shim = runner.codex_executable()
                self.assertTrue(os.path.isabs(resolved_shim))
                self.assertEqual(resolved_shim, os.path.abspath(str(custom_shim)))

            # 3. CODEX_BIN override (including relative path) wins as an absolute path; non-executable is ignored
            rel_override = os.path.relpath(override_bin, os.getcwd())
            self.assertFalse(os.path.isabs(rel_override))
            os.environ["CODEX_BIN"] = rel_override
            with patch.object(runner.shutil, "which", return_value=str(custom_shim)):
                resolved_override = runner.codex_executable()
                self.assertTrue(os.path.isabs(resolved_override))
                self.assertEqual(resolved_override, os.path.abspath(str(override_bin)))
            os.environ["CODEX_BIN"] = str(non_exec)
            with patch.object(runner.shutil, "which", return_value=str(custom_shim)):
                self.assertEqual(runner.codex_executable(), os.path.abspath(str(custom_shim)))
            os.environ.pop("CODEX_BIN", None)

            # 4. Dynamic ~/Applications/... expansion and fallback to ~/.local/bin/codex
            user_app_codex = fake_home / "Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
            user_app_codex.parent.mkdir(parents=True)
            user_app_codex.write_text("#!/bin/sh\n")
            user_app_codex.chmod(0o755)
            with patch.object(runner, "CHATGPT_APP_CODEX_CANDIDATES",
                              ("~/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",)), \
                    patch.object(runner.shutil, "which", return_value=None):
                self.assertEqual(runner.codex_executable(), os.path.abspath(str(user_app_codex)))

            with patch.object(runner, "CHATGPT_APP_CODEX_CANDIDATES", ()), \
                    patch.object(runner.shutil, "which", return_value=None):
                self.assertIsNone(runner.codex_executable())
                local_codex = fake_home / ".local" / "bin" / "codex"
                local_codex.parent.mkdir(parents=True)
                local_codex.write_text("#!/bin/sh\n")
                local_codex.chmod(0o755)
                self.assertEqual(runner.codex_executable(), os.path.abspath(str(local_codex)))

            # 5. has_codex_auth checks env vars, $CODEX_HOME/auth.json, and ~/.codex/auth.json
            self.assertFalse(runner.has_codex_auth())
            os.environ["CODEX_AUTH"] = "1"
            self.assertTrue(runner.has_codex_auth())
            os.environ.pop("CODEX_AUTH")
            os.environ["OPENAI_API_KEY"] = "sk-test"
            self.assertTrue(runner.has_codex_auth())
            os.environ.pop("OPENAI_API_KEY")

            custom_codex_home = self.root / "custom_codex_home"
            custom_codex_home.mkdir()
            (custom_codex_home / "auth.json").write_text('{"tokens": {}}')
            os.environ["CODEX_HOME"] = str(custom_codex_home)
            self.assertFalse((fake_home / ".codex" / "auth.json").exists())
            self.assertTrue(runner.has_codex_auth())
            os.environ.pop("CODEX_HOME")
            self.assertFalse(runner.has_codex_auth())

            auth_file = fake_home / ".codex" / "auth.json"
            auth_file.parent.mkdir(parents=True)
            auth_file.write_text('{"tokens": {}}')
            self.assertTrue(runner.has_codex_auth())

    def test_codex_inline_effort_selectors_in_show_config_raw_and_doctor(self):
        self.assertEqual(runner.parse_codex_model_spec(None), ("gpt-6-luna", "high"))
        self.assertEqual(runner.parse_codex_model_spec(""), ("gpt-6-luna", "high"))
        self.assertEqual(runner.parse_codex_model_spec("codex-max"), ("gpt-6-luna", "max"))
        self.assertEqual(runner.parse_codex_model_spec("gpt-6-luna-max"), ("gpt-6-luna", "max"))
        self.assertEqual(runner.parse_codex_model_spec("GPT-6-Luna (XHigh)"), ("gpt-6-luna", "xhigh"))
        self.assertEqual(runner.parse_codex_model_spec("gpt-6-luna"), ("gpt-6-luna", None))
        self.assertEqual(runner.parse_codex_model_spec("gpt-6-astra-high"), ("gpt-6-astra", "high"))
        self.assertEqual(runner.parse_codex_model_spec("gpt-6-astra"), ("gpt-6-astra", None))
        self.assertEqual(runner.parse_codex_model_spec("gpt-oss-120b-medium"), ("gpt-oss-120b-medium", None))

        for selector in ("codex-max", "gpt-6-luna-max", "codex,codex-max"):
            with self.subTest(selector=selector, mode="show_config"):
                code, stdout, stderr, call = self.invoke(["--models", selector, "--show-config"])
                self.assertEqual(code, 0, stderr)
                cfg = json.loads(stdout)
                self.assertEqual(
                    cfg["selected_workers"],
                    [{"provider": "codex", "model": "gpt-6-luna-max", "display_name": "GPT-6-Luna (Max)"}],
                )
                self.assertEqual(
                    cfg["providers"]["codex"],
                    {"model": "gpt-6-luna-max", "display_name": "GPT-6-Luna (Max)"},
                )
                call.assert_not_called()

        os.environ["CODEX_CLI"] = "installed"
        for selector in ("codex-max", "gpt-6-luna-max"):
            with self.subTest(selector=selector, mode="raw"):
                for old_rec in runner.RUNS_DIR.glob("*.json"):
                    old_rec.unlink()
                seen_cmds = []

                def fake_codex_exec(cmd, input=None, cwd=None, env=None, text=True, capture_output=True, timeout=None):
                    seen_cmds.append((cmd, timeout))
                    Path(cmd[cmd.index("-o") + 1]).write_text("luna max answer")
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

                stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
                with patch.object(runner, "codex_executable", return_value="/Applications/ChatGPT.app/codex"), \
                        patch.object(runner.subprocess, "run", side_effect=fake_codex_exec), \
                        redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    code = runner.main(["--models", selector, "--raw", "question"])
                self.assertEqual(code, 0, stderr_buf.getvalue())
                self.assertEqual(self.raw_response(stdout_buf.getvalue()), {"GPT-6-Luna (Max)": "luna max answer"})
                self.assertEqual(len(seen_cmds), 1)
                cmd, used_timeout = seen_cmds[0]
                self.assertEqual(cmd[cmd.index("-m") + 1], "gpt-6-luna")
                self.assertIn("-c", cmd)
                self.assertEqual(cmd[cmd.index("-c") + 1], 'model_reasoning_effort="max"')
                self.assertEqual(used_timeout, 180)
                rec = self.record()
                self.assertEqual(
                    rec["worker_configuration"],
                    [{"provider": "codex", "model": "gpt-6-luna-max", "display_name": "GPT-6-Luna (Max)"}],
                )

        for selector in ("codex-max", "gpt-6-luna-max"):
            with self.subTest(selector=selector, mode="doctor"):
                recorded = {}

                def probe(provider, prompt, api_key, model, system_prompt=None, max_tokens=None, timeout=None):
                    recorded[provider] = (api_key, model, max_tokens, timeout)
                    return "PONG"

                code, stdout, stderr, _ = self.invoke(["--models", selector, "--doctor"], side_effect=probe)
                self.assertEqual(code, 0, stderr)
                self.assertIn("gpt-6-luna-max", stdout)
                self.assertIn("Local CLI", stdout)
                self.assertEqual(recorded["codex"], ("installed", "gpt-6-luna-max", 128, 120))

        recorded_std = {}
        code, stdout, stderr, _ = self.invoke(
            ["--models", "codex", "--doctor"],
            side_effect=lambda p, pr, k, m, system_prompt=None, max_tokens=None, timeout=None: (
                recorded_std.setdefault(p, (k, m, max_tokens, timeout)) and "PONG"
            ),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(recorded_std["codex"], ("installed", "gpt-6-luna-high", 128, 35))

    def test_deepseek_v4_1_flash_and_effort_selectors(self):
        self.assertEqual(
            runner.parse_deepseek_model_spec("deepseek-v4.1"),
            ("deepseek-flash", "deepseek-flash", None, "deepseek-flash", "DeepSeek-V4.1-Flash"),
        )
        self.assertEqual(
            runner.parse_deepseek_model_spec("deepseek-flash"),
            ("deepseek-flash", "deepseek-flash", None, "deepseek-flash", "DeepSeek-V4.1-Flash"),
        )
        self.assertEqual(
            runner.parse_deepseek_model_spec("deepseek-v4.1-max"),
            ("deepseek-flash", "deepseek-flash", "max", "deepseek-flash-max", "DeepSeek-V4.1-Flash (Max)"),
        )
        self.assertEqual(
            runner.parse_deepseek_model_spec("deepseek-max"),
            ("deepseek", "deepseek-v4-pro", "max", "deepseek-v4-pro-max", "DeepSeek-V4-Pro (Max)"),
        )
        self.assertEqual(
            runner.parse_deepseek_model_spec("deepseek-v4-pro"),
            ("deepseek", "deepseek-v4-pro", None, "deepseek-v4-pro", "DeepSeek-V4-Pro"),
        )

        code, stdout, stderr, call = self.invoke(["--models", "deepseek-v4.1", "--show-config"])
        self.assertEqual(code, 0, stderr)
        cfg = json.loads(stdout)
        self.assertEqual(
            cfg["selected_workers"],
            [{"provider": "deepseek-flash", "model": "deepseek-flash", "display_name": "DeepSeek-V4.1-Flash"}],
        )
        call.assert_not_called()

        code, stdout, stderr, call = self.invoke(["--models", "deepseek,deepseek-v4.1", "--show-config"])
        self.assertEqual(code, 0, stderr)
        cfg_both = json.loads(stdout)
        self.assertEqual(
            cfg_both["selected_workers"],
            [
                {"provider": "deepseek", "model": "deepseek-v4-pro", "display_name": "DeepSeek-V4-Pro"},
                {"provider": "deepseek-flash", "model": "deepseek-flash", "display_name": "DeepSeek-V4.1-Flash"},
            ],
        )
        call.assert_not_called()

        seen_payloads = []

        class _FakeHTTPResp:
            def __init__(self, content_str):
                self._raw = json.dumps({"choices": [{"message": {"content": content_str}}]}).encode("utf-8")

            def read(self):
                return self._raw

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(req, timeout=None):
            seen_payloads.append(json.loads(req.data.decode("utf-8")))
            return _FakeHTTPResp("PONG")

        with patch.object(runner.urllib.request, "urlopen", side_effect=fake_urlopen):
            res_max = runner.call_model("deepseek", "Ping", "ds-key", "deepseek-v4-pro-max")
            res_flash = runner.call_model("deepseek-flash", "Ping", "ds-key", "deepseek-flash")
        self.assertEqual(res_max, "PONG")
        self.assertEqual(res_flash, "PONG")
        self.assertEqual(seen_payloads[0]["model"], "deepseek-v4-pro")
        self.assertEqual(seen_payloads[0]["reasoning_effort"], "max")
        self.assertEqual(seen_payloads[1]["model"], "deepseek-flash")
        self.assertNotIn("reasoning_effort", seen_payloads[1])

        os.environ["DEEPSEEK_API_KEY"] = "synthetic-ds-key"
        recorded_doc = {}
        code, stdout, stderr, _ = self.invoke(
            ["--models", "deepseek-max,deepseek-v4.1", "--doctor"],
            side_effect=lambda p, pr, k, m, system_prompt=None, max_tokens=None, timeout=None: (
                recorded_doc.setdefault(p, (k, m, max_tokens, timeout)) and "PONG"
            ),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(recorded_doc["deepseek"], ("synthetic-ds-key", "deepseek-v4-pro-max", 128, 60))
        self.assertEqual(recorded_doc["deepseek-flash"], ("synthetic-ds-key", "deepseek-flash", 128, 20))

    def test_kimi_k3_1_pro_highspeed_and_effort_selectors(self):
        self.assertEqual(
            runner.parse_kimi_model_spec("kimi"),
            ("kimi", "kimi-k3.1-pro", None, "kimi-k3.1-pro", "Kimi-K3.1-Pro"),
        )
        self.assertEqual(
            runner.parse_kimi_model_spec("moonshot"),
            ("kimi", "kimi-k3.1-pro", None, "kimi-k3.1-pro", "Kimi-K3.1-Pro"),
        )
        self.assertEqual(
            runner.parse_kimi_model_spec("kimi-highspeed"),
            ("kimi", "kimi-k3.1-pro-highspeed", None, "kimi-k3.1-pro-highspeed", "Kimi-K3.1-Pro-Highspeed"),
        )
        self.assertEqual(
            runner.parse_kimi_model_spec("kimi-max"),
            ("kimi", "kimi-k3.1-pro", "max", "kimi-k3.1-pro-max", "Kimi-K3.1-Pro (Max)"),
        )
        self.assertEqual(
            runner.parse_kimi_model_spec("kimi-highspeed-low"),
            ("kimi", "kimi-k3.1-pro-highspeed", "low", "kimi-k3.1-pro-highspeed-low", "Kimi-K3.1-Pro-Highspeed (Low)"),
        )

        code, stdout, stderr, call = self.invoke(["--models", "kimi-highspeed", "--show-config"])
        self.assertEqual(code, 0, stderr)
        cfg = json.loads(stdout)
        self.assertEqual(
            cfg["selected_workers"],
            [{"provider": "kimi", "model": "kimi-k3.1-pro-highspeed", "display_name": "Kimi-K3.1-Pro-Highspeed"}],
        )
        call.assert_not_called()

        code, stdout, stderr, call = self.invoke(["--models", "kimi,deepseek-v4.1", "--show-config"])
        self.assertEqual(code, 0, stderr)
        cfg_both = json.loads(stdout)
        self.assertEqual(
            cfg_both["selected_workers"],
            [
                {"provider": "kimi", "model": "kimi-k3.1-pro", "display_name": "Kimi-K3.1-Pro"},
                {"provider": "deepseek-flash", "model": "deepseek-flash", "display_name": "DeepSeek-V4.1-Flash"},
            ],
        )
        call.assert_not_called()

        seen_requests = []

        class _FakeHTTPResp:
            def __init__(self, content_str):
                self._raw = json.dumps({"choices": [{"message": {"content": content_str}}]}).encode("utf-8")

            def read(self):
                return self._raw

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(req, timeout=None):
            seen_requests.append((req.full_url, json.loads(req.data.decode("utf-8"))))
            return _FakeHTTPResp("PONG")

        with patch.object(runner.urllib.request, "urlopen", side_effect=fake_urlopen):
            res_max = runner.call_model("kimi", "Ping", "kimi-key", "kimi-k3.1-pro-max")
            with patch.dict(os.environ, {"MOONSHOT_API_BASE": "https://api.moonshot.ai/v1"}):
                res_hs = runner.call_model("kimi", "Ping", "kimi-key", "kimi-k3.1-pro-highspeed")
        self.assertEqual(res_max, "PONG")
        self.assertEqual(res_hs, "PONG")
        self.assertEqual(seen_requests[0][0], "https://api.moonshot.cn/v1/chat/completions")
        self.assertEqual(seen_requests[0][1]["model"], "kimi-k3.1-pro")
        self.assertEqual(seen_requests[0][1]["reasoning_effort"], "max")
        self.assertEqual(seen_requests[1][0], "https://api.moonshot.ai/v1/chat/completions")
        self.assertEqual(seen_requests[1][1]["model"], "kimi-k3.1-pro-highspeed")
        self.assertNotIn("reasoning_effort", seen_requests[1][1])

        os.environ["MOONSHOT_API_KEY"] = "synthetic-kimi-key"
        recorded_doc = {}
        code, stdout, stderr, _ = self.invoke(
            ["--models", "kimi-max", "--doctor"],
            side_effect=lambda p, pr, k, m, system_prompt=None, max_tokens=None, timeout=None: (
                recorded_doc.setdefault(p, (k, m, max_tokens, timeout)) and "PONG"
            ),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(recorded_doc["kimi"], ("synthetic-kimi-key", "kimi-k3.1-pro-max", 128, 60))

        recorded_hs = {}
        code, stdout, stderr, _ = self.invoke(
            ["--models", "kimi-highspeed", "--doctor"],
            side_effect=lambda p, pr, k, m, system_prompt=None, max_tokens=None, timeout=None: (
                recorded_hs.setdefault(p, (k, m, max_tokens, timeout)) and "PONG"
            ),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(recorded_hs["kimi"], ("synthetic-kimi-key", "kimi-k3.1-pro-highspeed", 128, 20))


if __name__ == "__main__":
    unittest.main(verbosity=2)
