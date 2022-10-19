import numpy as np
import ctypes
import struct
import time
import ioctl_numbers
from fcntl import ioctl

SPI_IOC_MAGIC = ord("k")  # unicode 107
ROWS = 60

messages = ROWS   # RAWS=60

__xmit_struct = struct.Struct("=QQIIHBBI") # struct original
__msg_size = __xmit_struct.size # 8+8+4+4+2+1+1+4=32
iow = ioctl_numbers._IOW(SPI_IOC_MAGIC, 0, __msg_size)

__handle = open("/dev/spidev0.0", "wb+", buffering=0) # binary writing
__xmit_buf = np.zeros((__msg_size * ROWS), dtype=np.uint8)
ioctl(__handle, iow, __xmit_buf, True)





