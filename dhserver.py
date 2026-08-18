from socket import *
import time
import struct

DHCP_SERVER = ('', 67)
DHCP_CLIENT = ('192.168.1.255', 68)
# DHCP_CLIENT = ('255.255.255.255', 68)

SERVER_IP = "192.168.1.1"
LEASE_TIME = 60

ip_pool = ["192.168.1.{}".format(i) for i in range(50, 151) if i != 100]

leases = {}

def get_ciaddr(msg):
    # bytes 12–15 in DHCP header
    return inet_ntoa(msg[12:16])

def build_ack(request_msg, yiaddr, server_ip):
    pkt = bytearray(build_offer(request_msg, yiaddr, server_ip))

    # change DHCP message type from OFFER (2) to ACK (5)
    if len(pkt) >= 243 and pkt[240] == 53 and pkt[241] == 1:
        pkt[242] = 5       # ACK

    return pkt

def get_requested_ip(msg):
    i = 240
    while i < len(msg):
        option = msg[i]
        if option == 255:  
            break
        if option == 0:     
            i += 1
            continue
        if i + 1 >= len(msg):
            break
        length = msg[i + 1]
        if i + 2 + length > len(msg):
            break
        if option == 50:   
            return msg[i + 2 : i + 2 + length]
        i += 2 + length
    return None


def build_offer(request_msg, yiaddr, server_ip):

    # start from a copy of the client's packet 
    pkt = bytearray(request_msg)

    # make sure the packet is at least 240 bytes 
    if len(pkt) < 240:
        pkt.extend(b'\x00' * (240 - len(pkt)))

    # operation code: 2 = BOOTREPLY (server to client)
    pkt[0] = 2

    # client IP address = 0.0.0.0 for DISCOVER/OFFER
    pkt[12:16] = b'\x00\x00\x00\x00'

    # the IP address we are offering
    pkt[16:20] = inet_aton(yiaddr)

    # server IP address
    pkt[20:24] = inet_aton(server_ip)

    # giaddr (not used)
    pkt[24:28] = b'\x00\x00\x00\x00'

    # ensure bytes 236–239 is correct
    pkt[236:240] = b'\x63\x82\x53\x63'

    # throw away any old options after 240
    pkt = pkt[:240]

    # build a set of DHCP options
    options = bytearray()

    # option 53: DHCP message type = 2 (OFFER)
    options += b'\x35\x01\x02'

    # option 54: Server identifier 
    options += b'\x36\x04' + inet_aton(server_ip)

    # option 51: Lease time
    options += b'\x33\x04' + struct.pack('!I', LEASE_TIME)

    # option 1: Subnet mask
    options += b'\x01\x04' + inet_aton("255.255.255.0")

    # option 3: Default gateway (router)
    options += b'\x03\x04' + inet_aton(server_ip)

    # option 255: End
    options += b'\xff'

    return pkt + options

def get_dhcp_type(msg):
    i = 240
    while i < len(msg):
        option = msg[i]
        if option == 255:
            break
        if option == 0:
            i += 1
            continue
        if i + 1 >= len(msg):
            break
        length = msg[i + 1]
        if i + 2 + length > len(msg):
            break
        if option == 53:
            return msg[i + 2]
        i += 2 + length
    return None

def choose_ip_for(mac_str):
   # get current time
   now = time.time()

   if mac_str in leases:
       lease = leases[mac_str]
       if lease["expires"] > now:
           lease["expires"] = now + LEASE_TIME
           return lease["ip"]
       
   if not ip_pool:
        return None
   
   ip = ip_pool.pop(0)

   leases[mac_str] = {
         "ip": ip,
         "expires": now + LEASE_TIME
    }
   
   return ip

# Create a UDP socket
s = socket(AF_INET, SOCK_DGRAM)

# Allow socket to broadcast messages
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

# Bind socket to the well-known port reserved for DHCP servers
s.bind(DHCP_SERVER)

while True: 
    # Receive a UDP message
    msg, addr = s.recvfrom(1024)

    # determine the DHCP message type
    mtype = get_dhcp_type(msg)
    if mtype is None:
        print("Received a DHCP message with no type, ignoring.")
        continue
    if mtype == 1:
        print("Received a DHCP DISCOVER message.")
    elif mtype == 3:
        print("Received a DHCP REQUEST message.")
    else:
        print("Received DHCP message type {} [not handled yet]".format(mtype))
        continue

    # Print the client's MAC Address from the DHCP header
    print("Client's MAC Address is " + format(msg[28], 'x'), end='')
    for i in range(29, 34):
        print(":" + format(msg[i], 'x'), end='')
    print()

    mac_str = ":".join(format(b, 'x') for b in msg[28:34])

    # handle DISCOVER
    if mtype == 1:
        offered_ip = choose_ip_for(mac_str)
        if offered_ip is None:
            print("No IP left in pool!")
            continue

        print("Sending DHCPOFFER:", offered_ip)
        offer_pkt = build_offer(msg, offered_ip, SERVER_IP)
        s.sendto(offer_pkt, DHCP_CLIENT)
        continue

    # handle REQUEST
    if mtype == 3:
        req_ip_bytes = get_requested_ip(msg)
        if req_ip_bytes is not None:
            requested_ip = inet_ntoa(req_ip_bytes)
            print("Client requested IP via option 50:", requested_ip)
        else:
            # this is probably a renewal.
            ciaddr = get_ciaddr(msg)
            print("No option 50, ciaddr is:", ciaddr)

            if ciaddr == "0.0.0.0":
                # ignore.
                print("REQUEST has neither option 50 nor ciaddr set; ignoring.")
                continue

            # treat ciaddr as the requested IP for renewal
            requested_ip = ciaddr
            print("Treating ciaddr as requested IP (renewal):", requested_ip)

        lease = leases.get(mac_str)
        if lease is None or lease["ip"] != requested_ip:
            print("Requested IP does not match lease — ignoring REQUEST.")
            continue

        print("Sending DHCPACK:", requested_ip)
        lease["expires"] = time.time() + LEASE_TIME
        ack_pkt = build_ack(msg, requested_ip, SERVER_IP)
        s.sendto(ack_pkt, DHCP_CLIENT)

    # Send a UDP message (Broadcast)
    #s.sendto(b'Hello World!', DHCP_CLIENT)