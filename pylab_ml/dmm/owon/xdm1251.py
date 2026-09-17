"""Measuremet-Unit (DMM) Owon XDM1251.

:Date: |today|
:Author: semi-ate <info@semi-ate.de>

https://www.ivifoundation.org/downloads/SCPI/scpi-99.pdf

.. pdf:: ../_static/XDM1000_Digital_Multimeter_Programming_Manual.pdf

"""
import bisect
from enum import Enum
from time import sleep
from pylab_ml.base_instrument import logger
from pylab_ml.collate_instrument import Interface
from pylab_ml.baseclass.base_measurement import Measure
from pylab_ml.attributes import create_attributes


class XDM1251(create_attributes, Measure):
    """
    Interface to the Measuremet-Unit (DMM) Owon XDM1251.

    The Owon XDM1251 can measure voltage, current, resistance, frequency, precisely

    :Date: |today|
    :Author: Semi-ATE <info@Semi-ATE.org>

    .. image:: ../_static/owon_xdm1251.jpg

    TODO: Calc commands not implemented
    """

    interchoices = [Interface.usbserial]
    time_beetween_functionswitch = 2.0

    _properties = {
        "beeper":      ((':SYST:BEEP:STAT?', ':SYST:BEEP:STAT '), "Beeper", {"ga": "_trstr(value)"}),
        "function":    ((':SENSE:FUNC?',  ":CONF:"),     "Function",    {"ga": "_trstr(value)"}),
        "current":     ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "capacitance": ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "diode":       ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "frequence":   ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "fresistance": ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "period":      ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "resistance":  ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "speed":       ((':RATE?',        ":RATE "),     "Speed",        None),
        "temperature": ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
        "voltage":     ((':MEAS?',         None),        None,          {"gb": "_checkfunction(value)"}),
    }

    class Beeper(Enum):
        """
        Possible setup for the beeper.

        on : set beeper on,
        off : set beeper off,

        """
        on = 'on'
        off = 'off'

    class Speed(Enum):
       """
       Possible speed for the instrument.

       F : high speed,
       M : middle speed,
       S : low speed

       """
       fast = 'F'
       mid  = 'M'
       slow = 'S'

    class Function(Enum):
       """
       Possible functions for the instrument.

       VOLT    : 'VOLT:DC'
       VOLT_AC : 'VOLT:AC'
       CURR    : 'CUR:DC'
       CURR_AC : 'CUR:AC'
       RES     : 'RES'
       FRES    : 'FRES'           # 4 Wire Res
       FREQ    : 'FREQ'
       PER     : 'PER',
       CAP     : 'CAP'
       TEMP    : 'TEMP'
       DIOD    : 'DIOD'

       """
       VOLT    = 'VOLT'
       VOLT_AC = 'VOLT:AC'
       CURR    = 'CURR'
       CURR_AC = 'CURR:AC'
       RES     = 'RES'
       FRES    = 'FRES'           # 4 Wire Res, setting not possible!?
       FREQ    = 'FREQ'
       PER     = 'PER'
       CAP     = 'CAP'
       TEMP    = 'TEMP'
       DIOD    = 'DIOD'


    RANGES = {
            "VOLT": [
                0.1,                # 100mV
                1,                  # 1V
                10,                 # 10V
                100,                # 100V
                1000],              # 1000V
            "VOLT_AC": [
                500E-3,             # 500mV
                5,                  # 5V
                50,                 # 50V
                500,                # 500V
                750],               # 750V
            "CURR": [
                50E-3,              # 50mA
                500E-3,             # 500mA
                5,                  # 5A
                10],                # 10A
            "CURR_AC": [
                50E-3,              # 50mA
                500E-3,             # 500mA
                5,                  # 5A
                10],                # 10A
            "RES": [
                100,                # 100Ohm
                1000,               # 1kOhm
                10E3,               # 10kOhm
                1E6,                # 1MOhm
                10E6,               # 10MOhm
                100E6],             # 100MOhm
            "FRES": [
                50],                # 50Ohm
            "CAP": [
                50E-9,              # 50nF
                500E-9,             # 500nF
                5E-6,               # 5uF
                50E-6,              # 50uF
                500E-6,             # 500uF
                5E-3,               # 5mF
                50E-3],             # 50mF
            "DIOD": None,
            "FREQ": None,           # no range possible
            "PER":  None,           #
            "TEMP": None,
#                [
#                "KITS90",
#                "PT100"
#                ]
        }

    def __init__(self, addr=None, interface=None, backend=None, identify=True, instName=None, **kwargs):
        """
        Connect and initialize the Owon XDM1251.

        Parameters
        ----------
            addr (int):
                Interface address
            interface (Interface):
                USBSerial
            backend (str):
                visa backend is either '@ni' for NI-Library or
                '@py' for pure python pyvisa-py backend.
                On default it uses '@ni' on win32 and '@py' on
                other platforms.
            instName (string):
                Instance Name from parent.

        Example: Initialization
           >>> vdd = XDM1251(addr=24)       # USB address
           >>> vdd.init()                   # connect and initialize instrument

        Example: Current measurement
           >>> i = vdd.current              # measure (supply) current

        Example: Voltage measurement
           >>> v = vdd.voltage              # measure voltage
        """
        self.is_local = False
        if 'addr' not in kwargs or kwargs['addr'] is None:
            kwargs['addr'] = '2E3C:5760'
        kwargs = {"addr": addr, "interface": interface, "backend": backend, "identify": identify, "instName": instName, **kwargs}
        create_attributes.__init__(self)
        Measure.__init__(self, **kwargs)
        logger.debug("Class {}".format(self.__class__.__name__))
        self.msg_row_col = (1, 12)
        self.com._init(self)

    def setup_inst(self):
        """Start setup instrument settings, called from class instruments."""
        if self.inst:
            self.inst._encoding = 'utf-8'
            self.inst.baud_rate= 115200
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
        self.createattributes(self._properties)

    def error_list(self):
        """List of instrument errors."""
        self.budget.set_slack(self)
        errorlist = []
        while True:
            errormsg = self.inst.query(':SYST:ERR?')
            if errormsg is None or errormsg == "":
                break
            (c, m) = errormsg.split(",")
            print("{} : {}".format(c, m))
            errorlist.append((c, m))
            if errormsg == '0,"No error"':
                break
        return errorlist


    def reset(self):
        """Reset and beep."""
        self.budget.set_slack(self)
        self.inst.write('*RST')
        self.inst.write(':SYST:BEEP')
        self.function_cache = "VOLT"

    @property
    def id(self):
        """Query IDN."""
        self.budget.set_slack(self)
        try:
            value = self.inst.query('*IDN?')
        except Exception:
            value = ""
        return value.replace('\r', '').replace('\n', '')

    def write(self, msg):
        """Write the instance with msg."""
        self.inst.write(msg)

    def read(self):
        """Read the instance."""
        return self.inst.read()

    @property
    def function(self):
        """Get or set measurement method.

        | DC_VOLTS =    DC Voltage
        | AC_VOLTS =    AC Voltage
        | DC_CURRENT =  DC Current
        | AC_CURRENT =  AC Current
        | FREQ = Frequency
        | TEMPERATURE = temperature, PT100 or KITS90
        | CAPACITANCE = Capacitance

        see ....
        """

    def _trstr(self, value):
        if len(value) == 1:
            return 'on' if value == '1' else 'off'
        return value[1:-1]

    def _checkfunction(self, value):
        if (getfunc := value.upper()[0:4]) != self.function_cache.name[0:4]:
            self.function = getfunc[0:3] if getfunc not in self.Function.__members__ else getfunc
            sleep(self.time_beetween_functionswitch)

    def message(self, message=None):
        """
        The XDM has not function to diplay a meassage.
        So this function use the logger.info()

        Parameters
        ----------
            message : str or None
                Message to be displayed on the info print.
        """
        logger.info(message)

    @property
    def range(self):
        """set/get range from the actual measurement function."""
        self.budget.set_slack(self)
        nfunction = self.function_cache.name
        if self.RANGES[nfunction] is None:
            return self.inst.query(':RANG?')
        if self.inst.query(f':SENS:{nfunction}:RANG:AUTO?') == '1':
            return f"auto: {self.inst.query(':RANGE?')}"

        return self.inst.query(f':SENS:{nfunction}:RANGE?')

    @range.setter
    def range(self, value):
        self.budget.set_slack(self)
        vfunction = self.function_cache.value
        nfunction = self.function_cache.name
        if (type(value) is bool and value) or value=='auto':
            self.inst.write(f':CONF:{vfunction} AUTO')
        else:
            _range = self.RANGES[nfunction][bisect.bisect_left(self.RANGES[nfunction], value)]
            self.inst.write(f':CONF:{vfunction} {_range}')
        qrange = self.inst.query(f':SENS:{vfunction}:RANGE?')
        message = f"set range {vfunction}: {qrange}"
        logger.info(message)


if __name__ == "__main__":
    from time import time
    from pylab_ml.base_instrument import logsetup
    import logging

    logsetup()
    addr = None                     # use addr if you have more than 1 device
    dmm = XDM1251(addr=addr, instName='dmm')

    if dmm.inst:
        if True:
            print("Device ID:", dmm.id)
            print(dmm.speed)
            dmm.speed = 'fast'
            print(dmm.speed)

            print(dmm.beeper)
            dmm.beeper = 'off'
            dmm.beeper = 'on'

            print(dmm.function)
            dmm.function = 'CURR'
            dmm.error_list()

            print(dmm.current)
            print(dmm.voltage)
            print(dmm.range)
            dmm.range = 100
            dmm.range = 0.05

            dmm.function = 'VOLT_AC'
            print(dmm.voltage)
            dmm.range = 50
            dmm.range = 0.05

            print(dmm.resistance)
            print(dmm.range)
            dmm.range = 100e3

            #dmm.function = 'FRES'
            #print(dmm.range)

            print(dmm.capacitance)
            print(dmm.range)
            dmm.range = 1e-6

            print(dmm.frequence)
            print(dmm.range)

            print(dmm.fresistance)
            print(dmm.temperature)
            print(dmm.diode)
            print(dmm.range)

            print(dmm.period)
            print(dmm.range)

        dmm.function = 'VOLT'
        dmm.range = 10
        logger.setLevel(logging.INFO)

        vsup = []
        cnt = 100
        for speed in ["slow", "mid", "fast"]:
            dmm.speed = speed
            t = time()
            for i in range (0, cnt):
                vsup.append(dmm.voltage)
            print(f"read {cnt} values with speed={speed} in {time()-t}s")

        dmm.close()

    else:
        print(f"XDM1251 not found at {addr}")
