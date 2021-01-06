from flask import Flask
from flask import request
from flask import jsonify

import socket
import threading
import re

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

        try:
            result = s.connect_ex((self.target, current_port))
            self.result[current_port] = (result == 0)
        except TypeError:
            pass
        except socket.gaierror:
            self.result[current_port] = False
        finally:
            s.close()


def check_url(url):
    import re
    regex = re.compile(
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return (re.match(regex, url) is not None)


@app.route('/')
def get():
    ip = request.args.get('ip')
    if not check_url(ip):
        return jsonify(error=f'invalid url: {ip}'), 400, {'ContentType': 'application/json'}
    port = request.args.get('port')

    result = dict()

    result['ip'] = ip
    ports = port.split(',')
    # port_list = list(map(int, port_list))
    port_list = list()
    for port in ports:
        try:
            port_list.append(int(port))
        except ValueError as e:
            # bad request
            return jsonify(error=str(e)), 400, {'ContentType': 'application/json'}

    port_scan = PortScan(ip, port_list)
    port_scan.scan()

    result['result'] = port_scan.result

    return jsonify(result), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)

    # port_scan = PortScan(
    #     # '192.168.3.2',
    #     'www.google.com',
    #     ['sjkdf', 80, 234]
    # )
    #
    # port_scan.scan()
    # print(port_scan.result)
