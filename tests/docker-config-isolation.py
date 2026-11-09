"""Exercise the workflow's real setup shell and Docker's real logout command.

Only synthetic credentials in temporary files are used; no daemon or AWS access.
"""
import base64
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(os.environ.get("BUILD_WORKFLOW", Path(__file__).resolve().parents[1]
                               / ".github/workflows/docker-build-push.yml"))
SOURCE = WORKFLOW.read_text()
STEP = "Isolate job Docker configuration"
REGISTRY = "000000000000.dkr.ecr.us-west-2.amazonaws.com"
AUTH = base64.b64encode(b"synthetic-user:synthetic-password").decode()


def setup_shell():
    steps = re.split(r"(?m)^      - name: ", SOURCE)
    match = next((s for s in steps if s.startswith(STEP + "\n")), None)
    if match is None:
        return ""  # Old workflow leaves Docker using the shared HOME config.
    return textwrap.dedent(match.split("        run: |\n", 1)[1])


class DockerConfigIsolation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="docker workflow ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "shared home"
        self.home.mkdir()

    def job(self, name, *, inherited=None, invalid_temp=False):
        runner_temp = self.root / name
        if not invalid_temp:
            runner_temp.mkdir(exist_ok=True)
        environment_file = self.root / (name + ".env")
        environment_file.touch()
        env = {"PATH": os.environ["PATH"], "HOME": str(self.home),
               "RUNNER_TEMP": str(runner_temp), "GITHUB_ENV": str(environment_file)}
        if inherited:
            env["DOCKER_CONFIG"] = str(inherited)
        result = subprocess.run(["bash", "-c", setup_shell()], env=env,
                                capture_output=True, text=True)
        for line in environment_file.read_text().splitlines():
            key, value = line.split("=", 1)
            env[key] = value
        return result, env, environment_file

    def credentials(self, env):
        directory = Path(env.get("DOCKER_CONFIG", self.home / ".docker"))
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "config.json"
        path.write_text(json.dumps({"auths": {REGISTRY: {"auth": AUTH}}}))
        return path

    def test_overlapping_logout_keeps_other_job_authenticated(self):
        self.assertIsNotNone(shutil.which("docker"), "Docker CLI is required")
        first, a, _ = self.job("runner one")
        second, b, _ = self.job("runner two")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        a_file, b_file = self.credentials(a), self.credentials(b)
        # Same operation performed by amazon-ecr-login's post-job cleanup.
        logout = subprocess.run(["docker", "logout", REGISTRY], env=b,
                                capture_output=True, text=True)
        self.assertEqual(logout.returncode, 0, logout.stderr)
        self.assertNotIn(REGISTRY, json.loads(b_file.read_text()).get("auths", {}))
        self.assertEqual(json.loads(a_file.read_text())["auths"].get(REGISTRY),
                         {"auth": AUTH}, "another job removed the first job's login")

    def test_paths_are_private_unique_and_do_not_reuse_inherited_config(self):
        inherited = self.home / "existing docker config"
        inherited.mkdir()
        sentinel = inherited / "keep"
        sentinel.write_text("existing runner configuration")
        first, a, _ = self.job("same runner", inherited=inherited)
        second, b, _ = self.job("same runner", inherited=inherited)
        self.assertEqual((first.returncode, second.returncode), (0, 0))
        self.assertNotEqual(a.get("DOCKER_CONFIG"), b.get("DOCKER_CONFIG"))
        for env in (a, b):
            path = Path(env["DOCKER_CONFIG"])
            self.assertEqual(path.parent, self.root / "same runner")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
        self.assertEqual(sentinel.read_text(), "existing runner configuration")

    def test_unavailable_temp_directory_fails_before_export(self):
        result, _, output = self.job("missing runner temp", invalid_temp=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), "")

    def test_setup_precedes_login_buildx_and_push(self):
        self.assertIn("      - name: " + STEP, SOURCE)
        position = SOURCE.index("      - name: " + STEP)
        for step in ("Login to Amazon ECR", "Set up Docker Buildx",
                     "Build and push image to Amazon ECR"):
            self.assertLess(position, SOURCE.index("      - name: " + step))
        self.assertNotIn("skip-logout: true", SOURCE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
