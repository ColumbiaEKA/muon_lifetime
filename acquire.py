import os
import sys
import time
import serial
import lecroy

def acquire(scope, directory, arm_attempts=20, acquire_attempts=20, poll_wait=0.5):
    scope.clear()
    sweep = 0
    try:
        # This is the main acquisition loop.
        while True:
            sys.stdout.write("Arming:")
            scope.arm()
            for attempt in range(arm_attempts):
                try:
                    internal = scope.internal
                    if internal[13]:
                        sys.stdout.write("Ready:")
                        break
                except lecroy.LeCroyTimeout:
                    sys.stdout.write('.')
            # If the scope fails to arm, try again
            else:
                print("Failed to arm!")
                continue
            # Add timeout condition if necessary.
            while True:
                try:
                    # Check state before re-acquiring as the scope may arm and trigger immediately.
                    if internal[0]:
                        sys.stdout.write("Triggered:")
                        break
                    else:
                        time.sleep(poll_wait)
                        internal = scope.internal
                        sys.stdout.write(':')
                except lecroy.LeCroyTimeout:
                    sys.stdout.write('.')
            for attempt in range(acquire_attempts):
                try:
                    wf, d = scope.parse_waveform(scope.send_and_receive('waveform?'))
                    break
                except lecroy.LeCroyTimeout:
                    sys.stdout.write('.')
            else:
                print("Failed to acquire waveform!")
                continue
            filename = 'sweep{:06}.txt'.format(sweep)
            with open(os.path.join(directory, filename), 'w') as f:
                print('Wrote ' + filename)
            sweep += 1
    except KeyboardInterrupt:
        scope.stop()
        scope.auto_calibrate = True
        scope.local()
        scope.serial.close()
        print("Stopped.")

def main(base_directory):
    data_directory = os.path.join(base_directory, time.strftime('%Y%m%dT%H%M%S'))
    os.mkdir(data_directory)
    print("Writing to {}".format(data_directory))
    port = 'COM1'
    baudrate = 19200 #9600
    timeout = 3
    xonxoff = True
    serial_port = serial.Serial(port, baudrate=baudrate, timeout=timeout, xonxoff=xonxoff)
    scope = lecroy.LeCroy(serial_port)
    scope.remote()
    print("Connected to {}".format(scope.identification))
    scope.auto_calibrate = False
    acquire(scope, data_directory)

if __name__ == "__main__":
    main(sys.argv[1])