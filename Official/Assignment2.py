#edited by steipatr at 15:23
import salabim as sim
import time, sys

class PassengerGenerator(sim.Component):
    def process(self):
        while True:
            Passenger()
            yield self.hold(sim.Exponential(60).sample())

class Passenger(sim.Component):
    def process(self):
        self.arrivaltime = env.now()
        # Passport control
        self.enter(waitingline_passport)
        if passportControl.ispassive():
            passportControl.activate()
        yield self.passivate()

        # Walking from passport control to security scan
        yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Put luggage on belt
        self.enter(waitingline_luggageDropoff)
        if luggageDropoff.ispassive():
            luggageDropoff.activate()
        yield self.passivate()

        # Security Scan
        self.enter(waitingline_security)
        if securityScan.ispassive():
            securityScan.activate()
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
        luggagePickup.monitor_time_in_complex.tally(env.now() - self.arrivaltime)

class Luggage(sim.Component):
    def __init__(self, passenger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = passenger

    def process(self):
        # Roll along luggage belt
        yield self.hold(10/0.5)

        # Enter luggage waiting line
        self.enter(waitingline_luggageLuggagePickup)
        if luggagePickup.ispassive():
            luggagePickup.activate()

        yield self.passivate()

class Server(sim.Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activeTime = 0
        self.activeTimeManual = 0
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

    def getUtilizationManual(self):
        return self.activeTimeManual / (env.now() - self._creation_time)

class PassportControl(Server):
    def process(self):
        while True:
            while len(waitingline_passport) == 0:
                self.endUtilTime()
                yield self.passivate()

            self.startUtilTime()
            self.passenger = waitingline_passport.pop()

            sample = sim.Triangular(30,90,45).sample()
            self.activeTimeManual += sample
            yield self.hold(sample)

            self.passenger.activate()

class LuggageDropoff(Server):
    def process(self):
        while True:
            while len(waitingline_luggageDropoff) == 0:
                yield self.passivate()

            self.passenger = waitingline_luggageDropoff.pop()

            Luggage(self.passenger)
            yield self.hold(sim.Uniform(20,40).sample())
            self.passenger.activate()

class SecurityScan(Server):
    def process(self):
        while True:
            while len(waitingline_security) == 0:
                self.endUtilTime()
                yield self.passivate()

            self.startUtilTime()
            self.passenger = waitingline_security.pop()
            sample = 10
            self.activeTimeManual += sample
            yield self.hold(sample)
            self.passenger.activate()

class PatDown(Server):
    def process(self):
        while True:
            while len(waitingline_patdown) == 0:
                self.endUtilTime()
                yield self.passivate()

            self.startUtilTime()
            self.passenger = waitingline_patdown.pop()

            sample = sim.Uniform(60,120).sample()
            self.activeTimeManual += sample
            yield self.hold(sample)

            self.passenger.activate()

class LuggagePickup(Server):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.monitor_time_in_complex = sim.Monitor(name='time in complex')

    def process(self):
        while True:
            while len(waitingline_passengerLuggagePickup) == 0 or len(waitingline_luggageLuggagePickup) == 0:
                yield self.passivate()

            for passenger in waitingline_passengerLuggagePickup:
                for luggage in waitingline_luggageLuggagePickup:
                    if luggage.owner.name() == passenger.name():
                        #found luggage of owner!
                        waitingline_passengerLuggagePickup.remove(passenger)
                        waitingline_luggageLuggagePickup.remove(luggage)
                        yield self.hold(sim.Uniform(20,40).sample())
                        passenger.activate()
                        #luggage.activate() This is problematic because it is never the luggage who activates successfully

                        break

            yield self.passivate()

env = sim.Environment()

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

env.run(duration=4*60*60)
