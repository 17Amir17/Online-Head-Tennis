import pygame
from pygame.locals import *
from pygame.color import *

import pymunk
import pymunk.pygame_util
from pymunk import Vec2d
import time, threading, socket, datetime, random, sys

#DEBUG
sleep = 0
# Vars
TITLE = "Head Tennis"
FPS = 60
SPS = 60 # Steps per second
GRAVITY = -1000
BT = 10 # Border Thickness
BL = 600 # Border Length


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Game():

    def __init__(self, title="Head Tennis", screen_x=1000, screen_y=600,\
                 fps=60, gravity=-1000, BT=10, addr = ('localHost', 9060)):
        """
        BT - Border Thickness
        BL - Border Length
        """
        self.players = []
        self.title=title
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.fps = fps
        self.gravity = gravity
        self.c = CollisionTypes()
        self.wait = False
        self.wait_time = 1
        self.server = Server(addr=addr)
        self.menu = Menu(addr, self.server)
        self.server.menu = self.menu
        self.setup(BT)
        self.loop()

    def setup(self, BT):
        #Setup pygame, pymunk and world
        pygame.init()
        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode((1, 1))
        self.clock = pygame.time.Clock()
        self.running = True
        self.space = pymunk.Space()
        self.space.gravity = (0.0, self.gravity)
        #self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)



        #Border
        BX = self.screen_x
        BY = self.screen_y
        border = [pymunk.Segment(self.space.static_body, (0.0, BT), (0.0, BY), BT),\
                  pymunk.Segment(self.space.static_body, (BX, BT), (BX, BY), BT),\
                  pymunk.Segment(self.space.static_body, (BX/2, 0.0), (BX/2, BY/4), BT),\
                  pymunk.Segment(self.space.static_body, (0.0, BY), (BX, BY), BT)]

        for b in border:
            b.elasticity = 0.95
            b.friction = 0.9
            b.collision_type = self.c.types['border']

        self.space.add(border)

        #Net
        net = pymunk.Segment(self.space.static_body, (BX/2, BY/4), (BX/2, BY), BT)
        net.collision_type = self.c.types['net']
        self.space.add(net)
        #Floor
        floor = pymunk.Segment(self.space.static_body, (0.0, BT), (BX, BT), BT)
        floor.elasticity = 0.95
        floor.friction = 0.9
        floor.collision_type = self.c.types['floor']

        self.space.add(floor)

        #Scoreboard
        self.scoreboard = Scoreboard()
        self.server.objects.append(self.scoreboard)
        # Ball
        self.ball = Ball()
        self.space.add(self.ball.body, self.ball.shape)
        self.server.objects.append(self.ball) #Add ball to server object list

        #Player2
        self.player1 = Player(-1)
        self.player1.type = 'player1'
        self.space.add(self.player1.body, self.player1.shape)
        self.server.objects.append(self.player1)
        #Racket1
        r = self.player1.racket
        r.type = 'racket1'
        self.space.add(r.body, r.shape)
        self.space.add(r.joint)
        self.server.objects.append(r)

        #Player2
        self.player2 = Player(1, position = (900, 60))
        self.player2.type = 'player2'
        self.space.add(self.player2.body, self.player2.shape)
        self.server.objects.append(self.player2)
        #Racket2
        r = self.player2.racket
        r.type = 'racket2'
        self.space.add(r.body, r.shape)
        self.space.add(r.joint)
        self.server.objects.append(r)

        """
        After all objects added call get get_player_obj in server
        """
        self.server.get_player_obj()

        self.players.append(self.player1)
        self.players.append(self.player2)

        #Setup Events
        player_racket_collision = self.space.add_collision_handler(self.c.types['racket'], self.c.types['player'])
        player_racket_collision.begin = self.ignore
        player_border_col = self.space.add_collision_handler(self.c.types['player'], self.c.types['border'])
        player_border_col.begin = self.player_wall_col
        player_border_release = self.space.add_collision_handler(self.c.types['player'], self.c.types['border'])
        player_border_release.separate = self.player_wall_release
        racket_border_col = self.space.add_collision_handler(self.c.types['racket'], self.c.types['border'])
        racket_border_col.begin = self.player_wall_col
        racket_border_release = self.space.add_collision_handler(self.c.types['racket'], self.c.types['border'])
        racket_border_release.separate = self.player_wall_release
        player_ground_rel = self.space.add_collision_handler(self.c.types['player'], self.c.types['floor'])
        player_ground_rel.separate = self.player_jump
        player_ground = self.space.add_collision_handler(self.c.types['player'], self.c.types['floor'])
        player_ground.begin = self.player_land
        ball_floor = self.space.add_collision_handler(self.c.types['ball'], self.c.types['floor'])
        ball_floor.begin = self.ball_floor_col
        ball_net = self.space.add_collision_handler(self.c.types['ball'], self.c.types['net'])
        ball_net.begin = self.ball_net_col

    def loop(self):
        while self.running:
            #Keep racket on player
            for p in self.players:
                p.update()
            # PYGAME EVENTS (KEY DOWN, QUIT, etc..)
            """
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    key = event.key
                    self.handle_controls(key, True)

                elif event.type == KEYUP:
                    key = event.key
                    self.handle_controls(key, False)
            """

            # Handle EVENTS
            if self.wait:
                time.sleep(self.wait_time)
                self.wait = False
            while len(self.server.playerList) != 2: # Dont play until 2 players
                time.sleep(self.wait_time)

            # Handle Controls
            for p in self.players:
                p.control()
            ### Clear screen
            #self.screen.fill(THECOLORS["white"])

            #Render
            #self.space.debug_draw(self.draw_options)

            #Step physics
            dt = 1.0/self.fps
            for x in range(1):
                self.space.step(dt)

            #More pygame stuff
            #pygame.display.flip()
            self.clock.tick(FPS)

    def handle_controls(self, key, down):
        if key == K_w:
            self.player1.jump = down
        elif key == K_a:
            self.player1.left = down
        elif key == K_d:
            self.player1.right = down
        elif key == K_SPACE:
            self.player1.swing = down
        elif key == K_UP:
            self.player2.jump = down
        elif key == K_LEFT:
            self.player2.left = down
        elif key == K_RIGHT:
            self.player2.right = down
        elif key == K_p:
            self.player2.swing = down
        elif key == K_q:
            self.running = False
        elif key == K_r:
            self.ball.body.position = (470, 300)

    def ignore(self, arbiter, space, data):
        return False

    def player_wall_col(self, arbiter, space, data):
        for p in self.players:
            p.player_wall_col(arbiter, space, data)
        return True

    def player_wall_release(self, arbiter, space, data):
        for p in self.players:
            p.player_wall_release(arbiter, space, data)
        return True

    def ball_floor_col(self, arbiter, space, data):
        self.ball.bounce += 1
        if self.ball.bounce >= 2:
            #Point!
            x = self.ball.body.position.x
            if x < self.screen_x/2:
                self.handle_score(1)
            else:
                self.handle_score(0)
            self.ball.reset()
            self.wait = True

        return True

    def ball_net_col(self, arbiter, space, data):
        self.ball.bounce = 0
        return False

    def player_jump(self, arbiter, space, data):
        for p in self.players:
            if arbiter.shapes[0] == p.shape:
                p.grounded = False

    def player_land(self, arbiter, space, data):
        for p in self.players:
            if arbiter.shapes[0] == p.shape:
                p.grounded = True
        return True

    def handle_score(self, index):
        s = self.scoreboard.score[index]
        if s == '40' and (self.scoreboard.score[0] == 'adv' or self.scoreboard.score[1] == 'adv'):
            self.scoreboard.score[0] = '40'
            self.scoreboard.score[1] = '40'
        elif s == '40' and self.scoreboard.score[0] == self.scoreboard.score[1]:
            s = 'adv'
        elif s == '0':
            s = '15'
        elif s == '15':
            s = '30'
        elif s == '30':
            s = '40'
        elif s == '40' or s == 'adv':
            s = '0'
            r = self.scoreboard.rounds[index]
            r = int(r) + 1
            self.scoreboard.rounds[index] = str(r)
            self.scoreboard.score = ['0', '0']
        self.scoreboard.score[index] = s

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Ball():

    def __init__(self, mass=10, size=15, position=(400, 300),\
                 elasticity = 0.95, friction = 0.9):
        self.c = CollisionTypes()
        self.type = 'ball'
        self.mass = mass
        self.size = size
        self.position = position
        self.elasticity = elasticity
        self.friction = friction
        self.body, self.shape = self.createBody(mass, size, position,\
                                                elasticity, friction)
        self.bounce = 0

    def createBody(self, mass, size, position,\
                   elasticity, friction):
        inertia = pymunk.moment_for_circle(mass, 0, size, (0,0))
        ball_body = pymunk.Body(mass, inertia)
        ball_body.position = position
        ball_shape = pymunk.Circle(ball_body, size, (0, 0))
        ball_shape.elasticity = elasticity
        ball_shape.friction = friction
        ball_shape.collision_type = self.c.types['ball']
        return ball_body, ball_shape

    def reset(self):
        self.position = 500, 300
        self.body.position = self.position
        r = random.sample([-1, 1], 1)[0]
        self.body._set_velocity((r*100, 200))
        self.bounce = 0

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Player():

    def __init__(self, side, position = (100, 60), mass = 200, size = 30,\
                 speed = 100, jump_multiplier = 3):
        """
        Side - 1 for right -1 for left
        """
        self.c = CollisionTypes()
        self.type = 'player'
        self.name = ' '
        self.side = side
        self.position = position
        self.mass = mass
        self.size = size
        self.speed = speed
        self.jump_multiplier = jump_multiplier
        self.grounded = True
        self.body, self.shape = self.createBody(position, mass, size)
        self.racket = Racket(side, self)
        self.left = self.right = self.jump = self.swing = False
        self.freezeX = [False, False]

    def createBody(self, position, mass, size):
        player_body = pymunk.Body(mass, pymunk.inf)
        player_body.position = position
        player_shape = pymunk.Circle(player_body, size, (0, 0))
        player_shape.collision_type = self.c.types['player']
        return player_body, player_shape

    def update(self):
        self.racket.body.position = self.body.position

    def control(self):
        v = self.body.velocity
        if self.left and self.right:
            v.x = 0
        elif self.left and not self.freezeX[0]:
            if v.x > -self.speed:
                self.body.apply_impulse_at_local_point((-self.speed*self.mass, 0), self.body.position)
        elif self.right and not self.freezeX[1]:
            if v.x < self.speed:
                self.body.apply_impulse_at_local_point((self.speed*self.mass, 0), self.body.position)
        else:
            v.x = 0
            self.body._set_velocity(v)
        if self.jump and self.grounded:
            if v.y < self.speed:
                self.body.apply_impulse_at_local_point((0, self.speed*self.mass*self.jump_multiplier), self.body.position)
            self.jump = False
        racket_body = self.racket
        angle = racket_body.body.angle*self.side
        if self.swing:
            if angle < racket_body.max_angle:
                racket_body.body._set_angular_velocity(self.side*racket_body.vel)
            else:
                racket_body.body._set_angular_velocity(0)
        else:
            if angle == racket_body.rest:
                racket_body.body._set_angular_velocity(0)
            elif angle < racket_body.rest:
                racket_body.body.angle = racket_body.rest
                racket_body.body._set_angular_velocity(0)
            else:
                racket_body.body._set_angular_velocity(-self.side*racket_body.vel)

    def player_wall_col(self, arbiter, space, data):
        if arbiter.shapes[0]._get_body().position != self.body.position and\
           arbiter.shapes[0]._get_body().position != self.racket.body.position:
            return False
        contact_point = arbiter._get_contact_point_set().normal
        if contact_point[0] == -1.0:
            self.freezeX[0] = True
            self.freezeX[1] = False
        if contact_point[0] == 1.0:
            self.freezeX[1] = True
            self.freezeX[0] = False

    def player_wall_release(self, arbiter, space, data):
        if arbiter.shapes[0]._get_body().position != self.body.position and\
           arbiter.shapes[0]._get_body().position != self.racket.body.position:
            return False
        contact_point = arbiter._get_contact_point_set().normal
        if contact_point[0] != 0:
            self.freezeX[0] = False
            self.freezeX[1] = False


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Racket():

    def __init__(self, side, player, elasticity = 0.2,\
                 sizeX = 70, sizeY = 5, vel = 10, rest = 0, max_angle = 2):
        self.c = CollisionTypes()
        self.type = 'racket'
        self.side = side
        self.player = player
        self.elasticity = elasticity
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.size = (sizeX, sizeY)
        self.vel = vel
        self.rest = rest
        self.max_angle = max_angle
        self.body, self.shape = self.createBody(side, player, elasticity, sizeX, sizeY)
        self.joint = pymunk.PinJoint(self.body, self.player.body, (0,0), (0, 0))

    def createBody(self, side, player, elasticity, sizeX, sizeY):
        points = ((0, 0), (0, sizeY), (side * sizeX, sizeY), (side * sizeX, 0))
        racket_body = pymunk.Body(10, pymunk.inf)
        racket_body.position = player.body.position
        racket = pymunk.Poly(racket_body, points)
        racket.collision_type = self.c.types['racket']
        racket.elasticity = elasticity
        return racket_body, racket

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class CollisionTypes():
    #Collision Types
    types = {
    "player":1,
    "ball": 2,
    "border": 3,
    "racket": 4,
    "floor": 5,
    "net": 6
    }

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class Scoreboard():

    def __init__(self):
        self.type = 'score'
        self.score = ['0', '0']
        self.rounds = ['0', '0']

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class Server():

    def __init__(self, objects=[], static=[], addr=('localHost', 9060), pps=60):
        """
        Sends frame data to streamers
        Updates player controls from controlers
        """
        print 'Running server...'
        self.menu = None # Menu
        self.addr = addr
        self.objects = objects # All frame objects to get data from
        self.pps = pps # Packets per second (tickrate)
        self.playerObj = {}
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(addr)
        self.clientList = []
        self.streamerList = []
        self.playerList = []
        self.sec_per_ping = .2 # Second per each ping
        self.max_live = 1.0 # Maximum wait time with no ping
        self.ping_wait = .1 # Time to wait between each set of pings
        self.playerHelper = PlayerHelper() # For getting free player slots and setting player names
        t = threading.Thread(target=self.listen)
        t.setDaemon(True)
        t.start()
        t = threading.Thread(target=self.pinger)
        t.setDaemon(True)
        t.start()

    def listen(self):
        """
        Messages from clients and handle them
        """
        print 'Listening...'
        while True:
            try:
                rec = self.s.recvfrom(1024)
                self.handle_data(rec)
            except Exception as e:
                #print str(e)
                pass

    def handle_data(self, rec):
        """
        Message first char:
        0 - Request for stream
        1 - Player connection
        2 - Player Control Update
        p - ping
        """
        data, addr = rec
        # print str(addr) + ": " + data
        if data[0] == '0': # Request for stream
            print 'Streamer connected'
            c = Client(addr, 'streamer')
            self.clientList.append(c)
            self.streamerList.append(c)
            self.s.sendto('hello', addr)
            if len(self.streamerList) == 1:
                t = threading.Thread(target=self.stream)
                t.setDaemon(True)
                t.start()
            self.updateMenu()
        elif data[0] == '1': # Player Connection
            print 'Controller Connected'
            name = data[1:]
            c = Client(addr, 'controller')
            self.clientList.append(c)
            self.playerList.append(c)
            self.playerHelper.playerConnected(addr, name) # Tell playerHelper that a player connected
            self.s.sendto('hello', addr)
            self.updateMenu()

        elif data[0] == '2': # Player control update
            self.handle_control_update(data)

        elif data[0] == 'p': # Ping
            c = self.getClient(addr)
            if c != False:
                c.pinged()

    def stream(self):
        """
        Send frame data to all streams
        """
        while True:
            try:
                count = 0
                data = self.get_frame_data()
                for s in self.streamerList:
                    count += 1
                    self.s.sendto(data, s.addr)
                if count < 1: # If all streamers disconnected stop streaming
                    print 'Nostreamer'
                    break
                time.sleep(1.0/self.pps)

            except Exception as e:
                print str(e)

    def get_frame_data(self):
        """
        Get data of current game frame (Attributes of all game objects)
        objData = type*size*pos*rotation
        data packet = objData#objData#....#END
        """
        data = ''
        for obj in self.objects:
            #body = obj.body
            #data += str(body.position.x) + '*' + str(body.position.y)
            t = obj.type
            if t == 'ball':
                size = str(obj.size)
                pos = str(obj.body.position.x) + ',' + str(obj.body.position.y)
                rotation = str(obj.body.angle)
                data += 'ball*' + size + '*' + pos + '*' + rotation + '#'
            elif t.startswith('player'):
                size = str(obj.size)
                pos = str(obj.body.position.x) + ',' + str(obj.body.position.y)
                data += t + '*' + size + '*' + pos + '*' + obj.name + '#'
            elif t.startswith('racket'):
                size = str(obj.size[0]) + ',' + str(obj.size[1])
                pos = str(obj.body.position.x) + ',' + str(obj.body.position.y)
                rotation = str(obj.body.angle)
                data += t + '*' + size + '*' + pos + '*' + rotation + '#'
            elif t == 'score':
                data += t + '*' + obj.score[0] + ',' + obj.score[1] + '*' + obj.rounds[0]\
                        + ',' + obj.rounds[1] + '#'
        data += 'END'
        return data

    def handle_control_update(self, data):
        """
        Updates controls based on data sent by Controller
        """
        try:
            split = data.split('*')
            playerType = split[1]
            left = int(split[2])
            right = int(split[3])
            jump = int(split[4])
            swing = int(split[5])

            player = self.playerObj[playerType]
            player.left = left
            player.right = right
            player.jump = jump
            player.swing = swing
        except Exception as e:
            print "ERROR: " + str(e)

    def kick(self, addr):
        """
        Remove client from all lists
        """
        for c in self.clientList:
            if c.compareClient(addr):
                self.clientList.remove(c)
                if c.type == 'streamer':
                    self.streamerList.remove(c)
                else:
                    self.playerList.remove(c)
                    self.playerHelper.playerDisconnected(addr) # Tell playerHelper that a player disconnected
                print str(addr) + ' disconnected'
                self.updateMenu()

    def pinger(self):
        """
        Check which clients are still connected
        """
        print "Pinging"
        while True:
            for c in self.clientList:
                deltaT = c.deltaT()
                if deltaT > self.max_live:
                    self.kick(c.addr)
                elif deltaT > self.sec_per_ping:
                    self.s.sendto("ping", c.addr)
            time.sleep(self.ping_wait)

    def getClient(self, addr):
        for c in self.clientList:
            if c.compareClient(addr):
                return c
        return False

    def get_player_obj(self):
        dic = {}
        for obj in self.objects:
            if obj.type.startswith('player'):
                dic[obj.type] = obj
        self.playerObj = dic
        self.playerHelper.playerObj[0] = dic['player1']
        self.playerHelper.playerObj[1] = dic['player2']

    def updateMenu(self):
        self.menu.writePlayerList()

class Client():

    def __init__(self, addr, clientType):
        self.addr = addr
        self.lastPing = datetime.datetime.now()
        self.type = clientType

    def deltaT(self):
        return (datetime.datetime.now() - self.lastPing).total_seconds()

    def compareClient(self, addr):
        return str(addr) == str(self.addr)

    def pinged(self):
        self.lastPing = datetime.datetime.now()


class PlayerHelper():

    def __init__(self):
        self.players = [[0, None], [0, None]]
        self.playerObj = [None, None]

    def playerConnected(self, addr, name):
        b = 0
        if self.players[0][0] == 0: # Player1 Connecting
            self.players[0][0] = 1
            self.players[0][1] = addr
        elif self.players[1][0] == 0: # Player2 Connecting
            self.players[1][0] = 1
            self.players[1][1] = addr
            b = 1
        try:
            self.playerObj[b].name = name
        except:
            print 'Fuck'

    def playerDisconnected(self, addr):
        b = 0
        if str(self.players[0][1]) == str(addr): # player1 leave
            self.players[0][0] = 0
            self.players[0][1] = None
        elif str(self.players[1][1]) == str(addr): # player2 leave
            self.players[1][0] = 0
            self.players[1][1] = None
            b = 1
        try:
            self.playerObj[b].name = ' '
        except:
            print 'Fuck'

    def getSlots(self):
        slots = str(self.players[0][0]) + str(self.players[1][0])
        return slots

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
*****************************************************************************
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class Menu():

    def __init__(self, addr, game):
        print 'Menu Init'
        self.addr = addr
        self.game = game
        self.server = socket.socket()
        self.connect(addr)
        t = threading.Thread(target = self.read)
        t.daemon = True
        t.start()

    def connect(self, addr):
        print 'Connecting to Menu Server'
        self.server.connect((addr[0], 9059))
        self.server.send('1' + str(addr[1]))

    def read(self):
        while True:
            try:
                msg = self.server.recv(128)
                """
                0 - Get Player List
                1 - Get Free Player Slots
                """
                print 'msg'
                if msg[0] == '0':
                    print 'GAME: Request to get player list'
                    self.server.send(self.getPlayerList())
                elif msg[0] == '1':
                    print 'GAME: Request to get free player slots'
                    self.server.send(self.getFreePlayerSlots())
            except Exception as e:
                break
                print 'In read ' + str(e)

    def writePlayerList(self):
        self.server.send(self.getPlayerList())

    def getPlayerList(self):
        players = len(self.game.playerList)
        spectators = len(self.game.streamerList) - players
        l = '0' + str(players) + ',' + str(spectators)
        return l

    def getFreePlayerSlots(self):
        #TODO This function
        print 'GAME: Getting Free Player Slots!'
        slots = '1' + self.game.playerHelper.getSlots()
        print 'GAME: ' + slots
        return slots


def main():
    print 'Running!'
    addr = (sys.argv[1], int(sys.argv[2]))
    g = Game(addr=addr)

if __name__ == '__main__':
    main()
