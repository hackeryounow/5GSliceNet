import abc
import copy
import os

from network.identifiers import Guami, TAI, NssaiInPlmn
from network.utils import ConfigUtils


class Node:
    def __init__(self, name, t_type):
        self.name = name
        self.t_type = t_type
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(project_root, f"../templates/free5gc/{t_type}.yaml")
        self.values_yaml = ConfigUtils.load_yaml(self.path)

    @abc.abstractmethod
    def configure(self):
        pass

    def to_dict(self):
        return {self.name: copy.deepcopy(self.values_yaml[self.t_type])}


class AMF(Node):
    def __init__(self, name: str, served_guami_list: list[Guami], supported_tai_list: list[TAI],
                 supported_plmns: list[NssaiInPlmn], dnn_list, locality="area1", ngap_ip_list="",
                 sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri=""):
        super().__init__(name, "amf")
        self.served_guami_list = served_guami_list
        self.supported_tai_list = supported_tai_list
        self.supported_plmns = supported_plmns
        self.dnn_list = dnn_list
        self.locality = locality
        self.ngap_ip_list = ngap_ip_list
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.configure()

    def configure(self):
        self.values_yaml["amf"]["config"]["amfName"] = self.name.upper()
        print(self.ngap_ip_list)
        self.values_yaml["amf"]["config"]["ngapIpList"] = self.ngap_ip_list
        self.values_yaml["amf"]["config"]["servedGuamiList"] = ConfigUtils.list2dict(self.served_guami_list)
        self.values_yaml["amf"]["config"]["supportTaiList"] = ConfigUtils.list2dict(self.supported_tai_list)
        self.values_yaml["amf"]["config"]["plmnSupportList"] = [supported_plmn.to_dict_for_amf() for supported_plmn in
                                                                self.supported_plmns]
        self.values_yaml["amf"]["config"]["supportDnnList"] = list(set(self.dnn_list))
        self.values_yaml["amf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["amf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["amf"]["config"]["nrfUri"] = self.nrf_uri
        self.values_yaml["amf"]["config"]["locality"] = self.locality

    @classmethod
    def random_amf_id(cls):
        return ConfigUtils.random_hex(6)


class AUSF(Node):
    def __init__(self, name, supported_plmns, locality="area1", sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri=""):
        super().__init__(name, "ausf")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.supported_plmns = supported_plmns
        self.locality = locality
        self.configure()

    def configure(self):
        self.values_yaml["ausf"]["config"]["plmnSupportList"] = ConfigUtils.list2dict(self.supported_plmns)
        self.values_yaml["ausf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["ausf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["ausf"]["config"]["nrfUri"] = self.nrf_uri
        self.values_yaml["ausf"]["config"]["locality"] = self.locality


class CHF(Node):
    def __init__(self, name, sbi_register_ipv4="", sbi_binding_ipv4="",
                 cgf_host_ipv4="", nrf_uri="", mongodb_uri=""):
        super().__init__(name, "chf")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.mongodb_uri = mongodb_uri
        self.cgf_host_ipv4 = cgf_host_ipv4
        self.configure()

    def configure(self):
        self.values_yaml["chf"]["config"]["cgf"]["hostIPv4"] = self.cgf_host_ipv4
        self.values_yaml["chf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["chf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["chf"]["config"]["nrfUri"] = self.nrf_uri
        self.values_yaml["chf"]["config"]["mongodb"]["url"] = self.mongodb_uri


class NRF(Node):
    def __init__(self, name, default_plmn, sbi_register_ipv4="", sbi_binding_ipv4=""):
        super().__init__(name, "nrf")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.default_plmn = default_plmn
        self.configure()

    def configure(self):
        self.values_yaml["nrf"]["config"]["DefaultPlmnId"] = self.default_plmn.to_dict()
        self.values_yaml["nrf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["nrf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4


class NSSF(Node):
    def __init__(self, name, plmns, nssais_in_plmns, sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri=""):
        super().__init__(name, "nssf")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nssais_in_plmns = nssais_in_plmns
        self.nrf_uri = nrf_uri
        self.plmns = plmns
        self.configure()

    def configure(self):
        self.values_yaml["nssf"]["config"]["nssfName"] = self.name.upper()
        self.values_yaml["nssf"]["config"]["supportedPlmnList"] = ConfigUtils.list2dict(self.plmns)
        self.values_yaml["nssf"]["config"]["supportedNssaiInPlmnList"] = [nssais_in_plmn.to_dict_for_nssf()
                                                                          for nssais_in_plmn in self.nssais_in_plmns]
        self.values_yaml["nssf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["nssf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["nssf"]["config"]["nrfUri"] = self.nrf_uri


class PCF(Node):
    def __init__(self, name, locality="area1", sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri="", mongodb_uri=""):
        super().__init__(name, "pcf")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.mongodb_uri = mongodb_uri
        self.locality = locality
        self.configure()

    def configure(self):
        self.values_yaml["pcf"]["config"]["pcfName"] = self.name.upper()
        self.values_yaml["pcf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["pcf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["pcf"]["config"]["nrfUri"] = self.nrf_uri
        self.values_yaml["pcf"]["config"]["mongodb"]["url"] = self.mongodb_uri
        self.values_yaml["pcf"]["config"]["locality"] = self.locality


class SMF(Node):
    def __init__(self, name, snssai_infos, plmns, pfcp, up_nodes, links,
                 locality="area1", ulcl=False, sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri=""):
        super().__init__(name, "smf")
        self.snssai_infos = snssai_infos
        self.plmns = plmns
        self.pfcp = pfcp
        self.up_nodes = up_nodes
        self.locality = locality
        self.ulcl = ulcl
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.links = links
        self.configure()

    @classmethod
    def format_up_nodes(cls, up_nodes_list):
        up_nodes = {}
        for up_node in up_nodes_list:
            up_nodes = up_nodes | up_node.to_dict()
        return up_nodes

    def configure(self):
        self.values_yaml["smf"]["config"]["smfName"] = self.name.upper()
        self.values_yaml["smf"]["config"]["snssaiInfos"] = ConfigUtils.list2dict(self.snssai_infos)
        self.values_yaml["smf"]["config"]["plmnList"] = ConfigUtils.list2dict(self.plmns)
        self.values_yaml["smf"]["config"]["pfcp"] = self.pfcp.to_dict()
        self.values_yaml["smf"]["config"]["userplaneInformation"]["upNodes"] = ConfigUtils.list2dict(self.up_nodes)
        self.values_yaml["smf"]["config"]["locality"] = self.locality
        self.values_yaml["smf"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["smf"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["smf"]["config"]["nrfUri"] = self.nrf_uri
        self.values_yaml["smf"]["config"]["userplaneInformation"]["links"] = ConfigUtils.list2dict(self.links)
        if self.ulcl:
            self.values_yaml["smf"]["config"]["ulcl"] = self.ulcl


class UDM(Node):
    def __init__(self, name,  sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri=""):
        super().__init__(name, "udm")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.configure()

    def configure(self):
        self.values_yaml["udm"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["udm"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["udm"]["config"]["nrfUri"] = self.nrf_uri


class UDR(Node):
    def __init__(self, name, sbi_register_ipv4="", sbi_binding_ipv4="", nrf_uri="", mongo_uri=""):
        super().__init__(name, "udr")
        self.sbi_register_ipv4 = sbi_register_ipv4
        self.sbi_binding_ipv4 = sbi_binding_ipv4
        self.nrf_uri = nrf_uri
        self.mongo_uri = mongo_uri
        self.configure()

    def configure(self):
        self.values_yaml["udr"]["config"]["sbi"]["registerIPv4"] = self.sbi_register_ipv4
        self.values_yaml["udr"]["config"]["sbi"]["bindingIPv4"] = self.sbi_binding_ipv4
        self.values_yaml["udr"]["config"]["nrfUri"] = self.nrf_uri
        self.values_yaml["udr"]["config"]["mongodb"]["url"] = self.mongo_uri


class UPF(Node):
    def __init__(self, name, pfcp, dnns, gtpu_if_list_name=""):
        super().__init__(name, "upf")
        self.pfcp = pfcp
        self.dnns = dnns
        self.gtpu_if_list_name = gtpu_if_list_name
        self.configure()

    def configure(self):
        self.values_yaml["upf"]["config"]["pfcp"] = self.pfcp.to_dict()
        self.values_yaml["upf"]["config"]["gtpu"]["ifList"]["name"] = self.gtpu_if_list_name
        self.values_yaml["upf"]["config"]["dnnList"] = ConfigUtils.list2dict(self.dnns)


class WebUI(Node):
    def __init__(self, name, mongodb_uri="", billing_server_host=""):
        super().__init__(name, "webui")
        self.mongodb_uri = mongodb_uri
        self.billing_server_host = billing_server_host
        self.configure()

    def configure(self):
        self.values_yaml["webui"]["config"]["mongodb"]["url"] = self.mongodb_uri
        self.values_yaml["webui"]["config"]["billingServer"]["hostIPv4"] = self.billing_server_host


class MongoDB(Node):
    def __init__(self, name, ):
        super().__init__(name, "mongodb")
        self.configure()

    def configure(self):
        pass
