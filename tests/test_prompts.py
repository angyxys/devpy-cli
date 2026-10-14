from devpy.agent.prompts import build_system_prompt


class TestBuildSystemPrompt:
    def test_local_mode(self):
        prompt = build_system_prompt("local")
        assert "DevPy" in prompt
        assert "local" in prompt.lower()
        assert "DRY-RUN" not in prompt

    def test_ssh_mode(self):
        prompt = build_system_prompt("ssh")
        assert "remote" in prompt.lower()
        assert "SSH" in prompt

    def test_dry_run(self):
        prompt = build_system_prompt("local", dry_run=True)
        assert "DRY-RUN" in prompt
        assert "simulated" in prompt.lower()

    def test_contains_rules(self):
        prompt = build_system_prompt("local")
        assert "Rules:" in prompt
        assert "destructive" in prompt.lower()

    def test_ssh_dry_run_combined(self):
        prompt = build_system_prompt("ssh", dry_run=True)
        assert "SSH" in prompt
        assert "DRY-RUN" in prompt
