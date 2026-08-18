from mininet.topo import Topo
from mininet.node import Node

class LinuxRouter(Node):
    """
    A Node with IP forwarding enabled.
    This is necessary for the node to act as a router.
    """
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class LabTopo(Topo):
    def build(self):
        # 1. Create Nodes
        # We set ip=None so Mininet doesn't auto-assign 10.0.0.x IPs
        
        # Server
        server = self.addHost('server', ip=None)
        
        # Routers (using custom LinuxRouter class)
        r1 = self.addNode('router1', cls=LinuxRouter, ip=None)
        r0 = self.addNode('router0', cls=LinuxRouter, ip=None)
        
        # Switch (transparent)
        s1 = self.addSwitch('s1')

        # Clients
        c0 = self.addHost('client0', ip=None)
        c1 = self.addHost('client1', ip=None)
        c2 = self.addHost('client2', ip=None)
        c3 = self.addHost('client3', ip=None)

        # 2. Create Links
        
        # Internet link: Server <-> Router1
        self.addLink(server, r1)
        
        # Backbone link: Router1 <-> Router0
        self.addLink(r1, r0)
        
        # LAN Gateway link: Router0 <-> Switch
        self.addLink(r0, s1)
        
        # LAN Client links: Switch <-> Clients
        self.addLink(s1, c0)
        self.addLink(s1, c1)
        self.addLink(s1, c2)
        self.addLink(s1, c3)

# Register the topology so 'mn' can find it
topos = { 'labtopo': (lambda: LabTopo()) }