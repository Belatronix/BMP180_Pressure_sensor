import smbus2
import time

address = 0x77
oss = 3
height = 53

bmp180 = smbus2.SMBus(1)


def byte_read(register):
    return bmp180.read_byte_data(address, register)


def kelvin(degree):
    return degree + 273.15


def word_read_signed(register):
    lsb = byte_read(register + 1)
    msb = byte_read(register)
    if msb > 127:
        msb -= 256
    return (msb << 8) + lsb


def word_read_unsigned(register):
    lsb = byte_read(register + 1)
    msb = byte_read(register)
    return (msb << 8) + lsb


def check_communication(register):
    if byte_read(0xd0) == 0x55:
        return True
    else:
        return False


AC1 = word_read_signed(0xAA)
AC2 = word_read_signed(0xAC)
AC3 = word_read_signed(0xAE)
AC4 = word_read_unsigned(0xB0)
AC5 = word_read_unsigned(0xB2)
AC6 = word_read_unsigned(0xB4)
B1 = word_read_signed(0xB6)
B2 = word_read_signed(0xB8)
MB = word_read_signed(0xBA)
MC = word_read_signed(0xBC)
MD = word_read_signed(0xBE)

# read uncompensated temperature value
bmp180.write_byte_data(address, 0xF4, 0x2E)
time.sleep(0.2)
UT = word_read_unsigned(0xF6)

# read uncompensated pressure value
bmp180.write_byte_data(address, 0xF4, (0x34 + (oss << 6)))
time.sleep(0.2)
MSB = bmp180.read_byte_data(address, 0xF6)
LSB = bmp180.read_byte_data(address, 0xF7)
XLSB = bmp180.read_byte_data(address, 0xF8)
UP = ((MSB << 16) + (LSB << 8) + XLSB) >> (8 - oss)

# calculate true temperature
X1 = ((UT - AC6) * AC5) / (2 ** 15)
X2 = (MC << 11) / (X1 + MD)
B5 = X1 + X2
T = (B5 + 8) / (2 ** 4)  # temperature in 0.1 °C

B6 = B5 - 4000
X1 = (B2 * (B6 * B6 / (2 ** 12))) / (2 ** 11)
X2 = AC2 * B6 / (2 ** 11)
X3 = X1 + X2
B3 = (((AC1 * 4 + X3) * 2 ** oss) + 2) / 4
X1 = AC3 * B6 / (2 ** 13)
X2 = (B1 * (B6 * B6 / (2 ** 12))) / (2 ** 16)
X3 = ((X1 + X2) + 2) / (2 ** 2)
B4 = AC4 * (X3 + 32768) / (2 ** 15)
B7 = (UP - B3) * (50000 >> oss)
if B7 < 0x80000000:
    p = (B7 * 2) / B4
else:
    p = (B7 / B4) * 2
X1 = (p / (2 ** 8)) * (p / (2 ** 8))
X1 = (X1 * 3038) / (2 ** 16)
X2 = (-7357 * p) / (2 ** 16)
p += (X1 + X2 + 3791) / (2 ** 4)

# pressure calculation at standard atmosphere(atm) => 1013,25 hPa at 15°C resp. 288,15 Kelvin

temperature_NN = T / 10 + 0.0065 * height
pressure_NN = p / (1 - (0.0065 * height / kelvin(temperature_NN))) ** 5.255

# print("Temperature: %s °C, Pressure: %s hPa, PressureNN: %s hPa" % (
#  round(T / 10, 3), round(p / 100, 4), round(pressure_NN / 100, 2)))


if __name__ == "__main__":
    print("Temperature: %s °C, Pressure: %s hPa, PressureNN: %s hPa" % (
        round(T / 10, 3), round(p / 100, 4), round(pressure_NN / 100, 2)))
