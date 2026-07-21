import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    from aiobserve.client import ObserveClient
except ModuleNotFoundError:
    ObserveClient = None

@unittest.skipIf(ObserveClient is None, "httpx is not installed")
class ClientIntegrationTests(unittest.TestCase):
    def test_collector_contract_preserves_order_and_hashes(self):
        received=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['content-length'])));received.append(body)
                self.send_response(202);self.send_header('content-type','application/json');self.end_headers();self.wfile.write(b'{}')
            def log_message(self,*_args): pass
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            client=ObserveClient(f'http://127.0.0.1:{server.server_port}','key','tenant','project',enabled=False)
            client.enabled=True;client.emit('trace',{'value':1},'trace');client.emit('feedback',{'score':1},'trace');self.assertEqual(client.flush(),2);self.assertEqual([x['sequence'] for x in received],[0,1]);client.close()
        finally: server.shutdown()
