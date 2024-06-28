import os.path
import secrets
import shutil

import yaml


class ConfigUtils:
    @classmethod
    def list2dict(cls, config_list):
        return [item.to_dict() for item in config_list]

    @classmethod
    def load_yaml(cls, file_path):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return data

    @classmethod
    def write_yaml(cls, data, file_path):
        # Dumper.ignore_aliases = lambda self, data: True
        with open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)

    @classmethod
    def random_hex(cls, length):
        hex_string = ''.join(secrets.choice('0123456789abcdef') for _ in range(length))
        return hex_string

    @classmethod
    def copy_folder(cls, src_folder, dest_folder):
        try:
            shutil.copytree(src_folder, dest_folder)
            print(f"Folder '{src_folder}' successfully copied to '{dest_folder}'.")
        except Exception as e:
            print(f"Error copying folder: {e}")

    @classmethod
    def tpl_dependency(cls, chart_name, alias):
        """
        :param chart_name: chart的对应文件夹的名称
        :param alias: chart的别名
        :param seq: chart的编号
        :return:
        """
        config = {
            "name": chart_name,
            "version": "~0.1.0",
            "repository": f"file://../{chart_name}",
            "condition": alias + ".enabled",
            "alias": alias
        }
        return config

    @classmethod
    def delete_folder(cls, path):
        print(path)
        if os.path.exists(path):
            shutil.rmtree(path)
