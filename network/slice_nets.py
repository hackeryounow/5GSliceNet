import abc
import copy

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
        return reduce(lambda d1, d2: {**d1, **d2}, nf_list)

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

    def configure(self):
        ConfigUtils.delete_folder(self.path)
        ConfigUtils.delete_folder(self.values_path)
        self.copy_charts()
        self._update_chart_yaml()
        self.save_values_yaml()

    @abc.abstractmethod
    def copy_charts(self):
        pass

    def _update_chart_yaml(self):
        chart_path = f"{self.path}/free5gc/Chart.yaml"
        chart_yaml = ConfigUtils.load_yaml(chart_path)
        chart_yaml["dependencies"].extend(self.update_dependency())
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
        chart_path = f"{self.path}/{chart_name}/Chart.yaml"
        chart_yaml = ConfigUtils.load_yaml(chart_path)
        # ConfigUtils.delete_folder(chart_path)
        chart_yaml["name"] = chart_name
        ConfigUtils.write_yaml(chart_yaml, chart_path)


class SliceNetModeOne(CommonSliceNet):
    def __init__(self, slices_num, dnn_names, path="5gc_mode1"):
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
        self.ausf_list.append(AUSF("ausf", supported_plmns))
        self.pcf_list.append(PCF("pcf"))
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
            interfaces = [interface]
            gnb = GnbNode("gNB1")
            up_node = PSAUpfNode("upf", snssai_upf_infos, interfaces)
            up_nodes = [gnb, up_node]
            link = Link("gNB1", f"UPF")
            links = [link]
            smf = SMF(f"smf{i + 1}", nssai_infos, supported_plmns, pfcp, up_nodes, links)
            self.smf_list.append(smf)
            pfcp = PfcpForUPF()
            dnn = DNN(dnn_names[i], pool)
            upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            self.upf_list.append(upf)

    def copy_charts(self):
        super().copy_common()
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf")
        for i in range(self.slices_num):
            ConfigUtils.copy_folder(f"charts/free5gc-smf", f"{self.path}/free5gc-smf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-smf{i + 1}")
            self.chg_sub_chart_name(f"free5gc-upf{i + 1}")

    def update_dependency(self):
        dependencies = []
        for i in range(self.slices_num):
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf{i + 1}", f"smf{i + 1}"))
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-upf{i + 1}", f"upf{i + 1}"))
        return dependencies


class CommonSliceNetModeTwo(CommonSliceNet):
    def __init__(self, slices_num, dnn_names, path="5gc_mode2"):
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
        self.amf = AMF("amf", served_guami_list, support_tai_list, support_plmn_list, supported_dnn_list)
        self.ausf = AUSF("ausf", supported_plmns)
        self.nrf = NRF("nrf", plmn)
        self.nssf = NSSF("nssf", supported_plmns, support_plmn_list)
        self.pcf = PCF("pcf")
        net_spliter = NetSpliter("10.70.0.0", "16")

        nssai_infos = []
        self.upf = []
        up_nodes = []
        links = []
        for i in range(self.slices_num):
            dnn_info = DnnInfo(dnn_names[i], "8.8.8.8", "2001:4860:4860::8888")
            dnn_infos = [dnn_info]
            nssai_info = SnssaiInfo(nssais[i], dnn_infos)
            nssai_infos.append(nssai_info)
            pool, static_pool = net_spliter.split()
            dnn_upf_info = DnnUpfInfo(dnn_names[i], pool, static_pool)
            dnn_upf_infos = [dnn_upf_info]
            snssai_upf_info = SnssaiUpfInfo(nssais[i], dnn_upf_infos)
            snssai_upf_infos = [snssai_upf_info]
            interface = Interface("", dnn_names[i])
            interfaces = [interface]
            up_node = PSAUpfNode(f"upf{i + 1}", snssai_upf_infos, interfaces)
            up_nodes.append(up_node)
            links.append(Link(f"gNB1", f"UPF{i + 1}"))
            pfcp = PfcpForUPF()
            dnn = DNN(dnn_names[i], pool)
            upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            self.upf.append(upf)
        pfcp = PfcpForSMF()
        self.smf = SMF("smf", nssai_infos, supported_plmns, pfcp, up_nodes, links)

    def copy_charts(self):
        super().copy_common()
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf")
        ConfigUtils.copy_folder("charts/free5gc-smf", f"{self.path}/free5gc-smf")
        for i in range(self.slices_num):
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")

    def update_dependency(self):
        dependencies = []
        for i in range(self.slices_num):
            dependencies.append(ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}"))
        return dependencies

    def to_dict(self):
        values_yaml = self.amf.to_dict() | self.ausf.to_dict() | self.chf.to_dict() | self.nrf.to_dict() | \
                      self.nssf.to_dict() | self.pcf.to_dict() | self.udm.to_dict() | self.udr.to_dict() | \
                      self.webui.to_dict() | self.mongodb.to_dict() | self.smf.to_dict()
        for i in range(self.slices_num):
            values_yaml = values_yaml | self.upf[i].to_dict()
        ConfigUtils.write_yaml(copy.deepcopy(values_yaml), self.values_path)


class CommonSliceNetModeThree(CommonSliceNet):
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

        self.ausf = AUSF("ausf", supported_plmns)
        self.nrf = NRF("nrf", plmn)
        self.nssf = NSSF("nssf", supported_plmns, support_plmn_list)
        self.amf = []
        self.smf = []
        self.upf = []
        self.pcf = []
        net_spliter = NetSpliter("10.80.0.0", "16")

        for i in range(self.area_num):
            locality = f"area{i + 1}"
            amf_id = AMF.random_amf_id()
            guami = Guami(plmn, amf_id)
            served_guami_list = [guami]
            tai = TAI(plmn)
            support_tai_list = [tai]
            amf = AMF(f"amf{i + 1}", served_guami_list, support_tai_list,
                      support_plmn_list, supported_dnn_list, locality=locality)
            self.amf.append(amf)
            self.pcf.append(PCF(f"pcf{i + 1}", locality=locality))
            pfcp = PfcpForSMF()
            dnn_info = DnnInfo(dnn_names[0], "8.8.8.8", "2001:4860:4860::8888")
            dnn_infos = [dnn_info]
            nssai_info = SnssaiInfo(nssais[0], dnn_infos)
            nssai_infos = [nssai_info]
            pool, static_pool = net_spliter.split()
            dnn_upf_info = DnnUpfInfo(dnn_names[0], pool, static_pool)
            dnn_upf_infos = [dnn_upf_info]
            snssai_upf_info = SnssaiUpfInfo(nssais[0], dnn_upf_infos)
            snssai_upf_infos = [snssai_upf_info]
            interface = Interface("", dnn_names[0])
            interfaces = [interface]
            up_node = PSAUpfNode("upf", snssai_upf_infos, interfaces)
            up_nodes = [up_node]
            link = Link("gNB1", f"UPF")
            links = [link]
            smf = SMF(f"smf{i + 1}", nssai_infos, supported_plmns, pfcp, up_nodes, links, locality=locality)
            self.smf.append(smf)
            pfcp = PfcpForUPF()
            dnn = DNN(dnn_names[0], pool)
            upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            self.upf.append(upf)

    def copy_charts(self):
        super().copy_common()
        for i in range(self.area_num):
            ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf{i + 1}")
            ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf{i + 1}")
            ConfigUtils.copy_folder("charts/free5gc-smf", f"{self.path}/free5gc-smf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")

    def to_dict(self):
        values_yaml = self.ausf.to_dict() | self.chf.to_dict() | self.nrf.to_dict() | \
                      self.nssf.to_dict() | self.udm.to_dict() | self.udr.to_dict() | \
                      self.webui.to_dict() | self.mongodb.to_dict()
        for i in range(self.area_num):
            values_yaml = values_yaml | self.upf[i].to_dict() | self.amf[i].to_dict() | \
                          self.pcf[i].to_dict() | self.smf[i].to_dict()
        ConfigUtils.write_yaml(copy.deepcopy(values_yaml), self.values_path)

    def update_dependency(self):
        dependencies = []
        for i in range(self.area_num):
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-amf{i + 1}", f"free5gc-amf{i + 1}"))
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-pcf{i + 1}", f"free5gc-pcf{i + 1}"))
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf{i + 1}", f"free5gc-smf{i + 1}"))
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-upf{i + 1}", f"free5gc-upf{i + 1}"))
        return dependencies


class CommonSliceNetModeFour(CommonSliceNet):

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
        self.amf = AMF("amf", served_guami_list, support_tai_list, support_plmn_list, supported_dnn_list)
        self.ausf = AUSF("ausf", supported_plmns)
        self.pcf = PCF("pcf")
        self.nrf = NRF("nrf", plmn)
        self.nssf = NSSF("nssf", supported_plmns, support_plmn_list)
        self.smf = []
        self.upf = []
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
            interfaces = [interface]
            iup_node = IUpfNode("iupf", snssai_upf_infos, interfaces)
            psa_up_node = PSAUpfNode("psaupf", snssai_upf_infos, interfaces)
            up_nodes = [iup_node, psa_up_node]
            link1 = Link("gNB1", f"UPF")
            link2 = Link("IUPF", f"PSAUPF")
            links = [link1, link2]
            smf = SMF(f"smf{i + 1}", nssai_infos, supported_plmns, pfcp, up_nodes, links, ulcl=True)
            self.smf.append(smf)
            pfcp = PfcpForUPF()
            dnn = DNN(dnn_names[i], pool)
            upf = UPF(f"upf{i + 1}", pfcp, [dnn])
            self.upf.append(upf)

    def copy_charts(self):
        super().copy_common()
        ConfigUtils.copy_folder("charts/free5gc-amf", f"{self.path}/free5gc-amf")
        ConfigUtils.copy_folder("charts/free5gc-pcf", f"{self.path}/free5gc-pcf")
        for i in range(self.slices_num):
            ConfigUtils.copy_folder(f"charts/free5gc-smf", f"{self.path}/free5gc-smf{i + 1}")
            ConfigUtils.copy_folder(f"charts/free5gc-upf", f"{self.path}/free5gc-upf{i + 1}")

    def update_dependency(self):
        dependencies = []
        for i in range(self.slices_num):
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-smf{i + 1}", f"free5gc-smf{i + 1}"))
            dependencies.append(ConfigUtils.tpl_dependency(f"free5gc-upf{i + 1}", f"free5gc-upf{i + 1}"))
        return dependencies

    def to_dict(self):
        values_yaml = self.amf.to_dict() | self.ausf.to_dict() | self.chf.to_dict() | self.nrf.to_dict() | \
                      self.nssf.to_dict() | self.pcf.to_dict() | self.udm.to_dict() | self.udr.to_dict() | \
                      self.webui.to_dict() | self.mongodb.to_dict()
        for i in range(self.slices_num):
            values_yaml = values_yaml | self.smf[i].to_dict()
            values_yaml = values_yaml | self.upf[i].to_dict()
        ConfigUtils.write_yaml(copy.deepcopy(values_yaml), "values4.yaml")
