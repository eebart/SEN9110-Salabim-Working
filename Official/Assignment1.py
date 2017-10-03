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
<<<<<<< HEAD
        
=======

        # Security Scan
        self.enter(waitingline_security)
        if securityScan.ispassive():
            securityScan.activate()
        yield self.passivate()

>>>>>>> fd7ceeaedeb650adbab9695d62d129e93313e455
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

def avg(lst):
    cleanedlst = [x for x in lst if str(x) != 'nan']
    if len(cleanedlst)==0:
        return 0
    return sum(cleanedlst)/len(cleanedlst)
            
#pax statistics
pax_thru_mean = []
pax_thru_95 = []

#queue statistics
passport_length = []
passport_waiting = []
luggage_drop_length = []
luggage_drop_waiting = []
luggage_pickup_length = []
luggage_pickup_waiting = []

#utilization statistics
passport_util = []
scanner_util = []
patdown_util = []

replications = 10
if len(sys.argv) > 1:
    replications = int(sys.argv[1])

trace = False
if replications == 1:
    trace = True

for exp in range(0,replications):
    #steipatr non-random seed for reproduceability
<<<<<<< HEAD
    env = sim.Environment(trace=False,random_seed=exp)
=======
    env = sim.Environment(trace=trace,random_seed=exp)
>>>>>>> fd7ceeaedeb650adbab9695d62d129e93313e455

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

    #TODO why suspend only length monitoring? Does everything need to be suspended?
    # Warm-up - don't collect statistics
    waitingline_passport.length.monitor(False)    
    waitingline_security.length.monitor(False)
    waitingline_patdown.length.monitor(False)
    waitingline_luggageDropoff.length.monitor(False)
    waitingline_luggageLuggagePickup.length.monitor(False)
    waitingline_passengerLuggagePickup.length.monitor(False)
    env.run(duration=60*60)

    # Collect statistics
    waitingline_passport.length.monitor(True)
    waitingline_security.length.monitor(True)
    waitingline_patdown.length.monitor(True)
    waitingline_luggageDropoff.length.monitor(True)
    waitingline_luggageLuggagePickup.length.monitor(True)
    waitingline_passengerLuggagePickup.length.monitor(True)
    env.run(duration=4*60*60)

    pax_thru_mean += [luggagePickup.monitor_time_in_complex.mean()]
    pax_thru_95 += [luggagePickup.monitor_time_in_complex.percentile(95)/replications]

    passport_length += [waitingline_passport.length.mean()]
    passport_waiting += [waitingline_passport.length_of_stay.mean()]
    luggage_drop_length += [waitingline_luggageDropoff.length.mean()]
    luggage_drop_waiting += [waitingline_luggageDropoff.length_of_stay.mean()]
    luggage_pickup_length += [waitingline_passengerLuggagePickup.length.mean()]
    luggage_pickup_waiting += [waitingline_passengerLuggagePickup.length_of_stay.mean()]
    
    passport_util += [passportControl.getUtilization()]
    scanner_util += [securityScan.getUtilization()]
    patdown_util += [patDown.getUtilization()]
    
print()
print("-- Passenger Statistics --")
print("passenger throughput time mean [s]:", avg(pax_thru_mean)) 
print("passenger throughput time 95% confidence interval [s]:", avg(pax_thru_95))
print()
print("-- Queue Statistics --")
print("passport queue length mean [persons]:",avg(passport_length))
print("passport queue waiting time mean [s]:", avg(passport_waiting))
print("luggage drop length mean [persons]:", avg(luggage_drop_length))
print("luggage drop waiting time mean [s]:", avg(luggage_drop_waiting))
print("luggage pickup length mean [persons]:", avg(luggage_pickup_length))
print("luggage pickup waiting time mean [s]:", avg(luggage_pickup_waiting))
print()
print("-- Utilization Statistics --")
<<<<<<< HEAD
print("passport control utilization [%]:", avg(passport_util)) 
print("scanner utilization [%]:", avg(scanner_util)) 
print("patdown utilization [%]:", avg(patdown_util))
print()
=======
print("passport control utilization:",passportControl.getUtilizationManual())
print("scanner utilization:",securityScan.getUtilizationManual())
print("patdown utilization:",patDown.getUtilizationManual())
print()
>>>>>>> fd7ceeaedeb650adbab9695d62d129e93313e455
