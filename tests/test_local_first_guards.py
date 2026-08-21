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

    def test_shared_runtime_dependencies_are_not_downgraded(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotRegex(requirements, r"sqlalchemy[^\n]*<\s*2(?:\.0)?(?:\D|$)")
        self.assertNotRegex(requirements, r"urllib3[^\n]*<\s*2(?:\.0)?(?:\D|$)")

    def test_agent_tracing_is_disabled(self):
        agent_sources = [
            ROOT / "backend" / "agent_factory.py",
            ROOT / "backend" / "service" / "mcp_client.py",
        ]
        for path in agent_sources:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("set_tracing_disabled(False)", source, path.as_posix())
            self.assertIn("set_tracing_disabled(True)", source, path.as_posix())

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


if __name__ == "__main__":
    unittest.main()
