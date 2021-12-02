from astropy.io import ascii
import astropy.units as u

import os


class SpecLine:
    def __init__(self, wavelenght: u.Quantity, name: str, flag: bool):
        self.wavelenght = wavelenght
        self.name = name
        self.flag = flag

    def wavelenght_at_z(self, z):
        return self.rest_wavelenght * (1 + z)


class SpecLineSet:
    def from_file(ifile=None):
        if ifile is None:
            ifile = os.path.join(
                os.path.dirname(__file__),
                'linelist_air.ecsv')
        tab = ascii.read(ifile, format='ecsv')
        r = tab[0]
        l = [SpecLine(r['wavelengt_air'],
                      name=r['name'],
                      flag=r['flag'])
             for r in tab]
        return SpecLineSet(l)

    def __init__(self, lines: list[SpecLine]):
        self.z = 0
        self.units = "AA"
        self.lines = lines
