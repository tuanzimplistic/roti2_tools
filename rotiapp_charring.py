from itor3_pyapp.app.common import *
from itor3_pyapp.app.dak import *
from itor3_pyapp.app.upr import *
from itor3_pyapp.app.log import *
from setting import *
#from report import *
import time

class Home():
    def __init__(self, vt, wp, kr):
        self.vt = vt
        self.wp = wp
        self.kr = kr
        self.done = False

    async def SetVTLimit(self):
        vtTopLimit = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR
        retCmdVal = self.vt.find_top_limit()
        if not retCmdVal:
            print("VT Top Limit sending error")
            retVal = CommandRetCode.CMD_RETCODE_GENERR
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal = await self.vt.wait()
            if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                vtTopLimit = self.vt.get_status().pos
                print("VT Top Limit:{}".format(vtTopLimit))
            else:
                print("VT Top Limit execution error: {}".format(retVal))

        return retVal, vtTopLimit

    async def _home(self):
        print('VT home')
        retires = 5
        ok = vt.find_datum()
        if ok:
            ok = False
            while retires > 0:
                retires -= 1
                await uasyncio.sleep(5)
                status = await self.SetVTLimit()
                print('VT status:', status)
                if status[0] == 0 and status[1] > 45 and status[1] < 49:
                    ok = True
                    break
                
        print('WP home')
        if ok:
            await uasyncio.sleep(1)
            ok = wp.find_datum(3)
        if ok:
            retires = 5
            while retires > 0:
                retires -= 1
                await uasyncio.sleep(3)
                ok = wp.move_absolute(50,50,5000)
                if ok:
                    ok = False
                    await uasyncio.sleep(5)
                    status = wp.get_status()
                    print('WP status:', status)
                    if status.state == 0 and status.press_gap > 48 and status.press_gap < 52 and status.pivot_gap > 48 and status.pivot_gap < 52:
                        ok = True
                        break
        print('KR home')
        if ok:
            await uasyncio.sleep(1)
            ok = kr.find_home()
        if ok:
            retires = 5
            while retires > 0:
                retires -= 1
                await uasyncio.sleep(5)
                ok = kr.move(0,330,100)
                if ok:
                    ok = False
                    await uasyncio.sleep(5)
                    status = kr.get_status()
                    print('KR status:', status)
                    if status.state == 0 and status.pos > 228 and status.pos < 332:
                        ok = True
                        break
        if ok:
            print('Found home')
            self.done = True
        else:
            print('Failed to find home')

    def find(self):
        uasyncio.run(self._home())

class Mon():
    def __init__(self, vt, kn, ds, wp, ht, kr):
        self.vt = vt
        self.kn = kn
        self.ds = ds
        self.wp = wp
        self.ht = ht
        self.kr = kr
        self.is_post_ok = False
        self.mon_temp = uasyncio.create_task(self._printLog())


    async def _printLog(self):
        prev_time = time.time()
        ht_status = ht.get_status()
        prev_ht1 = ht_status.ht1_temp
        prev_ht2 = ht_status.ht2_temp

        while True:
            await uasyncio.sleep(3)
            heaters_status = ht.get_status()
            ht1 = heaters_status.ht1_temp
            ht2 = heaters_status.ht2_temp
            cur_time = time.time()
            #print('Current Temperature', 'top:', ht1, 'bottom:', ht2)
            logger.debug({'Current Temperature top':'{0}', 'bottom':'{1}'}, ht1, ht2)

            # print ramprate of temperature per second
            elapsed_time = cur_time - prev_time
            ramp_rate1 = (ht1 - prev_ht1) / elapsed_time
            ramp_rate2 = (ht2 - prev_ht2) / elapsed_time
            prev_ht1 = ht1
            prev_ht2 = ht2
            prev_time = cur_time
            logger.debug({'Ramp rate deg/sec top':'{0:.1f}', 'bottom':'{1:.1f}'}, ramp_rate1, ramp_rate2)

            #get VT status and then print out the state and position of VT
            vt_status = vt.get_status()
            logger.debug({'Vt state:': '{0}', 'Vt position:': '{1}', 'Vt flags:': '{2}'}, vt_status.state, vt_status.pos, vt_status.flags)
             # get Charring pin status then print out it
            char_state = ht.char_get_state()
            logger.debug({'Charring top state:': '{0}', 'bottom state:': '{1}'}, char_state.chtop_state, char_state.chbtm_state)

    def post(self):
        uasyncio.run(self._post())

    async def _check(self, heater_type, wait_time):
        times = 0
        count = 0
        pre_ht = 0
        avg_temp = 0
        heaters_status = self.ht.get_status()
        if heater_type == 1:
            pre_ht = heaters_status.ht1_temp
        else:
            pre_ht = heaters_status.ht2_temp
        while True:
            dt = 0
            await uasyncio.sleep_ms(wait_time)
            heaters_status = self.ht.get_status()
            if heater_type == 1:
                dt = heaters_status.ht1_temp - pre_ht
                pre_ht = heaters_status.ht1_temp
                #print('top temp:', heaters_status.ht1_temp)
                logger.debug({'Current Temperature top':'{0}'}, heaters_status.ht1_temp)
            else:
                dt = heaters_status.ht2_temp - pre_ht
                pre_ht = heaters_status.ht2_temp
                #print('bottom temp:', heaters_status.ht2_temp)
                logger.debug({'Current Temperature bottom':'{0}'}, heaters_status.ht2_temp)
            if(dt > 5):
                count += 1
                avg_temp += dt
            times += 1
            if(times == 5):
                break
        #print('count:', count, 'average ramp temp:', avg_temp/count)
        logger.critical({'count':'{0}', 'average ramp temp': '{1}'}, count, avg_temp/count)
        return count > 2

    async def _post(self):
        heaters_status = self.ht.get_status()
        ht1 = heaters_status.ht1_temp
        ht2 = heaters_status.ht2_temp
        logger.debug({'Current Temperature top':'{0}', 'bottom':'{1}'}, ht1, ht2)
        if(ht1 + 60 > 130 or ht2 + 60 > 130):
            #print('Waring: Temperature is too high')
            logger.critical({'meaasge':'Temperature is too high to do POST'})
        else:
            self.ht.set_state(HT.HT_ID_TOP, 1, 130, 1.0, ht1 + 1)
            ok = await self._check(1, 1500) #check ht1 = top
            self.ht.set_state(HT.HT_ID_TOP, 0, 0, 0, 0)
            await uasyncio.sleep_ms(200)
            self.ht.set_state(HT.HT_ID_BTM, 1, 130, 1.0, ht2 + 1)
            ok = ok and await self._check(2, 1500) #check ht2 = bottom
            self.ht.set_state(HT.HT_ID_BTM, 0, 0, 0, 0) 
            await uasyncio.sleep_ms(200)
            #done post
            if(ok):
                #print('POST heater is OK')
                logger.critical({'POST':'heater is OK'})
                self.is_post_ok = True
            else:
                logger.critical({'POST':'heater is NOT OK'})


## TODO: remove these lines for production code
vt = VT()
kn = KN()
ds = DS()

wp = WP()
ht = HT()
kr = KR()

mon = Mon(vt, kn, ds, wp, ht, kr)
home = Home(vt, wp, kr)

def t(t):
    ht.set_state(HT.HT_ID_TOP, 1, t, 0.8, t)

def gt():
    while True:
        print(ht.get_status())
        time.sleep(0.3)

def c(s):
    if s== 1:
        ht.set_fan_pwm(0, 100)
        ht.set_fan_pwm(1, 100)
        ht.set_fan_pwm(2, 100)
        ht.set_fan_pwm(3, 100)
    else:
        ht.set_fan_pwm(0, 0)
        ht.set_fan_pwm(1, 0)
        ht.set_fan_pwm(2, 0)
        ht.set_fan_pwm(3, 0)

class rotiapp():
    ## VT position for dispensing
    DAK_DIS_VT_POS = 26
    DAK_DIS_VT_POS_WATER_OIL = 20

    ## VT Moving speed for dispensing
    DAK_DIS_VT_SPD = 20

    ## Time to dispense Flour in ms
    DAK_FLOUR_DIS_TIME = 3000

    ## Time to dispense Water in ms
    DAK_WATER_DIS_TIME = 1000

    ## Time to dispense Oil in ms
    DAK_OIL_DIS_TIME = 1000
    
    ## LoadCell Weight gain
    DAK_LC_WG = Machine.lc_weightGain
    
    ## Flour Weight
    DAK_FLOUR_WT = 24.5
    DAK_FLOUR_DIS_SPD = 5
    DAK_FLOUR_MIX_SPD = 10
    DAK_FLOUR_MIX_POS = 6
    DAK_FLOUR_MIX_TIME = 1000
    
    ## Water %
    DAK_WATER_PERCENT = 0.72

    ## Oil Weight
    DAK_OIL_WT = 1.3

    ##no activation retries
    NO_ACTIVATION_RETRY_TIMES = 3
    
    TOP_PRESS_TEMP = 130

    BTM_PRESS_TEMP = 110

    def __init__(self):
        self.myDak = dak()
        self.myUpr = upr()
        #self.htReport = HtReport(500)
        # self.uihelper = uihelper.uihelper(2)
        
        # This config is used to enable machine's modules, only used for 
        # machines lacking of some modules during development
        self._dakModuleDisable = {}
        self._uprModuleDisable = {}

        # Fans name
        self.SIDE_FAN_ON = Fan.FAN1_ON
        self.SIDE_FAN_OFF = Fan.FAN1_OFF
        self.VT_FAN_ON = Fan.FAN2_ON
        self.VT_FAN_OFF = Fan.FAN2_OFF
        self.TOP_FAN_ON = Fan.FAN3_ON
        self.TOP_FAN_OFF = Fan.FAN3_OFF
        self.BTM_FAN_ON = Fan.FAN4_ON
        self.BTM_FAN_OFF = Fan.FAN4_OFF

        # Fans ID
        self.SIDE_FAN_ID = 0x00
        self.VT_FAN_ID = 0x01
        self.TOP_FAN_ID = 0x02
        self.BTM_FAN_ID = 0x03

        # Kneading configs
        self._kneadingConfig = [
            {KnStrs.vtPos : 2,  KnStrs.vtSpd : 20, KnStrs.knSpd : 4,  KnStrs.knTime : 4000},

            {KnStrs.vtPos : 3,  KnStrs.vtSpd : 20, KnStrs.knSpd : 5,  KnStrs.knTime : 6000}, 
            {KnStrs.vtPos : 3,  KnStrs.vtSpd : 20, KnStrs.knSpd : 8, KnStrs.knTime : 6000},
            {KnStrs.vtPos : 4,  KnStrs.vtSpd : 20, KnStrs.knSpd : 10, KnStrs.knTime : 10000},
            {KnStrs.vtPos : 5,  KnStrs.vtSpd : 20, KnStrs.knSpd : 10, KnStrs.knTime : 4000},
            
            {KnStrs.vtPos : 9,  KnStrs.vtSpd : 20, KnStrs.knSpd : 10, KnStrs.knTime : 1000},
            {KnStrs.vtPos : 5,  KnStrs.vtSpd : 20, KnStrs.knSpd : 10, KnStrs.knTime : 5000},
            
            {KnStrs.vtPos : 12,  KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 2000},
            {KnStrs.vtPos : 8,  KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 3000},
            {KnStrs.vtPos : 14,  KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 2000},
            {KnStrs.vtPos : 9,  KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 3000},
            {KnStrs.vtPos : 11,  KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 2000}, 
            {KnStrs.vtPos : 18,  KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 4000},
            {KnStrs.vtPos : 30, KnStrs.vtSpd : 20, KnStrs.knSpd : 13, KnStrs.knTime : 1000},
            {KnStrs.vtPos : 30, KnStrs.vtSpd : 20, KnStrs.knSpd : 50, KnStrs.knTime : 4000},
    
            {KnStrs.vtPos : 30, KnStrs.vtSpd : 20, KnStrs.knSpd : 50, KnStrs.knTime : 1000}
           
        ]
    
        # Configs
        self.dakInit()
        self.uprInit()
        
    def dakInit(self):
        ## Set the weight gain
        self.myDak.ds.set_param(DS.DS_ID_FLOUR, DS.DS_PARAM_WEIGHTSCALE_GAIN, self.DAK_LC_WG)
        
        ## Set available modules, this setting is for development
        self.myDak.DisableModules(self._dakModuleDisable) #TODO: remove this for production code
        
        ## Set dispensing function
        self.myDak.SetDispenseFunction(self._dispense_by_time)

        ## Kneading Configs
        self.myDak.KneadingConfig(self._kneadingConfig)

    def KneadingConfig(self, knead_config):
        self.myDak.KneadingConfig(knead_config)
    
    def PressingConfig(self, press_config):
        self.myUpr.PressingConfig(press_config)

    def RoastingConfig(self, roast_config):
        self.myUpr.RoastingConfig(roast_config)

    def CoolingConfig(self, cool_config):
        self.myUpr.CoolingConfig(cool_config)

    def TransferConfig(self, transfer_config):
        self.myUpr.TransferringConfig(transfer_config)

    async def SetVTLimit(self):
        vtTopLimit = 0
        retCmdVal = self.myDak.vt.find_top_limit()
        if not retCmdVal:
            self.debugPrint("VT Top Limit sending error")
            return

        retVal = await self.myDak.vt.wait()
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            vtTopLimit = self.myDak.vt.get_status().pos
            self.myDak.SetVtLimit(vtTopLimit)
            self.debugPrint("VT Top Limit:{}".format(vtTopLimit))
        else:
            self.debugPrint("VT Top Limit execution error: {}".format(retVal))

        return retVal, vtTopLimit


    async def _dispense_by_time(self):
        self.debugPrint("Start Dispensing")
        totalTime = 0
        
        await self.myUpr._exe_conf([
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.VT_FAN_ID, 0]}
        ])
        ## Flour Dispensing 1st time
        retVal, exeTime = await self.myDak.DispenseElementByTime(DSConstants.DS_ID_FLOUR, 5000, self.DAK_FLOUR_DIS_SPD, 
            self.DAK_DIS_VT_POS - 5, self.DAK_DIS_VT_SPD)
        totalTime += exeTime
        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            self.debugPrint("Flour dispensing error")

        ## Mixing
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, exeTime = await self.myDak.FlourMixing(self.DAK_FLOUR_MIX_POS, self.DAK_DIS_VT_SPD, self.DAK_FLOUR_MIX_SPD, self.DAK_FLOUR_MIX_TIME)
            totalTime += exeTime
            if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                self.debugPrint("Flour mixing error")

        ## Water Dispensing
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, exeTime = await self.myDak.DispenseElementByTime(DSConstants.DS_ID_WATER, self.DAK_WATER_DIS_TIME, 0,
                self.DAK_DIS_VT_POS_WATER_OIL - 5, self.DAK_DIS_VT_SPD)
            totalTime += exeTime
            if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                self.debugPrint("Water dispense error")

        ## Oil Dispensing
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, exeTime = await self.myDak.DispenseElementByTime(DSConstants.DS_ID_OIL, self.DAK_OIL_DIS_TIME, 0,
                self.DAK_DIS_VT_POS_WATER_OIL - 5, self.DAK_DIS_VT_SPD)
            totalTime += exeTime
        # Turn on VT Fan
        await self.myUpr._exe_conf([
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.VT_FAN_ID, 100]}
        ])
        self.debugPrint("End Dispensing")
        return retVal, totalTime

    ## For debugging only
    async def _dakProcessingByWeight(self):
        totalTime = 0
        kneadTime = 0
        disTime = 0
        retVal, disTime = await self._dispense_by_weight()
        totalTime += disTime
        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            self.debugPrint("Dispensing Error!!! Stop DAK Processing")

        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, kneadTime = await self.myDak._knead()
            totalTime += kneadTime
        
        flourWt, waterWt, oilWt = self.myDak.GetWeightReport()
        self.debugPrint("Flour Weight    : {}".format(flourWt))
        self.debugPrint("Water Weight    : {}".format(waterWt))
        self.debugPrint("Oil Weight      : {}".format(oilWt))
        self.debugPrint("Doughball Weight: {}".format(flourWt + waterWt + oilWt))
        self.debugPrint("Dispensing Time : {}".format(disTime))
        self.debugPrint("Kneading Time   : {}".format(kneadTime))
        return retVal, totalTime

    async def _dakProcessingByTime(self):
        totalTime = 0
        retVal, disTime = await self._dispense_by_time()
        totalTime += disTime
        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            self.debugPrint("Dispensing Error!!! Stop DAK Processing")
        
        else:
            retVal, kneadTime = await self.myDak._knead()
            totalTime += kneadTime

        self.debugPrint("Dispensing Time: {}".format(disTime))
        self.debugPrint("Kneading Time  : {}".format(kneadTime))
        return retVal, totalTime

    async def _dispense_flour_by_weight(self):
        self.debugPrint("Start FLOUR Dispensing")
        totalTime = 0
        tries = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR
        flourWt = 0
        expectedWt = self.DAK_FLOUR_WT
        totalWt = 0
        TOLERANCE = 2.0

        while tries < self.NO_ACTIVATION_RETRY_TIMES:
            start = time.time()
            retVal, exeTime = await self.myDak.DispenseByWeight(DS.DS_ID_FLOUR, expectedWt, self.DAK_FLOUR_DIS_SPD, self.DAK_DIS_VT_POS, 
                                                                    self.DAK_DIS_VT_SPD)
            
            flourWt, _, _ =  self.myDak.GetWeightReport() 

            totalTime += exeTime
            totalWt += flourWt

            if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                self.debugPrint("FLOUR dispensed timeout {}".format(time.time() - start))
                self.debugPrint("FLOUR dispensed {} with retries {}".format(flourWt, tries))
                if flourWt < expectedWt:
                    expectedWt = expectedWt - flourWt
                    self.debugPrint("FLOUR Dispensing REMAINING: {}".format(expectedWt))
                ds.clear_error_flags(DS.DS_ID_FLOUR)
            else:
                if flourWt > expectedWt - TOLERANCE and flourWt < expectedWt + TOLERANCE:
                    self.debugPrint("FLOUR Dispensing: expected: {}, dispensed: {}, PASSED".format(expectedWt, flourWt))
                else:
                    retVal = CommandRetCode.CMD_RETCODE_GENERR
                    self.debugPrint("FLOUR Dispensing: expected: {}, dispensed: {}, FAILED".format(expectedWt, flourWt))
                break      
                    
            tries += 1   
            await uasyncio.sleep(2) 
            
        self.debugPrint("Total FLOUR Dispensed: expected: {}, dispensed: {}".format(self.DAK_FLOUR_WT, totalWt))

        if tries == self.NO_ACTIVATION_RETRY_TIMES:
            retVal = CommandRetCode.CMD_RETCODE_GENERR
            self.debugPrint("FLOUR DISPENSING FAILS AFTER RETRYING {} TIMES ACTIVATION".format(self.NO_ACTIVATION_RETRY_TIMES))

        # Flour Mixing
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, exeTime = await self.myDak.FlourMixing(self.DAK_FLOUR_MIX_POS, self.DAK_DIS_VT_SPD, self.DAK_FLOUR_MIX_SPD, self.DAK_FLOUR_MIX_TIME)
            totalTime += exeTime
            if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                self.debugPrint("Flour mixing error")
        
        self.debugPrint("End FLOUR Dispensing")    
        return retVal, totalTime, totalWt

    async def _dispense_water_by_weight(self, flourWt):                                                        
        self.debugPrint("Start WATER Dispensing")
        totalTime = 0
        tries = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR
        waterWt = 0
        DAK_WATER_WT = round(flourWt * self.DAK_WATER_PERCENT, 1)
        expectedWt = DAK_WATER_WT
        totalWt = 0
        TOLERANCE = 2.0

        while tries < self.NO_ACTIVATION_RETRY_TIMES:
            start = time.time()
            retVal, exeTime = await self.myDak.DispenseByWeight(DS.DS_ID_WATER, expectedWt, 0, self.DAK_DIS_VT_POS, self.DAK_DIS_VT_SPD)
            _, waterWt, _ = self.myDak.GetWeightReport()

            totalTime += exeTime
            totalWt += waterWt

            if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                self.debugPrint("WATER dispensed timeout {}".format(time.time() - start))
                self.debugPrint("WATER dispensed {} with retries {}".format(waterWt, tries))
                if waterWt < expectedWt:
                    expectedWt = expectedWt - waterWt
                    self.debugPrint("WATER Dispensing REMAINING: {}".format(expectedWt))
                ds.clear_error_flags(DS.DS_ID_WATER)
            else:
                if waterWt > expectedWt - TOLERANCE and waterWt < expectedWt + TOLERANCE:
                    self.debugPrint("WATER Dispensing: expected: {}, dispensed: {}, PASSED".format(expectedWt, waterWt))
                else:
                    retVal = CommandRetCode.CMD_RETCODE_GENERR
                    self.debugPrint("WATER Dispensing: expected: {}, dispensed: {}, FAILED".format(expectedWt, waterWt))     
                break

            tries += 1   
            await uasyncio.sleep(2)

        self.debugPrint("Total WATER Dispensed: expected: {}, dispensed: {}".format(DAK_WATER_WT, totalWt))

        if tries == self.NO_ACTIVATION_RETRY_TIMES:
            retVal = CommandRetCode.CMD_RETCODE_GENERR
            self.debugPrint("WATER DISPENSING FAILS AFTER RETRYING {} TIMES ACTIVATION".format(self.NO_ACTIVATION_RETRY_TIMES))
            
        self.debugPrint("End WATER Dispensing")
        return retVal, totalTime, totalWt

    async def _dispense_oil_by_weight(self): 
        self.debugPrint("Start OIL Dispensing")
        totalTime = 0
        tries = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR
        oilWt = 0
        expectedWt = self.DAK_OIL_WT
        totalWt = 0
        TOLERANCE = 1.0

        while tries < self.NO_ACTIVATION_RETRY_TIMES:
            start = time.time()
            retVal, exeTime = await self.myDak.DispenseByWeight(DS.DS_ID_OIL, expectedWt, 0, self.DAK_DIS_VT_POS, self.DAK_DIS_VT_POS)
            _,_,oilWt = self.myDak.GetWeightReport()

            totalTime += exeTime
            totalWt += oilWt

            if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                self.debugPrint("OIL dispensed timeout {}".format(time.time() - start))
                self.debugPrint("OIL dispensed {} with retries {}".format(oilWt, tries))
                if oilWt < expectedWt:
                    expectedWt = expectedWt - oilWt
                    self.debugPrint("OIL Dispensing REMAINING: {}".format(expectedWt))
                ds.clear_error_flags(DS.DS_ID_OIL)
            else:
                if oilWt > expectedWt- TOLERANCE and oilWt < expectedWt + TOLERANCE:
                    self.debugPrint("OIL Dispensing: expected: {}, dispensed: {}, PASSED".format(expectedWt, oilWt))
                else:
                    retVal = CommandRetCode.CMD_RETCODE_GENERR
                    self.debugPrint("OIL Dispensing: expected: {}, dispensed: {}, FAILED".format(expectedWt, oilWt))
                break        
                     
            tries += 1   
            await uasyncio.sleep(2)

        self.debugPrint("Total OIL Dispensed: expected: {}, dispensed: {}".format(self.DAK_OIL_WT, totalWt))

        if tries == self.NO_ACTIVATION_RETRY_TIMES:
            retVal = CommandRetCode.CMD_RETCODE_GENERR
            self.debugPrint("OIL DISPENSING FAILS AFTER TRYING {} TIMES ACTIVATION".format(self.NO_ACTIVATION_RETRY_TIMES))

        self.debugPrint("End OIL Dispensing")
        return retVal, totalTime, totalWt

    async def _dispense_by_weight(self):
        
        # Weight, weight_at_each_dispense, dis_speed, vtPos, vtSpd, mix_pos, mix_spd, mix_time
        # Turn off VT Fan
        await self.myUpr._exe_conf([
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.VT_FAN_ID, 0]}
        ])
        
        ## Flour Dispensing by weight
        retVal, totalTime, flourWt = await self._dispense_flour_by_weight()

        ## Water Dispensing by weight
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, totalTime, _ = await self._dispense_water_by_weight(flourWt)

        ## Oil Dispensing
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, totalTime, _ = await self._dispense_oil_by_weight()
        
        # Turn on VT Fan
        await self.myUpr._exe_conf([
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.VT_FAN_ID, 100]}
        ])

        # If dispensing fail, move VT to highest position for safety 
        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            await self.myDak._exe_conf([
                {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["move_block", 40, 35]}
            ])
            
        self.debugPrint("End Dispensing")
        return retVal, totalTime
        
    def uprInit(self):
        self.myUpr.DisableModules(self._uprModuleDisable) ## TODO: remove this for production code
        self._uprPressingInit()
        self._uprRoastingInit()
        self._uprCoolingInit()
        self._uprTransferringInit()

    def _uprTransferringInit(self):
        self.myUpr.TransferringConfig([
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 330, 200]},
            #{DakUprStrs.module : DakUprStrs.wp, "cmd" : [54, 5, 500]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [ 5, 5, 500]}
        ])
        
    def _uprPressingInit(self):
        self.myUpr.PressingConfig([
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["asyn",54, 54, 500]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 0, 200]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [50, 8, 500]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_TOP]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["press", 8, 500]}, # Press moving only
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["press", 30,500]},  # Press moving only
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_TOP, 245, 0.4, 240]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_BTM, 235, 0.6, 230]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [30,  30,  500]}
        ])

    async def Tapping(self):
        config_array = [
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [54, 54, 500]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 0, 200]},
        ]
        return await self.myUpr._exe_conf(config_array)

    async def WaitingPressTemp(self):
        config_array = [
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.SIDE_FAN_ID, 0]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdEQ, self.TOP_PRESS_TEMP, self.BTM_PRESS_TEMP, 10, 300000]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.BTM_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.TOP_FAN_ID,  0]},
        ]
        return await self.myUpr._exe_conf(config_array)


    def _uprRoastingInit(self):
       self.myUpr.RoastingConfig([
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [45, 40, 500]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [21000]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [35, 30, 500]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [5000]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [44, 40, 1000]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [22000]},
            
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [33, 30, 5000]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [2000]},
            

            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [58, 58, 500]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_BTM]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_TOP]},
            
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.BTM_FAN_ID,  100]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.TOP_FAN_ID,  100]},
        ])
        
    async def _uprKickingRoti_step1(self):
        config_array = [
            ## Kicker move step 1
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.chCmdOn, HT.HT_ID_CHARBTM, 45000]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.chCmdOn, HT.HT_ID_CHARTOP, 45000]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [3000]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 120, 100]}, # Take 5 sec
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [1000]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["rel", 160, 10, 10, 0]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["rel", 260, 10, 150, 0]}, # Take 15 sec
            #{DakUprStrs.module : DakUprStrs.kr, "cmd" : ["rel", 260, 10, 20, 0]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.chCmdOff, HT.HT_ID_CHARBTM]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["rel", 310, 10, 10, 0]},
        ]
        return await self.myUpr._exe_conf(config_array)
        
    async def _uprKickingRoti_step2(self):
        config_array = [
            ## Kicker move step 2
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.chCmdOff, HT.HT_ID_CHARTOP]},
            #{DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 180, 200]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 330, 265]},
            #{DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.BTM_FAN_ID,  0]},
            #{DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.TOP_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.SIDE_FAN_ID,  100]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdLE, HT.HT_ID_BTM, self.BTM_PRESS_TEMP, 300000]}, #20 gap 
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdLE, HT.HT_ID_TOP, self.TOP_PRESS_TEMP, 300000]}, #20 gap
        ]
        return await self.myUpr._exe_conf(config_array)

    def _uprCoolingInit(self):
        self.myUpr.CoolingConfig([
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_BTM]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_TOP]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.SIDE_FAN_ID,  100]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.BTM_FAN_ID,  100]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.TOP_FAN_ID,  100]},
            ## Wait for heaters cooling down
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdLE, HT.HT_ID_BTM, self.BTM_PRESS_TEMP, 300000]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdLE, HT.HT_ID_TOP, self.TOP_PRESS_TEMP, 300000]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.SIDE_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.BTM_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.TOP_FAN_ID,  0]},
        ])
    
    async def warmUp(self, topTemp, topDuty, topBeginTemp, btmTemp, btmDuty, btmBeginTemp, warmupTime, charOnTime):
        retVal, exeTime = await self.myUpr._exe_conf([
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.SIDE_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.BTM_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.fa, "cmd" : ["pwm", self.TOP_FAN_ID,  0]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_TOP, topTemp, topDuty, topBeginTemp]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_BTM, btmTemp, btmDuty, btmBeginTemp]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [warmupTime]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_BTM]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_TOP]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.chCmdOn, HT.HT_ID_CHARTOP, charOnTime]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.chCmdOn, HT.HT_ID_CHARBTM, charOnTime]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [charOnTime]}
        ])

        return retVal, exeTime
    
    async def transferDough(self):
         self.debugPrint("Closing Press for getting Doughball")
         return await self.myUpr.PerformTransfer()
    
    async def performUPR(self):
        transferTime = 0
        pressTime = 0
        roastTime = 0
        coolTime = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR

        retVal, transferTime = await self.myUpr._exe_conf([
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [62, 54, 500]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 330, 50]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [3000]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 160, 50]},
        ])

        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, pressTime = await self.myUpr._performPressing()
        
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, roastTime = await self.myUpr._performRoasting()

        #transfer roti out step 1
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, kickTime_step1 = await self._uprKickingRoti_step1()
        
        #transfer roti out step 2
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, kickTime_step2 = await self._uprKickingRoti_step2()

        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, coolTime = await self.myUpr._performCooling()

        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            ht.set_state(HT.HT_ID_TOP, 0, 0, 0, 0)
            ht.set_state(HT.HT_ID_BTM, 0, 0, 0, 0)
            ht.char_set_state_safe()
        
        self.debugPrint("Transferring Time: {}".format(transferTime))
        self.debugPrint("Pressing Time: {}".format(pressTime))
        self.debugPrint("Roasting Time: {}".format(roastTime))
        self.debugPrint("Kicking Time: {}".format(kickTime_step1 + kickTime_step2))
        self.debugPrint("Cooling Time: {}".format(coolTime))
        return retVal, (transferTime + pressTime + roastTime +coolTime)
    
    async def transferRoti(self):
        pass

    async def start_roti_making(self, numberOfRotis):
        roti_count = numberOfRotis
        roti_made = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR

        self.myDak.start_dak()
        await self.myUpr._exe_conf([
                    {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_TOP, self.TOP_PRESS_TEMP, 0.5, self.TOP_PRESS_TEMP-10]},
                    {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_BTM, self.BTM_PRESS_TEMP, 0.5, self.BTM_PRESS_TEMP-10]}
                ])
        
        while roti_made < roti_count:
            self.debugPrint("Making Roti {} / {}".format(roti_made+1, roti_count))
            waitingDbTime = await self.myDak.wait_for_dak_to_finish()
            roti_made = roti_made + 1
            coolTime = 0
            tappingTime = 0
            waitPressTemp = 0
            transferTime = 0
            kickTime_step1 = 0
            kickTime_step2 = 0
            pressTime = 0
            dbDropTime = 0

            ## Only do UPR processing when dougball created successfully
            if self.myDak.GetDoughballState() == 1:
                dispensingTime, kneadingTime = self.myDak.GetTimeReport()
                flourWt, waterWt, oilWt = self.myDak.GetWeightReport()

                #drop dough only for 1st db
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, dbDropTime = await self.doughDropWithRetry(flourWt + waterWt + oilWt, 5, 500, -30, 25, 3, 62, 50)
                    if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                        self.debugPrint("Dropping Doughball Failed!!! Stop the cycle")
                
                ## TODO: change this logic for parallel processing
                if roti_made < roti_count and retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    self.myDak.start_dak()

                ## Tapping
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, tappingTime = await self.Tapping()
                ## Waiting for temperature
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, waitPressTemp = await self.WaitingPressTemp()
                ## Pressing
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    self.debugPrint("TOP: {}, BTM: {}".format(self.myUpr.ht.get_status().ht1_temp, self.myUpr.ht.get_status().ht2_temp))
                    self.debugPrint("Start Pressing")
                    retVal, pressTime = await self.myUpr._performPressing()
                    self.debugPrint("Finish Pressing")

                #start upr
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    self.myUpr.start_upr()
                    await self.myUpr.wait_for_upr_to_finish()
                
                #transfer roti out step 1
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, kickTime_step1 = await self._uprKickingRoti_step1()
                
                #transfer roti out step 2
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, kickTime_step2 = await self._uprKickingRoti_step2()
                
                #Timing & Weight report
                _, roastTime,_ = self.myUpr.GetTimeReport()
                self.debugPrint("Roti no. {}".format(roti_made))
                self.debugPrint("Flour Weight      : {}".format(flourWt))
                self.debugPrint("Water Weight      : {}".format(waterWt))
                self.debugPrint("Oil Weight        : {}".format(oilWt))
                self.debugPrint("Doughball Weight  : {}".format(flourWt + waterWt + oilWt))
                self.debugPrint("Dispensing Time   : {}".format(dispensingTime))
                self.debugPrint("Kneading Time     : {}".format(kneadingTime))
                self.debugPrint("Waiting DB Time   : {}".format(waitingDbTime))
                # self.debugPrint("Transferring Time : {}".format(transferTime))
                self.debugPrint("Db Dropping Time  : {}".format(dbDropTime))
                self.debugPrint("Tapping Time      : {}".format(tappingTime))
                self.debugPrint("Cooling Time      : {}".format(waitPressTemp))
                # self.debugPrint("Cooling Time      : {}".format(coolTime))
                self.debugPrint("Pressing Time     : {}".format(pressTime))
                self.debugPrint("Roasting Time     : {}".format(roastTime))
                self.debugPrint("Kicking Time      : {}".format(kickTime_step1 + kickTime_step2))
                self.debugPrint("Total Time       : {}".format(waitingDbTime + tappingTime + waitPressTemp +
                    transferTime + dbDropTime + pressTime + roastTime + coolTime + kickTime_step1 + kickTime_step2))
                
                ## Report the HT During Roasting
                #for ht in self.htReport.GetHTArray():
                #    self.debugPrint(ht)
                
                await uasyncio.sleep(1)
            else:
                await self.myDak._exe_conf([
                    {DakUprStrs.module : DakUprStrs.kn, "cmd" : ["stop"]}
                ])
                self.debugPrint("Doughball creating failed!!! STOP THE ROTI CYCLE")
                break

        ## Cooling for last roti
        await self.myUpr._performCooling()

    async def doughDropWithRetry(self, dbWeight, wtTol, waitTime, vtLowPos, vtWtPos, attempt, pressPos, wedgePos):
        self.debugPrint("Doughball Drop, dbWt: {:.2f}".format(dbWeight))
        wtAfter = 0.0
        dbIsDropped = False
        curTryTime = 0

        ## Getting the current weight
        wtBefore = self.myDak.ds.get_status(0).weight
        self.debugPrint("Before Wt :{:.2f}".format(wtBefore))

        ## Exe time
        dbDropFirstTryExeTime = 0
        dbDropCommandLastMoveExeTime = 0
        dbDropRetryExeTime = 0

        dbDropCommandFirstTry = [
            {DakUprStrs.module : DakUprStrs.kn, "cmd" : ["run", 20]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 330, 50]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : [35, 5, 500]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["asyn", 5, 5, 500]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["move_nonblock", vtLowPos, 35]},
            {DakUprStrs.module : DakUprStrs.kn, "cmd" : ["stop"]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [waitTime]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_TOP, self.TOP_PRESS_TEMP, 0.5, self.TOP_PRESS_TEMP-10]},
            {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_BTM, self.BTM_PRESS_TEMP, 0.5, self.BTM_PRESS_TEMP-10]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["move_nonblock", vtWtPos, 35]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["asyn", 35, 5, 500]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [waitTime]},
        ]

        dbDropCommandLastMove = [
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["move_nonblock", 45, 35]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["asyn", pressPos, wedgePos, 500]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 180, 100]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.kr, "cmd" : ["abs", 160, 50]}
        ]

        dbDropCommandRetry = [
            {DakUprStrs.module : DakUprStrs.kn, "cmd" : ["run", 20]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["asyn", 5, 5, 500]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["move_nonblock", vtLowPos, 35]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [waitTime]},
            {DakUprStrs.module : DakUprStrs.kn, "cmd" : ["stop"]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["move_nonblock", vtWtPos, 35]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["asyn", 35, 5, 500]},
            {DakUprStrs.module : DakUprStrs.vt, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.wp, "cmd" : ["wait"]},
            {DakUprStrs.module : DakUprStrs.sl, "cmd" : [waitTime]},
        ]

        retVal, dbDropFirstTryExeTime = await self.myDak._exe_conf(dbDropCommandFirstTry)
        if retVal == CommandRetCode.CMD_RETCODE_NOERR:
            wtAfter = self.myDak.ds.get_status(0).weight
            self.debugPrint("After Wt: {:.2f}".format(wtAfter))
            ## Do comparison with wtTol
            if wtAfter <= (wtBefore - dbWeight) + wtTol:
                dbIsDropped = True

        # Check if the doughball is already dropped, execute the retry
        if dbIsDropped != True and retVal == CommandRetCode.CMD_RETCODE_NOERR:
            while curTryTime < attempt:
                retVal, exeTime = await self.myDak._exe_conf(dbDropCommandRetry)
                dbDropRetryExeTime += exeTime
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    wtAfter = self.myDak.ds.get_status(0).weight
                    self.debugPrint("After Wt: {:.2f}".format(wtAfter))
                    ## Do comparison with wtTol
                    if wtAfter <= (wtBefore - dbWeight ) + wtTol:
                        dbIsDropped = True
                        break
                else:
                    break
                
                curTryTime += 1

        if dbIsDropped == True and retVal == CommandRetCode.CMD_RETCODE_NOERR:
            retVal, dbDropCommandLastMoveExeTime = await self.myDak._exe_conf(dbDropCommandLastMove)
        else:
            retVal = CommandRetCode.CMD_RETCODE_GENERR

        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            self.debugPrint("Doughball Rounding Error!!!")

        ## Stop the kneader if something wrong
        if retVal != CommandRetCode.CMD_RETCODE_NOERR:
            await self.myDak._exe_conf([
                {DakUprStrs.module : DakUprStrs.kn, "cmd" : ["stop"]},
                {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_TOP]},
                {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdOFF, HT.HT_ID_BTM]},
            ])
        
        return retVal, dbDropFirstTryExeTime + dbDropRetryExeTime + dbDropCommandLastMoveExeTime

    async def start_roti_pressing(self):
        roti_count = 1
        roti_made = 0
        retVal = CommandRetCode.CMD_RETCODE_NOERR

        self.myDak.start_dak()
        await self.myUpr._exe_conf([
                    {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_TOP, self.TOP_PRESS_TEMP, 0.5, self.TOP_PRESS_TEMP-10]},
                    {DakUprStrs.module : DakUprStrs.ht, "cmd" : [DakUprStrs.htCmdON, HT.HT_ID_BTM, self.BTM_PRESS_TEMP, 0.5, self.BTM_PRESS_TEMP-10]}
                ])
        
        while roti_made < roti_count:
            self.debugPrint("Making Roti {} / {}".format(roti_made+1, roti_count))
            waitingDbTime = await self.myDak.wait_for_dak_to_finish()
            roti_made = roti_made + 1
            coolTime = 0
            transferTime = 0
            kickTime_step1 = 0
            kickTime_step2 = 0

            ## Only do UPR processing when dougball created successfully
            if self.myDak.GetDoughballState() == 1:
                dispensingTime, kneadingTime = self.myDak.GetTimeReport()
                flourWt, waterWt, oilWt = self.myDak.GetWeightReport()

                #drop dough only for 1st db
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, dbDropTime = await self.doughDropWithRetry(flourWt + waterWt + oilWt, 5, 1000, -30, 25, 3, 62, 50)
                    if retVal != CommandRetCode.CMD_RETCODE_NOERR:
                        self.debugPrint("Dropping Doughball Failed!!! Stop the cycle")
                
                ## TODO: change this logic for parallel processing
                # if roti_made < roti_count and retVal == CommandRetCode.CMD_RETCODE_NOERR:
                #     self.myDak.start_dak()

                ## Tapping
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, tappingTime = await self.Tapping()
                ## Waiting for temperature
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    retVal, waitPressTemp = await self.WaitingPressTemp()
                ## Pressing
                if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                    self.debugPrint("TOP: {}, BTM: {}".format(self.myUpr.ht.get_status().ht1_temp, self.myUpr.ht.get_status().ht2_temp))
                    self.debugPrint("Start Pressing")
                    retVal, pressTime = await self.myUpr._performPressing()
                    self.debugPrint("Finish Pressing")

                #start pressing
                #if retVal == CommandRetCode.CMD_RETCODE_NOERR:
                #    self.myUpr.start_upr()
                #    await self.myUpr.wait_for_upr_to_finish()
                
                self.debugPrint("Roti no. {}".format(roti_made))
                self.debugPrint("Flour Weight      : {}".format(flourWt))
                self.debugPrint("Water Weight      : {}".format(waterWt))
                self.debugPrint("Oil Weight        : {}".format(oilWt))
                self.debugPrint("Doughball Weight  : {}".format(flourWt + waterWt + oilWt))
                self.debugPrint("Dispensing Time   : {}".format(dispensingTime))
                self.debugPrint("Kneading Time     : {}".format(kneadingTime))
                self.debugPrint("Waiting DB Time   : {}".format(waitingDbTime))
                self.debugPrint("Db Dropping Time  : {}".format(dbDropTime))
                self.debugPrint("Tapping Time      : {}".format(tappingTime))
                self.debugPrint("Cooling Time      : {}".format(waitPressTemp))
                self.debugPrint("Pressing Time     : {}".format(pressTime))
                #self.debugPrint("Kicking Time      : {}".format(kickTime_step1 + kickTime_step2))
                self.debugPrint("Total Time       : {}".format(waitingDbTime + 
                    dbDropTime + tappingTime + waitPressTemp + pressTime))
                
                ## Report the HT During Roasting
                #for ht in self.htReport.GetHTArray():
                #    self.debugPrint(ht)
                
                await uasyncio.sleep(1)
            else:
                self.debugPrint("Doughball creating failed!!! STOP THE ROTI CYCLE")
                break

        ## Cooling for last roti
        await self.myUpr._performCooling()

    async def handleError(self, err_str):
        if (err_str == "drop-err"):
            # value = await self.uihelper.showErrorDialog("Clean the dough and press Enter!")
            
            await uasyncio.sleep(2)

    def debugPrint(self, message):
        # self.uihelper.debugPrint(message)
        print("rotiapp " + message)
        logger.debug({'rotiapp': message})
