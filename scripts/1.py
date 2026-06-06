                                thrust = 10.0

                turretbearing = aim(myvalues, othervalues)
                
                turretdeclination = np.random.uniform(-0.4, 0.4)

                if targetdistance > 2000:
                    # Approach rival directly
                    if turretbearing > 0.0:
                        steering = 1.0
                    elif turretbearing < 0.0:
                        steering = -1.0
                    else:
                        steering = 0.0

                else:
                    # Circle rival instead of stopping
                    circle_bearing = turretbearing + 90.0

                    if circle_bearing > 0.0:
                        steering = 1.0
                    elif circle_bearing < 0.0:
                        steering = -1.0
                    else:
                        steering = 0.0
                    thrust = 0.0

                # ----
