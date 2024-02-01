import socket
import re


def resolve_host(hostname):
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.error as err:
        print(f"Cannot resolve hostname {hostname}: {err}")
        return None


def validate_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def validate_hostname(hostname):
    if len(hostname) > 255 or len(hostname) == 0:
        return False
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


if __name__ == "__main__":
    # Test the functions
    print(resolve_host("google.com"))  # Should return the IP of google.com
    print(validate_ip("192.168.1.1"))  # Should return True
    print(validate_hostname("example.com"))  # Should return True
