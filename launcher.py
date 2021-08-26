import pygame, GUI, socket, threading, time, gc, Spectate
from pygame.locals import *

userControls = {}
addr = ('localHost', 9059)
button = 'data/button.jpg'

class Launcher():

    def __init__(self, addr):
        pygame.init()
        size = [1000, 600]
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.fps = 30
        pygame.display.set_caption('My Game')

        self.client = Client(addr)
        self.gui = GUI.GUI(self.screen)
        self.menu = Menu(self.client)
        self.roomPicker = RoomPicker(self.client, self.screen)
        self.roomCreator = RoomCreator(self.client)

        self.gui.userControls.append(self.menu.userControl)
        self.gui.userControls.append(self.roomPicker.userControl)
        self.gui.userControls.append(self.roomCreator.userControl)

        userControls['menu'] = self.menu
        userControls['roomPicker'] = self.roomPicker
        userControls['roomCreator'] = self.roomCreator

        self.loop()

    def loop(self):
        self.menu.show()
        done = False
        while True:

            click = key = shift = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                elif event.type == pygame.MOUSEBUTTONUP:
                    click = True
                elif event.type == pygame.KEYDOWN:
                    key = event.key

            pos = pygame.mouse.get_pos()
            keys = pygame.key.get_pressed()
            shift = keys[303] or keys[304]
            self.gui.update(pos, click, key, shift)

            # Update.

            # Draw.
            self.screen.fill([20, 255, 20])
            self.gui.draw()

            pygame.display.flip()
            self.clock.tick(self.fps)


        pygame.quit()

class Client():

    def __init__(self, addr):
        self.addr = addr
        self.s = socket.socket()
        self.name = ''

    def connect(self):
        try:
            print ('Connecting')
            self.s.connect(self.addr)
            self.s.send('0') # User client
            return 'Connected'
        except Exception as e:
            return e

    def login(self, name):
        try:
            print ('Logging in')
            self.s.send('0' + str(name))
            m = self.s.recv(1024)
            return m
        except Exception as e:
            return str(e)

    def requestRoomList(self):
        try:
            print ('Requesting room list')
            self.s.send('1')
            m = self.s.recv(1024)
            return m
        except Exception as e:
            return str(e)

    def requestCreateRoom(self, name):
        try:
            print ('Requesting to create room')
            self.s.send('2' + name)
            m = self.s.recv(1024)
            return m
        except Exception as e:
            return str(e)

    def requestPlayerCount(self, port):
        try:
            print ('Requesting to player count')
            self.s.send('3' + str(port))
            m = self.s.recv(128)
            return m
        except Exception as e:
            return str(e)

    def requestFreeSlots(self, port):
        try:
            print ('Requesting free slots')
            self.s.send('4' + str(port))
            m = self.s.recv(128)
            return m
        except Exception as e:
            return str(e)

class Menu():

    def __init__(self, client):
        self.client = client
        self.userControl = GUI.UserControl(hidden=True)
        self.t = GUI.Textbox(button, (300, 200), (400, 60))
        self.b1 = GUI.Button(button, (400, 320), (200, 60), text = 'Login', onClick=self.login)
        self.b2 = GUI.Button(button, (400, 420), (200, 60), text = 'Connect', onClick=self.connect, hidden=True)
        self.s = GUI.Text('Enter Name:', (300, 160), 20, (0, 0, 0))
        self.s1 = GUI.Text('', (300, 270), 20, (255, 0, 0))
        self.s2 = GUI.Text('', (0, 550), 20, (255, 0, 0))

        self.userControl.textboxes.append(self.t)
        self.userControl.buttons.append(self.b1)
        self.userControl.buttons.append(self.b2)
        self.userControl.labels.append(self.s)
        self.userControl.labels.append(self.s1)
        self.userControl.labels.append(self.s2)

        self.connect()

    def show(self):
        self.userControl.hidden = False

    def hide(self):
        self.userControl.hidden = True

    def connect(self):
        t = threading.Thread(target=self.doConnect)
        t.setDaemon(True)
        t.start()

    def doConnect(self):
        out = self.client.connect()
        print (out)
        if out == 'Connected':
            self.s2.color = (0, 0, 255)
            self.b2.hidden = True
        else:
            self.s2.color = (255, 0, 0)
            self.b2.hidden = False

        self.s2.setText(str(out))

    def login(self):
        t = threading.Thread(target=self.doLogin)
        t.setDaemon(True)
        t.start()

    def doLogin(self):
        name = self.t.getText()
        self.s1.setText('Loging in...')
        out = self.client.login(name)
        if out == 'OK':
            self.client.name = name
            self.s1.setText('Logged In')
            self.s1.color = (0, 0, 255)
            self.hide()
            userControls['roomPicker'].show()
        elif out == '-1':
            self.s1.setText('Name %s Already Taken' % name)
            self.s1.color = (255, 0, 0)
            self.t.setText('')
        else:
            self.s1.setText(out)
            self.s1.color = (255, 0, 0)

class RoomPicker():

    def __init__(self, client, screen):
        self.client = client
        self.screen = screen
        self.userControl = GUI.UserControl(hidden=True)
        self.rooms = []
        self.page = 1

        self.title = GUI.Text('Room Picker', (400, 50), 30, (0, 0, 0))
        self.l1 = GUI.Text('Name', (20, 100), 20, (0, 0, 0))
        self.l2 = GUI.Text('Players', (400, 100), 20, (0, 0, 0))
        self.l3 = GUI.Text('Spectators', (600, 100), 20, (0, 0, 0))
        self.lp = GUI.Text('1', (610, 510), 30, (0, 0, 0))
        self.refreshB = GUI.Button(button, (90, 500), (200, 60), text = 'Refresh', onClick=self.refresh)
        self.newRoom = GUI.Button(button, (300, 500), (200, 60), text = 'Create Room', onClick=self.createNewRoom)
        self.leftB = GUI.Button(button, (530, 500), (60, 60), text = '<-', onClick=self.left)
        self.rightB = GUI.Button(button, (650, 500), (60, 60), text = '->', onClick=self.right)

        self.userControl.labels.append(self.title)
        self.userControl.labels.append(self.l1)
        self.userControl.labels.append(self.l2)
        self.userControl.labels.append(self.l3)
        self.userControl.labels.append(self.lp)
        self.userControl.buttons.append(self.refreshB)
        self.userControl.buttons.append(self.newRoom)
        self.userControl.buttons.append(self.leftB)
        self.userControl.buttons.append(self.rightB)


    def show(self):
        self.userControl.hidden = False
        self.refresh()

    def hide(self):
        self.userControl.hidden = True

    def refresh(self):
        t = threading.Thread(target=self.doRefresh)
        t.setDaemon(True)
        t.start()

    def left(self):
        if self.page != 1:
            self.page -= 1
        self.lp.setText(str(self.page))
        self.refresh()

    def right(self):
        self.page += 1
        self.lp.setText(str(self.page))
        self.refresh()

    def clearMemory(self):
        for r in self.rooms:
            r.remove()
        self.rooms = []
        self.userControl.userControls = []
        gc.collect()

    def doRefresh(self):
        self.clearMemory()
        roomList = self.client.requestRoomList()
        anchor = 150
        if len(roomList) < 3:
            return

        rooms = roomList.split('#')[:-1]
        rLen = len(rooms)
        if rLen == (self.page - 1) * 7 + 7: # If exactly full page
            start = (self.page - 1) * 7
            end = start + 7
        elif rLen > (self.page - 1) * 7:
            start = (self.page - 1) * 7
            if self.page == rLen/7 + 1:
                end = start + rLen%7
            else:
                end = start + 7
        else:
            start = 0
            end = 0
        print (rooms)
        for i in range(start, end):
            r = rooms[i]
            rSplit = r.split('*')
            name = rSplit[0]
            addr = rSplit[1].split(',')
            addr = (addr[0] , int(addr[1]))
            players = rSplit[2] + '/2'
            spectators = rSplit[3]
            room = Room(self.client, self.screen, name, anchor, addr, players, spectators)
            self.userControl.userControls.append(room.userControl)
            self.rooms.append(room)
            anchor += 50


    def createNewRoom(self):
        self.hide()
        userControls['roomCreator'].show()

class Room():
    def __init__(self, client, screen, name, anchor, addr, players, spectators):
        self.userControl = GUI.UserControl()
        self.name = name
        self.anchor = anchor
        self.addr = addr
        self.players = players
        self.spectators = spectators
        self.screen = screen
        self.client = client

        self.l1 = GUI.Text(name, (20, anchor), 20, (0, 0, 0))
        self.l2 = GUI.Text(str(players), (400, anchor), 20, (0, 0, 0))
        self.l3 = GUI.Text(str(spectators), (600, anchor), 20, (0, 0, 0))
        self.b1 = GUI.Button(button, (700, anchor), (100, 30), text = 'Play', onClick=self.play)
        self.b2 = GUI.Button(button, (810, anchor), (100, 30), text = 'Spectate', onClick=self.specate)

        self.userControl.labels.append(self.l1)
        self.userControl.labels.append(self.l2)
        self.userControl.labels.append(self.l3)
        self.userControl.buttons.append(self.b1)
        self.userControl.buttons.append(self.b2)

    def play(self):
        print ('Connecting to ') + str(self.addr)
        slots = self.client.requestFreeSlots(self.addr[1])
        name = self.client.name
        if slots[0] == '0':
            s = Spectate.Spectator(self.screen, name=name, _type = 'player1', addr=self.addr)
        elif slots[1] == '0':
            s = Spectate.Spectator(self.screen, name=name, _type = 'player2', addr=self.addr)


    def specate(self):
        print ('Connecting to ') + str(self.addr)
        s = Spectate.Spectator(self.screen, _type = 0, addr=self.addr)

    def remove(self):
        self.userControl.remove()


class RoomCreator():

    def __init__(self, client):
        self.client = client
        self.userControl = GUI.UserControl(hidden=True)

        self.title = GUI.Text('Create Room', (400, 50), 30, (0, 0, 0))
        self.l1 = GUI.Text('Room Name', (450, 170), 20, (0, 0, 0))
        self.l2 = GUI.Text('', (300, 260), 20, (255, 0, 0))
        self.t = GUI.Textbox(button, (300, 200), (400, 60))
        self.newRoom = GUI.Button(button, (400, 300), (200, 60), text = 'Create Room', onClick=self.createNewRoom)
        self.backB = GUI.Button(button, (400, 400), (200, 60), text = 'Back', onClick=self.back)

        self.userControl.labels.append(self.title)
        self.userControl.labels.append(self.l1)
        self.userControl.labels.append(self.l2)
        self.userControl.buttons.append(self.newRoom)
        self.userControl.buttons.append(self.backB)
        self.userControl.textboxes.append(self.t)

    def show(self):
        self.userControl.hidden = False
        self.t.setText('')
        self.l2.setText('')

    def hide(self):
        self.userControl.hidden = True

    def createNewRoom(self):
        t = threading.Thread(target=self.doCreateNewRoom)
        t.start()

    def doCreateNewRoom(self):
        name = self.t.getText()
        out = self.client.requestCreateRoom(name)
        if out == 'OK':
            self.l2.setText('Room Created')
            self.l2.color = (0, 0, 255)
            print ('Room Created!')
        elif out == '-1':
            self.l2.setText('Room name %s Already Taken' % name)
            self.l2.color = (255, 0, 0)
            self.t.setText('')
        else:
            self.l2.setText(out)
            self.l2.color = (255, 0, 0)

    def back(self):
        self.hide()
        userControls['roomPicker'].show()

if __name__ == '__main__':
    f = open('ip.txt', 'r')
    addr = (f.read().replace('\n', ''), 9059)
    f.close()
    l = Launcher(addr)
