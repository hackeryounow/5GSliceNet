import copy
import os

from network.function import AMF
from network.identifiers import NssaiInPlmn
from network.utils import ConfigUtils

project_root = os.path.dirname(os.path.abspath(__file__))


def get_amf_served_guami_list(plmns):
    served_guami_list = []
    for plmn in plmns:
        mcc, mnc = plmn.mcc, plmn.mnc
        amf_id = AMF.random_amf_id()
        guami = {
            "plmnId": {
                "mcc": mcc,
                "mnc": mnc
            },
            "amfId": amf_id
        }
        served_guami_list.append(guami)
    return served_guami_list


def configure_amf(plmns, nssai_lists, supported_tai_list, dnn_list, locality="area1", name="AMF", ngap_ip_list="", register_ipv4="",
                  binding_ipv4="", nrf_uri=""):
    """
    :param plmns: 支持的PLMN，为一维数组，元素为PLMN对象
    :param nssai_lists: PLMN对应的NSSAI列表，为二维数组，元素为NSSAI对象
    :param supported_tai_list: 支持的TAI列表，为一维数组，元素为SupportedTAI对象
    :param dnn_list: DNN列表，为一维数组，元素为str字符串
    :param locality: AMF的位置
    :param name: AMF的名称
    :param ngap_ip_list: AMF的Ngap IP地址列表，为str字符串
    :param register_ipv4: AMF的注册IP
    :param binding_ipv4: AMF的绑定IP
    :param nrf_uri: NRF的URI地址
    :return:
    """
    path = os.path.join(project_root, '../templates/free5gc/amf.yaml')
    values_yaml = ConfigUtils.load_yaml(path)
    # 配置容器配置
    # 获得基本参数
    supported_nssai_in_plmn_list = [
        NssaiInPlmn(plmn, nssai_list) for plmn, nssai_list in zip(plmns, nssai_lists)
    ]
    # 设置amf配置
    values_yaml["amf"]["config"] = {
        "amfName": name,
        "ngapIpList": ngap_ip_list,
        "sbi": {
            "registerIPv4": register_ipv4,
            "bindingIPv4": binding_ipv4,
        },
        "servedGuamiList": get_amf_served_guami_list(plmns),
        "supportTaiList": ConfigUtils.list2dict(supported_tai_list),
        "plmnSupportList": ConfigUtils.list2dict(supported_nssai_in_plmn_list),
        "supportDnnList": dnn_list,
        "nrfUri": nrf_uri,
        "locality": locality
    }
    return copy.deepcopy(values_yaml["amf"])


def configure_nssf(plmns, nssai_lists, locality="area1", name="NSSF", register_ipv4="", binding_ipv4="", nrf_uri=""):
    value_yaml = ConfigUtils.load_yaml("../templates/free5gc/nssf.yaml")
    supported_nssai_in_plmn_list = [
        NssaiInPlmn(plmn, nssai_list) for plmn, nssai_list in zip(plmns, nssai_lists)
    ]
    value_yaml["nssf"]["config"] = {
        "nssfName": name,
        "sbi": {
            "registerIPv4": register_ipv4,
            "bindingIPv4": binding_ipv4,
        },
        "nrfUri": nrf_uri,
        "supportedPlmnList": ConfigUtils.list2dict(plmns),
        "supportedNssaiInPlmnList": ConfigUtils.list2dict(supported_nssai_in_plmn_list),
        "locality": locality
    }
    return copy.deepcopy(value_yaml["nssf"])


def configure_smf_snssai_infos(nssai_list, dnn_infos_list):
    snssai_infos = []
    for snssai, dnn_infos in zip(nssai_list, dnn_infos_list):
        snssai_infos.append({
            "sNssai": snssai.to_dict(),
            "dnnInfos": [dnn.to_dict() for dnn in dnn_infos]
        })
    return snssai_infos


def configure_smf_up_infos():
    pass


def configure_smf(nssais, dnn_infos_list, plmns, up_nodes, locality="area1", ulcl=False, name="SMF2", sbi_register_ipv4="",
                  sbi_binding_ipv4="", nrf_uri=""):
    values_yaml = ConfigUtils.load_yaml("../templates/free5gc/smf.yaml")
    values_yaml["smf"]["config"] = {
        "smfName": name,
        "sbi": {
            "registerIPv4": sbi_register_ipv4,
            "bindingIPv4": sbi_binding_ipv4
        },
        "snssaiInfos": configure_smf_snssai_infos(nssais, [dnn_infos_list]),
        "plmnList": ConfigUtils.list2dict(plmns),
        "userplaneInformation": {
            "upNodes": ConfigUtils.list2dict(up_nodes)
        },
        "nrfUri": nrf_uri,
        "locality": locality
    }
    if ulcl:
        values_yaml["smf"]["config"]["ulcl"] = ulcl
    return copy.deepcopy(values_yaml["smf"])


def configure_upf(dnns, locality="area1", pfcp_addr="", pfcp_node_id="", gtpu_if_list_name=""):
    """
    :param dnns: DNN信息列表，为一维数组，元素为DNN对象
    :param locality: UPF的地理位置
    :param pfcp_addr: PFCP地址
    :param pfcp_node_id: PFCP节点ID
    :param gtpu_if_list_name: GTPU接口列表名称
    :return:
    """
    values_yaml = ConfigUtils.load_yaml("../templates/free5gc/upf.yaml")
    values_yaml["upf"]["config"] = {
        "pfcp": {
            "addr": pfcp_addr,
            "nodeID": pfcp_node_id
        },
        "gtpu": {
            "ifList": {
                "name": gtpu_if_list_name
            }
        },
        "dnnList": ConfigUtils.list2dict(dnns),
        "locality": locality
    }
    return copy.deepcopy(values_yaml["upf"])
