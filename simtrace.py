'''
simtrace - main program for the host PC
 
(C) 2010-2011 by Harald Welte <hwelte@hmw-consulting.de>
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 
as published by the Free Software Foundation

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

__author__ = 'Dean Chester'
__email__ = 'dean.g.chester@googlemail.com'

import usb
import sys
import usb.backend.libusb1 as libusb1
from types import *

idVendor = 0x16c0
idProduct = 0x0762

def readUSB():
    try:
        rawIn = dev.read(SIMTRACE_IN_EP, 10000,None, 10000)
        rawIn = rawIn.tolist()
        while(rawIn[1] & SIMTRACE_FLAG_WTIME_EXP):
            tmpIn = dev.read(SIMTRACE_IN_EP, 10000,None, 10000)
            tmpIn = tmpIn.tolist()
            rawIn[0:4] = tmpIn[0:4]
            rawIn += tmpIn[4:]
        return rawIn
    except:
        return readUSB()

def printATR(atr):
    hex = ' '.join('%02x' % b for b in atr)
    print 'APDU ATR: (' + len(atr).__str__() + '): '+ hex

def readMoreData():
    tmpIn = readUSB()
    return tmpIn[4:]

def splitApdu(dataIn):
    apdus = []
    ins = dataIn[1]
    numAPDU = dataIn[4] + 7
    if(ins == dataIn[5]):
        dataIn.pop(5)
    apdus.append(dataIn[0:numAPDU])
    while(numAPDU < len(dataIn)):
        while((numAPDU + 4) > len(dataIn) | (numAPDU + dataIn[numAPDU + 4] + 7) > len(dataIn)):
            dataIn += readMoreData()
        nextAPDU = numAPDU + dataIn[numAPDU + 4] + 7
        if(nextAPDU >= len(dataIn)):
            dataIn += readMoreData()
        ins = dataIn[numAPDU+1]
        check = dataIn[numAPDU + 5]
        if(ins == check):
            dataIn.pop(numAPDU + 5)
        apdus.append(dataIn[numAPDU:nextAPDU])
        numAPDU = nextAPDU
    return apdus

SIMTRACE_OUT_EP = 0x01
SIMTRACE_IN_EP = 0x82
SIMTRACE_INT_EP	= 0x83

SIMTRACE_FLAG_ATR = 0x01	#/* ATR immediately after reset */
SIMTRACE_FLAG_WTIME_EXP	= 0x04	#/* work waiting time expired */
SIMTRACE_FLAG_PPS_FIDI = 0x08	#/* Fi/Di values in res[2] */

dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
if dev is None:
    raise ValueError('Device not found')

dev.set_configuration()

while(True):
    rawIn = readUSB()
    if(rawIn[1] & SIMTRACE_FLAG_ATR):
        printATR(rawIn[4:])
    else:
        rawIn = rawIn[4:]
        apdus = splitApdu(rawIn)
        for i in apdus:
            apdu = i
            hex = ' '.join('%02x' % b for b in apdu)
            print "APDU: (%d): %s" % (len(apdu), hex)
