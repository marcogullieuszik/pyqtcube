from spectral_cube import SpectralCube
import astropy.units as u
import numpy as np


def read(ifile, extn=1):
    return DataCube(SpectralCube.read(ifile, hdu=extn))


class DataCube:

    def __init__(self, cube: SpectralCube):
        self.__cube = cube

    @property
    def unit(self):
        return self.__cube.unit

    @property
    def shape(self):
        return self.__cube.shape

    @property
    def wavelenght(self):
        return self.__cube.spectral_axis

    @property
    def wcs(self):
        return self.__cube.wcs.celestial

    def get_channel(self, i) -> np.ndarray:
        return self.__cube[i].value

    def get_image_band(self, l1: u.Quantity, l2: u.Quantity):
        return (self.__cube.spectral_slab(l1, l2).moment0() / (l2 - l1)).to(self.unit).value

    def get_1dSpec(self, x, y, r=0):
        if r == 0:
            return self.__cube[:, y, x].value
        else:
            yy, xx = np.indices([r * 2 + 1, r * 2 + 1], dtype='float')
            radiusw = ((yy - r) ** 2 + (xx - r) ** 2)
            mask = radiusw <= r ** 2

            subcube = self.__cube[:, y - r:y + r + 1, x - r:x + r + 1]
            maskedsubcube = subcube.with_mask(mask)
            spec = maskedsubcube.mean(axis=(1, 2))
            return spec

    def closest_spectral_channel(self, v):
        return self.__cube.closest_spectral_channel(v)
