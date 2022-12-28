import json
import pathlib
from typing import Any, Union

import plugin_common.plugin_specs as model


def retrieve_plugins(plugin_path: pathlib.Path) -> list[model.PluginSpec]:
    """
    Deserialize the PluginSpec objects encoded in JSON file in the plugins folder

    :param plugin_path: a Path object pointing to the folder containing the PluginSpec JSON files
    :type: pathlib.Path
    :return: a list of de-serialized PluginSpec objects
    :rtype: list[model.PluginMenu]

    """
    plugins: list[model.PluginSpec] = []
    for plugin_json in plugin_path.glob('*.json'):
        try:
            with plugin_json.open(mode='r') as pj:
                json_str = pj.read()
                plugin: model.PluginSpec = json.loads(eval(json_str), object_hook=plugin_object_hook)
                plugins.append(plugin)
        except json.JSONDecodeError:
            pass
    return plugins


def save_plugins(plugins: list[model.PluginSpec], plugin_path: pathlib.Path):
    """
    Serialize a list of PluginSpec instances to JSON files.  The file names are based on the PluginSpec.name and author_name properties

    :param plugins: a list of PluginSpec objects
    :type plugins: list[plugin_manager.model.plugin.PluginSpec]
    :param plugin_path: a Path object pointing to the plugin folder
    :type plugin_path: pathlib.Path
    :return: None
    """
    for plugin in plugins:
        if isinstance(plugin, model.PluginSpec):
            json_str = json.dumps(plugin, cls=PluginSpecJSONEncoder)
            with pathlib.Path(plugin_path,
                              f'{plugin.author_name.replace(" ", "_")}-{plugin.name.replace(" ","_")}.json').open(mode='w') as pj:
                pj.write(json_str)
        else:
            raise TypeError(f'{plugin.__str__()} is not a valid plugin_manager.model.PluginSpec object')


def decode_bool(bool_str: str) -> bool:
    return bool_str in ['true', 'True']


class PluginSpecJSONEncoder(json.JSONEncoder):
    """
    Implements a custom json.JSONEncoder to encode instances of PluginSpec, PluginMenu and PluginMenuItem instances

    """
    def default(self, obj: Any):
        """
        This method is invoked to handle data types that can't be handled by the standard JSONEncoder

        :param obj:
        :return: Any
        """
        match obj.__class__.__name__:
            case model.PluginMenuItem.__name__:
                json_str = json.JSONEncoder().encode({'title': obj.title,
                                                      'entry_point': obj.entry_point_name,
                                                      'select_person': str(obj.select_person),
                                                      'select_date_range': str(obj.select_date_range),
                                                      'select_dp_type': str(obj.select_dp_type),
                                                      'class': model.PluginMenuItem.__name__})
                return json_str
            case model.PluginMenu.__name__:
                list_str = f'[{",".join([PluginSpecJSONEncoder().default(item) for item in obj.items])}]'
                json_str = json.JSONEncoder().encode({'title': obj.title,
                                                      'module': obj.module_name,
                                                      'items': list_str,
                                                      'class': obj.__class__.__name__})
                return json_str
            case model.PluginSpec.__name__:
                menu_list_str: str = f'[{",".join([PluginSpecJSONEncoder().default(menu) for menu in obj.menus])}]'
                json_str = json.JSONEncoder().encode({'name': obj.name,
                                                      'description': obj.description,
                                                      'author_name': obj.author_name,
                                                      'author_email': obj.author_email,
                                                      'menus': menu_list_str,
                                                      'class': obj.__class__.__name__})
                return json_str
            #  no match, revert to the standard encoder
            case _:
                return json.JSONEncoder.default(self, obj)


def plugin_object_hook(obj_dict: dict) -> Union[dict, model.PluginSpec, model.PluginMenu, model.PluginMenuItem]:
    """
    A custom object hook function to handle the decoding of JSON representations of ConfigInfo, ImportSpecs and
    ExportSpecs

    :param obj_dict: a dict containing JSON names and values
    :type obj_dict: dict[str, str]
    :return: an instance of the appropriate class (e.g. ConfigInfo, ImportSpecs, etc)
    :rtype: Union[dict, model.PluginSpec, model.PluginMenu, model.PluginMenuItem]


    """
    try:
        if 'class' in obj_dict:
            match obj_dict['class']:
                case model.PluginMenuItem.__name__:
                    return model.PluginMenuItem(title=obj_dict['title'],
                                                entry_point_name=obj_dict['entry_point'],
                                                select_person=decode_bool(obj_dict['select_person']),
                                                select_date_range=decode_bool(obj_dict['select_date_range']),
                                                select_dp_type=decode_bool(obj_dict['select_dp_type']))
                case model.PluginMenu.__name__:
                    items: list[model.PluginMenuItem] = []
                    for item in eval(obj_dict['items']):
                        items.append(plugin_object_hook(item))
                        """
                        items.append(model.PluginMenuItem(title=item['title'],
                                                                  entry_point=item['entry_point'],
                                                                  select_person=decode_bool(item['select_person']),
                                                                  select_date_range=decode_bool(item['select_date_range']),
                                                                  select_dp_type=decode_bool(item['select_dp_type'])))
                        """
                    return model.PluginMenu(title=obj_dict['title'], module_name=obj_dict['module'], items=items)
                case model.PluginSpec.__name__:
                    menus: list[model.PluginMenu] = []
                    for menu in eval(obj_dict['menus']):
                        menus.append(plugin_object_hook(menu))
                    return model.PluginSpec(name=obj_dict['name'],
                                            description=obj_dict['description'],
                                            version=obj_dict['version'],
                                            author_name=obj_dict['author_name'],
                                            author_email=obj_dict['author_email'],
                                            menus=menus)
                case _:
                    return obj_dict
        else:
            return obj_dict
    except TypeError:
        return obj_dict
