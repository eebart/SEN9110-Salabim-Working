# What's up guys!!

## Short summary of assignment

# Build a simulation model of airport that mimics:
# - Passport control (triangular 30-45-90 seconds)
# - Security scan (constant 10 seconds)
# Passengers arrive randomly (iat normal 60 seconds)
# Luggage on belt at security scan, one at a time (20-40 seconds)
# Conveyor 10m, speed 0.5 m/s
# At security scan manual check for 10% of passengers with one person, others don't wait
# After luggage, passengers take luggage again (20-40 seconds)
# Passenger movements 2.5km/h, 10m along luggage belt
# Distance between other processes 5m ????

# Model for 4 hours, warm-up 1 hour.
# Run 10 replications (average + 90% confidence interval)
# Provide utilization data of passport control, scanner and secondary check

import salabim as sim

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
        if luggagePickup.ispassive():
                luggagePickup.activate()
        self.passivate()

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

                        print(luggage)
                        print(passenger)

                        passenger.activate()
                        luggage.activate()

                        break

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


env = sim.Environment(trace=True)

PassengerGenerator()
passportcontrol = PassportControl()
securityscan = SecurityScan()
patdown = PatDown()
luggagePickup = LuggagePickup()

waitingline_passport = sim.Queue('waitingline_passport')
waitingline_security = sim.Queue('waitingline_security')
waitingline_patdown = sim.Queue('waitingline_patdown')

waitingline_luggageLuggagePickup = sim.Queue('waitingline_luggageLuggagePickup')
waitingline_passengerLuggagePickup = sim.Queue('waitingline_passengerLuggagePickup')

env.run(till=60*60)

print()
waitingline_passport.print_statistics()
waitingline_security.print_statistics()
waitingline_patdown.print_statistics()
waitingline_passengerLuggagePickup.print_statistics()
waitingline_luggageLuggagePickup.print_statistics()

#for running multiple repetitions
#repetitions = 100
#queue_mean = 0

#for exp in range(0,repetitions):
#    env = sim.Environment(trace=False,random_seed=exp)
#    CustomerGenerator()
#    clerks = sim.Queue('clerks')
#    for i in range(3):
#        Clerk().enter(clerks)
#    waitingline = sim.Queue('waitingline')

#    env.run(till=50000)

#    queue_mean += waitingline.length.mean()

#print("queue mean is",queue_mean/repetitions,"for",repetitions,"runs")
