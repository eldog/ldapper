import sys
import serial

COERCIVITY_HIGH = b'\x1Bh'
COERCIVITY_LOW = b'\x1Bl'

READ_WRITE_OK = b'0'
READ_WRITE_ERROR = b'1'
COMMAND_FORMAT_ERROR = b'2'
INVALID_COMMAND = b'4'
INVALID_CARD_SWIPE = b'9'

TRACK_1 = 1
TRACK_2 = 2
TRACK_3 = 3

BPI_75 = 0
BPI_210 = 1

class Track:
    def __init__(self, format_code, fields):
        self.format_code = format_code
        self.fields = fields

    def __str__(self):
        return str(self.fields)
    def __repr__(self):
        return str(self)

    @classmethod
    def from_stream(cls, stream):
        fields = []
        state = 0

        for _bytes_read in range(cls._TRACK_LENGTH):
            byte = stream.read()
            if state == 0:
                if byte != cls._START_SENTINEL:
                    raise IOError(byte)
                if cls._HAS_FORMAT_CODE:
                    state = 1
                else:
                    format_code = None
                    field = b''
                    state = 2
            elif state == 1:
                format_code = byte
                field = b''
                state = 2
            elif state == 2:
                if byte in (cls._FIELD_SEPERATOR, cls._END_SENTINEL):
                    fields.append(field)
                    if byte == cls._END_SENTINEL:
                        return cls(format_code, fields)
                    field = b''
                else:
                    field += byte
            else:
                raise AssertionError
        else:
            raise IOError


class TrackOne(Track):
    _FIELD_SEPERATOR = b'^'
    _START_SENTINEL = b'%'
    _END_SENTINEL = b'?'
    _TRACK_LENGTH = 78
    _HAS_FORMAT_CODE = True


class TrackTwo(Track):
    _FIELD_SEPERATOR = b'='
    _START_SENTINEL = b';'
    _END_SENTINEL = b'?'
    _TRACK_LENGTH = 39
    _HAS_FORMAT_CODE = False


class TrackThree(Track):
    _FIELD_SEPERATOR = b'='
    _START_SENTINEL = b';'
    _END_SENTINEL = b'?'
    _TRACK_LENGTH = 106
    _HAS_FORMAT_CODE = True


class MSR605:
    def __init__(self):
        self._serial = serial.Serial('/dev/ttyUSB0')

    def __enter__(self):
        self._serial.open()
        self.reset()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._serial.close()

    def _command(self, command):
        command = b'\x1B' + command
        bytes_written = self._serial.write(command)
        if  bytes_written != len(command):
            raise IOError('Tried to write %d b, wrote %d' % (len(command),
                                                             bytes_written))

    def reset(self):
        '''Reset the MSR605 to its initial state.'''
        self._command(b'\x61')

    def read(self):
        self._command(b'r')
        if self._serial.read(2) != b'\x1Bs':
            raise IOError
        def read_track(sentinel, factory):
            if self._serial.read(2) != sentinel:
                raise IOError
            try:
                return factory.from_stream(self._serial)
            except IOError as e:
                if e.args[0] != b'\x1B' or self._serial.read() != b'+':
                    raise e
                # Else, track empty
        tracks = (
            read_track(b'\x1B\x01', TrackOne),
            read_track(b'\x1B\x02', TrackTwo),
            read_track(b'\x1B\x03', TrackThree)
        )
        if self._serial.read(3) != b'?\x1C\x1B':
            raise IOError
        if self._serial.read() != READ_WRITE_OK:
            raise IOError
        return tracks

    def test_communication(self):
        '''Is the computer to MSR605 link is up and good?'''
        self._command(b'e')
        return self._serial.read(2) == b'\x1By'

    def all_led_off(self):
        self._command(b'\x81')

    def all_led_on(self):
        self._command(b'\x82')

    def green_led_on(self):
        self._command(b'\x83')

    def yellow_led_on(self):
        self._command(b'\x84')

    def red_led_on(self):
        self._command(b'\x85')

    def sensor_test(self):
        self._command(b'\x86')
        return self._serial.read(2) == b'\x1B\x30'

    def ram_test(self):
        self._command(b'\x87')
        return self._serial.read(2) == b'\x1B\x30'

    _BPI_MAP = {
        (TRACK_1, BPI_75) : b'\x4B',
        (TRACK_1, BPI_210): b'\xD2',
        (TRACK_2, BPI_75) : b'\xA0',
        (TRACK_2, BPI_210): b'\xA1',
        (TRACK_3, BPI_75) : b'\xC0',
        (TRACK_3, BPI_210): b'\xC1'
        }

    def set_bpi(self, track, bpi):
        self._command(b'b' + self._BPI_MAP[(track, bpi)])
        response = self._serial.read(2)
        if response == b'\x1BA':
            raise IOError() # Request Failed
        if response != b'\x1B0':
            raise IOError() # Unknown response


    def get_device_model(self):
        self._command(b't')
        b = b''
        while True:
            b += self._serial.read()
            if b[:1] == b'\x1B' and b[-1:] == b'S':
                return b[1:-1]

    def get_firmware_version(self):
        '''Returns the firmware version.'''
        self._command(b'v')
        response = self._serial.read(2)
        if response[:1] != b'\x1B':
            raise IOError
        return response[1]

    def set_bpc(self, track_1, track_2, track_3):
        '''For each track, set the bits per character.'''
        def check_bpc(bpc):
            if bpc < 5 or bpc > 8:
                raise ValueError
        check_bpc(track_1)
        check_bpc(track_2)
        check_bpc(track_3)
        bpc_bytes = bytes((track_1, track_2, track_3))
        self._command(b'o' + bpc_bytes)
        response = self._serial.read(5)
        if response != b'\x1B\x30' + bpc_bytes:
            raise IOError

    def set_coercivity_high(self):
        self._command(b'x')
        if self._serial.read(2) != b'\x1B0':
            raise IOError

    def set_coercivity_low(self):
        self._command(b'y')
        if self._serial.read(2) != b'\x1B0':
            raise IOError

    def get_coercivity(self):
        self._command(b'd')
        coercivity = self._serial.read(2)
        if coercivity == b'\x1Bh':
            return COERCIVITY_HIGH
        elif coercivity == b'\x1Bl':
            return COERCIVITY_LOW
        else:
            raise IOError

def main(argv=None):
    if argv is None:
        argv = sys.argv
    with MSR605() as msr605:
        while True:
            id = msr605.read()
            print(id)


if __name__ == '__main__':
    exit(main())
