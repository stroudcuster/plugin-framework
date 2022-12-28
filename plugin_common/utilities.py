import pathlib
from importlib import util as imputil
from typing import Optional


def whereami(package_name: str) -> pathlib.Path:
    """
    Returns a Path object pointing to the location of the application's package folder

    :return: the path of the application's package directory
    :rtype: pathlib.Path

    """
    origin = imputil.find_spec(package_name).origin
    return pathlib.Path(origin).parent


def find_project_root(node: Optional[pathlib.Path] = None) -> pathlib.Path:
    """
    This function starts with the provided file system node, or the location of the plugin_source package and
    works its way down the tree until it locates a directory that does not contain an __init__.py file and is not
    the src directory.

    :param node:
    :return: the project root path
    :rtype: pathlib.Path

    """
    if node is None:
        leaf: pathlib.Path = whereami('plugin_source')
    else:
        leaf = node
    if pathlib.Path(leaf, '__init__.py').exists():
        return find_project_root(leaf.parent)
    elif leaf.name == 'src':
        return find_project_root(leaf.parent)
    else:
        return leaf


def decode_version(ver_str: str) -> tuple[int, int, int]:
    """
    Converts a string version number in the form major.minor.micro to an tuple of integers so that two version numbers
    can be reliably compared

    :param ver_str: the version number in string form
    :return: the version number as a tuple of three integers
    :rtype: tuple[int, int, int]

    """
    major, minor, micro = ver_str.split('.')
    return int(major), int(minor), int(micro)
