# -*- coding: utf-8 -*-
# constants.py

"""
Some constants which can be used in JSON files to specify tests
"""


class EASConstants:
    def __init__(self):
        self.day = 1
        self.month = 28
        self.year = 365.25

        self.sun_radius = 695500e3  # metres
        self.earth_radius = 6371e3  # metres
        self.jupiter_radius = 71492e3  # metres
        self.phy_AU = 149597870700  # metres

        self.Rearth = 0.08911486  # Jupiter radii

        self.plato_noise = 0.000315  # noise in a 25-sec cadence pixel, from PSLS
