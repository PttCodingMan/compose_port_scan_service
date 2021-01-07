from flask import Flask
from flask import request
from flask import jsonify

import socket
import threading
import re

app = Flask(__name__)


class PortScan:
    def __init__(self, target, port_list):

        # 處理一下傳入的網址
        if target.startswith('https://'):
            target = target[len('https://'):]
        elif target.startswith('http://'):
            target = target[len('http://'):]

        # 把最後的斜線拿掉，不拿會都沒有回應
        if target.endswith('/'):
            target = target[:-1]

        self._target = target
        self._port_list = port_list

        self.result = dict()

    def check_url(self):
        # 檢查 url 是否符合格式
        if not isinstance(self._target, str):
            return False
        regex = re.compile(
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, self._target) is not None

    def check_port(self):
        # 檢查 port 是否符合格式
        if not isinstance(self._port_list, list):
            return False

        for port in self._port_list:
            if not isinstance(port, int):
                return False

            if not (0 <= port <= 65535):
                return False

        return True

    def scan(self):

        # 為提升效能，每個 port 都分出一個 thread 來打
        thread_list = list()

        for port in self._port_list:
            t = threading.Thread(target=self.run, args=(port,))
            t.start()
            thread_list.append(t)

        for t in thread_list:
            t.join()

    def run(self, current_port):
        # 設定 socket timeout
        socket.setdefaulttimeout(1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)

        try:
            # 連線
            result = s.connect_ex((self._target, current_port))
            # 如果沒例外，就看看結果如何，存起來
            self.result[current_port] = (result == 0)
        except TypeError:
            # 並不是一個網址
            pass
        except socket.gaierror:
            # url 主機不存在
            self.result[current_port] = False
        finally:
            # 無論如何記得關閉連線
            s.close()


def set_response(msg, code):
    return jsonify(msg), code, {'ContentType': 'application/json'}


@app.route('/api/v1/query_port')
def get():
    # 取得參數
    ip = request.args.get('ip')
    port = request.args.get('port')

    # 按照, 分開
    ports = port.split(',')

    # 轉成整數
    try:
        port_list = list(map(int, ports))
    except ValueError:
        # 表示無法被順利轉為整數
        return set_response(f'invalid port value: {port}', 400)

    # 初始化掃描物件
    port_scan = PortScan(ip, port_list)

    # 檢查參數正確性
    if not port_scan.check_url():
        return set_response(f'invalid url: {ip}', 400)
    if not port_scan.check_port():
        return set_response(f'invalid port: {port}', 400)

    # 開始掃描
    port_scan.scan()

    # 開始組合結果
    result = dict()

    result['ip'] = ip
    result['ports'] = port_scan.result

    return set_response(result, 200)


if __name__ == '__main__':
    # 啟動伺服器
    app.run(host='0.0.0.0', port=9999, debug=True)

    # 以下是本機測試
    def test(target, port_list):
        port_scan = PortScan(target, port_list)

        port_scan.scan()
        print(target, port_scan.result)

    # test('www.google.com', [80, 443, 987])
    # test('www.youtube.com/', [80, 443, 987])
    # test(28933, [80, 443, 987])
    # test('www.dkfjskjdf.com', [80, 443, 987])
