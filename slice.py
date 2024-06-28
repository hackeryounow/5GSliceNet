import copy
import os

from network.configuration import *
from network.identifiers import NSSAI, PLMN
from network.network import NetSpliter
from network.parameters import *
from network.utils import *


def retrieve_free5gc_dependency(chart_name, alias):
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


def retrieve_smf_nssai_infos(nssais, dnn_infos):
    nssai_infos = []
    for nssai in nssais:
        nssai_info = {
            "sNssai": {
                "sst": nssai.sst,
                "sd": nssai.sd
            },
            "dnnInfos": []
        }
        for dnn_info in dnn_infos:
            nssai_info["dnnInfos"].append({
                "dnn": dnn_info["dnn"],
                "dns": {
                    "ipv4": dnn_info["dns"]["ipv4"],
                    "ipv6": dnn_info["dns"]["ipv6"]
                }
            })
        nssai_infos.append(nssai_info)
    return nssai_infos


def retrieve_smf_upf_upNodes(nssais, dnn_up_infos, net_spliter):
    snssai_up_infos = []
    for nssai in nssais:
        nssai_up_info = {
            "sNssai": {
                "sst": nssai.sst,
                "sd": nssai.sd
            },
            "dnnUpfInfoList": []
        }

        for dnn_up_info in dnn_up_infos:
            pool, static_pool = net_spliter.split()
            nssai_up_info["dnnUpfInfoList"].append({
                "dnn": dnn_up_info["dnn"],
                "pools": [{
                    "cidr": copy.deepcopy(pool)
                }],
                "staticPools": [{
                    "cidr": copy.deepcopy(static_pool)
                }]
            })
        snssai_up_infos.append(nssai_up_info)
    return snssai_up_infos


def retrieve_plmn_support_list_for_amf(plmn_list, nssais_list):
    plmn_support_list = []
    for plmn in plmn_list:
        supported_plmn = {
            "plmnId": plmn.to_dict(),
            "snssaiList": nssais_list
        }
        plmn_support_list.append(supported_plmn)
    return plmn_support_list


def retrieve_plmn_nssai_list_for_nssf(plmn_list, nssais_list):
    supported_nssai_plmn_list = []
    for plmn in plmn_list:
        supported_nssai_plmn = {
            "plmnId": plmn.to_dict(),
            "supportedSnssaiList": nssais_list
        }
        supported_nssai_plmn_list.append(supported_nssai_plmn)
    return supported_nssai_plmn_list


# 1. 更改free5gc的Chart.yaml
def update_chart_yaml(chart_path, new_version, slice_types):
    """
    制作多切片的部署Chart.yaml
    :param chart_path: 5gc 的helm chart 的chart.yaml所在路径
    :param new_version: 版本号
    :param slice_types: 添加的切片类型，依据切片类型添加依赖
    :return: 无
    """
    chart_yaml_path = f"{chart_path}/Chart.yaml"
    chart_yaml = load_yaml(chart_yaml_path)
    for seq, slice_type in enumerate(slice_types):
        seq = seq + 1
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-smf{seq}", f"smf{seq}"))
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-upf{seq}", f"upf{seq}"))
    chart_yaml['version'] = new_version
    write_yaml(chart_yaml, chart_yaml_path)


def update_chart_yaml_for_slice(path, seq):
    update_chart_name(f"{path}/free5gc-smf{seq}", f"free5gc-smf{seq}")
    update_chart_name(f"{path}/free5gc-upf{seq}", f"free5gc-upf{seq}")


def update_chart_name(chart_path, name):
    chart_path = f"{chart_path}/Chart.yaml"
    nf_chart_yaml = load_yaml(chart_path)
    nf_chart_yaml["name"] = name
    write_yaml(nf_chart_yaml, chart_path)


# 2. 更改free5gc的values.yaml
def update_values_yaml(values_yaml_path, slice_types, plmns):
    plmn_list = []
    plmn_json_list = []
    for plmn_mcc, plmn_mnc in plmns:
        plmn = PLMN(plmn_mcc, plmn_mnc)
        plmn_list.append(plmn)
        plmn_json_list.append(plmn.to_dict())
    values_yaml = load_yaml(values_yaml_path)
    nssais = []
    for seq, slice_type in enumerate(slice_types):
        while True:
            sst = random_nssai_sst()
            sd = random_nssai_sd()
            nssai = NSSAI(sst, sd)
            if nssai not in nssais:
                nssais.append(nssai)
                break
    # 2.1 设置amf配置
    nssais_list = []
    for nssai in nssais:
        nssais_list.append(nssai.to_dict())
        pass
    plmn_support_list = retrieve_plmn_support_list_for_amf(copy.deepcopy(plmn_list), copy.deepcopy(nssais_list))
    values_yaml["amf"]["config"] = configure_amf(servedGuamiList, supportTaiList, plmn_support_list, supportDnnList,
                                                 networkName)

    # 2.2 设置nssf配置
    supported_nssai_in_plmn_list = retrieve_plmn_nssai_list_for_nssf(copy.deepcopy(plmn_list), copy.deepcopy(nssais_list))
    values_yaml["nssf"]["config"] = configure_nssf(plmn_json_list, supported_nssai_in_plmn_list)

    net_spliter = NetSpliter("10.60.0.0", "16")
    for idx, slice_type, nssai in zip(range(len(slice_types)), slice_types, nssais):
        nssai = copy.deepcopy(nssai)
        # 2.3 设置smf配置
        seq = idx + 1
        smf_name = "smf" + str(seq)
        values_yaml[smf_name] = copy.deepcopy(values_yaml["smf"])
        dnn_infos = copy.deepcopy(snssaiInfos[0]["dnnInfos"])
        snssai_infos = retrieve_smf_nssai_infos([nssai], dnn_infos)
        sNssaiUpfInfos = retrieve_smf_upf_upNodes([nssai], dnn_infos, net_spliter)
        userplane_information_up_nodes = copy.deepcopy(userplaneInformation_upNodes)
        userplane_information_up_nodes["UPF"]["sNssaiUpfInfos"] = copy.deepcopy(sNssaiUpfInfos)
        values_yaml[smf_name]["config"] = configure_smf(snssai_infos, copy.deepcopy(plmnList),
                                                        userplane_information_up_nodes,
                                                        name=smf_name)
        # 2.4 设置upf配置
        upf_name = "upf" + str(seq)
        values_yaml[upf_name] = copy.deepcopy(values_yaml["upf"])
        cidr = copy.deepcopy(net_spliter.network)
        dnn_list = copy.deepcopy(dnnList)
        dnn_list[0]["cidr"] = str(cidr)
        values_yaml[upf_name]["config"] = configure_upf(dnn_list, pfcp_addr="", pfcp_node_id="", gtpu_if_list_name="")
    return values_yaml


def is_folder_exist(path):
    return os.path.exists(path)


def re_mkdir(path):
    if is_folder_exist(path):
        shutil.rmtree(path)
        os.makedirs(path)


def select_upf_by_nssai():
    path = "5gc"
    re_mkdir(path)
    ConfigUtils.copy_folder("charts/common", f"{path}/common")
    ConfigUtils.copy_folder("charts/free5gc", f"{path}/free5gc")
    ConfigUtils.copy_folder("charts/free5gc-amf", f"{path}/free5gc-amf")
    ConfigUtils.copy_folder("charts/free5gc-ausf", f"{path}/free5gc-ausf")
    ConfigUtils.copy_folder("charts/free5gc-nrf", f"{path}/free5gc-nrf")
    ConfigUtils.copy_folder("charts/free5gc-nssf", f"{path}/free5gc-nssf")
    ConfigUtils.copy_folder("charts/free5gc-pcf", f"{path}/free5gc-pcf")
    ConfigUtils.copy_folder("charts/free5gc-chf", f"{path}/free5gc-chf")
    ConfigUtils.copy_folder("charts/free5gc-udm", f"{path}/free5gc-udm")
    ConfigUtils.copy_folder("charts/free5gc-udr", f"{path}/free5gc-udr")
    ConfigUtils.copy_folder("charts/free5gc-webui", f"{path}/free5gc-webui")
    ConfigUtils.copy_folder("charts/mongodb", f"{path}/mongodb")

    slice_types = ["1", "2", "3"]
    update_chart_yaml(f"{path}/free5gc", "0.1.0", slice_types)
    yaml_content = update_values_yaml(f"{path}/free5gc/values.yaml", slice_types, plmns=[("999", "70")])
    ConfigUtils.write_yaml(yaml_content, f"{path}/free5gc/values.yaml")
    # 3. 复制smf、upf的chart
    # copy_folder("free5gc-smf", "free5gc-smf" + str(seq))
    # copy_folder("free5gc-upf", "free5gc-upf" + str(seq))
    # 4. 更改新chart的chart.yaml
    # update_values_yaml_for_slice("free5gc-smf" + str(seq), smf_name)
    # update_values_yaml_for_slice("free5gc-upf" + str(seq), upf_name)
    for seq, slice_type in enumerate(slice_types):
        seq = seq + 1
        ConfigUtils.copy_folder("charts/free5gc-smf", f"{path}/free5gc-smf" + str(seq))
        ConfigUtils.copy_folder("charts/free5gc-upf", f"{path}/free5gc-upf" + str(seq))
        update_chart_yaml_for_slice(path, seq)
        # TODO: 缺少gNB和UE


def update_chart_yaml_v2(chart_path, area_num, new_version="0.1.0"):
    chart_yaml_path = f"{chart_path}/Chart.yaml"
    chart_yaml = load_yaml(chart_yaml_path)
    chart_yaml['dependencies'] = []
    # 更新公共的依赖，包括common、nrf、ausf、udr、udm、nssf、chf、webui、mongodb
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("common", "common"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-nrf", "nrf"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-ausf", "ausf"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-udr", "udr"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-udm", "udm"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-nssf", "nssf"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-chf", "chf"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("free5gc-webui", "webui"))
    chart_yaml['dependencies'].append(retrieve_free5gc_dependency("mongodb", "mongodb"))

    # 非通用的chart包括，amf、smf、pcf、upf、gnb
    for i in range(area_num):
        seq = i + 1
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-amf{seq}", f"amf{seq}"))
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-smf{seq}", f"smf{seq}"))
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-pcf{seq}", f"pcf{seq}"))
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-upf{seq}", f"upf{seq}"))
        chart_yaml['dependencies'].append(retrieve_free5gc_dependency(f"free5gc-gnb{seq}", f"gnb{seq}"))
    chart_yaml['version'] = new_version
    write_yaml(chart_yaml, chart_yaml_path)


def update_values_yaml_v2(values_yaml_path, area_num, plmn):
    values_yaml = load_yaml(values_yaml_path)
    # 更改通用配置的plmn和切片标识
    # TODO
    # 更改非通用chart的values配置
    for i in range(area_num):
        seq = i + 1
        amf_name = f"amf{seq}"
        values_yaml[amf_name] = copy.deepcopy(values_yaml["amf"])
        values_yaml[amf_name]["config"] = configure_amf(copy.deepcopy(plmn), copy.deepcopy(plmn), copy.deepcopy(plmn),
                                                        copy.deepcopy(plmn), amfName=amf_name)



def select_nearby_upf(area_num):
    path = "multi_area"
    re_mkdir(path)
    # 与区域有关的网元，amf、pcf、smf、upf
    # 与区域无关的网元，ausf、nrf、nssf
    # 1. 复制与区域无关的网元chart
    ConfigUtils.copy_folder("charts/free5gc-ausf", f"{path}/free5gc-ausf")
    ConfigUtils.copy_folder("charts/free5gc-nrf", f"{path}/free5gc-nrf")
    ConfigUtils.copy_folder("charts/free5gc-nssf", f"{path}/free5gc-nssf")
    # 公用组件
    ConfigUtils.copy_folder("charts/common", f"{path}/common")
    ConfigUtils.copy_folder("charts/free5gc", f"{path}/free5gc")
    ConfigUtils.copy_folder("charts/free5gc-chf", f"{path}/free5gc-chf")
    ConfigUtils.copy_folder("charts/free5gc-webui", f"{path}/free5gc-webui")
    ConfigUtils.copy_folder("charts/mongodb", f"{path}/mongodb")
    # 2. 复制与区域有关的网元chart，amf、pcf、smf、upf
    for i in range(area_num):
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{path}/free5gc-amf{i}")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{path}/free5gc-pcf{i}")
        ConfigUtils.copy_folder("charts/free5gc-smf", f"{path}/free5gc-smf{i}")
        ConfigUtils.copy_folder("charts/free5gc-upf", f"{path}/free5gc-upf{i}")
        ConfigUtils.copy_folder("charts/ueransim-gnb", f"{path}/ueransim-gnb{i}")
    # 3. 更新free5gc 的chart.yaml
    update_chart_yaml_v2(f"{path}/free5gc", area_num=3, new_version="0.1.0")
    # 4. 更新free5gc的values.yaml
    update_values_yaml_v2(f"{path}/free5gc/values.yaml", area_num=3, plmn=("999", "70"))
    # 5. 更改其他chart的配置

    pass