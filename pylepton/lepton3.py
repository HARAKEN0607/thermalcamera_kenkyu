import numpy as np
import ctypes
import struct
import time
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

__capture_buf = np.zeros((ROWS, VOSPI_FRAME_SIZE, 1), dtype=np.uint16) # [82行　1列]の[0]が60個

# __capture_buf[0]=0*82        0x000f=[0*14 1]
while (__capture_buf[0] & 0x000f) == 0x000f: # [0*15] == [0*14 1] repeat 14?
      ioctl(__handle, iow, __xmit_buf, True)

messages -= 1

print(messages)


