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


if __name__ == "__main__":
    unittest.main()
