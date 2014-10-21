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

    def _decimal_bytes_to_int(self, bytes):
        return int(''.join([str(d) for d in bytes]))

    def _decimal_bytes_to_str(self, bytes):
        return ''.join([chr(d) for d in bytes])

    @property
    def waveform(self):
        return self.send_and_receive('WAVEFORM?')

    def parse_waveform(self, message):
        content = message.split('#', 1)[1]
        block_length = int(content[1:int(content[0])+1])
        if len(content) != 1 + int(content[0]) + block_length:
            raise ValueError("Message length does not match value given in header.")
        hex_pairs = content[1 + int(content[0]):]
        decimal_data = [int(a + b, 16) for a, b in zip(hex_pairs[::2], hex_pairs[1::2])]
        waveform = {}
        waveform['descriptor_name'] = self._decimal_bytes_to_str(decimal_data[:16])
        waveform['template_name'] = self._decimal_bytes_to_str(decimal_data[16:32])
        waveform['comm_type'] = self._decimal_bytes_to_int(decimal_data[32:34])
        waveform['comm_order'] = self._decimal_bytes_to_int(decimal_data[34:36])
        waveform['wave_descriptor'] = self._decimal_bytes_to_int(decimal_data[36:40])
        waveform['user_text'] = self._decimal_bytes_to_int(decimal_data[40:44])
        waveform['res_desc1'] = self._decimal_bytes_to_int(decimal_data[44:48]) # This isn't documented
        waveform['trigtime_array'] = self._decimal_bytes_to_int(decimal_data[48:52])
        waveform['ris_time_array'] = self._decimal_bytes_to_int(decimal_data[52:56])
        waveform['res_array1'] = self._decimal_bytes_to_int(decimal_data[56:60])
        waveform['wave_array_1'] = self._decimal_bytes_to_int(decimal_data[60:64])
        waveform['wave_array_2'] = self._decimal_bytes_to_int(decimal_data[64:68])
        waveform['instrument_name'] = self._decimal_bytes_to_str(decimal_data[76:92])
        waveform['instrument_number'] = self._decimal_bytes_to_int(decimal_data[92:96])
        waveform['trace_label'] = self._decimal_bytes_to_str(decimal_data[96:112])
        waveform['wave_array_count'] = self._decimal_bytes_to_int(decimal_data[116:120])
        waveform['points_per_screen'] = self._decimal_bytes_to_int(decimal_data[120:124])
        waveform['timebase'] = self._decimal_bytes_to_int(decimal_data[324:326])
        waveform['fixed_vert_gain'] = self._decimal_bytes_to_int(decimal_data[332:334])
        waveform['wave_source'] = self._decimal_bytes_to_int(decimal_data[344:346])
        #waveform['waveform'] = decimal_data[waveform['wave_descriptor_length'] + waveform['user_text_length']:]
        return waveform, decimal_data


class LeCroyError(Exception):
    pass


class LeCroyTimeout(LeCroyError):
    pass