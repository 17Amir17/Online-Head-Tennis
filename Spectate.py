import socket, threading, datetime, time
import pygame
from pygame.locals import *
from pygame.color import *
from math import *

addr = ('localHost', 9060)

class Spectator():

    def __init__(self, screen, _type=0, addr=('localHost', 9060), size = (1000, 600), title='Spectator', fps=60):
        pygame.init()
        self.type = _type # 0 for streamer other for streamer + controller
        if self.type != 0:
            title = 'Head Tennis'
        self.addr = addr
        self.size = size
        self.fps = fps
        self.screen = screen#pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption(title)

        #Font
        pygame.font.init()
        self.myfont = pygame.font.SysFont('Comic Sans MS', 30)

        #Back
        self.background = Background('data/t.png', self.size)

        ball = Ball()
        player1 = Player(_type='player1', side=-1)
        player2 = Player(_type='player2', side=1)
        racket1 = Racket(player1, _type='racket1', side=-1)
        racket2 = Racket(player2, _type='racket2', side=1)
        self.scoreboard = Scoreboard()
        self.objects = [ball, player1, player2, racket1, racket2, self.scoreboard]
        self.allsprites = pygame.sprite.RenderPlain((player1, player2, ball))
        self.rackets = pygame.sprite.RenderPlain((racket1, racket2))

        self.listener = Listener(addr, size, self.objects)
        self.listener.start()

        if self.type != 0:
            self.controller = Controller(self.type, addr=self.addr)
            self.controller.start()

        self.running = True
        self.loop()

    def loop(self):
        BT = 20
        floor = (0, self.size[1]- BT, self.size[0], BT)
        roof = (0, 0, self.size[0], BT)
        wallL = (0, 0, BT, self.size[1])
        wallR = (self.size[0]- BT, 0, BT, self.size[1])
        net = (self.size[0]/2-BT/2, self.size[1] - self.size[1]/4, BT, self.size[1]/4)
        borders = [floor, roof, wallL, wallR, net]
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key, True)
                elif event.type == pygame.KEYUP:
                    self.handle_key(event.key, False)

            #Handle Events
            #pygame.event.pump()
            #Clear screen

            self.screen.fill(THECOLORS['white'])
            self.screen.blit(self.background.image, self.background.rect)

            #Render
            for b in borders:
                pygame.draw.rect(self.screen, THECOLORS['black'], b)

            self.allsprites.draw(self.screen)
            self.rackets.draw(self.screen)
            self.render_score()

            #Finishup
            pygame.display.update()
            self.clock.tick(self.fps)

    def handle_key(self, key, down):
        if self.type == '0':
            return
        elif key == K_ESCAPE:
            self.listener.run = False
            self.running = False
            if self.type != 0:
                self.controller.run = False
        if self.type == 0:
            return
        if key == K_w:
            self.controller.jump = int(down)
        elif key == K_a:
            self.controller.left = int(down)
        elif key == K_d:
            self.controller.right = int(down)
        elif key == K_SPACE:
            self.controller.swing = int(down)

    def render_score(self):
        rounds = self.scoreboard.rounds
        score = self.scoreboard.score
        r = rounds[0] + ':' + rounds[1]
        s = score[0] + ':' + score[1]
        roundSurface = self.myfont.render(r, False, (0, 0, 0))
        scoreSurface = self.myfont.render(s, False, (0, 0, 0))
        rX, rY = roundSurface.get_size()
        sX, sY = scoreSurface.get_size()
        X, Y = self.size
        self.screen.blit(roundSurface,(X/2 - rX, rY))
        self.screen.blit(scoreSurface,(X/2 - sX, rY + sY))

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class Background(pygame.sprite.Sprite):
    def __init__(self, image_file, scale):
        pygame.sprite.Sprite.__init__(self)  #call Sprite initializer
        self.image = pygame.image.load(image_file).convert()
        self.image = pygame.transform.scale(self.image, scale)
        self.rect = self.image.get_rect()

class Circle():

    def __init__(self, screen, size=15, pos = (-100, -100), _type='ball'):
        self.screen = screen
        self.size = size
        self.pos = pos
        self.type = _type
        self.angle = 0

    def draw(self):
        pygame.draw.circle(self.screen, THECOLORS['blue'], self.pos, self.size)

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Rect():
    def __init__(self, screen, size=(15, 15), pos = (-100, -100), _type='racket'):
        self.screen = screen
        self.size = size
        self.pos = pos
        self.type = _type
        self.angle = 0

    def draw(self):
        #print position
        x, y = self.size
        X, Y = self.pos
        if self.type == 'racket1':
            pygame.draw.rect(self.screen, THECOLORS['blue'], (X-x, Y, x, y))
        else:
            pygame.draw.rect(self.screen, THECOLORS['blue'], (X, Y, x, y))

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Player(pygame.sprite.Sprite):

    def __init__(self, _type ,side):
        pygame.sprite.Sprite.__init__(self)
        if _type =='player1':
            img = pygame.image.load('data/player.png')
        else:
            img = pygame.image.load('data/player2.png')
        self.side = side
        self.type = _type
        self.size = 50
        self.scale = 50, 50
        self.image = pygame.transform.scale(img, self.scale)
        if side == 1:
            self.image = pygame.transform.flip(self.image, True, False)
        self.image_clean = self.image.copy()
        self.image_clean.convert_alpha()
        self.rect = self.image.get_rect()
        self.pos = (0, 0)

    def set_pos(self, pos):
        self.pos = pos
        self.rect = self.image.get_rect(center=pos)
        #self.rect.x = pos[0]# - self.scale[0] * 2
        #self.rect.y = pos[1]# - self.scale[0] * 2

    def set_size(self, size):
        self.size = size
        if size != self.scale[0]:
            x, y = self.image.get_size()
            self.scale = size, size
            x = size*2
            self.image = pygame.transform.scale(self.image, (x, x))
            self.image_clean = pygame.transform.scale(self.image_clean, (x, x))

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Ball(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('data/ball.png')
        self.type = 'ball'
        self.scale = (50, 50)
        self.image = pygame.transform.scale(img, self.scale)
        self.image_clean = self.image.copy()
        self.image_clean.convert_alpha()
        self.rect = self.image.get_rect()
        self.pos = (0, 0)

    def rot(self, angle):
        """rotate an image while keeping its center"""
        cent = self.pos
        self.image = pygame.transform.rotate(self.image_clean, angle)
        self.rect = self.image.get_rect(center=cent)

    def set_pos(self, pos):
        self.pos = pos
        """
        Position is set by rotation cuz it works
        """
        #self.rect.x = pos[0]# - self.scale[0] * 2
        #self.rect.y = pos[1]# - self.scale[0] * 2

    def set_size(self, size):
        if size != self.scale[0]:
            x, y = self.image.get_size()
            self.scale = size, size
            x = size*2
            self.image = pygame.transform.scale(self.image, (x, x))
            self.image_clean = pygame.transform.scale(self.image_clean, (x, x))

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Racket(pygame.sprite.Sprite):

    def __init__(self, player, _type, side):
        self.type = _type
        self.player = player
        self.side = side
        self.rest = 45
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('data/racket.png')
        self.scale = (50, 50)
        self.image = pygame.transform.scale(img, self.scale)
        self.image = pygame.transform.rotate(self.image, self.rest)
        if side == 1:
            self.image = pygame.transform.flip(self.image, True, False)
        self.image_clean = self.image.copy()
        self.rect = self.image.get_rect()

    def rot_center(self, angle):
        """rotate an image while keeping its center"""
        self.image = pygame.transform.rotate(self.image_clean, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def rot(self, angle):
        self.image = pygame.transform.rotate(self.image_clean, angle)
        x, y = self.player.pos

        if self.side == 1:
            angle = -angle
        else:
            angle = 180 - angle
        self.rect = self.image.get_rect(center=self.cal_center((x, y),\
                                        self.player.size, angle))

    def set_pos(self, pos):
        x, y = self.image.get_size()
        if self.side == 1:
            x = 0
        self.rect.x = pos[0] - x
        self.rect.y = pos[1] -y/2

    def set_size(self, size):
        if size != self.scale:
            x, y = self.image.get_size()
            self.scale = size
            x = x + 5
            y = size[1] + y
            self.image = pygame.transform.scale(self.image, (x, y))
            self.image_clean = pygame.transform.scale(self.image_clean, (x, y))


    def cal_center(self, cent, r, angle):
        angle = radians(angle)
        Cx, Cy = cent
        X = Cx + (r * cos(angle)) + (self.side*5)
        Y = Cy + (r * sin(angle)) + 5
        return X, Y


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Scoreboard():

    def __init__(self):
        self.type = 'score'
        self.score = ('0', '0')
        self.rounds = ('0', '0')

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class Listener():

    def __init__(self, addr, size, objects):
        self.addr = addr
        self.size = size
        self.objects = objects
        self.objDict = self.getObjectDictionary(objects)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(1)
        self.connected = False
        self.run = True

    def start(self):
        t = threading.Thread(target=self.read)
        t.setDaemon(True)
        t.start()

    def read(self):
        print 'Reading!'
        self.connect()
        while self.run:
            try:
                data, addr = self.s.recvfrom(1024)
                #print data
                if data == 'ping':
                    self.s.sendto('p', addr) # Ping
                elif data == 'hello':
                    print 'Connected!'
                    self.connected = True
                else:
                    self.handle_data(data)
            except socket.timeout:
                print 'Timeout'
                self.connected = False
                self.connect()

    def connect(self):
        while self.connected == False and self.run:
            try:
                print self.read
                print 'Connecting...'
                self.s.sendto('0', self.addr)
                time.sleep(.1)
                data, addr = self.s.recvfrom(1024)
                if data == 'hello':
                    self.connected = True
            except:
                print 'Unable to connect'

    def handle_data(self, data):
        #print data
        objectsData = data.split('#')
        for objD in objectsData:
            """
            d0-type d1-size d2-pos d3-rotation
            """
            d = self.disect(objD)
            #print d
            if d != False:
                obj = self.objDict[d[0]]
                if d[0] == 'ball':
                    obj.set_size(d[1])
                    obj.set_pos(d[2])
                    obj.rot(d[3]*57.3)
                elif d[0].startswith('player'):
                    #obj.size = d[1]
                    #obj.pos = d[2]
                    obj.set_size(d[1])
                    obj.set_pos(d[2])
                elif d[0].startswith('racket'):
                    obj.set_size(d[1])
                    obj.set_pos(d[2])
                    obj.rot(d[3]*57.3)
                elif d[0] == 'score':
                    obj.score = d[1]
                    obj.rounds = d[2]


    def disect(self, data):
        split = data.split('*')
        t = split[0]
        sizeY = self.size[1]
        if t == 'ball':
            size = int(float(split[1]))
            x, y = split[2].split(',')
            pos = (int(float(x)), sizeY - int(float(y)))
            rotation = (float(split[3]))
            return (t, size, pos, rotation)
        elif t.startswith('player'):
            size = int(float(split[1]))
            x, y = split[2].split(',')
            pos = (int(float(x)), sizeY - int(float(y)))
            return (t, size, pos)
        elif t.startswith('racket'):
            x, y = split[1].split(',')
            size = (int(float(x)), int(float(y)))
            x, y = split[2].split(',')
            pos = (int(float(x)), sizeY - int(float(y)))
            rotation = (float(split[3]))
            return (t, size, pos, rotation)
        elif t == 'score':
            score = split[1].split(',')
            rounds = split[2].split(',')
            return (t, score, rounds)
        return False

    def getObjectDictionary(self, objects):
        dic = {}
        for obj in objects:
            dic[obj.type] = obj
        return dic

    def deltaT(self):
        return (datetime.datetime.now() - self.lastPing).total_seconds()

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class Controller():

    def __init__(self, side, addr=('localHost', 9060), pps=60):
        self.side = side
        self.addr = addr
        self.pps = pps # Packets per second
        self.left = self.right = self.jump = self.swing = 0
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(1)
        self.connected = False
        self.run = True

    def start(self):
        t = threading.Thread(target=self.read)
        t.setDaemon(True)
        t.start()
        t = threading.Thread(target=self.write)
        t.setDaemon(True)
        t.start()

    def read(self):
        print 'Reading!'
        self.connect()
        while self.run:
            try:
                data, addr = self.s.recvfrom(1024)
                #print data
                if data == 'ping':
                    self.s.sendto('p', addr) # Ping
                elif data == 'hello':
                    print 'Connected!'
                    self.connected = True
                else:
                    print data
            except socket.timeout:
                print 'Timeout'
                self.connected = False
                self.connect()

    def write(self):
        print 'Writing!'
        while self.run:
            while self.connected and self.run:
                """
                Packet data - 2*playerside*left*right*jump*swing
                """
                data = ["2", str(self.side), str(self.left), str(self.right),\
                        str(self.jump), str(self.swing)]
                data = '*'.join(data)
                self.s.sendto(data, self.addr)
                self.jump = '0'
                time.sleep(1.0/self.pps)
            time.sleep(1)

    def connect(self):
        while self.connected == False and self.run:
            try:
                print 'Connecting...'
                self.s.sendto('1', self.addr)
                time.sleep(.1)
                data, addr = self.s.recvfrom(1024)
                if data == 'hello':
                    self.connected = True
            except:
                print 'Unable to connect'

    def deltaT(self):
        return (datetime.datetime.now() - self.lastPing).total_seconds()

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def main():
    t = raw_input('Type?:')
    s = Spectator(_type = t, addr=addr)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
