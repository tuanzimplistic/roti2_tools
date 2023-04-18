
class R2_5_Temp:
    
    HEATER_SET_COEFF_SIG = 51
    AO_HEATER = 26
    
    ID_TO_HEATER =  {0:['top_press','top_press_ref','top_press_pid'], 1:['bottom_press','bottom_press_ref','bottom_press_pid'], 
                        2:['top_roast','top_roast_ref','top_roast_pid'], 3:['bottom_roast','bottom_roast_ref','bottom_roast_pid']}
    HEATER_TO_ID =  {'top_press':0, 'bottom_press':1, 'top_roast':2, 'bottom_roast':3}
    COEFF_TO_ID =   {'Coeff_A':0, 'Coeff_B':1, 'Coeff_C':2, 'Get_Coeffs':-1}
    
    
    def __init__(self):
        from websocket_server import WebsocketServer
        self.websocket = WebsocketServer(host='0.0.0.0', port=15234)
        self.websocket.set_fn_new_client(self.new_client)
        self.websocket.set_fn_message_received(self.coeff_received)
        self.websocket.run_forever(threaded=True)

    def new_client(self, client, server):
        print("Client connected")
        
    def coeff_received(self, client, server, message):
        print(message)
        import json
        obj = json.loads(message)
        
        command = obj['command']
        heater_id = 0
        coeff_id = 0
        q16_val = 0
        set_temp = 0
        set_pidbegin = 0
        set_pin = 0
        set_val = 0
        q16_maxon = 0
        
        pack_info = "BBBiiiBBi"
        
        if command == 0:
            heater_id = self.HEATER_TO_ID[obj['heater']]
        elif command == 1:
            heater_id = self.HEATER_TO_ID[obj['heater']]
            coeff_id = self.COEFF_TO_ID[obj['coeff']]
            q16_val = int(obj['val'])
            print(heater_id, coeff_id, q16_val)
        elif command == 2 or command == 4:
            heater_id = self.HEATER_TO_ID[obj['heater']]
            set_temp = int(obj['set_temp']) * 65536
            set_pidbegin = int(obj['set_pidbegin']) * 65536
            q16_maxon = int(obj['set_maxon']) * 65536
        elif command == 3:
            set_pin = int(obj['set_pin'])
            set_val = int(obj['set_val'])
        elif command == 5 or command == 6:
            pass
        QSpy._sendEvt(self.AO_HEATER, self.HEATER_SET_COEFF_SIG, pack(pack_info, command, heater_id, coeff_id, q16_val, set_temp, set_pidbegin, set_pin, set_val, q16_maxon))
    
    def isfloat(self, s):
        try:
            float(s)
            resultant_value = True
        except:
            resultant_value = False
        return resultant_value
        
    def QS_USER_03(self, packet):
        unpacked = qunpack("xxTxZ", packet)
        time = unpacked[0]
        data = unpacked[1]
        message = ''
        if data.startswith("coeffs"):
            result = ["A: ", "B: ", "C: "]
            i = 0
            data = data.split(" ")
            message += 'coeffs'
            for e in data:
                if(self.isfloat(e)):
                    message += result[i] + e + "(" + str(int((float(e)*65536))) + ") "
                    i += 1
        else:
            heaters = data.split("|")
            message += '{'
            c = len(heaters)
            for i in range(c):
                heaters[i] = heaters[i].strip()
                if(len(heaters[i]) > 0):
                    els = heaters[i].split("-")
                    hid = int(els[0])
                    cur_temp = els[1]
                    ref_temp = els[2]
                    pid_val = els[3]
                    message += '"' + self.ID_TO_HEATER[hid][0] + '":'
                    message += str(cur_temp)
                    message += ','
                    message += '"' + self.ID_TO_HEATER[hid][1] + '":'
                    message += str(ref_temp)
                    message += ','
                    message += '"' + self.ID_TO_HEATER[hid][2] + '":'
                    message += str(pid_val)
                    if i < c-2:
                        message += ','
            message += '}'
        print(message)
        self.websocket.send_message_to_all(message)


QView.customize(R2_5_Temp())
