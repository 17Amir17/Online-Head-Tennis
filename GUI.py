import sys

import pygame
from pygame.locals import *

class Text():

    def __init__(self, text, pos, size, color = (0, 0, 0), hidden=False):
        self.font = pygame.font.SysFont('Comic Sans MS', size)
        self.text = self.font.render(text, True, color)
        self.pos = pos
        self.rawText = text
        self.size =  size
        self.startSize = size
        self.line = False
        self.color = color
        self.hidden = hidden

    def setSize(self, size):
        self.font = pygame.font.SysFont('Comic Sans MS', size)
        self.size = size

    def setText(self, text):
        self.rawText = text

    def draw(self, screen):
        if not self.hidden:
            self.text = self.font.render(self.rawText + self.line*'|', True, self.color)
            screen.blit(self.text, self.pos)

class Button(pygame.sprite.Sprite):
    def __init__(self, image_file, pos, size, text = '', textSize=20, onClick=None, hidden=False):
        pygame.sprite.Sprite.__init__(self)  #call Sprite initializer
        self.size = size
        self.pos = pos
        self.rawText = text
        self.textSize = textSize
        self.onClick = onClick
        self.hidden = hidden
        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.scale(self.image, size)
        self.original = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = pos
        self.Label()

    def Label(self):
        self.text = Text(self.rawText, self.pos, self.textSize)
        size = self.text.text.get_width(), self.text.text.get_height()
        x, y = self.pos
        sX, sY = self.size
        pos = (x + (sX - size[0])/ 2, y + (sY - size[1])/2)
        self.text.pos = pos

    def draw(self, screen):
        if not self.hidden:
            screen.blit(self.image, self.rect)
            self.text.draw(screen)

    def checkCollide(self, pos):
        if self.rect.collidepoint(pos):
            alpha = 128
            self.image.fill((102, 255, 102, alpha), None, pygame.BLEND_RGBA_MULT)
            if self.onClick != None:
                self.onClick()

    def checkHover(self, pos):
        if self.rect.collidepoint(pos):
            alpha = 128
            self.image = self.original.copy()
            self.image.fill((102, 255, 102, alpha), None, pygame.BLEND_RGBA_MULT)
        else:
            self.image = self.original.copy()

    def unclick(self):
        self.image = self.original.copy()

    def remove(self):
        self.image = None
        self.original = None

class Textbox(pygame.sprite.Sprite):
    def __init__(self, image_file, pos, size, text = '', textSize=20, hidden=False, framesPerTick = 15):
        pygame.sprite.Sprite.__init__(self)  #call Sprite initializer
        self.count = 0
        self.framesPerTick = framesPerTick
        self.size = size
        self.pos = pos
        self.rawText = text
        self.textSize = textSize
        self.hidden = hidden
        self.focus = False
        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.scale(self.image, size)
        self.original = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = pos
        self.Label()

    def Label(self):
        self.text = Text(self.rawText, self.pos, self.textSize)
        size = self.text.text.get_width(), self.text.text.get_height()
        x, y = self.pos
        sX, sY = self.size
        pos = (x + (sX - size[0])/ 2, y + (sY - size[1])/2)
        self.text.pos = pos

    def draw(self, screen):
        self.count += 1
        if not self.hidden:
            screen.blit(self.image, self.rect)
            if self.focus and self.framesPerTick == self.count:
                self.text.line = True
            elif self.framesPerTick*2 == self.count:
                self.text.line = False
                self.count = 0
            self.text.draw(screen)

    def checkCollide(self, pos):
        #On click
        if self.rect.collidepoint(pos):
            self.focus = True
            self.text.line = True
        else:
            self.focus = False
            self.text.line = False

    def getText(self):
        return self.text.rawText

    def setText(self, text):
        self.text.setText(text)

    def setTextColor(self, color):
        self.text.color = color

    def keyDown(self, key, shift):
        distance = 50
        if key == 8: # Backspace
            try:
                t = self.text.rawText
                if t != '':
                    self.setText(t[:-1], True)
            except Exception as e:
                print e
        else:
            try:
                if shift:
                    key = chr(key).upper()
                else:
                    key = chr(key)
                t = self.text.rawText
                self.setText(t + key)

            except Exception as e:
                print e
                pass

    def setText(self, txt, backspace = False):
        distance = 50
        self.text.setText(txt)
        x, y = self.pos
        size = self.text.font.size(txt)
        size = [size[0] + distance, size[1]]
        sX, sY = self.size
        # Resize
        if not backspace:
            if size[0] > sX:
                self.text.setSize(self.text.size - 1)
                size[0] = self.text.text.get_width() + distance
        else:
            if size[0] < sX and self.text.size < self.text.startSize:
                self.text.setSize(self.text.size + 1)
                size[0] = self.text.text.get_width() + distance
        pos = (x + (sX - size[0] + distance)/ 2, y + (sY - size[1])/2)
        self.text.pos = pos

    def remove(self):
        self.image = None
        self.original = None

class UserControl():
    def __init__(self, hidden = False):
        self.hidden = hidden
        self.buttons = []
        self.textboxes = []
        self.labels = []
        self.userControls = []

    def update(self, pos, click, key, shift):
        if not self.hidden:
            for u in self.userControls:
                u.update(pos, click, key, shift)
        if click and not self.hidden:
            for b in self.buttons:
                if not b.hidden:
                    b.checkHover(pos)
                    b.checkCollide(pos)
            for t in self.textboxes:
                if not t.hidden:
                    t.checkCollide(pos)
        else:
            for b in self.buttons:
                b.unclick()
                b.checkHover(pos)
        if key != False:
            for t in self.textboxes:
                if t.focus and not t.hidden:
                    t.keyDown(key, shift)

    def draw(self, display):
        if not self.hidden:
            for u in self.userControls:
                u.draw(display)
            for b in self.buttons:
                b.draw(display)
            for t in self.textboxes:
                t.draw(display)
            for l in self.labels:
                l.draw(display)

    def remove(self):
        for b in self.buttons:
            b.remove()
        for t in self.textboxes:
            t.remove()
        for u in self.userControls:
            u.remove()
        self.buttons = []
        self.labels = []
        self.textboxes = []
        self.userControls = []
class GUI():

    def __init__(self, display):
        self.display = display
        self.userControls = []

    def update(self, pos, click, key, shift):
        for u in self.userControls:
            u.update(pos, click, key, shift)

    def draw(self):
        try:
            for u in self.userControls:
                u.draw(self.display)
        except Exception as e:
            print e
