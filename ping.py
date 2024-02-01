import os
import socket
import struct
import select
import time
import argparse
from utils import resolve_host, validate_ip, validate_hostname

# Constants
ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
DEFAULT_TIMEOUT = 1
DEFAULT_COUNT = 4


def checksum(source_string):
    sum = 0
    count_to = (len(source_string) // 2) * 2
    for count in range(0, count_to, 2):
        this_val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + this_val
        sum = sum & 0xffffffff

    if count_to < len(source_string):
        sum = sum + source_string[-1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receive_one_ping(sock, ID, timeout):
    time_remaining = timeout
    while True:
        start_time = time.time()
        readable = select.select([sock], [], [], time_remaining)
        time_spent = (time.time() - start_time)
        if readable[0] == []:  # Timeout
            return

        time_received = time.time()
        recv_packet, addr = sock.recvfrom(1024)

        icmp_header = recv_packet[20:28]
        type, code, checksum, packet_ID, sequence = struct.unpack(
            "bbHHh", icmp_header
        )
        if packet_ID == ID:
            bytes_in_double = struct.calcsize("d")
            time_sent = struct.unpack("d", recv_packet[28:28 + bytes_in_double])[0]
            return time_received - time_sent

        time_remaining = time_remaining - time_spent
        if time_remaining <= 0:
            return


def send_one_ping(sock, dest_addr, ID):
    dest_addr = socket.gethostbyname(dest_addr)

    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    data = struct.pack("d", time.time()) + bytes(48)

    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)

    # Recreate the header with the correct checksum and pack the final packet
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)
    packet = header + data
    sock.sendto(packet, (dest_addr, 1))


def do_one_ping(dest_addr, timeout=DEFAULT_TIMEOUT):
    icmp = socket.getprotobyname("icmp")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error as e:
        if e.errno == 1:
            e.msg += " ICMP messages can only be sent from processes running as root."
            raise socket.error(e.msg)
    except Exception as e:
        print("Exception: {}".format(e))

    my_ID = os.getpid() & 0xFFFF

    resolved_addr = resolve_host(dest_addr)  # Resolve the hostname to an IP address
    if resolved_addr is None:
        return None

    send_one_ping(sock, resolved_addr, my_ID)
    delay = receive_one_ping(sock, my_ID, timeout)

    sock.close()
    return delay


def verbose_ping(dest_addr, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
    sent_pings = 0
    received_pings = 0
    total_time = 0.0

    for i in range(count):
        print(f"Pinging {dest_addr}...")
        sent_pings += 1
        try:
            delay = do_one_ping(dest_addr, timeout)
        except socket.gaierror as e:
            print(f"Failed. (socket error: '{e[1]}')")
            continue

        if delay is None:
            print(f"Ping Timed out. (timeout within {timeout}s)")
        else:
            delay_ms = delay * 1000
            total_time += delay_ms
            received_pings += 1
            print(f"Received ping in {delay_ms:.4f}ms")

    print(f"{sent_pings} packets transmitted, {received_pings} packets received.")

    if received_pings > 0:
        average_time = total_time / received_pings
        print(f"Average round-trip time: {average_time:.4f}ms")
        packet_loss = ((sent_pings - received_pings) / sent_pings) * 100
        print(f"Packet loss: {packet_loss:.2f}%")
    else:
        print("No response received.")


def parse_arguments():
    parser = argparse.ArgumentParser(description='A simple Python ping command implementation.')
    parser.add_argument('destination', type=str, help='The IP address or domain to ping.')
    parser.add_argument('-c', '--count', type=int, default=DEFAULT_COUNT, help='Number of pings to perform.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    # Validate the destination input
    if validate_ip(args.destination) or validate_hostname(args.destination):
        verbose_ping(args.destination, count=args.count)
    else:
        print("Invalid IP address or hostname.")
