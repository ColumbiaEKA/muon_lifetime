import os
import sys
import time
import serial
import lecroy

def message(string):
    sys.stdout.write(string)
    sys.stdout.flush()

def acquire(scope, directory, arm_attempts=10, acquire_attempts=10, poll_wait=0.5):
    scope.clear()
    sweep = 0
    try:
        # This is the main acquisition loop.
        while True:
            message("Arming:")
            scope.arm()
            arm_timeouts = 0
            while arm_timeouts < arm_attempts:
                try:
                    internal = scope.internal
                    if internal[13]:
                        message("Armed:")
                        break
                except lecroy.LeCroyTimeout:
                    message('{}:'.format(arm_timeouts))
                    arm_timeouts += 1
            # If the scope fails to arm, try again
            else:
                message("Failed to arm!\n")
                scope.stop()
                continue
            # Add timeout condition if necessary.
            wait_timeouts = 0
            while True:
                try:
                    # Check state before re-acquiring as the scope may arm and trigger immediately.
                    if internal[0]:
                        message("Triggered:")
                        break
                    else:
                        time.sleep(poll_wait)
                        internal = scope.internal
                        message(':')
                except lecroy.LeCroyTimeout:
                    message('{}:'.format(wait_timeouts))
                    wait_timeouts += 1
            acquire_timeouts = 0
            while acquire_timeouts < acquire_attempts:
                try:
                    waveform = scope.parse_waveform(scope.waveform)
                    break
                except lecroy.LeCroyTimeout:
                    message('{}:'.format(acquire_timeouts))
                    acquire_timeouts += 1
            else:
                message("Failed to acquire waveform!\n")
                continue
            filename = 'sweep{:06}.txt'.format(sweep)
            with open(os.path.join(directory, filename), 'w') as f:
                f.writelines(['{}\n'.format(value) for value in waveform['data']])
                message('Wrote {}\n'.format(filename))
            sweep += 1
    except KeyboardInterrupt:
        scope.stop()
        scope.auto_calibrate = True
        scope.local()
        scope.serial.close()
        message("Stopped.\n")

def main(base_directory):
    port = 'COM1'
    baudrate = 19200 #9600
    timeout = 3
    xonxoff = True
    serial_port = serial.Serial(port, baudrate=baudrate, timeout=timeout, xonxoff=xonxoff)
    scope = lecroy.LeCroy(serial_port)
    scope.remote()
    print("Connected to {}".format(scope.identification))
    scope.auto_calibrate = False
    data_directory = os.path.join(base_directory, time.strftime('%Y%m%dT%H%M%S'))
    os.mkdir(data_directory)
    print("Writing to {}".format(data_directory))
    acquire(scope, data_directory)

if __name__ == "__main__":
    main(sys.argv[1])