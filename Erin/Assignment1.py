import salabim as sim
import time
import sys

class PassengerGenerator(sim.Component):
    def process(self):
        while True:
            Passenger()
            yield self.hold(sim.Normal(60).sample())

class Passenger(sim.Component):
    def process(self):
        # Passport control
        self.enter(waitingline_passport)
        if passportcontrol.ispassive():
            passportcontrol.activate()
        yield self.passivate()

        # Walking from passport control to security scan
        yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Security Scan
        self.enter(waitingline_security)
        if securityscan.ispassive():
            securityscan.activate()
        yield self.passivate()

        # Put luggage on belt
        yield self.hold(sim.Uniform(20,40).sample())
        Luggage(self.name())

        # 10% Pat Down Requirement
        if (sim.Uniform(1,100).sample() <= 10):
            # Walking from security scan to patdown
            yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s
            # Patdown
            self.enter(waitingline_patdown)
            if patdown.ispassive():
                patdown.activate()
            yield self.passivate()

        # Walking along luggage belt
        yield self.hold(10/(0.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Pick up luggage, not matching owner
        self.enter(waitingline_passengerLuggagePickup)
        if luggagePickup.ispassive():
            luggagePickup.activate()
        yield self.passivate()


class Luggage(sim.Component):
    def __init__(self, passengerName, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = passengerName

    def process(self):
        # Roll along luggage belt
        yield self.hold(10/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Enter luggage waiting line
        self.enter(waitingline_luggageLuggagePickup)
        #if luggagePickup.ispassive():
        #        luggagePickup.activate()
        self.passivate()

class PassportControl(sim.Component):
    def process(self):
        while True:
            while len(waitingline_passport) == 0:
                yield self.passivate()
            self.passenger = waitingline_passport.pop()
            yield self.hold(sim.Triangular(30.,90.,45.).sample())
            self.passenger.activate()

class SecurityScan(sim.Component):
    def process(self):
        while True:
            while len(waitingline_security) == 0:
                yield self.passivate()
            self.passenger = waitingline_security.pop()
            yield self.hold(10)
            self.passenger.activate()

class PatDown(sim.Component):
    def process(self):
        while True:
            while len(waitingline_patdown) == 0:
                yield self.passivate()
            self.passenger = waitingline_patdown.pop()
            yield self.hold(10) #TODO not yet defined
            self.passenger.activate()

class LuggagePickup(sim.Component):
    def process(self):
        while True:
            while len(waitingline_passengerLuggagePickup) == 0 or len(waitingline_luggageLuggagePickup) == 0:
                yield self.passivate()

            for passenger in waitingline_passengerLuggagePickup:
                for luggage in waitingline_luggageLuggagePickup:
                    if luggage.owner == passenger.name():
                        #found luggage of owner!
                        waitingline_passengerLuggagePickup.remove(passenger)
                        waitingline_luggageLuggagePickup.remove(luggage)

                        yield self.hold(sim.Uniform(20,40).sample())

                        passenger.activate()
                        #luggage.activate() This is problematic because it is never the luggage who activates successfully

                        break

#pax statistics
pax_thru_mean = 0
pax_thru_95 = 0

#queue statistics
passport_length = 0
passport_waiting = 0
luggage_drop_length = 0
luggage_drop_waiting = 0
luggage_pickup_length = 0
luggage_pickup_waiting = 0

#utilization statistics
passport_util = 0
scanner_util = 0
patdown_util = 0

replications = 10
if len(sys.argv) > 1:
    replications = int(sys.argv[1])

for exp in range(0,replications):
    #steipatr non-random seed for reproduceability
    env = sim.Environment(trace=False,random_seed=exp)

    PassengerGenerator()
    passportcontrol = PassportControl()
    securityscan = SecurityScan()
    patdown = PatDown()
    luggagePickup = LuggagePickup()

    waitingline_passport = sim.Queue('waitingline_passport')
    waitingline_security = sim.Queue('waitingline_security')
    waitingline_patdown = sim.Queue('waitingline_patdown')
    waitingline_luggage = sim.Queue('waitingline_luggage')

    waitingline_luggageLuggagePickup = sim.Queue('waitingline_luggageLuggagePickup')
    waitingline_passengerLuggagePickup = sim.Queue('waitingline_passengerLuggagePickup')

    # Warm-up - don't collect statistics
    waitingline_passport.length.monitor(False)
    waitingline_security.length.monitor(False)
    waitingline_patdown.length.monitor(False)
    waitingline_luggage.length.monitor(False)
    env.run(duration=60*60)

    # Collect statistics
    waitingline_passport.length.monitor(True)
    waitingline_security.length.monitor(True)
    waitingline_patdown.length.monitor(True)
    waitingline_luggage.length.monitor(True)
    env.run(duration=4*60*60)

    passport_length += waitingline_passport.length.mean()
    passport_waiting += waitingline_passport.length_of_stay.mean()
    luggage_pickup_length += waitingline_luggage.length.mean()
    luggage_pickup_waiting += waitingline_luggage.length_of_stay.mean()

print()
print("-- Pax Statistics --")
print("passenger throughput time mean:")
print("passenger throughput time 95% confidence interval:")
print()
print("-- Queue Statistics --")
print("passport queue length mean:",passport_length/replications)
print("passport queue waiting time mean [s]:",passport_waiting/replications)
print("luggage drop length mean:")
print("luggage drop waiting time mean [s]:")
print("luggage pickup length mean:",luggage_pickup_length/replications)
print("luggage pickup waiting time mean [s]:",luggage_pickup_waiting/replications)
print()
print("-- Utilization Statistics --")
print("passport control utilization:")
print("scanner utilization:")
print("patdown utilization:")
print()
