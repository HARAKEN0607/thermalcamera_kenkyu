import numpy as np
import ctypes
import struct
import time
import ioctl_numbers
from fcntl import ioctl


SPI_IOC_MAGIC   = ord("k")

SPI_IOC_RD_MODE          = ioctl_numbers._IOR(SPI_IOC_MAGIC, 1, "=B")
SPI_IOC_WR_MODE          = ioctl_numbers._IOW(SPI_IOC_MAGIC, 1, "=B")

SPI_IOC_RD_LSB_FIRST     = ioctl_numbers._IOR(SPI_IOC_MAGIC, 2, "=B")
SPI_IOC_WR_LSB_FIRST     = ioctl_numbers._IOW(SPI_IOC_MAGIC, 2, "=B")

SPI_IOC_RD_BITS_PER_WORD = ioctl_numbers._IOR(SPI_IOC_MAGIC, 3, "=B")
SPI_IOC_WR_BITS_PER_WORD = ioctl_numbers._IOW(SPI_IOC_MAGIC, 3, "=B")

SPI_IOC_RD_MAX_SPEED_HZ  = ioctl_numbers._IOR(SPI_IOC_MAGIC, 4, "=I")
SPI_IOC_WR_MAX_SPEED_HZ  = ioctl_numbers._IOW(SPI_IOC_MAGIC, 4, "=I")

SPI_CPHA   = 0x01                 # /* clock phase */
SPI_CPOL   = 0x02                 # /* clock polarity */
SPI_MODE_0 = (0|0)                # /* (original MicroWire) */
SPI_MODE_1 = (0|SPI_CPHA)
SPI_MODE_2 = (SPI_CPOL|0)
SPI_MODE_3 = (SPI_CPOL|SPI_CPHA)

class Lepton(object):
  """Communication class for FLIR Lepton module on SPI
  Args:
    spi_dev (str): Location of SPI device node. Default '/dev/spidev0.0'.
  """

  ROWS = 60
  COLS = 80
  VOSPI_FRAME_SIZE = COLS + 2
  VOSPI_FRAME_SIZE_BYTES = VOSPI_FRAME_SIZE * 2
  MODE = SPI_MODE_3
  BITS = 8
  SPEED = 18000000
  SPIDEV_MESSAGE_LIMIT = 24

  def __init__(self, spi_dev = "/dev/spidev0.0"):
    self.__spi_dev = spi_dev
    self.__txbuf = np.zeros(Lepton.VOSPI_FRAME_SIZE, dtype=np.uint16)

    # struct spi_ioc_transfer {
    #   __u64     tx_buf;
    #   __u64     rx_buf;
    #   __u32     len;
    #   __u32     speed_hz;
    #   __u16     delay_usecs;
    #   __u8      bits_per_word;
    #   __u8      cs_change;
    #   __u32     pad;
    # };
    self.__xmit_struct = struct.Struct("=QQIIHBBI")
    self.__msg_size = self.__xmit_struct.size
    self.__xmit_buf = np.zeros((self.__msg_size * Lepton.ROWS), dtype=np.uint8)
    self.__msg = ioctl_numbers._IOW(SPI_IOC_MAGIC, 0, self.__xmit_struct.format)
    self.__capture_buf = np.zeros((Lepton.ROWS, Lepton.VOSPI_FRAME_SIZE, 1), dtype=np.uint16)

    for i in range(Lepton.ROWS):
      self.__xmit_struct.pack_into(self.__xmit_buf, i * self.__msg_size,
        self.__txbuf.ctypes.data,                                            #   __u64     tx_buf;
        self.__capture_buf.ctypes.data + Lepton.VOSPI_FRAME_SIZE_BYTES * i,  #   __u64     rx_buf;
        Lepton.VOSPI_FRAME_SIZE_BYTES,                                      #   __u32     len;
        Lepton.SPEED,                                                       #   __u32     speed_hz;
        0,                                                                  #   __u16     delay_usecs;
        Lepton.BITS,                                                        #   __u8      bits_per_word;
        1,                                                                  #   __u8      cs_change;
        0)                                                                  #   __u32     pad;

  def __enter__(self):
    # "In Python 3 the only way to open /dev/tty under Linux appears to be 1) in binary mode and 2) with buffering disabled."
    self.__handle = open(self.__spi_dev, "wb+", buffering=0)

    ioctl(self.__handle, SPI_IOC_RD_MODE, struct.pack("=B", Lepton.MODE))
    ioctl(self.__handle, SPI_IOC_WR_MODE, struct.pack("=B", Lepton.MODE))

    ioctl(self.__handle, SPI_IOC_RD_BITS_PER_WORD, struct.pack("=B", Lepton.BITS))
    ioctl(self.__handle, SPI_IOC_WR_BITS_PER_WORD, struct.pack("=B", Lepton.BITS))

    ioctl(self.__handle, SPI_IOC_RD_MAX_SPEED_HZ, struct.pack("=I", Lepton.SPEED))
    ioctl(self.__handle, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack("=I", Lepton.SPEED))

    return self

  def __exit__(self, type, value, tb):
    self.__handle.close()

  @staticmethod
  def capture_segment(handle, xs_buf, xs_size, capture_buf):
    messages = Lepton.ROWS

    iow = ioctl_numbers._IOW(SPI_IOC_MAGIC, 0, xs_size)
    ioctl(handle, iow, xs_buf, True)

    while (capture_buf[0] & 0x000f) == 0x000f: # byteswapped 0x0f00
      ioctl(handle, iow, xs_buf, True)

    messages -= 1

  def capture(self, data_buffer = None, log_time = False, debug_print = False, retry_reset = True):

    start = time.time()

    if data_buffer is None:
      data_buffer = np.ndarray((Lepton.ROWS, Lepton.COLS, 1), dtype=np.uint16)
    elif data_buffer.ndim < 2 or data_buffer.shape[0] < Lepton.ROWS or data_buffer.shape[1] < Lepton.COLS or data_buffer.itemsize < 2:
      raise Exception("Provided input array not large enough")

    while True:
      Lepton.capture_segment(self.__handle, self.__xmit_buf, self.__msg_size, self.__capture_buf[0])
      if retry_reset and (self.__capture_buf[20, 0] & 0xFF0F) != 0x1400: # make sure that this is a well-formed frame, should find line 20 here
        # Leave chip select deasserted for at least 185 ms to reset
        if debug_print:
          print("Garbage frame number reset waiting...")
        time.sleep(0.185)
      else:
        break

    self.__capture_buf.byteswap(True)
    data_buffer[:,:] = self.__capture_buf[:,2:]

    end = time.time()

    if debug_print:
      print("---")
      for i in range(Lepton.ROWS):
        fid = self.__capture_buf[i, 0, 0]
        crc = self.__capture_buf[i, 1, 0]
        fnum = fid & 0xFFF
        print("0x{0:04x} 0x{1:04x} : Row {2:2} : crc={1}".format(fid, crc, fnum))
      print("---")

    if log_time:
      print("frame processed int {0}s, {1}hz".format(end-start, 1.0/(end-start)))

    # TODO: turn on telemetry to get real frame id, sum on this array is fast enough though (< 500us)
    return data_buffer, data_buffer.sum()

with Lepton() as l:
    a = l.capture()

cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX) # extend contrast
np.right_shift(a, 8, a) # fit data into 8 bits
cv2.imwrite("home/pi/thermalcamera_kenkyu/output.jpg", np.uint8(a)) # write it!