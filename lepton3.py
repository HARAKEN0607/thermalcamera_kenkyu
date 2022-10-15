import numpy as np
import ctypes
import struct
import time
import ioctl
# from fcntl import ioctl

SPI_IOC_MAGIC   = ord("k")  # unicode 107

messages = 60   # RAWS

__xmit_struct = struct.Struct("=QQIIHBBI") # struct original
__msg_size = __xmit_struct.size # 8+8+4+4+2+1+1+4=32

iow = ioctl._IOW(SPI_IOC_MAGIC, 0, __msg_size)



# iow = _IOW(SPI_IOC_MAGIC, 0, )