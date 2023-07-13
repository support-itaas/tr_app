# import json
# import random
# import urllib.request
#
# from odoo.http import request
#
# baseurl = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
# print("BASEURL", baseurl)
# HOST = baseurl
# PORT = 8015
# DB = "wiz_140422_thai"
# USER = "admin"
# PASS = "admin"
#
#
# def json_rpc(url, method, params):
#     data = {
#         "jsonrpc": "2.0",
#         "method": method,
#         "params": params,
#         "id": random.randint(0, 1000000000),
#     }
#     req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={
#         "Content-Type": "application/json",
#     })
#     reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
#     # if reply.get("error"):
#     # 	raise Exception(reply["error"])
#     print("REPLY >>>---",reply)
#     return reply["result"]
#
#
# def call(url, service, method, *args):
#     return json_rpc(url, "call", {"service": service, "method": method, "args": args})
#
#
# url = "http://%s:%s/jsonrpc" % (HOST, PORT)
# print("URL >>>---",url)
# uid = call(url, "common", "login", DB, USER, PASS)
# print(url)
# print("uid", uid)
