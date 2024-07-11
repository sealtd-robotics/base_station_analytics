#!/usr/bin/env python
import time 
from struct import pack, unpack
import serial
import sys, getopt
import socket
import select 

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

def check_frequency(msg_type, _port, _baudrate):
    """
    Pass in the message type # to check its arrival frequency
    For example: check_frequency(1005)
    """
    ser = serial.Serial(port=_port, baudrate=_baudrate)

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
                            print (time.asctime( time.localtime(time.time()) ) + (" , Message = ") + (str(header)))
                            if header == msg_type:
                                print (time.asctime( time.localtime(time.time()) ) + " , New {} msg arrive after {} sec".format(msg_type, time.time() - t0))
                                t0 = time.time()
                        else:
                            # print(size, buffer[i:i+size])
                            pass
                        data = data[i+size::]
                    else:
                        data = data[i+1::]
        data += dat
        t = time.time()

def forward_correction_from_udp(msg_type):
    multicast_group = ('234.5.6.7')

    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # group = socket.inet_aton(multicast_group)
    # sock.bind((multicast_group, 54008))
    # mreq = pack("4s4s", socket.inet_aton(multicast_group), socket.inet_aton("195.0.0.217"))
    # sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    # sock.setblocking(0)

    # Unicast
    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(("", 54000))
    # sock.settimeout(0.9)

    # for robot
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 54008))

    group = socket.inet_aton(multicast_group)
    mreq = pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setblocking(0)

    data = b""
    t = time.time()
    t0 = time.time()
    while True:
        try:
            ready = select.select([sock], [], [], 0.5)
            if ready[0]:
                dat = sock.recv(1024)
            # print(len(dat))
            # print(unpack(len(dat)*'B', dat))
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
                                    print (time.asctime( time.localtime(time.time()) ) + (" , Message = ") + (str(header)))
                                    if header == msg_type:
                                        print(time.asctime( time.localtime(time.time()) ) + " , New {} msg arrive after {} sec".format(msg_type, time.time() - t0))
                                        t0 = time.time()
                                else:
                                    # print(size, buffer[i:i+size])
                                    pass
                                data = data[i+size::]
                            else:
                                data = data[i+1::]
                data += dat
                t = time.time()
            else:
                # print("no data, re init socket")
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(("", 54008))

                group = socket.inet_aton(multicast_group)
                mreq = pack('4sL', group, socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                sock.setblocking(0)
        except Exception as e:
            print("An exception occurred")
            print(e)

if __name__ == '__main__':
    # check_frequency(sys.argv[1:])
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:p:b:m:", ["help", "interface=", "port=", "baudrate=", "mfile="])
    except getopt.GetoptError as err:
        print(err)

    interface = "serial"
    msg_type = 1005
    baud_rate = 9600
    port = "/dev/ttyUSB0"
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print("Description: Tool to check on base station data frequency.")
            print("To get help: ./serial_read.py -h OR ./serial_read.py --help")
            print('Options: ./serial_read.py -i <interface type> -p <port name> -b <baud rate> -m <message type>')
            print('  <interface type> : serial or ethernet. Default: ethernet.')
            print('  <port name> : /dev/ttyUSB0, /dev/ttyACM0, etc. Default: /dev/ttyUSB0')
            print('  <baud rate> : integer (9600, 115200,...). Default: 9600')
            print('  <message type>: 1005, 1006, 1007, etc..Default: 1005')
            sys.exit()
        elif opt in ("-i", "--interface"):
            interface = str(arg)
        elif opt in ("-p", "--port"):
            interface_name = arg
        elif opt in ("-m", "--mfile"):
            msg_type = int(arg)
        elif opt in ("-b", "--baudrate"):
            baud_rate = int(arg)

    
    if interface == "serial":
        s = "serial"
        print("CHECK FREQUENCY FOR MSG TYPE {} on serial at port {} with baudrate {}".format(msg_type, port, baud_rate))
        check_frequency(msg_type, port, baud_rate)
    else:
        print("CHECK FREQUENCY FOR MSG TYPE {} on ethernet at port 5400.".format(msg_type))
        forward_correction_from_udp(msg_type)
    
