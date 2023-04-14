# This is an example of QView customization for a specific application
# (DPP in this case). This example animates the Phil images on the
# QView canvas. Additionally, there is a button in the middle of the screen,
# which, when clicked once pauses the DPP ("forks" are not being served).
# A second click on the button, "un-pauses" the DPP ("forks" are served
# to all hungry Philosophers).
#
# This version of the DPP customization uses the application-specific
# packet QS_USER_00 (PHILO_STAT) produced when the status of a Philo changes.
#

class itor3:
    ## Active Object Value:
    AO_VT = 12
    AO_DS = 17
    AO_HT = 26
    AO_CHAR = 27

    GET_OBJECT_DICTIONARY_SIG =  4
    GET_FUNC_DICTIONARY_SIG = 5
    GET_SIGNAL_DICTIONARY_SIG = 6

    ## VT Active Object Signal
    VT_TICK_SIG = 42 #MAX_PUB_SIG
    VT_MOVE_SIG = 43
    VT_MOVE_REL_SIG = 44
    VT_FIND_DATUM_SIG = 45
    VT_FIND_DATUM_ABORT_SIG = 46
    VT_FIND_TOP_LIMIT_SIG = 47
    VT_FIND_TOP_LIMIT_ABORT_SIG = 48
    VT_CALIBRATE_FLAG_SIG = 49

    ## DS Signal
    DISPENSE_BY_WEIGHT_SIG = 43 
    DISPENSE_BY_POSITION_SIG = 44
    DISPENSE_BY_TIME_SIG = 45 
    DISPENSE_ABORT_SIG = 46
    DISPENSE_CLOSE_SHUTTER_SIG = 47
    DISPENSE_FIND_HOME_SIG = 48

    ## Heater Signal
    MAX_PUB_SIG = 40
    HEATER_CTRL_TIMEOUT_SIG = MAX_PUB_SIG
    HEATER_UPDATE_TIMEOUT_SIG = HEATER_CTRL_TIMEOUT_SIG + 1
    HEATER_SV_TIMEOUT_SIG = HEATER_UPDATE_TIMEOUT_SIG + 1
    HEATER_ERROR_CLEAR_SIG = HEATER_SV_TIMEOUT_SIG + 1
    HEATER_OPEN_LOOP_SIG = HEATER_ERROR_CLEAR_SIG + 1
    HEATER_CLOSE_LOOP_SIG =  HEATER_OPEN_LOOP_SIG + 1
    HEATER_OFF_SIG =  HEATER_CLOSE_LOOP_SIG + 1
    HEATER_WD_TIMEOUT_SIG = HEATER_OFF_SIG + 1
    HEATER_WD_ENABLE_SIG = HEATER_WD_TIMEOUT_SIG

    ## Char Signal
    CHARRING_ON_SIG = 42
    CHARRING_OFF_SIG = 43
    CHARRING_PROCESS_TIMEOUT_SIG = 44

    ## Heater ID
    HEATER_TOP_ID = 0
    HEATER_BTM_ID = 1

    ## CHAR ID
    CHAR_TOP_ID = 0
    CHAR_BTM_ID = 1

    ##
    GET_OBJECT_DICTIONARY_SIG = 4
    GET_FUNC_DICTIONARY_SIG = 5
    GET_SIGNAL_DICTIONARY_SIG = 6

    def __init__(self):
        # add commands to the Custom menu...
        QView.custom_menu.add_command(label="Custom command",
                                      command=self.cust_command)

        # configure the custom QView.canvas...
        QView.show_canvas() # make the canvas visible
        #QView.canvas.configure(width=400, height=260)
        
        self._heaters = [{"id" : StringVar(), "state" : StringVar(), "dutyCycle" : StringVar(), "round_dutyCycle" : StringVar(),
                    "ref_temp" : StringVar(), "round_ref_temp" : StringVar(), "cur_temp" : StringVar(), "round_cur_ref_temp" : StringVar()} for k in range(4)]

        ## Creating UI for 4 heaters
        self.heaters_frame = LabelFrame(QView.canvas, text="Heaters")
        self.ht_UI(0, "TOP").grid(row=0, column=0)
        self.ht_UI(1, "BTM").grid(row=0, column=1)
        self.ht_UI(2, "CHAR TOP").grid(row=0, column=2)
        self.ht_UI(3, "CHAR BTM").grid(row=0, column=3)
        self.graph_windows = None
        Button(self.heaters_frame, text="OPEN HEATER GRAPH", command= lambda: self.ht_graph_start_stop()).grid(row=0, column = 5)
        self.heaters_frame.pack()

        # # Creating Controlling for Heater
        self.ht_graph_enabled = False
        self.ht_start_timestamp = 0
        self.heater_control_frame = LabelFrame(QView.canvas, text="Heater Control")
        self.ht_control(self.heater_control_frame)
        # self.ht_graph(self.heater_control_frame)
        self.heater_control_frame.pack(fill=BOTH, expand=True)

        # ## Charring Controoling
        # self.charring_control_frame = LabelFrame(QView.canvas, text="Charring Control")
        # self.char_control(self.charring_control_frame)
        # # self.ht_graph(self.heater_control_frame)
        # self.charring_control_frame.pack()
        

        self._motors = [{
            "id"  : StringVar(),
            "pos" : StringVar(),
            "spd" : StringVar(),
            "cur" : StringVar()
        } for k in range(6)]
        ## Creating UI for 6 motors
        # self.motors_frame = LabelFrame(QView.canvas, text="Motors")
        # self.mt_UI(0, "VT").grid(row=0, column=0)
        # self.mt_UI(1, "Kicker").grid(row=0, column=1)
        # self.mt_UI(2, "Wedge").grid(row=0, column=2)
        # self.mt_UI(3, "Flour").grid(row=0, column=3)
        # self.mt_UI(4, "Press").grid(row=1, column=0)
        # self.mt_UI(5, "Kneader").grid(row=1, column=1)
        # self.motors_frame.pack()

        ## Creating UI for loadcell
        # self.lc_UI()

        ## Creating UI for AOs
        self._aos = [{
            "state" : StringVar(),
            "flag" : StringVar()
        } for k in range(5)] # DS, KN, VT, WP, KR
        self._ao_state_name = {
            "DS" : ["IDLE", "BUSY"],
            "KN" : ["IDLE", "BUSY"],
            "VT" : ["IDLE", "MOVING", "FINDING DATUM", "FINDING TOP LIMIT", "CALIBRATING FLAG"],
            "WP" : ["IDLE", "MOVING", "FINDING DATUM"],
            "KR" : ["IDLE", "MOVING", "FINDING DATUM", "FINDING LIMIT"]
        }
        # self.ao_frame = LabelFrame(QView.canvas, text = "Active Objects")
        # self.ao_UI(0, "DS").grid(row = 0, column = 0)
        # self.ao_UI(1, "KN").grid(row = 0, column = 1)
        # # self.ao_UI(2, "VT").grid(row = 0, column = 2)
        # self.vtUI()
        # self.ao_UI(3, "WP").grid(row = 0, column = 3)
        # self.ao_UI(4, "KR").grid(row = 0, column = 4)
        # self.ao_frame.pack()

        ## VT
        # self.vt_UI_create()
        # self.ds_UI_create()

        # request target reset on startup...
        # NOTE: Normally, for an embedded application you would like
        # to start with resetting the Target, to start clean with
        # Qs dictionaries, etc.
        #
        # Howver, this is a desktop appliction, which you cannot reset
        # (and restart). Therefore, the desktop applications must be started
        # *after* the QView is already running.
        #reset_target()

    def ht_graph_start_stop(self):
        if self.graph_windows == None:
            self.graph_windows = Toplevel(QView.canvas)
            self.graph_windows.title("Roti Graph")
            self.graph_windows.protocol("WM_DELETE_WINDOW", self.on_closing_ht_graph)

            self.ht_graph(self.graph_windows)
            self.ani = FuncAnimation(self.figure2, self.animate, interval = 500)

        self.ht_graph_enabled = not self.ht_graph_enabled
        if not self.ht_graph_enabled:
            self.x_vals = []
            self.y_vals = []
            self.x_vals1 = []
            self.y_vals1 = []
            self.ht_start_timestamp = 0
            
        if self.ht_graph_enabled:
            timestr = time.strftime("%Y%m%d-%H%M%S") + '.csv'
            # print(timestr)
            self.f = open(timestr, 'w')
            self.writer = csv.writer(self.f)
            header = ['Timestamp', "TOP", "BTM"]
            self.writer.writerow(header)
            self.temp_top = 0.0
            self.temp_btm = 0.0
            self.temp_cnt = 0

        if not self.ht_graph_enabled:
            self.f.close()

    def on_closing_ht_graph(self):
        self.ht_graph_enabled = not self.ht_graph_enabled
        if not self.ht_graph_enabled:
            self.f.close()

        self.graph_windows.destroy()
        self.graph_windows = None

    # on_reset() callback
    def on_reset(self):
        # clear the lists
        self._philo_obj   = [0, 0, 0, 0, 0]
        self._philo_state = [0, 0, 0]

    # on_run() callback
    def on_run(self):
        glb_filter("QS_USER_00")

        # NOTE: the names of objects for current_obj() must match
        # the QS Object Dictionaries produced by the application.
        current_obj(OBJ_AO, "Table_inst")

        # turn lists into tuples for better performance
        self._philo_obj = tuple(self._philo_obj)
        self._philo_state = tuple(self._philo_state)

    def ht_graph(self, parrents):
        self.x_vals = []
        self.y_vals = []

        self.x_vals1 = []
        self.y_vals1 = []
        #self.index = count()

        ## Add figure and line
        self.figure2 = plt.figure()
        
        self.ax2 = self.figure2.add_subplot(111)
        
        self.ax2.plot(self.x_vals, self.y_vals, label = "TOP")
        self.ax2.plot(self.x_vals1, self.y_vals1, label = "BTM")
    
        self.line2 = FigureCanvasTkAgg(self.figure2, parrents)
        
        
        self.line2.get_tk_widget().pack(side = LEFT, fill=BOTH, expand=True)
        self.ht_cnt = 0

        # self.ax3 = self.figure2.add_subplot(111)


    def animate(self, i):
        self.ax2.cla()
        self.ax2.plot(self.x_vals, self.y_vals)
        self.ax2.plot(self.x_vals1, self.y_vals1)
        
    def char_control(self, parrents):
        self._char_on_time_top = IntVar()
        self._char_on_time_top.set(30000)

        self._char_on_time_btm = IntVar()
        self._char_on_time_btm.set(30000)

        Entry(parrents, textvariable=self._char_on_time_top).grid(row=0, column=0)
        Button(parrents, text="CHAR TOP ON", command= lambda: self.ht_char_on(0, self._char_on_time_top.get())).grid(row=0, column = 1)

        Entry(parrents, textvariable=self._char_on_time_btm).grid(row=1, column=0)
        Button(parrents, text="CHAR BTM ON", command= lambda: self.ht_char_on(1, self._char_on_time_btm.get())).grid(row=1, column = 1)

        Button(parrents, text="CHAR TOP OFF", command= lambda: self.ht_char_off(0)).grid(row=2, column = 1)
        Button(parrents, text="CHAR BTM OFF", command= lambda: self.ht_char_off(1)).grid(row=3, column = 1)

    def ht_char_on(self, id, on_time):
        print("ht_char_on: {} {}".format(id, on_time))
        if id == 0: #TOP
            QSpy._sendEvt(self.AO_CHAR + self.CHAR_TOP_ID, self.CHARRING_ON_SIG, pack("h", on_time))
        elif id == 1: #BTM
            QSpy._sendEvt(self.AO_CHAR + self.CHAR_BTM_ID, self.CHARRING_ON_SIG, pack("h", on_time))

    def ht_char_off(self, id):
        if id == 0: #TOP
            QSpy._sendEvt(self.AO_CHAR + self.CHAR_TOP_ID, self.CHARRING_OFF_SIG)
        elif id == 1: #BTM
            QSpy._sendEvt(self.AO_CHAR + self.CHAR_BTM_ID, self.CHARRING_OFF_SIG)

    def ht_control(self, parrents):
        ## Line Frequency & Line Type
        Label(parrents, text="Line Frequency: ", anchor="nw").grid(row= 0, column=0)

        self._ht_line_freq = StringVar()
        self._ht_line_freq.set("NA")
        _ht_line_freq_lbl = Label(parrents, textvariable=self._ht_line_freq, anchor="e")

        # Line Type
        Label(parrents, text="Line Type:", anchor="nw").grid(row=1, column=0)
        self._ht_line_type = StringVar()
        self._ht_line_type.set("NA")
        _ht_line_type_lbl = Label(parrents, textvariable=self._ht_line_type, anchor="e")

        _ht = StringVar()
        _ht.set("TOP") # default value
        _ht_option = OptionMenu(parrents, _ht, "TOP", "BTM")
        
        ## OPEN Loop
        self._ht_set_temp = DoubleVar()
        self._ht_set_temp.set(0.5)
        _ht_set_temp_entry = Entry(parrents, textvariable=self._ht_set_temp)

        _ht_set_temp_btn = Button(parrents, text="HEATER OPEN LOOP ON", command= lambda: self.ht_open_loop_on(_ht.get(), self._ht_set_temp.get()))

        ## Heater Close Loop On
        self._ht_cl_set_temp = DoubleVar()
        self._ht_cl_set_temp.set(100.0)
        self._ht_cl_max_duty = DoubleVar()
        self._ht_cl_max_duty.set(0.5)
        self._ht_pid_begin = DoubleVar()
        self._ht_pid_begin.set(80)

        _ht_cl_set_temp_entry = Entry(parrents, textvariable=self._ht_cl_set_temp)
        _ht_cl_max_duty_entry = Entry(parrents, textvariable=self._ht_cl_max_duty)
        _ht_cl_pid_begin_entry = Entry(parrents, textvariable=self._ht_pid_begin)

        _ht_cl_set_temp_bt = Button(parrents, text="HEATER CLOSE LOOP ON", command= lambda: self.ht_close_loop_on(_ht.get(), self._ht_cl_set_temp.get(), 
            self._ht_cl_max_duty.get(), self._ht_pid_begin.get()))

        ## Heater OFF Button
        _ht_off_btn = Button(parrents, text="HEATER OFF", command= lambda: self.ht_off(_ht.get()))

        _ht_line_freq_lbl.grid(row=0, column = 1)
        _ht_line_type_lbl.grid(row=1, column=1)

        _ht_option.grid(row=2, column=0)
        _ht_set_temp_entry.grid(row=3, column=0)
        _ht_set_temp_btn.grid(row=3, column=1)
        
        _ht_cl_set_temp_entry.grid(row=4, column=0)
        _ht_cl_max_duty_entry.grid(row=4, column=1)
        _ht_cl_pid_begin_entry.grid(row=4, column=2)
        _ht_cl_set_temp_bt.grid(row=4, column=3)

        _ht_off_btn.grid(row = 5, column=1)

        ## Object, Function and Signal Names
        Button(parrents, text="GET HT OBJECT NAME", command= lambda: self.ht_get_name(self.GET_OBJECT_DICTIONARY_SIG)).grid(row=6, column=0)
        Button(parrents, text="GET HT FUNC NAME", command= lambda: self.ht_get_name(self.GET_FUNC_DICTIONARY_SIG)).grid(row=7, column=0)
        Button(parrents, text="GET HT SIG NAME", command= lambda: self.ht_get_name(self.GET_SIGNAL_DICTIONARY_SIG)).grid(row=8, column=0)

        Button(parrents, text="CLEAR ERROR", command= lambda: self.ht_clear_error()).grid(row = 9, column = 0)
        
        Button(parrents, text="ENABLE WD", command= lambda: self.ht_en_wd(1)).grid(row = 10, column = 0)
        Button(parrents, text="DISABLE WD", command= lambda: self.ht_en_wd(0)).grid(row = 11, column = 0)

    def ht_en_wd(self, en_flag):
        QSpy._sendEvt(self.AO_HT, self.HEATER_WD_ENABLE_SIG, pack("b", en_flag))

    def ht_clear_error(self):
        QSpy._sendEvt(self.AO_HT, self.HEATER_ERROR_CLEAR_SIG)

    def ht_get_name(self, id):
        QSpy._sendEvt(self.AO_HT, id)

    def ht_close_loop_on(self, ht_id, refTemp, maxDuty, pidBegin):
        print("{} {}".format(ht_id, refTemp))
        if ht_id == "TOP":
            QSpy._sendEvt(self.AO_HT, self.HEATER_CLOSE_LOOP_SIG, pack("biii", self.HEATER_TOP_ID, round(refTemp * 65536.0), round(maxDuty * 65536.0), round(pidBegin*65536.0)))
            # QSpy._sendEvt(self.AO_HT, self.HEATER_OPEN_LOOP_SIG, pack("<ii", 0, 100))
        elif ht_id == "BTM":
            # QSpy._sendEvt(self.AO_HT, self.HEATER_OPEN_LOOP_SIG, pack("<ii", 1, 100))
            QSpy._sendEvt(self.AO_HT, self.HEATER_CLOSE_LOOP_SIG, pack("biii", self.HEATER_BTM_ID, round(refTemp * 65536.0), round(maxDuty * 65536.0), round(pidBegin*65536.0)))

    def ht_open_loop_on(self, ht_id, dutyCycle):
        print("{} {}".format(ht_id, dutyCycle))
        if ht_id == "TOP":
            QSpy._sendEvt(self.AO_HT, self.HEATER_OPEN_LOOP_SIG, pack("bi", self.HEATER_TOP_ID, round(dutyCycle * 65536.0)))
            # QSpy._sendEvt(self.AO_HT, self.HEATER_OPEN_LOOP_SIG, pack("<ii", 0, 100))
        elif ht_id == "BTM":
            # QSpy._sendEvt(self.AO_HT, self.HEATER_OPEN_LOOP_SIG, pack("<ii", 1, 100))
            QSpy._sendEvt(self.AO_HT, self.HEATER_OPEN_LOOP_SIG, pack("bi", self.HEATER_BTM_ID, round(dutyCycle * 65536.0)))

    def ht_off(self, ht_id):
        if ht_id == "TOP":
            QSpy._sendEvt(self.AO_HT, self.HEATER_OFF_SIG, pack("b", 0))
        elif ht_id == "BTM":
            QSpy._sendEvt(self.AO_HT, self.HEATER_OFF_SIG, pack("b", 1))

    # example of a custom command
    def cust_command(self):
        command(1, 12345)

    def vt_find_datum(self):
        QSpy._sendEvt(self.AO_VT, self.VT_FIND_DATUM_SIG)

    def vt_find_top(self):
        QSpy._sendEvt(self.AO_VT, self.VT_FIND_TOP_LIMIT_SIG, pack("<i", 0))

    def vt_get_dics(self, id, object_id):
        if id == 0:
            QSpy._sendEvt(object_id, self.GET_OBJECT_DICTIONARY_SIG)
        elif id == 1:
            QSpy._sendEvt(object_id, self.GET_FUNC_DICTIONARY_SIG)
        elif id == 2:
            QSpy._sendEvt(object_id, self.GET_SIGNAL_DICTIONARY_SIG)

    def vt_calibrate(self):
        QSpy._sendEvt(self.AO_VT, self.VT_CALIBRATE_FLAG_SIG)

    def vt_move(self, isRel, pos, spd):
        if isRel:
            QSpy._sendEvt(self.AO_VT, self.VT_MOVE_REL_SIG, pack("<ii", pos * 65536, spd * 65536))
        else:
            QSpy._sendEvt(self.AO_VT, self.VT_MOVE_SIG, pack("<ii", pos * 65536, spd * 65536))
        # QSpy._sendEvt(self.AO_VT, self.VT_MOVE_SIG, pack("<ii", 8, 0xff))

    # example of a custom interaction with a canvas object (pause/serve)
    def cust_pause(self, event):
        if QView.canvas.itemcget(self.btn, "image") != str(self.img_UP):
            QView.canvas.itemconfig(self.btn, image=self.img_UP)
            post("SERVE_SIG")
            QView.print_text("Table SERVING")
        else:
            QView.canvas.itemconfig(self.btn, image=self.img_DWN)
            post("PAUSE_SIG")
            QView.print_text("Table PAUSED")
            
    def ht_UI(self, id, name):
        # Create init value
        self._heaters[id]["id"].set("NA")
        self._heaters[id]["state"].set("NA")
        self._heaters[id]["dutyCycle"].set("NA")
        self._heaters[id]["round_dutyCycle"].set("NA")
        self._heaters[id]["ref_temp"].set("NA")
        self._heaters[id]["round_ref_temp"].set("NA")
        self._heaters[id]["cur_temp"].set("NA")
        self._heaters[id]["round_cur_ref_temp"].set("NA")

        ht = self.heaterUI(self.heaters_frame, name, self._heaters[id]["id"], self._heaters[id]["state"], self._heaters[id]["dutyCycle"], self._heaters[id]["round_dutyCycle"],
                            self._heaters[id]["ref_temp"], self._heaters[id]["round_ref_temp"], self._heaters[id]["cur_temp"], self._heaters[id]["round_cur_ref_temp"])
        return ht.GetFrame()

    def mt_UI(self, id, name):
        self._motors[id]["pos"].set("NA")
        self._motors[id]["spd"].set("NA")
        self._motors[id]["cur"].set("NA")

        mt = self.motorUI(self.motors_frame, name, self._motors[id]["pos"], self._motors[id]["spd"], self._motors[id]["cur"])
        return mt.GetFrame()

    def lc_UI(self):
        self.loadcell_frame = LabelFrame(QView.canvas, text="Loadcell")
        # Position
        self._lc_raw_data = StringVar()
        self._lc_physical_data = StringVar()
        self._lc_port_output = StringVar()

        self._lc_raw_data.set("NA")
        self._lc_physical_data.set("NA")
        self._lc_port_output.set("NA")
        
        _raw_label = Label(self.loadcell_frame,        text="Raw Data: ", anchor=NW)
        _physic_label = Label(self.loadcell_frame,     text="Physical Data: ", anchor=NW)
        _portoutput_label = Label(self.loadcell_frame, text="Port Output: ", anchor=NW)

        _lc_raw_lbl = Label(self.loadcell_frame, anchor=E, textvariable=self._lc_raw_data)
        _lc_phy_lbl = Label(self.loadcell_frame, anchor=E, textvariable=self._lc_physical_data)
        _lc_port_lbl = Label(self.loadcell_frame, anchor=E, textvariable=self._lc_port_output)

        _raw_label.grid(row=0, column=0)
        _lc_raw_lbl.grid(row=0, column=1)
        _physic_label.grid(row=1, column = 0)
        _lc_phy_lbl.grid(row = 1, column = 1)
        _portoutput_label.grid(row = 2, column = 0)
        _lc_port_lbl.grid(row = 2, column = 1)
            
        self.loadcell_frame.pack(side = LEFT)

    def ao_UI(self, id, name):
        self._aos[id]["state"].set("NA")
        self._aos[id]["flag"].set("NA")
        ao = self.aoUI(self.ao_frame, name, self._aos[id]["state"], self._aos[id]["flag"])
        return ao.GetFrame()

    def vt_UI_create(self):
        self.vt_frame = LabelFrame(QView.canvas, text="VT AO")
        self._vt_state = StringVar()
        self._vt_flag = StringVar()
        self._vt_position = StringVar()

        self._vt_state.set("NA")
        self._vt_flag.set("NA")
        self._vt_position.set("NA")
        
        ## Create vt.find_datum() button
        Button(self.vt_frame, text="FIND DATUM", command=self.vt_find_datum).grid(row=0, column=0, columnspan=3)
        
        ## vt.move() absolute button
        self._vt_ab_pos = IntVar()
        self._vt_ab_spd = IntVar()
        self._vt_ab_pos.set(0)
        self._vt_ab_spd.set(20)
        self._vt_ab_pos_entry = Entry(self.vt_frame, textvariable=self._vt_ab_pos)
        self._vt_ab_spd_entry = Entry(self.vt_frame, textvariable=self._vt_ab_spd)
        self._vt_ab_pos_entry.grid(row=1, column= 0)
        self._vt_ab_spd_entry.grid(row=1, column=1)

        Button(self.vt_frame, text="MOVE ABSOLUTE", command= lambda: self.vt_move(0, self._vt_ab_pos.get(), self._vt_ab_spd.get())).grid(row=1, column=2)
        # self._vt_find_datum_button = Button(self.vt_frame, text="MOVE RELATIVE", command= lambda: self.vt_move(50, 15)).grid(row=1, column=0, columnspan=1)

        ## Create VT calibration button
        Button(self.vt_frame, text="CALIBRATE", command=self.vt_calibrate).grid(row=2, column=0, columnspan=3)

        ## VT finding top limit
        Button(self.vt_frame, text="FIND TOP LIMIT", command=self.vt_find_top).grid(row=3, column=0, columnspan=3)

        ## Get Object Dic
        self._object_id = IntVar()
        self._object_id.set(0)
        Entry(self.vt_frame, textvariable=self._object_id).grid(row=4, column=0)
        Button(self.vt_frame, text="GET OBJECT DIC", command= lambda: self.vt_get_dics(0, self._object_id.get())).grid(row=4, column=1, columnspan=3)

        ## Get Func Dic
        Button(self.vt_frame, text="GET FUNCS DIC", command= lambda: self.vt_get_dics(1, self._object_id.get())).grid(row=5, column=0, columnspan=3)

        ## Get Signal Dic
        Button(self.vt_frame, text="GET SIGNAL DIC", command= lambda: self.vt_get_dics(2, self._object_id.get())).grid(row=6, column=0, columnspan=3)


        ## VT State UI
        self.vtUI(self.vt_frame, "VT State", flag=self._vt_flag, state=self._vt_state, position=self._vt_position).GetFrame().grid(row = 7, column = 0)

        self.vt_frame.pack()

    def ds_UI_create(self):
        self.ds_frame = LabelFrame(QView.canvas, text="DS AO")
        # self._ds_state = StringVar()
        # self._ds_flag = StringVar()
        # self._ds_position = StringVar()

        # self._ds_state.set("NA")
        # self._ds_flag.set("NA")
        # self._ds_position.set("NA")
        
        ## Create ds.dis_by_weight() button
        self._ds_id = IntVar()
        self._ds_weight = DoubleVar()
        self._ds_weight_spd = DoubleVar()
        self._ds_close_shutter = IntVar()
        self._ds_id.set(0)
        self._ds_weight.set(10.0)
        self._ds_weight_spd.set(5.0)
        self._ds_close_shutter.set(0)
        
        self._ds_id_entry = Entry(self.ds_frame, textvariable=self._ds_id)
        self._ds_weight_entry = Entry(self.ds_frame, textvariable=self._ds_weight)
        self._ds_weight_spd_entry = Entry(self.ds_frame, textvariable=self._ds_weight_spd)
        self._ds_shutter_entry = Entry(self.ds_frame, textvariable=self._ds_close_shutter)

        self._ds_id_entry.grid(row=0, column=0)
        self._ds_weight_entry.grid(row=0, column=1)
        self._ds_weight_spd_entry.grid(row=0, column=2)
        self._ds_shutter_entry.grid(row=0, column=3)

        Button(self.ds_frame, text="DISPENSE BY WEIGHT", command= lambda: self.ds_dispense_by_weight(self._ds_id.get(), self._ds_weight.get(), self._ds_weight_spd.get(), self._ds_close_shutter.get()) ).grid(row=0, column=4)
        

        ## Create ds.dis_by_time() button
        self._ds_id_time = IntVar()
        self._ds_time = IntVar()
        self._ds_time_spd = DoubleVar()
        self._ds_id.set(0)
        self._ds_time.set(1000)
        self._ds_time_spd.set(5.0)
        
        self._ds_id_time_entry = Entry(self.ds_frame, textvariable=self._ds_id_time)
        self._ds_time_entry = Entry(self.ds_frame, textvariable=self._ds_time)
        self._ds_time_spd_entry = Entry(self.ds_frame, textvariable=self._ds_time_spd)
        
        self._ds_id_time_entry.grid(row=1, column=0)
        self._ds_time_entry.grid(row=1, column=1)
        self._ds_time_spd_entry.grid(row=1, column=2)

        Button(self.ds_frame, text="DISPENSE BY TIME", command= lambda: self.ds_dispense_by_time(self._ds_id_time.get(), self._ds_time.get(), self._ds_time_spd.get())).grid(row=1, column=3)

        self.ds_frame.pack()

    def ds_dispense_by_weight(self, id, weight, spd, toCloseShutter):
        QSpy._sendEvt(self.AO_DS, self.DISPENSE_BY_WEIGHT_SIG + id, pack("<iib", int(weight * 65536), int(spd * 65536), toCloseShutter))

    def ds_dispense_by_time(self, id, time, spd):
        QSpy._sendEvt(self.AO_DS, self.DISPENSE_BY_WEIGHT_SIG + id, pack("<ii", time, int(spd * 65536)))

    # intercept the QS_USER_00 application-specific packet
    # this packet has the following structure (see bsp.c:displayPhilStat()):
    # record-ID, seq-num, Timestamp, format-byte, Philo-num,
    #    format-bye, Zero-terminated string (status)
    # def QS_USER_00(self, packet):
    #     data = qunpack("xxTxbxixixi", packet)
    #     # QView.print_text("{} {} {} {} {} {}".format(data[0], data[1], data[2], data[3]))
    #     id = data[1]
    #     self._motors[id]["pos"].set("{:.2f}".format(data[2] / 65536.0))
    #     self._motors[id]["spd"].set("{:.2f}".format(data[3] / 65536.0))
    #     self._motors[id]["cur"].set("{:.2f}".format(data[4] / 65536.0))

    # Loadcell
    # def QS_USER_02(self, packet):
    #     data = qunpack("xxTxixixixi", packet)
    #     QView.print_text("{} {} {} {}".format(data[0], data[1], data[2], data[3]))
    #     self._lc_raw_data.set("{:.2f}".format(data[1] / 65536.0))
    #     self._lc_physical_data.set("{:.2f}".format(data[3] / 65536.0))
    #     self._lc_port_output.set("{:02x}".format(data[4]))
            
    def QS_USER_03(self, packet):
        # data = qunpack("xxTxbxbxixixi", packet)
        # data = qunpack("xxTxb", packet)
        heater_type = ["HEATER_LINE_220V", "HEATER_LINE_110V", "HEATER_LINE_UNDEFINED"]
        data = qunpack("xxTxbxixixixbxixixixbxi", packet)
        
        #TOP
        self._heaters[0]["id"].set("{}".format(0))
        self._heaters[0]["state"].set("{}".format(data[1]))
        self._heaters[0]["dutyCycle"].set("{:.2f}".format(data[2] / 65536.0))
        self._heaters[0]["ref_temp"].set("{:.2f}".format(data[3] / 65536.0))
        self._heaters[0]["cur_temp"].set("{:.2f}".format(data[4] / 65536.0))

        #BTM
        self._heaters[1]["id"].set("{}".format(1))
        self._heaters[1]["state"].set("{}".format(data[5]))
        self._heaters[1]["dutyCycle"].set("{:.2f}".format(data[6] / 65536.0))
        self._heaters[1]["ref_temp"].set("{:.2f}".format(data[7] / 65536.0))
        self._heaters[1]["cur_temp"].set("{:.2f}".format(data[8] / 65536.0))

        #     ## Update Line Type
        self._ht_line_type.set(heater_type[data[9]])
        
        ## Update Line Frequency:
        self._ht_line_freq.set("{}".format(round(data[10] / 65536.0, 2)))

        ## Update graph
        if self.ht_graph_enabled:
            if self.ht_start_timestamp == 0:
                self.ht_start_timestamp = data[0]
            
            # Update TOP
            # self.x_vals.append(data[0] - self.ht_start_timestamp)
            self.x_vals.append(data[0])
            self.y_vals.append(data[4] / 65536.0)
            self.temp_top = data[4] / 65536.0
            self.ht_cnt += 1
            
            # Update BTM
            self.x_vals1.append(data[0])
            self.y_vals1.append(data[8] / 65536.0)
            self.temp_btm = data[8] / 65536.0
            self.ht_cnt += 1
                
            #Write data to the csv file
            # if self.ht_cnt == 2:
            # self.writer.writerow([data[0] - self.ht_start_timestamp, self.temp_top, self.temp_btm])
            self.writer.writerow([data[0], self.temp_top, self.temp_btm])
            # self.ht_cnt = 0

    ## VT Active Object
    def QS_USER_04(self, packet):
        # Get log ID
        data = qunpack("xxTxb", packet)
        if data[1] == 0: # Debug Log
            data = qunpack("xxTxbxbxbxi", packet)
            state = data[1]
            flag = data[2]
            pos = data[3]

            self._vt_state.set(self._ao_state_name["VT"][state])
            self._vt_flag.set("{0:b}".format(flag))
            self._vt_position.set("{:.2f}".format(pos / 65536.0))
        elif data[1] == 1: # Find datum log
            pass

        
        
        
    class motorUI():
        def __init__(self, parent, name, pos_var, spd_var, cur_var):
            self._frame = LabelFrame(parent, text=name, padx=82)

            # Position
            pos_label = Label(self._frame, text="Position: ", anchor=NW)
            spd_label = Label(self._frame, text="Speed: ", anchor=NW)
            cur_label = Label(self._frame, text="Current: ", anchor=NW)

            pos = Label(self._frame, anchor=E, textvariable=pos_var)
            spd = Label(self._frame, anchor=E, textvariable=spd_var)
            cur = Label(self._frame, anchor=E, textvariable=cur_var)

            pos_label.grid(row=0, column=0)
            pos.grid(row=0, column=1)

            spd_label.grid(row=1, column=0)
            spd.grid(row=1, column=1)

            cur_label.grid(row=2, column=0)
            cur.grid(row=2, column=1)

        def GetFrame(self):
            return self._frame

    class heaterUI():
        def __init__(self, parent, name, id, state, duty_cycle, round_duty_cycle, ref_temp, round_ref_temp, temp, round_temp):
            self._frame = LabelFrame(parent, text=name)

            # Labels
            id_label = Label(self._frame, text="ID: ", anchor=NW)
            state_label = Label(self._frame, text="State: ", anchor=NW)
            dutyCycle_label = Label(self._frame, text="Duty Cycle: ", anchor=NW)
            round_dutyCycle_label = Label(self._frame, text="Rounded Duty Cycle: ", anchor=NW)
            ref_temp_label = Label(self._frame, text="Reference Temperaature: ", anchor=NW)
            round_ref_temp_label = Label(self._frame, text="Rounded Reference Temperature: ", anchor=NW)
            temp_label = Label(self._frame, text="Current Temperature: ", anchor=NW)
            round_temp_label = Label(self._frame, text="Rounded Current Temperature: ", anchor=NW)

            # Values
            id_value_label = Label(self._frame, textvariable=id, anchor=E)
            state_value_label = Label(self._frame, textvariable=state, anchor=E)
            dutyCycle_value_label = Label(self._frame, textvariable=duty_cycle, anchor=E)
            round_dutyCycle_value_label = Label(self._frame, textvariable=round_duty_cycle, anchor=E)
            ref_temp_value_label = Label(self._frame, textvariable=ref_temp, anchor=E)
            round_ref_temp_value_label = Label(self._frame, textvariable=round_ref_temp, anchor=E)
            temp_value_label = Label(self._frame, textvariable=temp, anchor=E)
            round_temp_value_label = Label(self._frame, textvariable=round_temp, anchor=E)

            # Grid
            id_label.grid(row=0, column=0, sticky="W")
            id_value_label.grid(row=0, column=1)

            state_label.grid(row=1, column=0, sticky="W")
            state_value_label.grid(row=1, column=1)

            dutyCycle_label.grid(row=2, column=0, sticky="W")
            dutyCycle_value_label.grid(row=2, column=1)

            round_dutyCycle_label.grid(row=3, column=0, sticky="W")
            round_dutyCycle_value_label.grid(row=3, column=1)

            ref_temp_label.grid(row=4, column=0, sticky="W")
            ref_temp_value_label.grid(row=4, column=1)

            round_ref_temp_label.grid(row=5, column=0, sticky="W")
            round_ref_temp_value_label.grid(row=5, column=1)

            temp_label.grid(row=6, column=0, sticky="W")
            temp_value_label.grid(row=6, column=1)

            round_temp_label.grid(row=7, column=0, sticky="W")
            round_temp_value_label.grid(row=7, column=1)

        def GetFrame(self):
            return self._frame

    class aoUI():
        def __init__(self, parents, name, state, flag):
            self._frame = LabelFrame(parents, text=name)
            
            #Label
            state_lbl = Label(self._frame, text = "State: ", anchor = NW)
            flag_lbl = Label(self._frame, text = "Flag: ", anchor = NW)

            #Value
            state_value_lbl = Label(self._frame, textvariable=state, anchor = E, width = 15)
            flag_value_lbl = Label(self._frame, textvariable=flag, anchor = E, width = 15)

            #Grid
            state_lbl.grid(row=0,column=0,sticky="W")
            state_value_lbl.grid(row=0,column=1)

            flag_lbl.grid(row = 1, column = 0, sticky = "W")
            flag_value_lbl.grid(row=1, column = 1, sticky = "W")

        def GetFrame(self):
            return self._frame
    
    class vtUI(aoUI):
        def __init__(self, parents, name, state, flag, position):
            super().__init__(parents, name, state, flag)

            # VT position
            pos_lbl = Label(self._frame, text="Position: ", anchor=NW)
            pos_value_lbl = Label(self._frame, textvariable=position, anchor=E, width= 15)

            # Grid
            pos_lbl.grid(row=2, column=0)
            pos_value_lbl.grid(row=2, column=1)

#=============================================================================
QView.customize(itor3()) # set the QView customization
