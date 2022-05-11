# -*- coding: utf-8 -*-
# constants.py

"""
Some constants which can be used in task descriptions
"""


class EASConstants:
    def __init__(self):
        self.day = 1  # days
        self.month = 28  # days
        self.year = 365.25  # days

        self.sun_radius = 695500e3  # metres
        self.earth_radius = 6371e3  # metres
        self.jupiter_radius = 71492e3  # metres
        self.phy_AU = 149597870700  # metres

        self.Rearth = 0.08911486  # Jupiter radii

        self.plato_noise = 0.000315  # PLATO noise in a 25-sec cadence pixel, from PSLS
