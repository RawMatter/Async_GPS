import asyncio
from enum import Enum
from operator import xor


class FIX_INDICATOR(Enum):
        NOT_AVAILABLE = 0
        GPS_SPS_MODE = 1
        DIFFERENTIAL_GPS = 2
        DEAD_RECKONING = 6

class Gps(asyncio.Protocol):
    def __init__(self) -> None:
        super().__init__()
        self.connected = False
        
    def connection_made(self, transport):
        """Store the serial transport and prepare to receive data.
        """
        self.transport = transport
        self.buf = bytes()
        self.msgs_recvd = 0
        self.message_types = []
        self.print_raw = True
        print('Reader connection created')

    def data_received(self, data):
        """Store characters until a newline is received.
        """
        self.buf += data
        if b'\n' in self.buf:
            lines = self.buf.split(b'\n')
            self.buf = lines[-1]  # whatever was left over
            for line in lines[:-1]:
                if self.print_raw:
                    print(f'Reader received: {line.decode()}')
                self.msgs_recvd += 1
                if self.validate_checksum(line):
                    self.connected = True
                    self.decode_data(line)
                self.buf = bytes()

    def got_fix(self):
        if self.connected:
            if int(self.fix_indicator) >= 1:
                return True
        return False

    def decode_data(self,data):
        data = data.decode()
        
        # Insert spaces between concurrent commas to facilitate reliable splitting
        i = 5
        while i < len(data):
            if data[i] == ",":
                if data[i-1] ==",":
                    data = data[:i] + " " + data[i:]
            i += 1
                    
        components = data.split(',')
        message_type = components[0]
        if message_type == "$GPGGA":
            self.decode_GPGGA(components)
        elif message_type == "$GPGLL":
            self.decode_GPGLL(components)
        elif message_type == "$GPGSA":
            self.decode_GPGSA(components)
        elif message_type == "$GPVTG":
            self.decode_GPVTG(components)
        elif message_type == "$GPRMC":
            self.decode_GPRMC(components)
        elif message_type == "$GPGSV":
            self.decode_GPGSV(components)
        return
    
    def validate_checksum(self, data):
        if data[0] != 0x24:
            # Junk data line, probably first
            print("Not start of message")
            return False
    
        sum = data[1]
        i = 2
        # scan until we hit ASCII
        while data[i] != 0x2A:
            sum = xor(sum,data[i])
            i += 1
        
        checksum = data[-3:].decode()
        sum = f"{sum:x}".upper()
        if sum == checksum:
            return True
        return False

    def decode_GPGGA(self,components):
        '''Global positioning systemw fix data (time, position, fix type data)
        '''
        if components[0] != '$GPGGA':
            print("ERRRRRROOOORRRR")
            # Incorrect deocoder
            return
        self.utc_time = components[1]
        self.latitude = components[2]
        self.hemisphere = components[3]
        self.longitude = components[4]
        self.half = components[5]
        self.fix_indicator = FIX_INDICATOR(int(components[6]))
        self.satellite_count = int(components[7])
        self.hdop = float(components[8])
        self.altitude = float(components[9])
        self.altitude_units = components[10]
        self.geoid_serperation = float(components[11])
        self.geoid_units = components[12]
        self.comp_age_diff = components[13]
        self.station_id = components[14]
        #TODO Validate checksum
        # self.print_GPGGA()
        return

    def print_GPGGA(self):
        message = f'''
        utc_time = {self.utc_time}
        latitude = {self.latitude}
        hemisphere = {self.hemisphere}
        longitude = {self.longitude}
        half = {self.half}
        fix_indicator = {self.fix_indicator}
        satellite_count = {self.satellite_count}
        hdop = {self.hdop}
        altitude = {self.altitude}
        altitude units = {self.altitude_units}
        comp_age_diff = {self.comp_age_diff}
        self.geoid_serperation = {self.geoid_serperation}
        self.geoid_units = {self.geoid_units}
        station_id = {self.station_id}
        '''
        print(message)
        

    def decode_GPGLL(self,components):
        '''Global positioning system fix data (time, position, fix type data)
        '''

        


        return

    def decode_GPGSA(self,components):
        '''GPS receiver operating mode, satellites used in the position solution, and DOP values.
        '''
        self.mode1 = components[1]
        self.mode2 = components[2]
        self.ch1_sat = components[3]
        self.ch2_sat = components[4]
        self.ch3_sat = components[5]
        self.ch4_sat = components[6]
        self.ch5_sat = components[7]
        self.ch6_sat = components[8]
        self.ch7_sat = components[9]
        self.ch8_sat = components[10]
        self.ch9_sat = components[11]
        self.ch10_sat = components[12]
        self.ch11_sat = components[13]
        self.ch12_sat = components[14]
        self.pdop = components[15]
        self.vdop = components[16]
        
        return

    def decode_GPVTG(self,components):
        '''Course and speed information relative to the ground
        '''
        self.true_course = components[1]
        self.magnetic_course = components[3]
        self.speed_knotts = components[5]
        self.speed_kmh = components[7]
        return

    def decode_GPRMC(self,components):
        '''Time, date, position, course and speed data
        '''
        self.utc_time = components[1]
        self.latitude = components[2]
        self.hemisphere = components[3]
        self.longitude = components[4]
        self.half = components[5]
        self.ground_speed = components[6]
        self.ground_speed_units = components[7]
        self.date = components[8]
        self.magnetic_variation = components[9]
        self.magnetic_variation_direction = components[10]
        self.mode = components[11]
        return

    def decode_GPGSV(self,components):
        '''The number of GPS satellites in view satellite ID numbers, elevation, azimuth and SNR values.
        '''
        return

    def connection_lost(self, exc):
        print('Reader closed')
    
    def disconnect(self):
        self.transport.close()