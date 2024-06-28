# AMF configuration
servedGuamiList = [
    {
        "plmnId": {"mcc": 999, "mnc": 70},
        "amfId": "cafe00"
    }
]
supportTaiList = [
    {
        "plmnId": {"mcc": 999, "mnc": 70},
        "tac": "000001"
    }
]
plmnSupportList = [
    {
        "plmnId": {"mcc": 999, "mnc": 70},
        "snssaiList": [
            {"sst": 1, "sd": "ffffff"},
            {"sst": 1, "sd": "010203"},
            {"sst": 1, "sd": "112233"}
        ]
    }
]
supportDnnList = ["internet", "MEC"]
networkName = {
    "full": "Gradiant5G",
    "short": "G5G"
}

# NSSF configuration
supportedPlmnList = [{"mcc": 999, "mnc": 70}]
supportedNssaiInPlmnList = [
    {
        "plmnId": {"mcc": 999, "mnc": 70},
        "supportedSnssaiList": [
            {"sst": 1, "sd": "ffffff"},
            {"sst": 1, "sd": "010203"},
            {"sst": 1, "sd": "112233"}
        ]
    }
]

# SMF configuration
snssaiInfos = [
    {
        "sNssai": {
            "sst": 1,
            "sd": "010203"
        },
        "dnnInfos": [
            {
                "dnn": "internet",
                "dns": {
                    "ipv4": "8.8.8.8",
                    "ipv6": "2001:4860:4860::8888"
                }
            }
        ]
    }
]
plmnList = [
    {
        "mcc": 999,
        "mnc": 70
    }
]
userplaneInformation_upNodes = {
    "UPF": {
        "nodeID": "",
        "addr": "",
        "sNssaiUpfInfos": [
            {
                "sNssai": {
                    "sst": 1,
                    "sd": "010203"
                },
                "dnnUpfInfoList": [
                    {
                        "dnn": "internet",
                        "pools": [{"cidr": "10.60.0.0/16"}],
                        "staticPools": [{"cidr": "10.60.100.0/24"}]
                    }
                ]
            }
        ],
        "interfaces": {
            "endpoints": "",
            "networkInstances": "internet"
        }
    }
}

# UPF configuration
dnnList = [
    {
        "dnn": "internet",
        "cidr": "10.60.0.0/24"
    }
]