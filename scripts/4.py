'''
Seek and Destroying Script
'''

import socket
from struct import *
import datetime, time
from TelemetryDictionary import telemetrydirs as td
import sys

import math
import numpy as np

from Command import Command
from Command import Recorder
import Configuration

FIRE = 11

def getAzimuth(x1, z1, x2, z2): 
    dx = (x2 - x1) 
    dz = (z2 - z1) 

    val = np.arctan2(dz, dx) * 180.0/np.pi

    if (val >= 90):
        val -= 90
    else:
        val += 270

    return val

def getAzimuthRadians(x1, z1, x2, z2):
    x = getAzimuth(x1, z1, x2, z2) * (np.pi / 180.0) * (-1)

    if (getAzimuth(x1, z1, x2, z2) > 180 and getAzimuth(x1, z1, x2, z2) < 360):
        x = getAzimuth(x1, z1, x2, z2) - 360
        x = x * (np.pi / 180.0) * (-1)

    return x

quadrant = 0
sp = 0
escaping_water = False

turretdeclination = -0.6
last_enemy_health = None

def getContinuosAzimuthRadians(x1, z1, x2, z2):
    global quadrant
    global sp

    x = getAzimuthRadians(x1, z1, x2, z2)

    currquadrant = 0
    if (x1 < 0 and z1 > 0):
        currquadrant = 1
    if (x1 < 0 and z1 < 0):
        currquadrant = 2
    if (x1 > 0 and z1 < 0):
        currquadrant = 3
    if (x1 > 0 and z1 > 0):
        currquadrant = 4

    if (quadrant == 3 and currquadrant == 2):
        sp += 1
        x = x + sp * 2 * np.pi

    if (quadrant == 2 and currquadrant == 3):
        sp -= 1
        x = x + sp * 2 * np.pi

    quadrant = currquadrant

    return x

def aim(values1, values2):
    angle = getAzimuth(values1[td['x']], values1[td['z']], values2[td['x']], values2[td['z']])
    azimuth1 = values1[td['azimuth']]

    angle2 = angle - azimuth1

    return angle2

class Controller:
    def __init__(self, tankparam):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tankparam = int(tankparam)

        port = 4601
        if (tankparam == 1):
            port = 4601
        elif (tankparam == 2):
            port = 4602

        self.server_address = ('0.0.0.0', port)
        print('Starting up on %s port %s' % self.server_address)

        self.sock.bind(self.server_address)
        self.sock.settimeout(5)

        self.length = 84 + 3 * 4
        self.unpackcode = '<LLififffffffffffffffffff'

        self.recorder = Recorder()
        self.tank = tankparam

    def read(self):
        data, address = self.sock.recvfrom(self.length)

        if len(data) > 0 and len(data) == self.length:
            new_values = unpack(self.unpackcode, data)
            return new_values

        return None

    def run(self):
        global escaping_water
        global turretdeclination
        global last_enemy_health

        if (self.tank == 1):
            command = Command(Configuration.ip, 4501)
        elif (self.tank == 2):
            command = Command(Configuration.ip, 4502)

        while (True):
            try:
                tank1values = self.read()
                if int(tank1values[td['number']]) != 1:
                    continue

                tank2values = self.read()
                if int(tank2values[td['number']]) != 2:
                    continue

                if (self.tank == 1):
                    myvalues = tank1values
                    othervalues = tank2values
                else:
                    myvalues = tank2values
                    othervalues = tank1values

                self.recorder.recordvalues(myvalues, othervalues)

                print(
                    f"Tank {myvalues[td['number']]}: "
                    f"x={myvalues[td['x']]:.2f}, "
                    f"z={myvalues[td['z']]:.2f}, "
                    f"Radar X={myvalues[td['radarx']]:.2f}, "
                    f"Radar Y={myvalues[td['radary']]:.2f}, "
                    f"Radar Z={myvalues[td['radarz']]:.2f}, "
                    f"health={myvalues[td['health']]:.2f}"
                )

                # m -------

                vec2d = (
                    float(myvalues[td['x']]),
                    float(myvalues[td['z']])
                )

                polardistance = math.sqrt(
                    vec2d[0] ** 2 + vec2d[1] ** 2
                )

                vec2dtotarget = (
                    float(othervalues[td['x']]) - float(myvalues[td['x']]),
                    float(othervalues[td['z']]) - float(myvalues[td['z']])
                )

                targetdistance = math.sqrt(
                    vec2dtotarget[0] ** 2 + vec2dtotarget[1] ** 2
                )

                thrust = 0.0
                steering = 0.0

                turretbearing = aim(myvalues, othervalues)

                enemy_health = othervalues[td['health']]
                enemy_radarx = othervalues[td['radarx']]
                enemy_radarz = othervalues[td['radarz']]

                enemy_was_hit = False
                radar_detected_shot = False

                if last_enemy_health is not None:
                    if enemy_health < last_enemy_health:
                        enemy_was_hit = True

                if enemy_radarx != 0.0 or enemy_radarz != 0.0:
                    radar_detected_shot = True

                if enemy_was_hit:
                    turretdeclination = turretdeclination

                elif radar_detected_shot:
                    shot_dx = enemy_radarx - othervalues[td['x']]
                    shot_dz = enemy_radarz - othervalues[td['z']]

                    target_dx = othervalues[td['x']] - myvalues[td['x']]
                    target_dz = othervalues[td['z']] - myvalues[td['z']]

                    shot_projection = (shot_dx * target_dx) + (shot_dz * target_dz)

                    if shot_projection < 0:
                        turretdeclination += 0.2
                    else:
                        turretdeclination -= 0.2

                    if turretdeclination > 0.8:
                        turretdeclination = 0.8

                    if turretdeclination < -0.6:
                        turretdeclination = -0.6

                else:
                    turretdeclination += 0.2

                    if turretdeclination > 0.8:
                        turretdeclination = -0.6

                last_enemy_health = enemy_health

                # =========================
                # CHASE MODE
                # =========================

                if targetdistance > 2000:
                    if turretbearing > 0.0:
                        steering = 1.0
                        thrust = 10.0

                    elif turretbearing < 0.0:
                        steering = -1.0
                        thrust = 10.0

                # =========================
                # CIRCLE MODE
                # =========================

                else:
                    circle_bearing = turretbearing + 90.0

                    if circle_bearing > 0.0:
                        steering = 1.0

                    elif circle_bearing < 0.0:
                        steering = -1.0

                    if polardistance >= 1700:
                        escaping_water = True

                    if polardistance <= 1000:
                        escaping_water = False

                    if escaping_water:
                        thrust = -10.0
                    else:
                        thrust = 10.0

                # =========================
                # FIRE CONTROL
                # =========================

                if targetdistance < 2100:
                    command.command = FIRE

                if targetdistance < 200:
                    thrust = 0.0

                # ----

                command.send_command(
                    myvalues[td['timer']],
                    self.tank,
                    thrust,
                    steering,
                    turretdeclination,
                    turretbearing
                )

            except socket.timeout:
                print("Episode Completed")
                break

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python SeekAndDestroy.py [tank_number]")
        sys.exit(1)

    controller = Controller(sys.argv[1])
    controller.run()
