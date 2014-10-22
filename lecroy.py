class LeCroy(object):

    program_message_terminator = '\r'
    default_response_message_terminator = '\n\r'
    response_message_terminator = '\\n'

    boolean_to_token = {True: 'ON',
                        False: 'OFF'}
    token_to_boolean = {'ON': True,
                        'OFF': False}

    def __init__(self, serial_port):
        self.serial = serial_port
        self.echo_off()
        self.serial.write('COMM_RS232 EO,"{}"; *STB?{}'.format(self.response_message_terminator,
                                                               self.program_message_terminator))
        self.serial.readline()
        self.header = 'OFF'

    def send(self, message):
        self.serial.write(message + self.program_message_terminator)

    def receive(self):
        response = self.serial.readline()
        if not response:
            raise LeCroyTimeout()
        return response.rstrip()

    def send_and_receive(self, message):
        self.send(message)
        return self.receive()

    def echo_on(self):
        self.serial.write(chr(27)+']')

    def echo_off(self):
        self.serial.write(chr(27)+'[')

    def local(self):
        self.serial.write(chr(27)+'L')

    def remote(self):
        self.serial.write(chr(27)+'R')

    @property
    def header(self):
        return self.send_and_receive('COMM_HEADER?')

    @header.setter
    def header(self, mode):
        if not mode.upper() in ('SHORT', 'LONG', 'OFF'):
            raise LeCroyError("Invalid communication header mode: {}".format(mode))
        self.send('COMM_HEADER {}'.format(mode))

    @property
    def identification(self):
        return self.send_and_receive('*IDN?')

    def clear(self):
        self.send('*CLS')

    @property
    def internal(self):
        binary = format(int(self.send_and_receive('INR?')), '016b')
        return [bool(int(b)) for b in reversed(binary)]

    def arm(self):
        self.send('ARM')

    def stop(self):
        self.send('STOP')

    @property
    def auto_calibrate(self):
        return self.token_to_boolean[self.send_and_receive('AUTO_CALIBRATE?')]

    @auto_calibrate.setter
    def auto_calibrate(self, boolean):
        self.send('AUTO_CALIBRATE {}'.format(self.boolean_to_token[boolean]))

    def _hex_bytes_to_int(self, bytes):
        return int(''.join(bytes), 16)

    def _hex_bytes_to_str(self, bytes):
        return ''.join([chr(int(b, 16)) for b in bytes])

    def _hex_bytes_to_signed_int(self, bytes):
        binary_format_code = '{{:0{}b}}'.format(8 * len(bytes))
        binary = binary_format_code.format(int(''.join(bytes), 16))
        return int(binary, 2) - int(binary[0], 2) * 2**len(binary)

    @property
    def waveform(self):
        return self.send_and_receive('WAVEFORM?')

    def parse_waveform(self, message):
        content = message.split('#', 1)[1]
        block_length = int(content[1:int(content[0])+1])
        if len(content) != 1 + int(content[0]) + block_length:
            raise ValueError("Message length does not match value given in header.")
        hex_nibbles = content[1 + int(content[0]):]
        # Add ordering check.
        hex_bytes = [a+b for a, b in zip(hex_nibbles[::2], hex_nibbles[1::2])]
        waveform = {}
        waveform['descriptor_name'] = self._hex_bytes_to_str(hex_bytes[:16])
        waveform['template_name'] = self._hex_bytes_to_str(hex_bytes[16:32])
        waveform['comm_type'] = self._hex_bytes_to_int(hex_bytes[32:34])
        waveform['comm_order'] = self._hex_bytes_to_int(hex_bytes[34:36])
        waveform['wave_descriptor'] = self._hex_bytes_to_int(hex_bytes[36:40])
        waveform['user_text'] = self._hex_bytes_to_int(hex_bytes[40:44])
        waveform['res_desc1'] = self._hex_bytes_to_int(hex_bytes[44:48]) # This isn't documented
        waveform['trigtime_array'] = self._hex_bytes_to_int(hex_bytes[48:52])
        waveform['ris_time_array'] = self._hex_bytes_to_int(hex_bytes[52:56])
        waveform['res_array1'] = self._hex_bytes_to_int(hex_bytes[56:60])
        waveform['wave_array_1'] = self._hex_bytes_to_int(hex_bytes[60:64])
        waveform['wave_array_2'] = self._hex_bytes_to_int(hex_bytes[64:68])
        waveform['res_array2'] = self._hex_bytes_to_int(hex_bytes[68:72])
        waveform['res_array3'] = self._hex_bytes_to_int(hex_bytes[72:76])
        waveform['instrument_name'] = self._hex_bytes_to_str(hex_bytes[76:92])
        waveform['instrument_number'] = self._hex_bytes_to_int(hex_bytes[92:96])
        waveform['trace_label'] = self._hex_bytes_to_str(hex_bytes[96:112])
        #
        waveform['wave_array_count'] = self._hex_bytes_to_int(hex_bytes[116:120])
        waveform['points_per_screen'] = self._hex_bytes_to_int(hex_bytes[120:124])
        #
        waveform['timebase'] = self._hex_bytes_to_int(hex_bytes[324:326])
        #
        waveform['fixed_vert_gain'] = self._hex_bytes_to_int(hex_bytes[332:334])
        waveform['wave_source'] = self._hex_bytes_to_int(hex_bytes[344:346])
        data = hex_bytes[waveform['wave_descriptor'] + waveform['user_text']:]
        waveform['data'] = [self._hex_bytes_to_signed_int((high, low))
                            for high, low in zip(data[::2], data[1::2])]
        return waveform


class LeCroyError(Exception):
    pass


class LeCroyTimeout(LeCroyError):
    pass