import os

from devpy.security.audit import audit_files, audit_dependencies, check_file_permissions


class TestAudit:
    def test_check_file_permissions_ok(self, tmp_dir):
        path = tmp_dir / ".env"
        path.write_text("SECRET=value")
        os.chmod(str(path), 0o600)
        ok, msg = check_file_permissions(str(path))
        assert ok
        assert "600" in msg or "ok" in msg.lower()

    def test_check_file_permissions_too_open(self, tmp_dir):
        path = tmp_dir / ".env"
        path.write_text("SECRET=value")
        os.chmod(str(path), 0o644)
        ok, msg = check_file_permissions(str(path))
        assert not ok

    def test_check_missing_file(self, tmp_dir):
        ok, msg = check_file_permissions(str(tmp_dir / "missing"))
        assert not ok
        assert msg == "missing"

    def test_audit_files(self, tmp_dir):
        env_file = tmp_dir / ".env"
        env_file.write_text("KEY=val")
        os.chmod(str(env_file), 0o600)
        results = audit_files()
        assert isinstance(results, list)

    def test_audit_dependencies_pinned(self, tmp_dir):
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\ndependencies = ["requests==2.31.0"]\n')
        warnings = audit_dependencies()
        unpinned = [w for w in warnings if "Unpinned" in w]
        assert len(unpinned) == 0

    def test_audit_dependencies_unpinned(self, tmp_dir):
        pyproject = tmp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\ndependencies = ["requests", "flask>=2.0"]\n')
        warnings = audit_dependencies()
        assert len(warnings) >= 1
