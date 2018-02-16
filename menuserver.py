import socket, threading, game, time, os

addr = ('localHost', 9059)
port = [9060]
userClientList = []
serverRoomList = []

class Server():

    def __init__(self, addr):
        self.addr = addr
        self.s = socket.socket()
        self.s.bind(addr)
        self.s.listen(10)
        print 'Runnign Server on ' + str(addr)
        self.loop()

    def loop(self):
        while True:
            try:
                client, addr = self.s.accept()
                print str(addr) + ' connected'

                """
                0 - UserClient
                1 - ServerRoom
                """
                client.settimeout(1)
                msg = client.recv(5)
                client.settimeout(None)
                if msg[0] == '0':
                    print 'User Client Connected'
                    userClient = UserClient(client, addr)
                    userClientList.append(userClient)
                elif msg[0] == '1':
                    print 'Server Room Connected ' + msg[1:]
                    port = msg[1:]
                    for r in serverRoomList:
                        if str(r.addr[1]) == port:
                            r.server = client
                            r.t.start()

            except Exception as e:
                client.close()
                print 'In loop ' + str(e)


class UserClient():

    def __init__(self, client, addr):
        self.name = ''
        self.client = client
        self.addr = addr
        thread = threading.Thread(target=self.session)
        thread.setDaemon(True)
        thread.start()

    def session(self):
        try:
            while True:
                """
                0 - Set username
                1 - Request Server List
                2 - Create Room
                3 - Request Player Count
                4 - Request free player slot
                """
                msg = self.client.recv(128)
                if msg[0] == '0':
                    print 'Request to set username'
                    self.setUsername(msg[1:])
                elif msg[0] == '1':
                    print 'Request to get room list'
                    self.client.send(self.getServerList())
                elif msg[0] == '2':
                    print 'Request to create room'
                    self.createNewRoom(msg[1:])
                elif msg[0] == '3':
                    print 'Request to get player count'
                    self.client.send(self.getPlayerCount(msg[1:]))
                elif msg[0] == '4':
                    print 'Request to get free slots'
                    self.client.send(self.getFreePlayerSlots(msg[1:]))
                else:
                    raise Exception('Uknown bla bla')

        except Exception as e:
            print 'In session ' + str(e)
            userClientList.remove(self)
            print userClientList
            self.client.close()

    def setUsername(self, username):
        for user in userClientList:
            if user.name == username:
                self.client.send('-1')
                return
        self.name = username
        self.client.send('OK')

    def createNewRoom(self, name):
        for room in serverRoomList:
            if room.name == name:
                self.client.send('-1')
                return

        address = (addr[0], port[0])
        t = threading.Thread(target=self.startGame, args=(address,))
        t.start()
        r = ServerRoom(name, address)
        serverRoomList.append(r)
        port[0] += 1

        while r.server == None:
            time.sleep(.1)
        self.client.send('OK')

    def startGame(self, addr):
        print 'Starting Game'
        os.system('game.py ' + addr[0] + ' ' + str(addr[1]))

    def getServerList(self):
        #TEMPORARY
        s = ''
        for room in serverRoomList:
            s += room.name + '*' + str(room.addr[0]) + ',' + str(room.addr[1])+\
                 '*' + str(room.players) + '*' + str(room.spectators) + '#'
        if s == '':
            s = ' '
        return s

    def getPlayerCount(self, port):
        for room in serverRoomList:
            if str(room.addr[1]) == port:
                return str(room.players)
        return '-1'

    def getFreePlayerSlots(self, port):
        for room in serverRoomList:
            if str(room.addr[1]) == port:
                room.server.send('1')
                time.sleep(.1)
                return room.slots
        return '-1'

class ServerRoom():

    def __init__(self, name, addr):
        self.name = name
        self.addr = addr
        self.players = 0
        self.spectators = 0
        self.slots = '00'
        self.server = None
        self.t = threading.Thread(target = self.read)
        self.t.setDaemon(True)

    def read(self):
        print 'Reading!'
        while True:
            try:
                msg = self.server.recv(128)
                """
                0 - Player List
                """
                if msg[0] == '0':
                    d = msg[1:].split(',')
                    self.players = int(d[0])
                    self.spectators = int(d[1])
                if msg[0] == '1':
                    self.slots = msg[1:]
            except Exception as e:
                break
                print 'In Menu read ' + str(e)




if __name__ == '__main__':
    s = Server(addr)
