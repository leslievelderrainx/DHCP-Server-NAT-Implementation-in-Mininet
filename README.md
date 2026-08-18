# DHCP Server & NAT Implementation in Mininet

A custom DHCP server and NAT-enabled network implemented using Python and Mininet. 
The project simulates a multi-router network in which clients dynamically obtain 
IPv4 addresses through DHCP and communicate with an external network through NAT.

## Overview

The project consists of two main components:

- **DHCP Server:** A Python-based DHCP server that handles DHCPDISCOVER and 
  DHCPREQUEST messages and responds with DHCPOFFER and DHCPACK messages.
- **Mininet Network:** A simulated network containing multiple clients, a switch, 
  two Linux routers, and an external server.

## Network Topology

       Server
          |
       Router 1
          |
       Router 0
          |
        Switch
      /  /  \  \
    Client0 Client1 Client2 Client3

The client LAN uses the `192.168.1.0/24` network. client0 uses a static IPv4 address, while client1, client2, and client3 obtain their network configuration dynamically from the DHCP server.

## NAT Configuration

NAT was configured on `router1` using IP masquerading to allow clients on the 
private `192.168.1.0/24` LAN to communicate with the external `10.0.0.0/24` network.

Traffic from the private LAN was routed through `router0` and then translated by 
`router1` before reaching the external server. NAT functionality was verified 
using `tcpdump` on the WAN interface of `router1`, confirming that packets reaching 
the external network used `router1`'s `10.0.0.1` address rather than the clients' 
private `192.168.1.x` addresses.

## Features

- Dynamically assigns IPv4 addresses from a predefined address pool
- Tracks client leases using MAC addresses
- Supports DHCP DISCOVER, OFFER, REQUEST, and ACK messages
- Supports DHCP lease renewal
- Provides clients with a subnet mask and default gateway
- Enables IP forwarding between simulated networks
- Uses NAT to allow private LAN clients to communicate with the external network

## Technologies

- Python
- Mininet
- Linux
- UDP sockets
- DHCP
- IPv4
- NAT
- iptables
- tcpdump
- dhclient

## Testing

The implementation was tested within Mininet using tools including:

- `dhclient` to request and renew DHCP leases
- `ping` to verify connectivity between hosts
- `tcpdump` to inspect DHCP traffic and verify NAT behavior

Testing confirmed that clients could dynamically obtain IP addresses and 
communicate across the simulated network.
