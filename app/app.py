from flask import Flask
from flask import request
import json
import socket
import threading

app = Flask(__name__)


class PortScan:
    def __init__(self, target, port_list):
        self.target = target
        self.port_list = port_list

        self.result = dict()

    def scan(self):

        thread_list = list()

        for port in self.port_list:
            t = threading.Thread(target=self.run, args=(port,))
            t.start()
            thread_list.append(t)

        for t in thread_list:
            t.join()

    def run(self, current_port):
        socket.setdefaulttimeout(1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)

        result = s.connect_ex((self.target, current_port))
        self.result[current_port] = (result == 0)
        s.close()


@app.route('/')
def get():
    ip = request.args.get('ip')
    port = request.args.get('port')

    result = dict()

    result['ip'] = ip
    port_list = port.split(',')
    port_list = list(map(int, port_list))

    port_scan = PortScan(ip, port_list)
    port_scan.scan()

    result['result'] = port_scan.result

    return json.dumps(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)

    # port_scan = PortScan(
    #     # '192.168.3.2',
    #     'www.google.com',
    #     [443, 80, 234]
    # )
    #
    # port_scan.scan()
    # print(port_scan.result)
