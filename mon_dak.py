class MDAK:
    def __init__(self):
        from websocket_server import WebsocketServer
        self.websocket = WebsocketServer(host='0.0.0.0', port=13254)
        self.websocket.set_fn_new_client(self.new_client)
        self.websocket.run_forever(threaded=True)

    def new_client(self, client, server):
        print("Client connected")

    def toJson(self, packet):
        unpacked = qunpack("xxTxZ", packet)
        time = unpacked[0]
        data = unpacked[1]
        json = '{"time":' + str(time) + ',' + data + '}'
        return json

    def QS_USER_18(self, packet):
        json = self.toJson(packet)
        self.websocket.send_message_to_all(json)

    def QS_USER_19(self, packet):
        json = self.toJson(packet)
        self.websocket.send_message_to_all(json)


QView.customize(MDAK())
