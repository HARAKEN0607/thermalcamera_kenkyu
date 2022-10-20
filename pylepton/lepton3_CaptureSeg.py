import numpy as np
import struct
import ioctl_numbers
from fcntl import ioctl

SPI_IOC_MAGIC = ord("k")  # unicode 107
ROWS = 60
COLS = 80
VOSPI_FRAME_SIZE = COLS + 2

messages = ROWS   # RAWS=60

__xmit_struct = struct.Struct("=QQIIHBBI") # struct original
__msg_size = __xmit_struct.size # 8+8+4+4+2+1+1+4=32
iow = ioctl_numbers._IOW(SPI_IOC_MAGIC, 0, __msg_size) # writing mode

__handle = open("/dev/spidev0.0", "wb+", buffering=0) # binary writing
__xmit_buf = np.zeros((__msg_size * ROWS), dtype=np.uint8) # 32*60 [0 codes]
ioctl(__handle, iow, __xmit_buf, True) # writing to camera

__capture_buf = np.zeros((ROWS, VOSPI_FRAME_SIZE, 1), dtype=np.uint16) # [60行　82列]の枠に0が一つずつ

print(__capture_buf)
# __capture_buf[0]=0*82    __capture_buf[0][0]=0    0x000f=[0*14 1]
# __capture_buf[0][0] & 0x000f = 0


# while (__capture_buf[0][0] & 0x000f) == 0x000f: # __capture_buf[0]=0*82    __capture_buf[0][0]=0    0x000f=[0*14 1]
#     ioctl(__handle, iow, __xmit_buf, True)      # __capture_buf[0][0] & 0x000f = 0
#
# messages -= 1 # messages(60)-1



