import socket

port = 50002

sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sck.bind(("0.0.0.0", 55555))

while True:
    clients = []

    while True:
        data, address = sck.recvfrom(128)

        print(f"connection from {address}")
        clients.append(address)

        sck.sendto(b"ready", address)

        if len(clients) == 2:
            print("got 2 clients, sending details to each")
            break
    c1 = clients.pop()
    c1_address, c1_port = c1
    c2 = clients.pop()
    c2_address, c2_port = c2

    sck.sendto(f"{c1_address} {c1_port} {port}".encode(), c1)
    sck.sendto(f"{c2_address} {c2_port} {port}".encode(), c2)

