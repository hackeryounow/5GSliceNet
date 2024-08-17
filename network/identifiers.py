import abc
import random
from abc import ABC

from network.utils import ConfigUtils


class NSSAI:
    """
    NSSAI Information Format:
    SST: Slice/Service Type (8 bits)
    SD: Slice Differentiator (24 bits)
    """

    def __init__(self, sst=None, sd=None):
        self.sst = sst
        self.sd = sd
        if self.sst is None:
            self.sst = NSSAI.random_nssai_sst()
        if self.sd is None:
            self.sd = NSSAI.random_nssai_sd()

    def __eq__(self, other):
        return self.sst == other.sst and self.sd == other.sd

    def __str__(self):
        return "sst: " + str(self.sst) + ", sd: " + str(self.sd)

    @classmethod
    def random_nssai_sst(cls):
        return random.randint(1, 15)

    @classmethod
    def random_nssai_sd(cls):
        return ConfigUtils.random_hex(6)

    def to_dict(self):
        return {"sst": self.sst, "sd": self.sd}


class PLMN:
    """
    PLMN Information Format:
    MCC: Mobile Country Code (3 digits, 12 bits)
    MNC: Mobile Network Code (2 or 3 digits, 12 bits)
    """

    def __init__(self, mcc, mnc):
        self.mcc = mcc
        self.mnc = mnc

    def to_dict(self):
        return {"mcc": self.mcc, "mnc": self.mnc}

    def __eq__(self, other):
        return self.mcc == other.mcc and self.mnc == other.mnc

    def __str__(self):
        return "mcc: " + str(self.mcc) + ", mnc: " + str(self.mnc)


class NssaiInPlmn:
    def __init__(self, plmn, nssai_list):
        self.plmn = plmn
        self.nssai_list = nssai_list

    def to_dict_for_amf(self):
        return self.to_dict()

    def to_dict_for_nssf(self):
        return self.to_dict(key="supportedSnssaiList")

    def to_dict(self, key="snssaiList"):
        return {"plmnId": self.plmn.to_dict(), key: [nssai.to_dict() for nssai in self.nssai_list]}

    def __str__(self):
        return str(self.to_dict())


class TAI:
    """
    TAI Information Format:
    PLMN Information:
      MCC: Mobile Country Code (3 digits, 12 bits)
      MNC: Mobile Network Code (2 or 3 digits, 12 bits)
    TAC: Tracking Area Code (16 bits)
    """

    def __init__(self, plmn, tac=None):
        self.plmn = plmn
        self.tac = tac
        if self.tac is None:
            self.tac = TAI.random_tac()

    @classmethod
    def random_tac(cls):
        return ConfigUtils.random_hex(6)

    def to_dict(self):
        return {"plmnId": self.plmn.to_dict(), "tac": self.tac}

    def __str__(self):
        return "plmnId: " + str(self.plmn) + ", tac: " + str(self.tac)


class DNN:
    def __init__(self, dnn, cidr):
        self.dnn = dnn
        self.cidr = cidr

    def to_dict(self):
        return {"dnn": self.dnn, "cidr": self.cidr}


class DnnInfo:
    def __init__(self, dnn, dns_ipv4="8.8.8.8", dns_ipv6="2001:4860:4860::8888"):
        self.dnn = dnn
        self.dns_ipv4 = dns_ipv4
        self.dns_ipv6 = dns_ipv6

    def to_dict(self):
        return {"dnn": self.dnn, "dns": {"ipv4": self.dns_ipv4, "ipv6": self.dns_ipv6}}

    def __eq__(self, other):
        return self.dnn == other.dnn and self.dns_ipv4 == other.dns_ipv4 and self.dns_ipv6 == other.dns_ipv6

    def __str__(self):
        return str(self.to_dict())


class DnnUpfInfo:
    def __init__(self, dnn, cidr, static_cidr):
        self.dnn = dnn
        self.cidr = cidr
        self.static_cidr = static_cidr

    def __eq__(self, other):
        return self.dnn == other.dnn and self.cidr == other.cidr and self.static_cidr == other.static_cidr

    def __str__(self):
        return str(self.to_dict(with_cidr=True))

    def to_dict(self, with_cidr=False):
        if with_cidr:
            return {"dnn": self.dnn, "pools": {"cidr": [self.cidr]}, "staticPools": {"cidr": [self.static_cidr]}}
        return {"dnn": self.dnn}


class Interface:
    def __init__(self, endpoint, network_instances, interface_type="N3"):
        self.endpoint = endpoint
        self.network_instances = network_instances
        self.interface_type = interface_type

    def to_dict(self):
        return {"endpoints": self.endpoint, "networkInstances": self.network_instances,
                "interfaceType": self.interface_type}


class SnssaiInfo:
    def __init__(self, snssai: NSSAI, dnn_infos: list[DnnInfo]):
        self.snssai = snssai
        self.dnn_infos = dnn_infos

    def to_dict(self):
        return {
            "sNssai": self.snssai.to_dict(),
            "dnnInfos": [dnn_info.to_dict() for dnn_info in self.dnn_infos]
        }


class SnssaiUpfInfo:
    def __init__(self, snssai: NSSAI, dnn_upf_infos: list[DnnUpfInfo]):
        self.snssai = snssai
        self.dnn_upf_infos = dnn_upf_infos

    def __eq__(self, other):
        return self.snssai == other.snssai and self.dnn_upf_infos == other.dnn_upf_infos

    def __str__(self):
        return str(self.to_dict(dnn_with_cidr=True))

    def to_dict(self, dnn_with_cidr=False):
        return {
            "sNssai": self.snssai.to_dict(),
            "dnnUpfInfoList": [dnn_upf_info.to_dict(dnn_with_cidr) for dnn_upf_info in self.dnn_upf_infos]
        }


class UpNode:
    def __init__(self, t_type=""):
        self.t_type = t_type

    @abc.abstractmethod
    def to_dict(self):
        pass


class GnbNode(UpNode):
    def __init__(self, name):
        super().__init__("AN")
        self.name = name

    def to_dict(self):
        return {
            self.name:
                {"type": self.t_type}
        }


class UpfNode(UpNode, ABC):
    def __init__(self, name: str, snssai_upf_infos: list[SnssaiUpfInfo], interfaces: list[Interface], t_type: str,
                 node_id="", addr=""):
        super().__init__(t_type=t_type)
        self.name = name
        self.snssai_upf_infos = snssai_upf_infos
        self.interfaces = interfaces
        self.node_id = node_id
        self.addr = addr


class IUpfNode(UpfNode):

    def __init__(self, name, snssai_upf_infos, interfaces, node_id="", addr=""):
        super().__init__(name, snssai_upf_infos, interfaces, t_type="I-UPF", node_id=node_id, addr=addr)

    def to_dict(self):
        return {
            "upperName": self.name.upper(),
            "name": self.name,
            "nodeId": self.node_id,
            "addr": self.addr,
            "snssaiUpfInfos": [snssai_upf_info.to_dict() for snssai_upf_info in
                               self.snssai_upf_infos],
            "interfaces": ConfigUtils.list2dict(self.interfaces)
        }


class PSAUpfNode(UpfNode):
    def __init__(self, name: str, snssai_upf_infos: list[SnssaiUpfInfo], interfaces, node_id="", addr=""):
        super().__init__(name, snssai_upf_infos, interfaces, t_type="PSA-UPF", node_id=node_id, addr=addr)

    def to_dict(self):
        return {
            "upperName": self.name.upper(),
            "name": self.name,
            "nodeId": self.node_id,
            "addr": self.addr,
            "snssaiUpfInfos": [snssai_upf_info.to_dict(dnn_with_cidr=True) for snssai_upf_info in
                               self.snssai_upf_infos],
            "interfaces": ConfigUtils.list2dict(self.interfaces)
        }


class PfcpForSMF:
    def __init__(self, node_id="", listen_addr="", external_addr=""):
        self.node_id = node_id
        self.listen_addr = listen_addr
        self.external_addr = external_addr

    def to_dict(self):
        return {"nodeId": self.node_id, "listenAddr": self.listen_addr, "externalAddr": self.external_addr}


class PfcpForUPF:
    def __init__(self, node_id="", addr=""):
        self.node_id = node_id
        self.addr = addr

    def to_dict(self):
        return {"nodeId": self.node_id, "addr": self.addr}


class Guami:
    """
    GUAMI Information Format:
    PLMN Information:
      MCC: Mobile Country Code (3 digits, 12 bits)
      MNC: Mobile Network Code (2 or 3 digits, 12 bits)
    AMF ID Information:
      AMF Region ID: (8 bits)
      AMF Set ID: (10 bits)
      AMF Pointer: (6 bits)
    """

    def __init__(self, plmn, amf_id=None):
        self.plmn = plmn
        self.amf_id = amf_id

    def to_dict(self):
        return {"plmnId": self.plmn.to_dict(), "amfId": self.amf_id}

    def __eq__(self, other):
        return self.plmn == other.plmn and self.amf_id == other.amf_id

    def __str__(self):
        return "plmnId: " + str(self.plmn) + ", amfId: " + str(self.amf_id)


class Link:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    def to_dict(self):
        return {"A": self.src, "B": self.dst}

    def __str__(self):
        return str(self.to_dict())
