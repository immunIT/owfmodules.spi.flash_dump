# -*- coding:utf-8 -*-

# Octowire Framework
# Copyright (c) Jordan Ovrè / Paul Duncan
# License: GPLv3
# Paul Duncan / Eresse <eresse@dooba.io>
# Jordan Ovrè / Ghecko <ghecko78@gmail.com


import shutil
import struct
import time

from octowire.spi import SPI
from octowire.gpio import GPIO
from octowire_framework.module.AModule import AModule


class SPIDump(AModule):
    def __init__(self, owf_config):
        super(SPIDump, self).__init__(owf_config)
        self.meta.update({
            'name': 'SPI dump flash',
            'version': '1.0.0',
            'description': 'Module to dump an SPI flash',
            'author': 'Jordan Ovrè <ghecko78@gmail.com> / Paul Duncan <eresse@dooba.io>'
        })
        self.owf_serial = None
        self.options = [
            {"Name": "spi_bus", "Value": "", "Required": True, "Type": "int",
             "Description": "The octowire SPI device (0=SPI0 or 1=SPI1)", "Default": 0},
            {"Name": "cs_pin", "Value": "", "Required": True, "Type": "int",
             "Description": "The octowire GPIO used as chip select (CS)", "Default": 0},
            {"Name": "dumpfile", "Value": "", "Required": True, "Type": "file_w",
             "Description": "The dump filename", "Default": ""},
            {"Name": "sectors", "Value": "", "Required": True, "Type": "int",
             "Description": "The number of sector (4096) to read.\nFor example 1024 sector * 4096 = 4MiB",
             "Default": 1024},
            {"Name": "start_sector", "Value": "", "Required": True, "Type": "int",
             "Description": "The starting sector (1 sector = 4096 bytes)", "Default": 0},
            {"Name": "spi_baudrate", "Value": "", "Required": True, "Type": "int",
             "Description": "set SPI baudrate (1000000 = 1MHz) maximum = 50MHz", "Default": 1000000},
            {"Name": "spi_polarity", "Value": "", "Required": True, "Type": "int",
             "Description": "set SPI polarity (1=high or 0=low)", "Default": 0},
            {"Name": "spi_phase", "Value": "", "Required": True, "Type": "string",
             "Description": "set SPI phase (1=high or 0=low)", "Default": 0}
        ]
        self.advanced_options.append(
            {"Name": "sector_size", "Value": "", "Required": True, "Type": "int",
             "Description": "Flash sector size", "Default": 0x1000}
        )

    @staticmethod
    def _sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def dump_flash(self):
        bus_id = self.get_option_value("spi_bus")
        cs_pin = self.get_option_value("cs_pin")
        spi_baudrate = self.get_option_value("spi_baudrate")
        spi_cpol = self.get_option_value("spi_polarity")
        spi_cpha = self.get_option_value("spi_phase")
        sector_size = self.get_advanced_option_value("sector_size")
        sectors = self.get_option_value("sectors")
        current_sector_addr = self.get_option_value("start_sector")
        dump_file = self.get_option_value("dumpfile")
        size = sector_size * sectors
        t_width, _ = shutil.get_terminal_size()
        buff = bytearray()

        spi_interface = SPI(serial_instance=self.owf_serial, bus_id=bus_id)
        cs = GPIO(serial_instance=self.owf_serial, gpio_pin=cs_pin)
        cs.direction = GPIO.OUTPUT
        cs.status = 1
        spi_interface.configure(baudrate=spi_baudrate, clock_polarity=spi_cpol, clock_phase=spi_cpha)

        self.logger.handle("Start dumping {}.".format(self._sizeof_fmt(size)), self.logger.HEADER)
        try:
            start_time = time.time()
            while current_sector_addr < size:
                # cmd = EEPROM Read 0x03 instruction + start address
                cmd = b"\x03" + (struct.pack(">L", current_sector_addr)[1:])
                cs.status = 0
                spi_interface.transmit(cmd)
                resp = spi_interface.receive(sector_size)
                cs.status = 1
                if not resp:
                    raise Exception("Unexpected error while reading the SPI flash")
                buff.extend(resp)
                print(" " * t_width, end="\r", flush=True)
                print("Read: {}".format(self._sizeof_fmt(current_sector_addr)), end="\r", flush=True)
                current_sector_addr += sector_size
            cs.status = 0
            self.logger.handle("Successfully dump {} from flash memory.".format(self._sizeof_fmt(current_sector_addr)),
                               self.logger.SUCCESS)
            self.logger.handle("Dumped in {} seconds.".format(time.time() - start_time, self.logger.INFO))
            with open(dump_file, 'wb') as f:
                f.write(buff)
            self.logger.handle("Dump saved into {}".format(dump_file), self.logger.RESULT)
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)

    def run(self):
        """
        Main function.
        The aim of this module is to dump an spi flash
        :return: Nothing
        """
        self.connect()
        if not self.owf_serial:
            return
        try:
            self.dump_flash()
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
