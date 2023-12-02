from Server import Server
from Client import Client

import sys


print(bin(4|128))

print("PKS - COMMUNICATOR")
mode = ""
user = None
LOCALHOST = False
while mode != "0" and mode != "1":
    print("Choose a mode (0 - Sender , 1 - Receiver)")
    print("To QUIT enter '-1'")
    mode = input(": ")
    if mode == "0":

        user = Client(("localhost", 9000) if LOCALHOST else (input("IP: "), 9000))

    elif mode == "1":

        #user = Server("localhost" if LOCALHOST else input(), 9000 if LOCALHOST else input())

        user = Server()

    elif mode == "-1":
        print("Exiting...")
        sys.exit(0)

while True:
    status = user.start()
    if status == 45 and mode == "0":
        #user = Server("localhost" if LOCALHOST else input(), 9000 if LOCALHOST else input())
        user = Server()
        mode = "1"

    elif status == 45 and mode == "1":
        address = user.client
        user.socket.close()
        user = Client((address[0], 9000))
        mode = "0"

    elif status == 1:
        print("Exiting...")
        sys.exit(0)

    elif status == 2:
        print("Client Timed-out, Exiting...")
        sys.exit(0)