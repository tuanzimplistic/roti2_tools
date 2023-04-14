import logging
from websocket_server import WebsocketServer
import time
import random

def new_client(client, server):
	i = 0
	while True:
		time.sleep(1)
		server.send_message_to_all('{"top_press":' + str(round(random.uniform(30, 150), 1)) + ',"bottom_press":'  + str(round(random.uniform(30, 150), 1)) + 
                                     ',"top_roast":' + str(round(random.uniform(30, 150), 1)) + ',"bottom_roast":'  + str(round(random.uniform(30, 150), 1)) +'}')
		i+=1

def message_received(client, server, message):
	print(message)
    
server = WebsocketServer(host='0.0.0.0', port=12345, loglevel=logging.INFO)
server.set_fn_message_received(message_received)
server.set_fn_new_client(new_client)
server.run_forever()
