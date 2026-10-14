import pytest

from devpy.agent.tools import sanitize_command


class TestSanitizeCommand:
    def test_simple_command(self):
        assert sanitize_command("ls -la") == "ls -la"

    def test_strips_whitespace(self):
        assert sanitize_command("  pwd  ") == "pwd"

    def test_rejects_semicolon(self):
        with pytest.raises(ValueError, match="chaining"):
            sanitize_command("ls; rm -rf /")

    def test_rejects_pipe(self):
        with pytest.raises(ValueError, match="chaining"):
            sanitize_command("cat file | grep secret")

    def test_rejects_ampersand(self):
        with pytest.raises(ValueError, match="chaining"):
            sanitize_command("cmd1 && cmd2")

    def test_rejects_command_substitution_dollar(self):
        with pytest.raises(ValueError, match="substitution"):
            sanitize_command("echo $(whoami)")

    def test_rejects_command_substitution_backtick(self):
        with pytest.raises(ValueError, match="substitution"):
            sanitize_command("echo `id`")

    def test_rejects_redirect_output(self):
        with pytest.raises(ValueError, match="redirection"):
            sanitize_command("echo test > /etc/passwd")

    def test_rejects_redirect_input(self):
        with pytest.raises(ValueError, match="redirection"):
            sanitize_command("cmd < input.txt")

    def test_rejects_newlines(self):
        with pytest.raises(ValueError, match="Newlines"):
            sanitize_command("cmd1\ncmd2")

    def test_allows_safe_commands(self):
        safe = ["ps aux", "cat /var/log/app.log", "whoami", "df -h", "uname -a"]
        for cmd in safe:
            assert sanitize_command(cmd) == cmd
