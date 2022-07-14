import time 
from struct import pack, unpack
import serial
import sys, getopt

def crc24quick(crc, size, buffer):
    crctab = [0x00000000,0x01864CFB,0x038AD50D,0x020C99F6,0x0793E6E1,0x0615AA1A,0x041933EC,0x059F7F17,
    0x0FA18139,0x0E27CDC2,0x0C2B5434,0x0DAD18CF,0x083267D8,0x09B42B23,0x0BB8B2D5,0x0A3EFE2E]

    i = 0
    while (size):
        crc ^= (buffer[i] << 16)
        crc = (crc << 4) ^ crctab[(crc >> 20) & 0x0F]
        crc = (crc << 4) ^ crctab[(crc >> 20) & 0x0F]
        size -= 1
        i += 1
    
    return (crc & 0xFFFFFF)

def check_frequency(argv):
    """
    Pass in the message type # to check its arrival frequency
    For example: check_frequency(1005)
    """
    ser = serial.Serial("/dev/ttyUSB0", baudrate=9600)
    msg_type = 1005

    try:
        opts, args = getopt.getopt(argv, "hm:", ["mfile="])
    except getopt.GetoptError as err:
        print(err)

    for opt, arg in opts:
        if opt == '-h':
            print('./serial_read.py -m <message type>')
            sys.exit()
        elif opt in ("-m", "--mfile"):
            msg_type = int(arg)

    print("CHECK FREQUENCY FOR MSG TYPE {}".format(msg_type))

    data = b''
    t = time.time()
    t0 = time.time()
    skip = True
    while True:
        dat = ser.read()
        if (time.time() - t) > 0.5:
            print("====")
            while (len(data) > 0):
                # print("Raw len: ", len(data))
                buffer = unpack(len(data)*'B', data)
                # print(buffer)
                i = 0
                while (i < len(data) and buffer[i] != 0xD3):
                    i += 1

                if (i == len(data) ):
                    data = b""
                    # print("!!!! exceed limit")
                    break

                if buffer[i] == 0xD3:
                    
                    if (i+2) > len(data)-1:
                        break

                    if (buffer[i+1] & 0xFC == 0x00):
                        size = ((buffer[i+1] & 3) << 8 | buffer[i+2]) + 6
                        # print("Real size: ", size)
                        if len(data[i::]) < size:
                            # print("!!!!! Under size")
                            break
                        
                        if (crc24quick(0x000000, size, buffer[i:i+size]) == 0x00):
                            header = (buffer[3] << 4) | (buffer[4] >> 4)
                            print(header)
                            if header == msg_type:
                                print("New {} msg arrive after {} sec".format(msg_type, time.time() - t0))
                                t0 = time.time()
                        else:
                            # print(size, buffer[i:i+size])
                            pass
                        data = data[i+size::]
                    else:
                        data = data[i+1::]
        data += dat
        t = time.time()

if __name__ == '__main__':
    check_frequency(sys.argv[1:])
