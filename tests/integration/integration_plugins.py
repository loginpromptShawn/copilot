import pathlib

from copilot_app.plugins.plugin_manager import PluginManager


def integration_load_plugins():
    base = pathlib.Path(__file__).resolve().parents[2] / "src" / "copilot_app" / "plugins" / "installed"
    pm = PluginManager(installed_dir=base)
    pm.load_plugins()
    assert "example" in pm.active_plugins


def integration_activate_deactivate_plugins():
    base = pathlib.Path(__file__).resolve().parents[2] / "src" / "copilot_app" / "plugins" / "installed"
    pm = PluginManager(installed_dir=base)
    pm.load_plugins()
    app_context = {"app": None, "config": None}
    pm.activate_all(app_context)
    plugin = pm.get_plugin("example")
    assert plugin is not None
    assert getattr(plugin, "activated", False) is True
    pm.deactivate_all()
    assert getattr(plugin, "activated", False) is False


def integration_get_plugin_metadata():
    base = pathlib.Path(__file__).resolve().parents[2] / "src" / "copilot_app" / "plugins" / "installed"
    pm = PluginManager(installed_dir=base)
    pm.load_plugins()
    p = pm.get_plugin("example")
    assert p is not None
    assert p.name == "example"
    assert p.version == "1.0"
