#!/usr/bin/python

import serial
from time import sleep

class MagicBall():
    def __init__(self, port):
        self.ser = serial.Serial()
        self.ser.baudrate = 4800
        self.ser.port = port
        self.ser.parity = serial.PARITY_EVEN
        self.ser.timeout = 3
        self.ser.open()
        self.encoding = 'cp437'
        self.interCharPause = 0.01 # pause in seconds when sending a character - otherwise the magicball seems to skip characters

    def deviceSelection(self):
        raise RuntimeError("Not implemented")

    def receiveIdentification(self):
        identification = dict()
        self.__byteWriteCheckEcho(b'\x1b')
        self.__byteWriteCheckEcho(b'\x53')
        self.__byteWriteCheckEcho(b'\x03')
        rawStrings = self.__readUntil(b'\x03')
        strings = rawStrings.split(b'\x00')[:-1]
        identification["Version"]       = strings[0].decode(self.encoding)
        identification["Manufacturer"]  = strings[1].decode(self.encoding)
        identification["Serial"]        = strings[6].decode(self.encoding)
        identification["Standard Text"] = strings[7].decode(self.encoding) + " / " + strings[8].decode(self.encoding)
        identification["Font"]          = strings[9].decode(self.encoding) + " / " + strings[10].decode(self.encoding)
        identification["Memory"]        = int( strings[11].decode(self.encoding), 16 )
        return identification

    def receiveStandardText(self):
        self.__byteWriteCheckEcho(b'\x1b')
        self.__byteWriteCheckEcho(b'\x46')
        self.__byteWriteCheckEcho(b'\x03')
        rawText = self.__readUntil(b'\x03')
        return rawText[:-2].decode(self.encoding)

    def receiveText(self):
        self.__byteWriteCheckEcho(b'\x1b')
        self.__byteWriteCheckEcho(b'\x54')
        self.__byteWriteCheckEcho(b'\x03')
        rawText = self.__readUntil(b'\x03')
        return rawText[:-2].decode(self.encoding)

    def sendText(self, text):
        self.__byteWriteCheckEcho(b'\x02')
        self.__byteWriteCheckEcho(b'\x0d')
        try:
            for c in bytes(text,self.encoding):
                self.__byteWriteCheckEcho( c.to_bytes(1, byteorder='big') )
        finally:
            self.__byteWriteCheckEcho(b'\x03')

    def __readUntil(self, lastByte):
        if not ( type(lastByte) is bytes and len(lastByte) is 1 ):
            raise ValueError("Expected exactly one byte as last byte to read")
        received = bytearray()
        while True:
            receivedByte = self.ser.read(1)
            if len(receivedByte) == 0:
                raise RuntimeError("Timed out")
            received.append(receivedByte[0])
            if receivedByte == lastByte:
                break
        return received

    def __byteWriteRead(self, toWrite):
        if not ( type(toWrite) is bytes and len(toWrite) is 1 ):
            raise ValueError("Expected exactly one byte to write")
        sleep(self.interCharPause)
        self.ser.write( toWrite )
        sleep(self.interCharPause)
        return self.ser.read(1)

    def __byteWriteCheckEcho(self, toWrite, expectedEcho=None):
        if expectedEcho is None:
            expectedEcho = toWrite
        reply = self.__byteWriteRead( toWrite )
        if len(reply) == 0:
            raise RuntimeError("No response from MagicBall")
        if reply != expectedEcho:
            raise RuntimeError("Unexpected reply from MagicBall")
        return reply


def main():
    import sys
    import getopt

    actions = ['receiveIdentification', 'receiveStandardText', 'receiveText', 'sendText']
    device = '/dev/ttyUSB0'

    HELP = (
        "Usage: MagicBall.py [-d <Device>] <Action>\n" +
        "\nOptions:\n" +
        "  -d <Device>    The device file to open. Defaults to \"" + device + "\"\n" +
        "\nActions:\n" +
        "  receiveIdentification\n" +
        "  receiveStandardText\n" +
        "  receiveText\n" +
        "  sendText \"<Text>\"\n"
    )

    try:
        opts, args = getopt.getopt( sys.argv[1:], 'd:' )
    except getopt.GetoptError:
        print( HELP )
        sys.exit( "Failed to parse command line!" )

    for opt, arg in opts:
        if opt == '-h':
            print( HELP )
            sys.exit()
        elif opt == '-d':
            device = arg

    # action given?
    if len(args) < 1:
        print( HELP )
        sys.exit( "Expecting an argument as <Action>!")

    # is action valid?
    action = args[0]
    if action not in actions:
        print( HELP )
        sys.exit( "Invalid action!")

    # are the action's arguments valid?
    if action == 'sendText':
        if len(args) != 2:
            print( HELP )
            sys.exit( "Expecting the <Text> to send as one additional argument!")
    else:
        if len(args) > 1:
            print( HELP )
            sys.exit( "No additional argument expected for '" + action + "'!")


    print("Opening device '" + device + "'")
    magicBall = MagicBall(device)

    if action == 'sendText':
        print("Sending Text \"" + args[1] + "\"")
        magicBall.sendText( args[1] )
        print("Verifying Text")
        text = magicBall.receiveText()
        if text != args[1]:
            print("Sent \"" + args[1] + "\" but MagicBall content reads \"" + text + "\"")
        else:
            print("Done")
    elif action == 'receiveText':
        print("Receiving Text")
        print("Received \""+magicBall.receiveText()+"\"")
    elif action == 'receiveStandardText':
        print("Receiving Standard Text")
        print("Received \""+magicBall.receiveStandardText()+"\"")
    elif action == 'receiveIdentification':
        print("Receiving Identification")
        print("Received " + str(magicBall.receiveIdentification()) )

    sys.exit( 0 )


if __name__ == '__main__':
    main()
