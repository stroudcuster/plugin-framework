import json
import pathlib
import sys

from plugin_common.utilities import whereami, find_project_root, decode_version

if sys.version_info.major == 3 and sys.version_info.minor <= 10:
    import tomli as TOML
else:
    import TOML

import plugin_common.plugin_specs as ps
import plugin_common.json_handler as jh

project_root: pathlib.Path = find_project_root()
pyproj_path: pathlib.Path = pathlib.Path(project_root, 'pyproject.toml')
try:
    with pyproj_path.open(mode='rb') as f:
        pyproj_dict = TOML.load(f)
except FileNotFoundError:
    pyproj_dict = {}

PLUGIN_NAME = pyproj_dict['project']['name']


def get_help_docs_uri() -> str:
    """
    Entry point for retrieving the plug in package's help document URI

    :return: help doc directory URI
    :rtype: str

    """
    return pathlib.Path(whereami('help'), 'index.html').as_uri()


def get_version() -> tuple[int, int, int]:
    """
    Entry point for retrieving the plug in package's version number from either the pyproject.toml file or
    a version.py in the project's root package.  The version number is returned as a three integer tuple to allow
    version numbers to be consistently compared.

    :return: major, minor and micro elements of the version number
    :rtype: tuple[int, int, int]

    """
    try:
        return decode_version(pyproj_dict['project']['version'])
    except KeyError:
        try:
            import plugin_source.version
            return decode_version(plugin_source.version.__version__)
        except ImportError:
            raise Exception('No source for version.')


def get_plugin_specs() -> ps.PluginSpec:
    """
    Entry point for retrieving the plug in projects PluginSpec instance

    :return: the package's PluginSpec instance
    :rtype: plugin_common.plugin_specs.PluginSpec
    """
    json_path: pathlib.Path = pathlib.Path(whereami('plugin_source'), 'json', f'{PLUGIN_NAME}.json')
    if json_path.exists():
        with json_path.open(mode='r') as pj:
            json_str = pj.read()
            plugin: ps.PluginSpec = json.loads(eval(json_str), object_hook=jh.plugin_object_hook)
            if isinstance(plugin, ps.PluginSpec):
                return plugin
            else:
                raise json.JSONDecodeError(f'{json_path.__str__()} format is not valid for PlugSpec', doc=json_str,
                                           pos=0)
    else:
        raise FileNotFoundError()


if __name__ == '__main__':
    pass
