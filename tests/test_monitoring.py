import time

from devpy.agent.monitoring import MonitorRegistry


class TestMonitorRegistry:
    def test_start_and_list(self):
        registry = MonitorRegistry()
        result = registry.start("web", 80.0, lambda n: 50.0, lambda *a: None)
        assert "web" in result
        assert "web" in registry.list_active()
        registry.stop_all()

    def test_stop(self):
        registry = MonitorRegistry()
        registry.start("db", 90.0, lambda n: 50.0, lambda *a: None)
        assert registry.stop("db")
        assert "db" not in registry.list_active()

    def test_stop_nonexistent(self):
        registry = MonitorRegistry()
        assert not registry.stop("ghost")

    def test_stop_all(self):
        registry = MonitorRegistry()
        registry.start("c1", 80.0, lambda n: 50.0, lambda *a: None)
        registry.start("c2", 90.0, lambda n: 50.0, lambda *a: None)
        registry.stop_all()
        assert registry.list_active() == {}

    def test_replace_existing_monitor(self):
        registry = MonitorRegistry()
        registry.start("web", 80.0, lambda n: 50.0, lambda *a: None)
        registry.start("web", 95.0, lambda n: 50.0, lambda *a: None)
        active = registry.list_active()
        assert active["web"] == 95.0
        registry.stop_all()

    def test_alert_triggers_on_threshold(self):
        registry = MonitorRegistry()
        alerts = []

        def alert_fn(name, current, threshold):
            alerts.append((name, current, threshold))

        registry.start("hot", 50.0, lambda n: 90.0, alert_fn)
        time.sleep(0.5)
        assert len(alerts) > 0
        assert alerts[0][0] == "hot"
        assert alerts[0][1] == 90.0
        registry.stop_all()

    def test_empty_list(self):
        registry = MonitorRegistry()
        assert registry.list_active() == {}
