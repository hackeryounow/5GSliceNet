import ipaddress


class NetSpliter:
    def __init__(self, ip_network, mask):
        self.ip_network = ip_network
        self.mask = mask
        self.network = ipaddress.IPv4Network(f"{self.ip_network}/{self.mask}", strict=False)
    def _next_network(self):
        network_int = int(self.network.network_address)
        next_network_int = network_int + self.network.num_addresses
        next_network_address = ipaddress.IPv4Address(next_network_int)
        self.ip_network = str(next_network_address)
        self.network = ipaddress.IPv4Network(f"{self.ip_network}/{self.mask}", strict=False)
        return str(self.network)

    def _next_static_pool(self, prefixlen_diff=4):
        subnets = self.network.subnets(prefixlen_diff=prefixlen_diff)
        next(subnets)
        static_pool = next(subnets)
        return str(static_pool)

    def split(self):
        return self._next_network(), self._next_static_pool()





