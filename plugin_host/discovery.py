import json
import pathlib
import sys
from typing import Any, Callable, Optional
if sys.version_info.major == 3 and sys.version_info.minor < 10:
    from importlib_metadata import entry_points, EntryPoint
else:
    from importlib.metadata import entry_points, EntryPoint


import plugin_common.plugin_specs as ps
import plugin_common.json_handler as jh
import plugin_common.utilities as util

HELP_DOCS_URI = 'help_docs_uri'
VERSION = 'version'
PLUGIN_SPECS = 'plugin_specs'

entrypoints_type = dict[str, dict[str, EntryPoint]]
plugin_specs_map_type = dict[str, ps.PluginSpec]


class IntegrationManager:
    """
    This class manages the discovery, installation and update of plugin functionality that is packaged according
    to the formats and protocols support by this framework.  It is expected that this class with be fronted by
    a class or classes providing a GUI or web service giving access to this class' functionality

    """
    def __init__(self, json_path: pathlib.Path, group: str, menu_parent: Any):
        """
        Creates an instance of PluginManager

        :param json_path: the path to the directory containing the JSON serialized PluginSpec files installed in the host application
        :type json_path: pathlib.Path
        :param group: the group name that identifies plugins that are extend the functionality of the host application
        :type group: str

        """
        self.json_path: pathlib.Path = json_path
        self.group: str = group
        self.menu_parent = menu_parent
        self.entrypoints: entrypoints_type = {}
        self.entrypoints = self.discover_entrypoints()
        self.installed_plugins: plugin_specs_map_type = self.get_installed_plugins()
        self.updated_plugins: plugin_specs_map_type = {}
        self.new_plugins: plugin_specs_map_type = {}
        self.help_uri_map: dict[str, str] = {}
        self.updated_plugins, self.new_plugins, help_uri_map = self.get_discovered_plugins()

    def discover_entrypoints(self) -> entrypoints_type:
        """
        This method uses the importlib.metadata library to discovery entry points in installed packages.  The entry
        points retrieved have a common group name which corresponds to the name of a plugin as recorded in the name\
        property of plugin_common.plugin_specs.PluginSpec

        :return: a dict keyed by the root package name of the plugin source, containing dicts keyed by entrypoint name and having importlib.metadata.EntryPoint values
        :rtype: dict[str, dict[str, importlib.metadata.EntryPoint]

        """
        entrypoints: entrypoints_type = {}
        ep = entry_points(group=self.group)
        for entrypoint in ep:
            key = entrypoint[0: entrypoint.index('.')]
            try:
                entrypoints[key][entrypoint.name] = entrypoint
            except KeyError:
                entrypoints[key] = {entrypoint.name: entrypoint}
        return entrypoints

    def get_installed_plugins(self) -> plugin_specs_map_type:
        """
        Creats a dict keyed by PluginSpec.name containing values of PluginSpec.  These instances are instantiated
        from JSON serialized PluginSpec files in the host application's json directory

        :return: a map of PluginSpecs installed in the host application
        :rtype: dict[str, plugin_common.plugin_specs.PluginSpec

        """
        plugin_map: plugin_specs_map_type = {}
        for jsonf in self.json_path.glob('*.json'):
            with jsonf.open(mode='r') as jf:
                json_str: str = jf.read()
                plugin_spec: ps.PluginSpec = json.loads(eval(json_str), object_hook=jh.plugin_object_hook)
                plugin_map[plugin_spec.name] = plugin_spec
        return plugin_map

    def get_discovered_plugins(self) -> tuple[plugin_specs_map_type, plugin_specs_map_type, dict[str, str]]:
        """
        Retrieves the PlugSpec's, versions and help doc URI for packages collected by the discover_entrypoints
        method

        :return: a tuple containing maps of updated PluginSpec instances, new (uninstalled) PluginSpec instances and a map of help doc URI
        :rtype: tuple[plugin_specs_map_type, plugin_spec_map_type, dict[str, str]

        """
        help_uri_map: dict[str, str] = {}
        upd_plugin_specs: plugin_specs_map_type = {}
        new_plugin_specs: plugin_specs_map_type = {}
        for key, entrypoints in self.entrypoints:
            version_callable: Optional[Callable] = None
            plugin_spec_callable: Optional[Callable] = None
            for entrypoint in entrypoints:
                if entrypoint.name == HELP_DOCS_URI:
                    help_uri_map[key] = entrypoint.load()()
                elif entrypoint.name == VERSION:
                    version_callable = entrypoint.load()
                elif entrypoint.name == PLUGIN_SPECS:
                    plugin_spec_callable = entrypoint.load()
            if version_callable is not None and plugin_spec_callable is not None:
                version = version_callable()
                if key in self.installed_plugins:
                    installed_version = self.installed_plugins[key].version
                    if util.decode_version(version) > util.decode_version(installed_version):
                        upd_plugin_specs[key] = plugin_spec_callable()
                else:
                    new_plugin_specs[key] = plugin_spec_callable()
            else:
                if version_callable is None:
                    ...
                if plugin_spec_callable is None:
                    ...

        return upd_plugin_specs, new_plugin_specs, help_uri_map

    def update_plugin(self, key: str) -> None:
        """
        Replaces a currently installed JSON PluginSpec file with one of a more recent version

        :param key: the PluginSpec.name property
        :type key: str
        :return: None

        """
        update: ps.PluginSpec = self.updated_plugins[key]
        jsonf: pathlib.Path = pathlib.Path(self.json_path, f'{update.name}.json')
        json_str = jh.PluginSpecJSONEncoder().encode(update)
        with jsonf.open(mode='w') as jf:
            jf.write(json_str)

    def install_plugin(self, key: str) -> None:
        """
        Installs a new JSON PluginSpec file into the host app's PluginSpec directory

        :param key: the name of the PluginSpec to be installed
        :type key: str
        :return: None

        """
        new: ps.PluginSpec = self.new_plugins[key]
        jsonf: pathlib.Path = pathlib.Path(self.json_path, f'{new.name}.json')
        if not jsonf.exists():
            json_str = jh.PluginSpecJSONEncoder().encode(new)
            with jsonf.open(mode='w') as jf:
                jf.write(json_str)

    def uninstall_plugin(self, key: str) -> None:
        """
        Uninstalls a JSON PluginSpec from the host app's PluginSpec directory

        :param key: the name of the PluginSpec to be removed
        :return:
        """
        installed: ps.PluginSpec = self.installed_plugins[key]
        jsonf: pathlib.Path = pathlib.Path(self.json_path, f'{installed.name}.json')
        jsonf.unlink(missing_ok=True)
        try:
            del self.installed_plugins[key]
            del self.updated_plugins[key]
        except KeyError:
            pass

    def create_menus(self, clean_menu: Callable, not_found_action: Callable, selection_action: Callable,
                     add_menu_item: Callable, add_menu: Callable):
        """
        Rebuild the menus for currently installed PluginSpec instances

        :param clean_menu: a callback routine the will remove the plugin menu item from the menu parent in preparation for rebuilding the menu
        :param not_found_action: the callback to be used when an entry point can not be found
        :type not_found_action: Callable
        :param selection_action: the callback to be used for Person, date range and DataPointType selections
        :type selection_action: Callable
        :param add_menu_item: the callback to be used to add menu items to the menu
        :type add_menu_item: Callable
        :param add_menu: the callback to be used to associate the menu created with a parent menu
        :type add_menu: Callable
        :return: None

        """
        clean_menu(self.menu_parent)
        for plugin_spec in self.installed_plugins.values():
            for plugin_menu in plugin_spec.menus:
                plugin_menu.create_menu(not_found_action=not_found_action, selection_action=selection_action,
                                        add_menu_item=add_menu_item, add_menu=add_menu)
