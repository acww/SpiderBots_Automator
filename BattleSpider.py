import pigpio
from time import sleep
import threading
"""
    Version 0.3

With a suitable infrared LED connected to PIN, an object of this class provides
methods to control a Hexbug BattleSpider using channel 3.  It relies on having
pigpio installed and running:
http://abyz.me.uk/rpi/pigpio/python.html

In order to get any brighness (ie transmission range) out of the LED, use a
NPN transistor as a switch:
 https://www.electronicsclub.info/transistorcircuits.htm
with the base connected to GPIO pin, PIN, via a resistor (1) to limit the
current from the pi; the emitter to the pi's earth pin, and the collector
connected via the LED and a resistor (2) to the pi's 5v pin.  Resistor 1 in
my case is 10k; resistor 2 is 22 ohms and the LED has not burnt out yet...

The code here is based on the research and fantastic write-up by Brian Schwind:
https://blog.bschwind.com/2016/05/29/sending-infrared-commands-from-a-raspberry-pi-without-lirc/

"""
class BattleSpider:
        PIN = 0
        DUTY_CYCLE = 0.5
        KHERTZ = 38
        # set the following bits low for the action
        # 6 and 7 are the channel - "11" for channel 3
        PRTY= 5        #  There needs to be an even number of 1s and 0s
        FIRE= 4
        BWD = 3
        RGHT= 2
        LEFT= 1
        FWD = 0

        transmitting = False
        lock = threading.Lock()
        codeBuffer = [1,1,1,1, 1,1,1,1]

        # The wave form to send consists of a sequence of a series of signals
        # and gaps, where the signal component is a 38kHz square wave.
        # Eg these 2 sig & 3 gaps: _-_-_-_-________-_-_-_-___
        # consist of 15 pigpio 'pulses'

        def __init__(self):
                print('Error 63: usage is BattleSpider(pin_no)')
                exit()

        def __init__(self, pin):
                self.PIN = pin
                self.pi = pigpio.pi();
                self.pi.set_mode(self.PIN,pigpio.OUTPUT)

        """ adds the required sequences of pulses to the waveForm to represent
        the hexbug code to send. The code parrameter is a string of 1s and 0s,
        that happen to come in sets of 8, prceeded by a 1600 long introductory
        signal. """
        def addByte(self, waveForm, codeBufferList):
                self.addSig(waveForm,1600)
                self.addGap(waveForm,350)
                for c in codeBufferList:
                        if(c==0):
                                self.addSig(waveForm,900)
                        else:
                                self.addSig(waveForm,350)
                        self.addGap(waveForm,350)

        """ adds a pulse to the waveForm representing a pause in transmission
        of so mant micro seconds."""
        def addGap(self, waveForm, micros):
                waveForm.append( pigpio.pulse(1<<self.PIN,0,micros) )

        """ adds a sequence of pulses representing the 38kHz signal recognised
        by the IR reciever. """
        def addSig(self,wf, micros):
                # convert micros to numPulses at 38kHz
                oneCycleTime = 1000.0/self.KHERTZ # 1000000 micros in a second
                onFor = int(oneCycleTime * self.DUTY_CYCLE)
                offFor= int(oneCycleTime * (1.0 - self.DUTY_CYCLE))
                numPulses = int(micros/oneCycleTime)*2
                for i in range(numPulses):
                        if i%2 == 0 :
                                wf.append( pigpio.pulse(1<<self.PIN,0,onFor) )
                        else :
                                wf.append( pigpio.pulse(0,1<<self.PIN,offFor) )

        """
        commands for driving the battle spider. Note that these commands
        return immediately but the bot keeps doing the action (with the
        exception of 'fire'). You can call fwd while it is going backward,
        and it stops going backward, but you can call turn while it is going
        forward and it will turn and go forward.  To stop moving, call stop()
        and to stop turning call stopTurn()
        """
        def fwd(self):
                self.lock.acquire()
                print("forward")
                if not self.transmitting:
                        x = threading.Thread(target=self.transmit, args=("01111011",))
                        x.start()
                else:
                        self.codeBuffer[self.BWD] = 1
                        self.codeBuffer[self.FWD] = 0
                        self.setParity()
                self.lock.release()

        def bwd(self):
                self.lock.acquire()
                print("backward")
                if not self.transmitting:
                        x = threading.Thread(target=self.transmit, args=("11101011",))
                        x.start()
                else:
                        self.codeBuffer[self.FWD] = 1
                        self.codeBuffer[self.BWD] = 0
                        self.setParity()
                self.lock.release()

        def stop(self):
                self.lock.acquire()
                print("stop f/b")
                if not self.transmitting:
                        pass
                else:
                        self.codeBuffer[self.FWD] = 1
                        self.codeBuffer[self.BWD] = 1
                        self.setParity()
                self.lock.release()

        def right(self):
                self.lock.acquire()
                print("right")
                if not self.transmitting:
                        x = threading.Thread(target=self.transmit, args=("11011011",))
                        x.start()
                else:
                        self.codeBuffer[self.LEFT] = 1
                        self.codeBuffer[self.RGHT] = 0
                        self.setParity()
                self.lock.release()

        def left(self):
                self.lock.acquire()
                print("left")
                if not self.transmitting:
                        x = threading.Thread(target=self.transmit, args=("10111011",))
                        x.start()
                else:
                        self.codeBuffer[self.RGHT] = 1
                        self.codeBuffer[self.LEFT] = 0
                        self.setParity()
                self.lock.release()

        def stopTurn(self):
                self.lock.acquire()
                print("stop turn")
                if not self.transmitting:
                        pass
                else:
                        self.codeBuffer[self.RGHT] = 1
                        self.codeBuffer[self.LEFT] = 1
                        self.setParity()
                self.lock.release()

        def fire(self):
                self.lock.acquire()
                print("fire")
                if not self.transmitting:
                        x = threading.Thread(target=self.transmit, args=("11110011",))
                        x.start()
                else:
                        self.codeBuffer[self.FIRE] = 0
                        self.setParity()
                        # transmit resets this after the timeout
                self.lock.release()


        """ a 'private' function run in a thread that continuously sends the
        current command every 300 ms
        """
        def transmit(self, code):
                # initialise the codeBuffer with code
                for c in range(8) :
                        if code[c] == "1" :
                                self.codeBuffer[c] = 1
                        else :
                                self.codeBuffer[c] = 0
                self.transmitting = True
                pulses = []
                # send the wakeup long signal
                self.pi.wave_clear()
                self.addByte(pulses,self.codeBuffer)
                self.addGap(pulses,11500)
                self.addByte(pulses,self.codeBuffer)
                self.addGap(pulses,100500)
                self.pi.wave_add_generic(pulses)
                x = self.pi.wave_create()
                self.pi.wave_send_once(x)
                while self.pi.wave_tx_busy() :
                        sleep(0.040)
                self.pi.wave_delete(x)
                # repeat the command until told to stop
                while not self.allOnes(self.codeBuffer) :
                        pulses = []
                        self.pi.wave_clear()
                        self.addByte(pulses,self.codeBuffer)
                        if self.codeBuffer[self.FIRE] == 0 :
                                self.addByte(pulses,self.codeBuffer)
                                self.codeBuffer[self.FIRE] = 1
                                self.setParity()
                        self.addGap(pulses,300000)
                        self.pi.wave_add_generic(pulses)
                        x = self.pi.wave_create()
                        self.pi.wave_send_once(x)
                        while self.pi.wave_tx_busy() :
                                sleep(0.040)
                        self.pi.wave_delete(x)
                # send the terminator
                pulses = []
                self.pi.wave_clear()
                self.addByte(pulses,self.codeBuffer)
                self.addGap(pulses,300000)
                for i in range(2) :
                        # print(self.codeBuffer)
                        self.pi.wave_add_generic(pulses)
                        x = self.pi.wave_create()
                        self.pi.wave_send_once(x)
                        while self.pi.wave_tx_busy() :
                                sleep(0.040)
                        self.pi.wave_delete(x)
                self.pi.write(self.PIN,0)
                self.transmitting = False

        def setParity(self):
                self.codeBuffer[self.PRTY] = 1
                zeros = 0
                for c in self.codeBuffer :
                        if c == 0 :
                                zeros = zeros +1;
                if zeros == 1 or zeros == 3 :
                        self.codeBuffer[self.PRTY] = 0

        def allOnes(self, bits):
                for c in bits :
                        if c==0 :
                                return False;
                return True

# -- end BattleSpider class --


""" ------------------------------ example usage -----------------------

b1 = BattleSpider(14)
usrIn = '_'
while usrIn != 'q':
        usrIn = input('>')
        if usrIn == 'x':
                b1.fire()
        elif usrIn == 'f':
                b1.fwd()
        elif usrIn == 'b':
                b1.bwd()
        elif usrIn == 'r':
                b1.right()
        elif usrIn == 'l':
                b1.left()
        elif usrIn == 'p':
                b1.fwdLeft()
        elif usrIn == 'z':
                b1.fwdRight()
        elif usrIn == 's':
                b1.stop()
        elif usrIn == 't':
                b1.stopTurn()
"""