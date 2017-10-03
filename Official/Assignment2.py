import salabim as sim
import time, sys

SCALE = 10
NUM_QUEUES = 6      # Number of machines in the machine shop

HOURS = 20              # Simulation time in hours
SIM_TIME = HOURS * 60 * 60  # Simulation time in seconds

class QueueAnimate(sim.Animate):
    def __init__(self, queue):
        self.queue = queue
        super().__init__(rectangle0=(0, 0, 0, 0), linewidth0=0)

    def rectangle(self, t):
        d = len(self.queue)
        return(165, 100 + self.queue.n * 90,165 + d * SCALE, 100 + self.queue.n * 90 + 20)
        # x0, 150                            (x coordinate of bottom left)
        # y0, 100 + self.queue.n * 90.       (y coordinate of bottom left)
        # x1, 150 + d * SCALE                (width of rectangle)
        # y1, 100 + self.queue.n * 90 + 20.  (height of rectangle)

    def fillcolor(self, t):
        return self.queue.color

class QueueTextAnimate(sim.Animate):
    def __init__(self, queue):
        self.queue = queue
        super().__init__(x0=25, y0=100 + self.queue.n * 90, text='', anchor='sw')

    def text(self, t):
        return '{}     {}'.format(self.queue.text, len(self.queue))

class ServerAnimate(sim.Animate):
    def __init__(self, server):
        self.server = server
        super().__init__(rectangle0=(0, 0, 0, 0), linewidth0=0)

    def rectangle(self, t):
        return(0, 100 + self.server.number * 90, 20, 120 + self.server.number * 90)

    def fillcolor(self, t):
        if self.server.mode() == 'idle':
            return 'green'
        if self.server.mode() == 'busy':
            return 'red'

def do_animation():
    env.animation_parameters(modelname='Airport Security Control', speed=4)
    ServerAnimate(passportControl)
    ServerAnimate(luggageDropoff)    
    ServerAnimate(securityScan)
    ServerAnimate(patDown)
    ServerAnimate(luggagePickup)
    for _,queue in queues.items():
        QueueAnimate(queue)
        QueueTextAnimate(queue)
    #Animate(x0=100,y0=100,rectangle0==(-10,-10,10,10))

class PassengerGenerator(sim.Component):
    def process(self):
        while True:
            Passenger()
            yield self.hold(sim.Exponential(60).sample())

class Passenger(sim.Component):
    def process(self):
        self.arrivaltime = env.now()
        # Passport control
        self.enter(queues['waitingline_passport'])
        if passportControl.ispassive():
            passportControl.activate()
        yield self.passivate()

        # Walking from passport control to security scan
        yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Put luggage on belt
        self.enter(queues['waitingline_luggageDropoff'])
        if luggageDropoff.ispassive():
            luggageDropoff.activate()
        yield self.passivate()

        # Security Scan
        self.enter(queues['waitingline_security'])
        if securityScan.ispassive():
            securityScan.activate()
        yield self.passivate()

        # 10% Pat Down Requirement
        if (sim.Uniform(1,100).sample() <= 10):
            # Walking from security scan to patdown
            yield self.hold(5/(2.5*1000/(60*60))) # convert 2.5 km/h to m/s
            # Patdown
            self.enter(queues['waitingline_patdown'])
            if patDown.ispassive():
                patDown.activate()
            yield self.passivate()

        # Walking along luggage belt
        yield self.hold(10/(0.5*1000/(60*60))) # convert 2.5 km/h to m/s

        # Pick up luggage, matching owner
        self.enter(queues['waitingline_passengerLuggagePickup'])
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
        self.enter(queues['waitingline_luggageLuggagePickup'])
        if luggagePickup.ispassive():
            luggagePickup.activate()

        yield self.passivate()

class Server(sim.Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activeTime = 0
        self.activeTimeManual = 0
        self.startProcessTime = -1
        self.number = 0

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number = 5

    def process(self):
        while True:
            while len(queues['waitingline_passport']) == 0:
                self.endUtilTime()
                yield self.passivate(mode='idle')
                print(passportControl.mode())

            self.startUtilTime()
            self.passenger = queues['waitingline_passport'].pop()

            sample = sim.Triangular(30,90,45).sample()
            self.activeTimeManual += sample
            yield self.hold(sample, mode='busy')
            print(passportControl.mode())

            self.passenger.activate()

class LuggageDropoff(Server):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number = 4

    def process(self):
        while True:
            while len(queues['waitingline_luggageDropoff']) == 0:
                yield self.passivate(mode='idle')

            self.passenger = queues['waitingline_luggageDropoff'].pop()

            Luggage(self.passenger)
            yield self.hold(sim.Uniform(20,40).sample(), mode='busy')
            self.passenger.activate()

class SecurityScan(Server):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number = 3

    def process(self):
        while True:
            while len(queues['waitingline_security']) == 0:
                self.endUtilTime()
                yield self.passivate(mode='idle')

            self.startUtilTime()
            self.passenger = queues['waitingline_security'].pop()
            sample = 10
            self.activeTimeManual += sample
            yield self.hold(sample, mode='busy')
            self.passenger.activate()

class PatDown(Server):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number = 2

    def process(self):
        while True:
            while len(queues['waitingline_patdown']) == 0:
                self.endUtilTime()
                yield self.passivate(mode='idle')

            self.startUtilTime()
            self.passenger = queues['waitingline_patdown'].pop()

            sample = sim.Uniform(60,120).sample()
            self.activeTimeManual += sample
            yield self.hold(sample, mode='busy')

            self.passenger.activate()

class LuggagePickup(Server):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.monitor_time_in_complex = sim.Monitor(name='time in complex')
      self.number = 0

    def process(self):
        while True:
            while len(queues['waitingline_passengerLuggagePickup']) == 0 or len(queues['waitingline_luggageLuggagePickup']) == 0:
                yield self.passivate(mode='idle')

            for passenger in queues['waitingline_passengerLuggagePickup']:
                for luggage in queues['waitingline_luggageLuggagePickup']:
                    if luggage.owner.name() == passenger.name():
                        #found luggage of owner!
                        queues['waitingline_passengerLuggagePickup'].remove(passenger)
                        queues['waitingline_luggageLuggagePickup'].remove(luggage)
                        yield self.hold(sim.Uniform(20,40).sample(), mode='busy')
                        passenger.activate()
                        #luggage.activate() This is problematic because it is never the luggage who activates successfully

                        break

            yield self.passivate(mode='idle')

class Queue(sim.Queue):
    def __init__(self, name=None,text=None, queue_num=1, color='red'):
        super().__init__(name)
        self.n = queue_num
        self.color = color
        self.text = text

env = sim.Environment()

PassengerGenerator()
passportControl = PassportControl()
luggageDropoff = LuggageDropoff()
securityScan = SecurityScan()
patDown = PatDown()
luggagePickup = LuggagePickup()

queues = {
    'waitingline_passport': Queue(name='waitingline_passport', text='Passport Control', queue_num=5, color='black'),
    'waitingline_luggageDropoff': Queue(name='waitingline_luggageDropoff', text='Luggage Dropoff ', queue_num=4, color='black'),
    'waitingline_security': Queue(name='waitingline_security', text='Security Scan   ', queue_num=3, color='black'),
    'waitingline_patdown': Queue(name='waitingline_patdown', text='Pat Down        ', queue_num=2, color='black'),
    'waitingline_luggageLuggagePickup': Queue(name='waitingline_luggageLuggagePickup', text='Waiting Luggage ',queue_num=1, color='brown'),
    'waitingline_passengerLuggagePickup': Queue(name='waitingline_passengerLuggagePickup', text='Luggage Pickup  ', queue_num=0, color='black'),
}

do_animation()
env.run(duration=SIM_TIME)
