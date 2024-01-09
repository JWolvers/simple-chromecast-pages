import pychromecast
from pychromecast.controllers import dashcast
import time
import signal
import socket
import threading
import os
import sys

class ChromecastApp:
    def __init__(self):
        self.current_number = 0
        self.d = None
        self.cast = None
        self.setup_chromecast()
        self.start_server_thread()

    def setup_chromecast(self):
        chromecasts = pychromecast.get_chromecasts()
        if not chromecasts:
            print('No Chromecast found')
            exit(0)

        self.cast = chromecasts[0][0]
        self.cast.wait()
        print(f'Connected to Chromecast: {self.cast.name}')

        self.d = dashcast.DashCastController()
        self.cast.register_handler(self.d)

        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

        self.update_url()

    def update_url(self):
        self.d.load_url(
            f"https://jwolvers.github.io/simple-chromecast-pages/queue?current={self.current_number}",
            callback_function=lambda result: print(f"Reloaded URL with current={self.current_number}")
        )

    def handle_client_connection(self, client_socket):
        request = client_socket.recv(1024)
        msg = request.decode()
        print(f'Received: {msg}')
        if msg == '+':
            self.current_number += 1
            self.update_url()
        elif msg == '-':
            self.current_number -= 1
            self.update_url()
        elif msg.isdecimal():
            self.current_number = int(msg)
            self.update_url()
        client_socket.close()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', 8000))
        server.listen(5)
        print('Listening on localhost:8000')
        while True:
            client_sock, address = server.accept()
            print(f'Accepted connection from {address[0]}:{address[1]}')
            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_sock,)
            )
            client_handler.start()

    def start_server_thread(self):
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

    def shutdown_handler(self, signum, frame):
        print('Shutting down...')
        os._exit(0)

def check_server_running():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 8000))
        if len(sys.argv) > 1:
            message = sys.argv[1].encode()
            client_socket.sendall(message)
        else:
            client_socket.sendall(b'+')
        client_socket.close()
        return True
    except ConnectionError:
        return False

if __name__ == '__main__':
    if not check_server_running():
        print('No app running, starting server!')
        app = ChromecastApp()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            app.shutdown_handler(None, None)
    else:
        print("Another instance is running. Sent signal to increase waiting count.")
