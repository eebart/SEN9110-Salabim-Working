import salabim as sim
import time, sys

class PassengerGenerator(sim.Component):
    def process(self):
        while True:
            Passenger()
            yield self.hold(sim.Normal(60).sample())

class Passenger(sim.Component):
    def process(self):
        # Passport control
        self.enter(waitingline_passport)
        if passportControl.ispassive():
            passportControl.activate()
        yield self.passivate()

        # Walking from passport control to security scan
        yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Security Scan
        self.enter(waitingline_security)
        if securityScan.ispassive():
            securityScan.activate()
        yield self.passivate()

        # Put luggage on belt
        self.enter(waitingline_luggageDropoff)
        if luggageDropoff.ispassive():
            luggageDropoff.activate()
        yield self.passivate()

        # 10% Pat Down Requirement
        if (sim.Uniform(1,100).sample() <= 10):
            # Walking from security scan to patdown
            yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s
            # Patdown
            self.enter(waitingline_patdown)
            if patDown.ispassive():
                patDown.activate()
            yield self.passivate()

        # Walking along luggage belt
        yield self.hold(10/(0.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Pick up luggage, matching owner
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

class Server(sim.Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activeTime = 0
        self.startProcessTime = -1

    def startUtilTime(self):
        self.startProcessTime = env.now()

    def endUtilTime(self):
        if self.startProcessTime >= 0:
            endNow = env.now()
            self.activeTime += endNow - self.startProcessTime
            self.startProcessTime = -1

    def getUtilization(self):
        return self.activeTime / (env.now() - self._creation_time)

class PassportControl(Server):
    def process(self):
        while True:
            while len(waitingline_passport) == 0:
                self.endUtilTime()
                yield self.passivate()

            self.startUtilTime()
            self.passenger = waitingline_passport.pop()
            yield self.hold(sim.Uniform(20,40).sample())

            self.passenger.activate()


class LuggageDropoff(Server):
    def process(self):
        while True:
            while len(waitingline_luggageDropoff) == 0:
                yield self.passivate()

            self.passenger = waitingline_luggageDropoff.pop()

            Luggage(self.passenger.name())
            yield self.hold(sim.Triangular(30.,90.,45.).sample())
            self.passenger.activate()

class SecurityScan(Server):
    def process(self):
        while True:
            while len(waitingline_security) == 0:
                self.endUtilTime()
                yield self.passivate()

            self.startUtilTime()
            self.passenger = waitingline_security.pop()
            yield self.hold(10)
            self.passenger.activate()

class PatDown(Server):
    def process(self):
        while True:
            while len(waitingline_patdown) == 0:
                self.endUtilTime()
                yield self.passivate()

            self.startUtilTime()
            self.passenger = waitingline_patdown.pop()
            yield self.hold(sim.Uniform(60,120).sample())
            self.passenger.activate()

class LuggagePickup(Server):
    def process(self):
        noMatches = False

        while True:
            while len(waitingline_passengerLuggagePickup) == 0 or len(waitingline_luggageLuggagePickup) == 0 or noMatches:
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

            noMatches = True

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
    env = sim.Environment(trace=True,random_seed=exp)

    PassengerGenerator()
    passportControl = PassportControl()
    luggageDropoff = LuggageDropoff()
    securityScan = SecurityScan()
    patDown = PatDown()
    luggagePickup = LuggagePickup()

    waitingline_passport = sim.Queue('waitingline_passport')
    waitingline_security = sim.Queue('waitingline_security')
    waitingline_patdown = sim.Queue('waitingline_patdown')
    waitingline_luggageDropoff = sim.Queue('waitingline_luggageDropoff')
    waitingline_luggageLuggagePickup = sim.Queue('waitingline_luggageLuggagePickup')
    waitingline_passengerLuggagePickup = sim.Queue('waitingline_passengerLuggagePickup')

    # Warm-up - don't collect statistics
    waitingline_passport.length.monitor(False)
    waitingline_security.length.monitor(False)
    waitingline_patdown.length.monitor(False)
    waitingline_luggageDropoff.length.monitor(False)
    env.run(duration=60*60)

    # Collect statistics
    waitingline_passport.length.monitor(True)
    waitingline_security.length.monitor(True)
    waitingline_patdown.length.monitor(True)
    waitingline_luggageDropoff.length.monitor(True)
    env.run(duration=4*60*60)

    passport_length += waitingline_passport.length.mean()
    passport_waiting += waitingline_passport.length_of_stay.mean()
    luggage_pickup_length += waitingline_luggageDropoff.length.mean()
    luggage_pickup_waiting += waitingline_luggageDropoff.length_of_stay.mean()

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
print("passport control utilization:",passportControl.getUtilization())
print("scanner utilization:",securityScan.getUtilization())
print("patdown utilization:",patDown.getUtilization())
print()
