                # m -------

                vec2d = (float(myvalues[td['x']]), float(myvalues[td['z']]))
                polardistance = math.sqrt(vec2d[0] ** 2 + vec2d[1] ** 2)

                vec2dtotarget = (
                    float(othervalues[td['x']]) - float(myvalues[td['x']]),
                    float(othervalues[td['z']]) - float(myvalues[td['z']])
                )
                targetdistance = math.sqrt(vec2dtotarget[0] ** 2 + vec2dtotarget[1] ** 2)

                thrust = 0.0
                steering = 0.0

                turretbearing = aim(myvalues, othervalues)
                turretdeclination = np.random.uniform(-0.4, 0.4)

                desired_distance = 2000.0

                if polardistance < 1700:

                    if targetdistance > desired_distance:
                        # Approach rival until reaching circle distance
                        thrust = 10.0

                        if turretbearing > 0.0:
                            steering = 1.0
                        elif turretbearing < 0.0:
                            steering = -1.0

                    else:
                        # Circle rival while trying to stay around 2000 distance
                        thrust = 10.0

                        circle_offset = 90.0
                        distance_error = targetdistance - desired_distance

                        desired_bearing = turretbearing + circle_offset + (distance_error * 0.05)

                        if desired_bearing > 0.0:
                            steering = 1.0
                        elif desired_bearing < 0.0:
                            steering = -1.0

                else:
                    thrust = 0.0
                    steering = 0.0

                if targetdistance < 200:
                    command.command = FIRE
                    thrust = 0.0

                # ----
