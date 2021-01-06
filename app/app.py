from flask import Flask
from flask import request
from flask import jsonify

import socket
import threading
import re

app = Flask(__name__)


class PortScan:
    def __init__(self, target, port_list):

        if target.startswith('https://'):
            target = target[len('https://'):]
        elif target.startswith('http://'):
            target = target[len('http://'):]

        self.target = target
        self.port_list = port_list

        self.result = dict()

    def check_url(self):
        if not isinstance(self.target, str):
            return False
        regex = re.compile(
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, self.target) is not None

    def check_port(self):

        if not isinstance(self.port_list, list):
            return False

        for port in self.port_list:
            if not isinstance(port, int):
                return False

            if not (0 <= port <= 65353):
                return False

        return True

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


@app.route('/')
def get():
    ip = request.args.get('ip')
    port = request.args.get('port')

    ports = port.split(',')

    try:
        port_list = list(map(int, ports))
    except ValueError as e:
        return jsonify(error=f'invalid port value: {port}'), 400, {'ContentType': 'application/json'}

    port_scan = PortScan(ip, port_list)

    if not port_scan.check_url():
        return jsonify(error=f'invalid url: {ip}'), 400, {'ContentType': 'application/json'}
    if not port_scan.check_port():
        return jsonify(error=f'invalid port: {port}'), 400, {'ContentType': 'application/json'}

    port_scan.scan()

    result = dict()

    result['ip'] = ip
    result['ports'] = port_scan.result

    return jsonify(result), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)


    def test(target, port_list):
        port_scan = PortScan(target, port_list)

        port_scan.scan()
        print(target, port_scan.result)

    # test('www.google.com', [80, 443, 987])
    # test('www.youtube.com/', [80, 443, 987])
    # test(28933, [80, 443, 987])
    # test('www.dkfjskjdf.com', [80, 443, 987])
