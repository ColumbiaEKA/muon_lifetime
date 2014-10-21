import serial
import lecroy

port = 'COM1'
baudrate = 19200 #9600
timeout = 3
xonxoff = True
serial_port = serial.Serial(port, baudrate=baudrate, timeout=timeout, xonxoff=xonxoff)
scope = lecroy.LeCroy(serial_port)
scope.remote()
print("Connected to {}".format(scope.identification))

import pickle
w = pickle.load(open('waveform.pkl'))
