# -*- coding: utf-8 -*-

# Octowire Framework
# Copyright (c) ImmunIT - Jordan Ovrè / Paul Duncan
# License: Apache 2.0
# Paul Duncan / Eresse <pduncan@immunit.ch>
# Jordan Ovrè / Ghecko <jovre@immunit.ch>

import shutil
import struct
import time

from octowire.spi import SPI
from octowire.gpio import GPIO
from octowire_framework.module.AModule import AModule


class FlashDump(AModule):
    def __init__(self, owf_config):
        super(FlashDump, self).__init__(owf_config)
        self.meta.update({
            'name': 'SPI flash dump',
            'version': '1.0.0',
            'description': 'Dump generic SPI flash memories',
            'author': 'Jordan Ovrè / Ghecko <jovre@immunit.ch>, Paul Duncan / Eresse <pduncan@immunit.ch>'
        })
        self.owf_serial = None
        self.options = {
            "spi_bus": {"Value": "", "Required": True, "Type": "int",
                        "Description": "SPI bus (0=SPI0 or 1=SPI1)", "Default": 0},
            "cs_pin": {"Value": "", "Required": True, "Type": "int",
                       "Description": "GPIO used as chip select (CS)", "Default": 0},
            "dumpfile": {"Value": "", "Required": True, "Type": "file_w",
                         "Description": "Dump output filename", "Default": ""},
            "sectors": {"Value": "", "Required": True, "Type": "int",
                        "Description": "Number of sector (4096 bytes) to read.\nFor example 1024 sector * 4096 = 4MiB",
                        "Default": 1024},
            "start_sector": {"Value": "", "Required": True, "Type": "int",
                             "Description": "Start sector index (1 sector = 4096 bytes)", "Default": 0},
            "spi_baudrate": {"Value": "", "Required": True, "Type": "int",
                             "Description": "SPI frequency (1000000 = 1MHz) maximum = 50MHz", "Default": 1000000},
            "spi_polarity": {"Value": "", "Required": True, "Type": "int",
                             "Description": "SPI polarity (1=high or 0=low)", "Default": 0},
            "spi_phase": {"Value": "", "Required": True, "Type": "string",
                          "Description": "SPI phase (1=high or 0=low)", "Default": 0}
        }
        self.advanced_options.update({
            "sector_size": {"Value": "", "Required": True, "Type": "int",
                            "Description": "Flash sector size", "Default": 0x1000}
        })

    @staticmethod
    def _sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def dump_flash(self):
        bus_id = self.options["spi_bus"]["Value"]
        cs_pin = self.options["cs_pin"]["Value"]
        spi_baudrate = self.options["spi_baudrate"]["Value"]
        spi_cpol = self.options["spi_polarity"]["Value"]
        spi_cpha = self.options["spi_phase"]["Value"]
        sector_size = self.advanced_options["sector_size"]["Value"]
        sectors = self.options["sectors"]["Value"]
        current_sector_addr = self.options["start_sector"]["Value"]
        dump_file = self.options["dumpfile"]["Value"]
        size = sector_size * sectors
        t_width, _ = shutil.get_terminal_size()
        buff = bytearray()

        spi_interface = SPI(serial_instance=self.owf_serial, bus_id=bus_id)
        cs = GPIO(serial_instance=self.owf_serial, gpio_pin=cs_pin)
        cs.direction = GPIO.OUTPUT
        cs.status = 1
        spi_interface.configure(baudrate=spi_baudrate, clock_polarity=spi_cpol, clock_phase=spi_cpha)

        self.logger.handle("Starting dump: {}.".format(self._sizeof_fmt(size)), self.logger.HEADER)
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
                current_sector_addr += sector_size
            cs.status = 0
            self.logger.handle("Successfully dumped {} from flash memory.".format(self._sizeof_fmt(current_sector_addr)),
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
        Dump generic SPI flash memories
        :return: Nothing
        """
        self.connect()
        if not self.owf_serial:
            return
        try:
            self.dump_flash()
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
