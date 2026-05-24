#!/usr/bin/env python3
import argparse
import socket
import threading
import time
from contextlib import closing

try:
    from zeroconf import IPVersion, ServiceInfo, Zeroconf
except ImportError:
    IPVersion = None
    ServiceInfo = None
    Zeroconf = None

MDNS_GROUP = "224.0.0.251"
MDNS_PORT = 5353


def local_ip() -> str:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


def encode_name(name: str) -> bytes:
    return b"".join(bytes([len(part)]) + part.encode("ascii") for part in name.rstrip(".").split(".")) + b"\0"


def decode_name(packet: bytes, offset: int) -> tuple[str, int]:
    labels = []
    jumped = False
    end = offset
    while True:
        length = packet[offset]
        if length == 0:
            offset += 1
            if not jumped:
                end = offset
            break
        if length & 0xC0 == 0xC0:
            pointer = ((length & 0x3F) << 8) | packet[offset + 1]
            if not jumped:
                end = offset + 2
            offset = pointer
            jumped = True
            continue
        offset += 1
        labels.append(packet[offset : offset + length].decode("ascii", errors="ignore"))
        offset += length
        if not jumped:
            end = offset
    return ".".join(labels).lower(), end


def mdns_hostname_responder(name: str) -> None:
    target = f"{name}.local"
    answer_name = encode_name(target)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.bind(("", MDNS_PORT))
        group = socket.inet_aton(MDNS_GROUP) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group)

        while True:
            packet, source = sock.recvfrom(9000)
            if len(packet) < 12:
                continue
            question_count = int.from_bytes(packet[4:6], "big")
            offset = 12
            questions = []
            for _ in range(question_count):
                qname, offset = decode_name(packet, offset)
                if offset + 4 > len(packet):
                    break
                qtype = int.from_bytes(packet[offset : offset + 2], "big")
                qclass = int.from_bytes(packet[offset + 2 : offset + 4], "big")
                offset += 4
                questions.append((qname, qtype, qclass))

            if not any(qname == target and qtype in (1, 28, 255) for qname, qtype, _ in questions):
                continue

            question_bytes = b"".join(
                encode_name(qname) + qtype.to_bytes(2, "big") + qclass.to_bytes(2, "big")
                for qname, qtype, qclass in questions
            )
            answer = (
                answer_name
                + (1).to_bytes(2, "big")
                + (0x8001).to_bytes(2, "big")
                + (120).to_bytes(4, "big")
                + (4).to_bytes(2, "big")
                + socket.inet_aton(local_ip())
            )
            response = (
                packet[:2]
                + b"\x84\x00"
                + len(questions).to_bytes(2, "big")
                + (1).to_bytes(2, "big")
                + b"\x00\x00\x00\x00"
                + question_bytes
                + answer
            )
            sock.sendto(response, (MDNS_GROUP, MDNS_PORT))
            sock.sendto(response, source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="printora")
    parser.add_argument("--port", type=int, default=8085)
    args = parser.parse_args()

    host = f"{args.name}.local."
    service_name = f"{args.name}._http._tcp.local."
    ip = local_ip()
    threading.Thread(target=mdns_hostname_responder, args=(args.name,), daemon=True).start()
    zeroconf = None
    info = None
    if Zeroconf and ServiceInfo and IPVersion:
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        info = ServiceInfo(
            "_http._tcp.local.",
            service_name,
            addresses=[socket.inet_aton(ip)],
            port=args.port,
            properties={"path": "/"},
            server=host,
        )
        zeroconf.register_service(info)
    print(f"announcing http://{args.name}.local:{args.port}/ at {ip}:{args.port}", flush=True)
    try:
        while True:
            time.sleep(15)
            current_ip = local_ip()
            if current_ip == ip:
                continue
            ip = current_ip
            if zeroconf and info and ServiceInfo:
                zeroconf.unregister_service(info)
                info = ServiceInfo(
                    "_http._tcp.local.",
                    service_name,
                    addresses=[socket.inet_aton(ip)],
                    port=args.port,
                    properties={"path": "/"},
                    server=host,
                )
                zeroconf.register_service(info)
            print(f"announcing http://{args.name}.local:{args.port}/ at {ip}:{args.port}", flush=True)
    finally:
        if zeroconf and info:
            zeroconf.unregister_service(info)
            zeroconf.close()


if __name__ == "__main__":
    raise SystemExit(main())
