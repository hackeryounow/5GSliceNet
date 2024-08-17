import abc
import copy
from abc import ABC
from collections import ChainMap

from network.function import AUSF, CHF, NRF, NSSF, PCF, SMF, UPF, UDM, UDR, WebUI, MongoDB, AMF
from network.identifiers import PLMN, Guami, TAI, NSSAI, NssaiInPlmn, PfcpForSMF, DnnInfo, SnssaiInfo, DnnUpfInfo, \
    SnssaiUpfInfo, Interface, PSAUpfNode, PfcpForUPF, DNN, Link, IUpfNode, GnbNode
from network.network import NetSpliter
from network.utils import ConfigUtils
from functools import reduce


class SliceNet:
    def __init__(self, path="5gc"):
        self.path = path
        self.values_path = f"{self.path}/free5gc/values.yaml"
        self.amf_list = []
        self.ausf_list = []
        self.pcf_list = []
        self.nrf_list = []
        self.nssf_list = []
        self.smf_list = []
        self.upf_list = []
        self.udm_list = []
        self.chf_list = []
        self.udr_list = []
        self.webconsole_list = []
        self.db_list = []

    def to_dict(self):
        nf_list = (self.amf_list + self.ausf_list + self.pcf_list +
                   self.nrf_list + self.nssf_list + self.smf_list +
                   self.upf_list + self.udm_list + self.chf_list +
                   self.udr_list + self.webconsole_list + self.db_list)
        return dict(ChainMap(*[nf.to_dict() for nf in nf_list]))

    def save_values_yaml(self):
        values_yaml = copy.deepcopy(self.to_dict())
        ConfigUtils.write_yaml(values_yaml, self.values_path)


class CommonSliceNet(SliceNet):
    def __init__(self, path="5gc"):
        super().__init__(path)
        self.values_path = f"{self.path}/free5gc/values.yaml"
        self.chf_list.append(CHF("chf"))
        self.udm_list.append(UDM("udm"))
        self.udr_list.append(UDR("udr"))
        self.webconsole_list.append(WebUI("webui"))
        self.db_list.append(MongoDB("mongodb"))
        self.dependencies = []
        self.net_spliter = NetSpliter("10.60.0.0", "16")

    def configure(self):
        ConfigUtils.delete_folder(self.path)
        ConfigUtils.delete_folder(self.values_path)
        self.copy_charts()
        self._update_chart_yaml()
        self.save_values_yaml()

    def copy_charts(self):
        self.copy_common()
        self.copy_specific_charts()

    @abc.abstractmethod
    def copy_specific_charts(self):
        pass

    def _update_chart_yaml(self):
        chart_template_path = f"{self.path}/../templates/free5gc/chart.yaml"
        chart_path = f"{self.path}/free5gc/Chart.yaml"
        chart_yaml = ConfigUtils.load_yaml(chart_template_path)
        self.update_dependency()
        chart_yaml["dependencies"].extend(self.dependencies)
        ConfigUtils.write_yaml(chart_yaml, chart_path)

    @abc.abstractmethod
    def update_dependency(self):
        pass

    def copy_common(self):
        ConfigUtils.copy_folder("charts/common", f"{self.path}/common")
        ConfigUtils.copy_folder("charts/free5gc", f"{self.path}/free5gc")
        ConfigUtils.copy_folder("charts/free5gc-webui", f"{self.path}/free5gc-webui")
        ConfigUtils.copy_folder("charts/mongodb", f"{self.path}/mongodb")
        ConfigUtils.copy_folder("charts/free5gc-chf", f"{self.path}/free5gc-chf")
        ConfigUtils.copy_folder("charts/free5gc-ausf", f"{self.path}/free5gc-ausf")
        ConfigUtils.copy_folder("charts/free5gc-nrf", f"{self.path}/free5gc-nrf")
        ConfigUtils.copy_folder("charts/free5gc-nssf", f"{self.path}/free5gc-nssf")
        ConfigUtils.copy_folder("charts/free5gc-udm", f"{self.path}/free5gc-udm")
        ConfigUtils.copy_folder("charts/free5gc-udr", f"{self.path}/free5gc-udr")

    def chg_sub_chart_name(self, chart_name):
        """
        Change subchart name.
        :param chart_name: subchart name would be changed as `chart_name`.
        :return: None
        """
        chart_path = f"{self.path}/{chart_name}/Chart.yaml"
        chart_yaml = ConfigUtils.load_yaml(chart_path)
        # ConfigUtils.delete_folder(chart_path)
        chart_yaml["name"] = chart_name
        ConfigUtils.write_yaml(chart_yaml, chart_path)


class NormalSliceNet(CommonSliceNet, ABC):
    def __init__(self, slices_num, dnn_names, path="5gc"):
        super().__init__(path)
        amf_id = AMF.random_amf_id()
        plmn = PLMN("999", "70")
        self.supported_plmns = [plmn]
        guami = Guami(plmn, amf_id)
        served_guami_list = [guami]
        tai = TAI(plmn)
        support_tai_list = [tai]
        self.nssais = [NSSAI() for _ in range(slices_num)]
        nssai_in_plmn = NssaiInPlmn(plmn, self.nssais)
        support_plmn_list = [nssai_in_plmn]
        supported_dnn_list = dnn_names
        self.dnn_names = dnn_names
        self.slices_num = slices_num
        self.amf_list.append(AMF("amf", served_guami_list, support_tai_list, support_plmn_list, supported_dnn_list))
        self.pcf_list.append(PCF("pcf"))
        self.ausf_list.append(AUSF("ausf", self.supported_plmns))
        self.nrf_list.append(NRF("nrf", plmn))
        self.nssf_list.append(NSSF("nssf", self.supported_plmns, support_plmn_list))

    def create_upf(self, i, pool):
        pfcp = PfcpForUPF()
        dnn = DNN(self.dnn_names[i], pool)
        upf = UPF(self.dnn_names[i], pfcp, [dnn])
        return upf


class SliceNetModeOne(NormalSliceNet):
    def __init__(self, slices_num, dnn_names, path="5gc_mode1"):
        super().__init__(slices_num, dnn_names, path)
        # TODO: 配置切片与垂直行业网络对应
        for i in range(self.slices_num):
            pool, static_pool = self.net_spliter.split()
            smf = self._create_smf(i, pool, static_pool)
            self.smf_list.append(smf)
            upf = self.create_upf(i, pool)
            self.upf_list.append(upf)

    def _create_smf(self, i, pool, static_pool):
        dnn_info = DnnInfo(self.dnn_names[i], "8.8.8.8", "2001:4860:4860::8888")
        dnn_infos = [dnn_info]
        nssai_info = SnssaiInfo(self.nssais[i], dnn_infos)
        nssai_infos = [nssai_info]
        dnn_upf_info = DnnUpfInfo(self.dnn_names[i], pool, static_pool)
        dnn_upf_infos = [dnn_upf_info]
        snssai_upf_info = SnssaiUpfInfo(self.nssais[i], dnn_upf_infos)
        snssai_upf_infos = [snssai_upf_info]
        interface = Interface("", self.dnn_names[i])
        interfaces = [interface]
        up_node = PSAUpfNode(f"upf{i + 1}", snssai_upf_infos, interfaces)
        # gnb = GnbNode("gNB1")
        up_nodes = [up_node]
        link = Link("gNB1", up_node.name.upper())
        links = [link]
        pfcp = PfcpForSMF()
        smf = SMF(f"smf{i + 1}", nssai_infos, self.supported_plmns, pfcp, up_nodes, links)
        return smf

    def copy_specific_charts(self):
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf")
        for i in range(self.slices_num):
            ConfigUtils.copy_folder(f"charts/free5gc-smf-ulcl", f"{self.path}/free5gc-smf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-smf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-upf{i + 1}")

    def update_dependency(self):
        self.dependencies.append(ConfigUtils.tpl_dependency("free5gc-amf", "amf"))
        self.dependencies.append(ConfigUtils.tpl_dependency("free5gc-pcf", "pcf"))
        for i in range(self.slices_num):
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf{i + 1}", f"smf{i + 1}"))
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-upf{i + 1}", f"upf{i + 1}"))


class SliceNetModeTwo(NormalSliceNet):
    def __init__(self, slices_num, dnn_names, path="5gc_mode2"):
        super().__init__(slices_num, dnn_names, path)

        nssai_infos = []
        up_nodes = []
        links = []
        for i in range(self.slices_num):
            dnn_info = DnnInfo(dnn_names[i], "8.8.8.8", "2001:4860:4860::8888")
            dnn_infos = [dnn_info]
            nssai_info = SnssaiInfo(self.nssais[i], dnn_infos)
            nssai_infos.append(nssai_info)
            pool, static_pool = self.net_spliter.split()
            dnn_upf_info = DnnUpfInfo(dnn_names[i], pool, static_pool)
            dnn_upf_infos = [dnn_upf_info]
            snssai_upf_info = SnssaiUpfInfo(self.nssais[i], dnn_upf_infos)
            snssai_upf_infos = [snssai_upf_info]
            interface = Interface("", dnn_names[i])
            interfaces = [interface]
            up_node = PSAUpfNode(f"upf{i + 1}", snssai_upf_infos, interfaces)
            up_nodes.append(up_node)
            links.append(Link(f"gNB1", up_node.name.upper()))
            upf = self.create_upf(i, pool)
            self.upf_list.append(upf)
        pfcp = PfcpForSMF()
        self.smf_list.append(SMF(f"smf1", nssai_infos, self.supported_plmns, pfcp, up_nodes, links))

    def copy_specific_charts(self):
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf")
        ConfigUtils.copy_folder("charts/free5gc-smf-ulcl", f"{self.path}/free5gc-smf1")
        for i in range(self.slices_num):
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-upf{i + 1}")

    def update_dependency(self):
        self.dependencies.append(ConfigUtils.tpl_dependency("free5gc-amf", "amf"))
        self.dependencies.append(ConfigUtils.tpl_dependency("free5gc-pcf", "pcf"))
        self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf1", f"smf1"))
        self.chg_sub_chart_name(f"free5gc-smf1")
        for i in range(self.slices_num):
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-upf{i + 1}", f"upf{i + 1}"))


class SliceNetModeThree(CommonSliceNet):
    """
    Select nearby UPF according to the connected gNodeB
    """
    def __init__(self, slices_num, dnn_names, area_num, path="5gc_mode3"):
        super().__init__(path)
        self.area_num = area_num
        plmn = PLMN("999", "70")
        supported_plmns = [plmn]

        nssais = [NSSAI() for _ in range(slices_num)]
        nssai_in_plmn = NssaiInPlmn(plmn, nssais)
        support_plmn_list = [nssai_in_plmn]
        supported_dnn_list = dnn_names
        self.slices_num = slices_num
        self.amf_list.append(AUSF("ausf", supported_plmns))
        self.nrf_list.append(NRF("nrf", plmn))
        self.nssf_list.append(NSSF("nssf", supported_plmns, support_plmn_list))

        for i in range(self.area_num):
            locality = f"area{i + 1}"
            amf_id = AMF.random_amf_id()
            guami = Guami(plmn, amf_id)
            served_guami_list = [guami]
            tai = TAI(plmn)
            support_tai_list = [tai]
            amf = AMF(f"amf{i + 1}", served_guami_list, support_tai_list,
                      support_plmn_list, supported_dnn_list, locality=locality)
            self.amf_list.append(amf)
            self.pcf_list.append(PCF(f"pcf{i + 1}", locality=locality))
            pfcp = PfcpForSMF()
            dnn_info = DnnInfo(dnn_names[0], "8.8.8.8", "2001:4860:4860::8888")
            dnn_infos = [dnn_info]
            nssai_info = SnssaiInfo(nssais[0], dnn_infos)
            nssai_infos = [nssai_info]
            pool, static_pool = self.net_spliter.split()
            dnn_upf_info = DnnUpfInfo(dnn_names[0], pool, static_pool)
            dnn_upf_infos = [dnn_upf_info]
            snssai_upf_info = SnssaiUpfInfo(nssais[0], dnn_upf_infos)
            snssai_upf_infos = [snssai_upf_info]
            interface = Interface("", dnn_names[0])
            interfaces = [interface]
            up_node = PSAUpfNode(f"upf{i + 1}", snssai_upf_infos, interfaces)
            up_nodes = [up_node]
            link = Link("gNB1", up_node.name.upper())
            links = [link]
            smf = SMF(f"smf{i + 1}", nssai_infos, supported_plmns, pfcp, up_nodes, links, locality=locality)
            self.smf_list.append(smf)
            pfcp = PfcpForUPF()
            dnn = DNN(dnn_names[0], pool)
            upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            self.upf_list.append(upf)

    def copy_specific_charts(self):
        for i in range(self.area_num):
            ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf{i + 1}")
            ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf{i + 1}")
            ConfigUtils.copy_folder("charts/free5gc-smf-ulcl", f"{self.path}/free5gc-smf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")

    def update_dependency(self):
        for i in range(self.area_num):
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-amf{i + 1}", f"amf{i + 1}"))
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-pcf{i + 1}", f"pcf{i + 1}"))
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf{i + 1}", f"smf{i + 1}"))
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-upf{i + 1}", f"upf{i + 1}"))
            self.chg_sub_chart_name(f"free5gc-upf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-smf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-amf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-pcf{i + 1}")


class SliceNetModeFour(CommonSliceNet):

    def __init__(self, slices_num, dnn_names, path="5gc_mode4"):
        super().__init__(path)
        amf_id = AMF.random_amf_id()
        plmn = PLMN("999", "70")
        supported_plmns = [plmn]
        guami = Guami(plmn, amf_id)
        served_guami_list = [guami]
        tai = TAI(plmn)
        support_tai_list = [tai]
        nssais = [NSSAI() for _ in range(slices_num)]
        nssai_in_plmn = NssaiInPlmn(plmn, nssais)
        support_plmn_list = [nssai_in_plmn]
        supported_dnn_list = dnn_names
        self.slices_num = slices_num
        self.amf_list.append(AMF("amf", served_guami_list, support_tai_list, support_plmn_list, supported_dnn_list))
        self.amf_list.append(AUSF("ausf", supported_plmns))
        self.nrf_list.append(NRF("nrf", plmn))
        self.nssf_list.append(NSSF("nssf", supported_plmns, support_plmn_list))
        net_spliter = NetSpliter("10.60.0.0", "16")
        # TODO: 配置切片与垂直行业网络对应
        for i in range(self.slices_num):
            pfcp = PfcpForSMF()
            dnn_info = DnnInfo(dnn_names[i], "8.8.8.8", "2001:4860:4860::8888")
            dnn_infos = [dnn_info]
            nssai_info = SnssaiInfo(nssais[i], dnn_infos)
            nssai_infos = [nssai_info]
            pool, static_pool = net_spliter.split()
            dnn_upf_info = DnnUpfInfo(dnn_names[i], pool, static_pool)
            dnn_upf_infos = [dnn_upf_info]
            snssai_upf_info = SnssaiUpfInfo(nssais[i], dnn_upf_infos)
            snssai_upf_infos = [snssai_upf_info]
            interface = Interface("", dnn_names[i])
            interface2 = Interface("", dnn_names[i], "N9")
            interfaces = [interface, interface2]
            iup_node = IUpfNode(f"iupf{i+1}", snssai_upf_infos, interfaces)
            interface3 = Interface("", dnn_names[i], "N9")
            interfaces2 = [interface3]
            psa_up_node = PSAUpfNode(f"psaupf{i+1}", snssai_upf_infos, interfaces2)
            up_nodes = [iup_node, psa_up_node]
            link1 = Link("gNB1", iup_node.name.upper())
            link2 = Link(iup_node.name.upper(), psa_up_node.name.upper())
            links = [link1, link2]
            smf = SMF(f"smf{i + 1}", nssai_infos, supported_plmns, pfcp, up_nodes, links, ulcl=True)
            self.smf_list.append(smf)
            pfcp = PfcpForUPF()
            dnn = DNN(dnn_names[i], pool)
            i_upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            psa_upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            self.upf_list.append(i_upf)
            self.upf_list.append(psa_upf)

    def copy_specific_charts(self):
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf")
        for i in range(self.slices_num):
            ConfigUtils.copy_folder(f"charts/free5gc-smf-ulcl", f"{self.path}/free5gc-smf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-iupf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-psaupf{i + 1}")

    def update_dependency(self):
        self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-amf", f"amf"))
        self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-pcf", f"pcf"))
        for i in range(self.slices_num):
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf{i + 1}", f"smf{i + 1}"))
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-iupf{i + 1}", f"iupf{i + 1}"))
            self.dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-psaupf{i + 1}", f"psaupf{i + 1}"))
            self.chg_sub_chart_name(f"free5gc-iupf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-psaupf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-smf{i + 1}")

