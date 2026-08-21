import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LocalFirstGuardTests(unittest.TestCase):
    def test_retired_remote_services_are_not_hard_coded(self):
        backend = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "backend").rglob("*.py")
        )
        self.assertNotIn("comfyui-copilot-server.onrender.com", backend)
        self.assertNotIn("mcp.api-inference.modelscope.net", backend)

        frontend = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "ui" / "src").rglob("*.ts*")
        )
        self.assertNotIn("localhost:8000", frontend)
        self.assertNotIn("/api/chat/track_event", frontend)

        config_source = (ROOT / "ui" / "src" / "config.ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("const defaultApiBaseUrl = ''", config_source)

    def test_shared_runtime_dependencies_are_not_downgraded(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotRegex(requirements, r"sqlalchemy[^\n]*<\s*2(?:\.0)?(?:\D|$)")
        self.assertNotRegex(requirements, r"urllib3[^\n]*<\s*2(?:\.0)?(?:\D|$)")
        self.assertRegex(requirements, r"(?m)^socksio(?:[<>=].*)?$")

    def test_agent_tracing_is_disabled(self):
        package_init = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn(
            'os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")',
            package_init,
        )

        backend = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "backend").rglob("*.py")
        )
        self.assertNotIn("set_tracing_disabled(", backend)

    def test_checkpoint_access_requires_session_scope(self):
        dao_path = ROOT / "backend" / "dao" / "workflow_table.py"
        dao_source = dao_path.read_text(encoding="utf-8")
        tree = ast.parse(dao_source)
        required = {
            "get_workflow_version_by_id",
            "update_workflow_version",
            "update_workflow_ui",
            "get_workflow_data_by_id",
            "update_workflow_ui_by_id",
        }
        functions = {
            node.name: {arg.arg for arg in node.args.args}
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in required:
            self.assertIn("session_id", functions[name], name)

        self.assertGreaterEqual(
            dao_source.count("WorkflowVersion.session_id == session_id"),
            3,
        )

        controller = (
            ROOT / "backend" / "controller" / "conversation_api.py"
        ).read_text(encoding="utf-8")
        frontend_api = (
            ROOT / "ui" / "src" / "apis" / "workflowChatApi.ts"
        ).read_text(encoding="utf-8")
        self.assertIn("get_workflow_data_by_id(version_id, session_id)", controller)
        self.assertIn("session_id: sessionId", frontend_api)

    def test_api_keys_are_not_logged(self):
        auth_source = (ROOT / "backend" / "utils" / "auth_utils.py").read_text(
            encoding="utf-8"
        )
        controller = (
            ROOT / "backend" / "controller" / "conversation_api.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("api_key[:", auth_source)
        self.assertNotIn('log.info(f"config: {config}")', controller)
        self.assertNotIn('log.info(f"Debug agent config: {config}")', controller)
        self.assertGreaterEqual(controller.count("redact_sensitive_config(config)"), 2)
        self.assertNotIn('"model": "gemini-2.5-flash"', controller)

        mcp_source = (
            ROOT / "backend" / "service" / "mcp_client.py"
        ).read_text(encoding="utf-8")
        rewrite_source = (
            ROOT / "backend" / "service" / "workflow_rewrite_tools.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("messages: {messages}", mcp_source)
        self.assertNotIn("workflow_data: {workflow_data}", rewrite_source)

    def test_workflow_mutations_require_request_approval(self):
        context_source = (
            ROOT / "backend" / "utils" / "request_context.py"
        ).read_text(encoding="utf-8")
        controller = (
            ROOT / "backend" / "controller" / "conversation_api.py"
        ).read_text(encoding="utf-8")
        frontend = (
            ROOT / "ui" / "src" / "apis" / "workflowChatApi.ts"
        ).read_text(encoding="utf-8")

        self.assertIn("def require_mutation_approval", context_source)
        self.assertIn("X-Copilot-Mutation-Approval", controller)
        self.assertIn("X-Copilot-Mutation-Approval", frontend)

        guarded_actions = {
            ROOT / "backend" / "service" / "workflow_rewrite_tools.py": [
                "update_workflow",
                "remove_node",
            ],
            ROOT / "backend" / "service" / "link_agent_tools.py": [
                "apply_connection_fixes",
            ],
            ROOT / "backend" / "service" / "parameter_tools.py": [
                "update_workflow_parameter",
            ],
            ROOT / "backend" / "service" / "debug_agent.py": [
                "run_workflow",
            ],
        }
        for path, actions in guarded_actions.items():
            source = path.read_text(encoding="utf-8")
            for action in actions:
                self.assertIn(
                    f'require_mutation_approval("{action}")',
                    source,
                    f"{path.name}:{action}",
                )


if __name__ == "__main__":
    unittest.main()
