import os
import sys
import time
import serial
import pickle
import lecroy

def message(string):
    sys.stdout.write(string)
    sys.stdout.flush()

def acquire(scope, directory, arm_attempts=10, acquire_attempts=10, poll_wait=0.5, pickle_all_data=False):
    scope.clear()
    sweep = 0
    try:
        # This is the main acquisition loop.
        while True:
            # Tell the scope to arm and wait until it does.
            message("Arming")
            scope.arm()
            arm_timeouts = 0
            while arm_timeouts < arm_attempts:
                try:
                    internal = scope.internal
                    if internal[13]:
                        message("\rWaiting")
                        break
                except lecroy.LeCroyTimeout:
                    arm_timeouts += 1
            # If the scope fails to arm, try again
            else:
                message("\rFailed to arm!\n")
                scope.stop()
                continue

            # Now that the scope is armed, wait for it to trigger.
            # This loop never times out, so wait_timeouts is not used.
            wait_timeouts = 0
            while True:
                try:
                    # Check state before re-acquiring as the scope may arm and trigger immediately.
                    if internal[0]:
                        message("\rAcquiring waveform")
                        break
                    else:
                        time.sleep(poll_wait)
                        internal = scope.internal
                except lecroy.LeCroyTimeout:
                    wait_timeouts += 1

            # Now that the scope has triggered, attept to acquire the waveform.
            acquire_timeouts = 0
            while acquire_timeouts < acquire_attempts:
                try:
                    waveform = scope.parse_waveform(scope.waveform)
                    break
                except lecroy.LeCroyTimeout:
                    acquire_timeouts += 1
            else:
                message("\rFailed to acquire waveform!\n")
                continue

            # Write the data to disk.
            if pickle_all_data:
                pickle_filename = 'sweep{:06}.pkl'.format(sweep)
                with open(os.path.join(directory, pickle_filename), 'w') as f:
                    pickle.dump(waveform, f)
            data_filename = 'sweep{:06}.txt'.format(sweep)
            with open(os.path.join(directory, data_filename), 'w') as f:
                f.writelines(['{:.5f}\n'.format(value) for value in waveform['voltage_waveform']])
                message('\rWrote {}\n'.format(data_filename))
            sweep += 1
    except KeyboardInterrupt:
        scope.stop()
        scope.local()
        scope.serial.close()
        message("\rStopped.\n")


def main(user_directory, base_directory='C:\Student Directories', port='COM1', baudrate=19200, timeout=3, xonxoff=True):
    serial_port = serial.Serial(port, baudrate=baudrate, timeout=timeout, xonxoff=xonxoff)
    scope = lecroy.LeCroy(serial_port)
    scope.remote()
    try:
        print("Connected to {}".format(scope.identification))
    except lecroy.LeCroyTimeout:
        print("Failed to connect to scope. The scope baud rate must be {}.".format(baudrate))
        sys.exit()
    data_directory = os.path.join(base_directory, user_directory, time.strftime('%Y-%m-%d_%H%M%S'))
    try:
        os.mkdir(data_directory)
    except OSError:
        print("Failed to create directory {}".format(data_directory))
        print("The directory {} must exist.".format(os.path.join(base_directory, user_directory)))
        sys.exit()
    print("Writing to {}".format(data_directory))
    acquire(scope, data_directory)

if __name__ == "__main__":
    main(sys.argv[1])