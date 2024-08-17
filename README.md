# 5GSliceNet

5GSliceNet, an open-source project that aims to develop a tool to design 5G core slices, 
provides an easy-to-use, cross-platform, automatic solution for multi-slice network research. 
5GSliceNet generates a slices network deployment files according to the user's requirements. Its network components are from 
[UERANSIM](https://github.com/aligungr/UERANSIM) and [Free5GC](https://github.com/free5gc/free5gc).

## Overview

5GSliceNet supports the following four slice forms:

| Mode | Description                                                                       | Common Network Functions | Specific Network Functions | Other Network Functions |
| --- |-----------------------------------------------------------------------------------|--------------------------|----------------------------|-------------------------|
| 1 | N Slices = n × (1 UPF + 1 SMF)                                                    | AMF、AUSF、NRF、NSSF        | UPF、SMF                    | CHF、UDR、UDM、PCF         |
| 2 | N Slices = n × (1 UPF)                                                            | AMF、AUSF、NRF、NSSF、SMF    | UPF                        | CHF、UDR、UDM、PCF         |
| 3 | Select nearby UPF according to the connected gNodeB (Multiple areas in one slice) | AUSF、NRF、NSSF            | AMF、PCF、SMF、UPF            | CHF、UDR、UDM             |
| 4 | ULCL                                                                              | AMF、AUSF、NRF、NSSF        | SMF、UPF                    | CHF、UDR、UDM、PCF         |
| 5 | Mixed                                                                             | -                        | -                          | -                       |

![](./resources/slicenet.png)

## Getting Started


### Prerequisites
- Kubernetes
- Docker
- Helm

### How to use
1. Pull the basic charts from the repository:
2. Generate the network deployment files:
3. Deploy the 5g slicenet charts:
