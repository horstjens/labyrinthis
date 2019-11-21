"""
author: Horst JENS, Peter van der Linden und Anton Schmidt
email: horstjens@gmail.com
contact: see http://spielend-programmieren.at/de:kontakt
license: gpl, see http://www.gnu.org/licenses/gpl-3.0.de.html
download: https://github.com/horstjens/
idea: python3/pygame 2d vector dungeon crawl roguelike

"""
import pygame
import random
import os

def mouseVector():
    return pygame.math.Vector2(pygame.mouse.get_pos()[0],
                               - pygame.mouse.get_pos()[1])
def randomize_color(color, delta=50):
    d=random.randint(-delta, delta)
    color = color + d
    color = min(255,color)
    color = max(0, color)
    return color

def make_text(msg="pygame is cool", fontcolor=(255, 0, 255), fontsize=42, font=None):
    """returns pygame surface with text. You still need to blit the surface."""
    myfont = pygame.font.SysFont(font, fontsize)
    mytext = myfont.render(msg, True, fontcolor)
    mytext = mytext.convert_alpha()
    return mytext

def write(background, text="bla", pos=None, color=(0,0,0),
          fontsize=None, center=False, x=None, y=None):
        """write text on pygame surface. pos is a 2d Vector """
        if pos is None and (x is None or y is None):
            print("Error with write function: no pos argument given and also no x and y:", pos, x, y)
            return
        if pos is not None:
            # pos has higher priority than x or y
            x = pos.x
            y = -pos.y
        if fontsize is None:
            fontsize = 24
        font = pygame.font.SysFont('mono', fontsize, bold=True)
        fw, fh = font.size(text)
        surface = font.render(text, True, color)
        if center: # center text around x,y
            background.blit(surface, (x-fw//2, y-fh//2))
        else:      # topleft corner is x,y
            background.blit(surface, (x,y))

def elastic_collision(sprite1, sprite2):
        """elasitc collision between 2 VectorSprites (calculated as disc's).
           The function alters the dx and dy movement vectors of both sprites.
           The sprites need the property .mass, .radius, pos.x pos.y, move.x, move.y
           by Leonard Michlmayr"""
        if sprite1.static and sprite2.static:
            return 
        dirx = sprite1.pos.x - sprite2.pos.x
        diry = sprite1.pos.y - sprite2.pos.y
        sumofmasses = sprite1.mass + sprite2.mass
        sx = (sprite1.move.x * sprite1.mass + sprite2.move.x * sprite2.mass) / sumofmasses
        sy = (sprite1.move.y * sprite1.mass + sprite2.move.y * sprite2.mass) / sumofmasses
        bdxs = sprite2.move.x - sx
        bdys = sprite2.move.y - sy
        cbdxs = sprite1.move.x - sx
        cbdys = sprite1.move.y - sy
        distancesquare = dirx * dirx + diry * diry
        if distancesquare == 0:
            dirx = random.randint(0,11) - 5.5
            diry = random.randint(0,11) - 5.5
            distancesquare = dirx * dirx + diry * diry
        dp = (bdxs * dirx + bdys * diry) # scalar product
        dp /= distancesquare # divide by distance * distance.
        cdp = (cbdxs * dirx + cbdys * diry)
        cdp /= distancesquare
        if dp > 0:
            if not sprite2.static:
                sprite2.move.x -= 2 * dirx * dp
                sprite2.move.y -= 2 * diry * dp
            if not sprite1.static:
                sprite1.move.x -= 2 * dirx * cdp
                sprite1.move.y -= 2 * diry * cdp


def fight(attacker, defender):
    Viewer.log.append([(0,255,0), "{} strikes at {}".format(attacker.__class__.__name__, defender.__class__.__name__)])
    strike(attacker, defender)
    if defender.hitpoints > 0:
        Viewer.log.append([(0,200,0),"{} strikes back against {}".format(defender.__class__.__name__, attacker.__class__.__name__)])
        strike(defender, attacker)
        
def strike(attacker, defender):
    """attacker strikes once against defender"""
    attacker.attack_animation()
    # attack vs defense
    d1 = random.randint(1,6)
    d2 = random.randint(1,6)
    d3 = random.randint(1,6)
    d4 = random.randint(1,6)
    # attack value + d1+d2 > defense value + d3 +d4 ?
    a = attacker.attack + d1 + d2
    d = defender.defense + d3 + d4
    if d >= a:
        damage = 0
    else:
        damage = a-d
    m = pygame.math.Vector2( 0.35 * (defender.pos.x- attacker.pos.x) ,
                             0.25 * (defender.pos.y - attacker.pos.y ))
    if m.y == 0: 
        m.y = 15
    Flytext(text="{}{} HP".format("-" if damage >0 else "", damage), 
            pos = pygame.math.Vector2(defender.pos.x, defender.pos.y+20), 
            move = m,
            color = (200,0,0) if damage > 0 else (20,20,20), max_age=2,
            fontsize=60)
    text = "hit!" if damage > 0 else "fail..."
    text += " attack+2d6 = {} + {} + {} = {} Vs. defense+2d6 = {} + {} + {} = {}".format(
            attacker.attack, d1, d2, attacker.attack+d1+d2, defender.defense, d3, d4, defender.defense + d3+d4)
    if damage > 0:
        text += "  DAMAGE {} HP".format(damage)
    defender.hitpoints -= damage
    Viewer.log.append([(255,255,255), text])
                
                
    
class State():
    """
      We define a state object which provides some utility functions for the
      individual states within the state machine.
      """

    def __init__(self):
        print('Processing current state:', str(self))

    def on_event(self, event):
        """
        Handle events that are delegated to this State.
        """
        pass

    def __repr__(self):
        """
        Leverages the __str__ method to describe the State.
        """
        return self.__str__()

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__

class NoneState(State):
    """for Monsters that do neither sleep nor patrol at all"""
    
    def on_event(self, event):
        return self 
        
class BerserkState(State):
    
    def on_event(self, event):
        return self

class SleepState(State):

    def on_event(self, event):
        if event == 'wake up':
            return PatrolState()
        elif event == "attacked":
            return PatrolState()
        return self

class PatrolState(State):

    def on_event(self, event):
        if event == 'sleepy':
            return SleepState()
        return self


class VectorSprite(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygames sprite class"""
    number = 0
    numbers = {} # { number, Sprite }

    def __init__(self, **kwargs):
        self._default_parameters(**kwargs)
        VectorSprite.number += 1
        VectorSprite.numbers[self.number] = self
        self._overwrite_parameters()
        pygame.sprite.Sprite.__init__(self, self.groups) #call parent class. NEVER FORGET !
        self.number = VectorSprite.number # unique number for each sprite

        self.create_image()
        self.distance_traveled = 0 # in pixel
        #self.rect.center = (-300,-300) # avoid blinking image in topleft corner
        if self.angle != 0:
            self.set_angle(self.angle)
        self.tail = [] 

    def _overwrite_parameters(self):
        """change parameters before create_image is called""" 
        pass

    def _default_parameters(self, **kwargs):    
        """get unlimited named arguments and turn them into attributes
           default values for missing keywords"""

        for key, arg in kwargs.items():
            setattr(self, key, arg)
        if "layer" not in kwargs:
            self._layer = 4
        else:
            self._layer = self.layer
        if "static" not in kwargs:
            self.static = False
        if "selected" not in kwargs:
            self.selected = False
        if "pos" not in kwargs:
            self.pos = pygame.math.Vector2(random.randint(0, Viewer.width),-50)
        if "move" not in kwargs:
            self.move = pygame.math.Vector2(0,0)
        if "fontsize" not in kwargs:
            self.fontsize = 22
        if "friction" not in kwargs:
            self.friction = 1.0 # no friction
        if "radius" not in kwargs:
            self.radius = 5
        if "width" not in kwargs:
            self.width = self.radius * 2
        if "height" not in kwargs:
            self.height = self.radius * 2
        
        if "hitpoints" not in kwargs:
            self.hitpoints = 100
        self.hitpointsfull = self.hitpoints # makes a copy
        if "mass" not in kwargs:
            self.mass = 10
        if "damage" not in kwargs:
            self.damage = 10
        if "bounce_on_edge" not in kwargs:
            self.bounce_on_edge = False
        if "kill_on_edge" not in kwargs:
            self.kill_on_edge = False
        if "angle" not in kwargs:
            self.angle = 0 # facing right?
        if "max_age" not in kwargs:
            self.max_age = None
        if "max_distance" not in kwargs:
            self.max_distance = None
        if "picture" not in kwargs:
            self.picture = None
        if "bossnumber" not in kwargs:
            self.bossnumber = None
        if "kill_with_boss" not in kwargs:
            self.kill_with_boss = False
        if "sticky_with_boss" not in kwargs:
            self.sticky_with_boss = False
        if "mass" not in kwargs:
            self.mass = 15
        if "upkey" not in kwargs:
            self.upkey = None
        if "downkey" not in kwargs:
            self.downkey = None
        if "rightkey" not in kwargs:
            self.rightkey = None
        if "leftkey" not in kwargs:
            self.leftkey = None
        if "speed" not in kwargs:
            self.speed = None
        if "age" not in kwargs:
            self.age = 0 # age in seconds
        if "warp_on_edge" not in kwargs:
            self.warp_on_edge = False
        if "gravity" not in kwargs:
            self.gravity = None
        if "survive_north" not in kwargs:
            self.survive_north = False
        if "survive_south" not in kwargs:
            self.survive_south = False
        if "survive_west" not in kwargs:
            self.survive_west = False
        if "survive_east" not in kwargs:
            self.survive_east = False
        if "speed" not in kwargs:
            self.speed = 0
        if "gravity" not in kwargs:
            self.gravity = None
        if "ydistance" not in kwargs:
            self.ydistance = 0
        if "always_create_image" not in kwargs:
            self.always_create_image = False
        if "bounty" not in kwargs:
            self.bounty = 0
        if "gold" not in kwargs:
            self.gold = 0
        if "color" not in kwargs:
            self.color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))

    def kill(self):
        
        if self.number in self.numbers:
           del VectorSprite.numbers[self.number] # remove Sprite from numbers dict
        
        if self.bounty > 0:
            VectorSprite.numbers[1].gold += self.bounty 
            Flytext(pos=pygame.math.Vector2(self.pos.x, self.pos.y),
                    text="{} gold".format(self.bounty),
                    move=pygame.math.Vector2(0, 5),
                    max_age = 5,
                    fontsize = 33,
                    color = (255,255,0))
            
        
        pygame.sprite.Sprite.kill(self)
   
    
    def create_image(self):
        if self.picture is not None:
            self.image = self.picture.copy()
        else:
            self.image = pygame.Surface((self.width,self.height))
            self.image.fill((self.color))
        self.image = self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect= self.image.get_rect()
        self.width = self.rect.width
        self.height = self.rect.height
    
    def rotate_to(self, final_degree):
        if final_degree < self.angle:
            self.rotate(- self.turnspeed)
        elif final_degree > self.angle:
            self.rotate(self.turnspeed)
        else:
            return
        
    def forward(self, speed=10):
        m = pygame.math.Vector2(speed, 0)
        m.rotate_ip(self.angle)
        self.move += m
        
    def rotate(self, by_degree):
        """rotates a sprite and changes it's angle by by_degree"""
        self.angle += by_degree
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def set_angle(self, degree):
        """rotates a sprite and changes it's angle to degree"""
        self.angle = degree
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, self.angle)
        #self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    #def update(self, seconds):
    #    """calculate movement, position and bouncing on edge"""
    #    # ----- kill because... ------
    #    if self.hitpoints <= 0:
    #        self.kill()
    #    if self.max_age is not None and self.age > self.max_age:
    #        self.kill()
    #    if self.max_distance is not None and self.distance_traveled > self.max_distance:
    #        self.kill()
    #    if self.always_create_image:
    #        self.create_image()
    #        #print("i create new image")
    #    # ---- movement with/without boss ----
    #    if self.bossnumber is not None:
    #        if self.kill_with_boss:
    #            if self.bossnumber not in VectorSprite.numbers:
    #                self.kill()
    #        if self.sticky_with_boss and self.bossnumber in VectorSprite.numbers:
    #            boss = VectorSprite.numbers[self.bossnumber]
    #            #self.pos = pygame.math.Vector2(boss.pos.x, boss.pos.y + self.ydistance)
    #            self.pos = pygame.math.Vector2(boss.pos.x, boss.pos.y+self.ydistance)
    #            self.set_angle(boss.angle)
    #    self.pos += self.move * seconds
    #    self.move *= self.friction
    #    if self.gravity is not None:
    #        self.move += self.gravity
    #    self.distance_traveled += self.move.length() * seconds
    #    self.age += seconds
    #    self.wallbounce()
    #
    #    self.rect.center = ( round(self.pos.x, 0), -round(self.pos.y, 0) )


    def update(self, seconds):
        """calculate movement, position and bouncing on edge"""
        # ----- kill because... ------
        if self.hitpoints <= 0:
            self.kill()
        if self.max_age is not None and self.age > self.max_age:
            self.kill()
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        # ---- new image calculating ? ---
        if self.always_create_image:
            self.create_image()
        # ---- movement with/without boss ----
        if self.bossnumber is not None:
            if self.kill_with_boss:
                if self.bossnumber not in VectorSprite.numbers:
                    self.kill()
                elif VectorSprite.numbers[self.bossnumber].hitpoints <= 0:
                    self.kill()
            if self.sticky_with_boss and self.bossnumber in VectorSprite.numbers:

                boss = VectorSprite.numbers[self.bossnumber]
                #print("bosspos", boss.pos)
                self.pos = boss.pos # pygame.math.Vector2(boss.pos.x, boss.pos.y)
                self.set_angle(boss.angle)
                #print(self.number, self.bossnumber, boss)
        self.pos += self.move * seconds
        self.move *= self.friction
        self.distance_traveled += self.move.length() * seconds
        self.age += seconds
        #self.wallbounce()
        self.rect.center = (round(self.pos.x, 0), -round(self.pos.y, 0) + self.ydistance)
        #if self.sticky_with_boss:
        #    print("self pos", self.pos)
        #    print("self rect center", self.rect.center)




    def wallbounce(self):
        # ---- bounce / kill on screen edge ----
        # ------- left edge ----
        if self.pos.x < 0:
            if self.kill_on_edge:
                self.kill()
            elif self.bounce_on_edge:
                self.pos.x = 0
                self.move.x *= -1
            elif self.warp_on_edge:
                self.pos.x = Viewer.width 
        # -------- upper edge -----
        if self.pos.y  > 0:
            if self.kill_on_edge and not self.survive_north:
                self.kill()
            elif self.bounce_on_edge:
                self.pos.y = 0
                self.move.y *= -1
            elif self.warp_on_edge:
                self.pos.y = -Viewer.height
        # -------- right edge -----                
        if self.pos.x  > Viewer.width:
            if self.kill_on_edge:
                self.kill()
            elif self.bounce_on_edge:
                self.pos.x = Viewer.width
                self.move.x *= -1
            elif self.warp_on_edge:
                self.pos.x = 0
        # --------- lower edge ------------
        if self.pos.y   < -Viewer.height:
            if self.kill_on_edge:
                self.hitpoints = 0
                self.kill()
            elif self.bounce_on_edge:
                self.pos.y = -Viewer.height
                self.move.y *= -1
            elif self.warp_on_edge:
                self.pos.y = 0


class Hitpointbar(VectorSprite):

    def _overwrite_parameters(self):
        pass
        # print("ich bin hitpointbar", self.number, "my bossnumber is", self.bossnumber)
        # print("my boss is a ", VectorSprite.numbers[self.bossnumber])

    def create_image(self):
        try:
            boss = VectorSprite.numbers[self.bossnumber]
        except:
            return
        width = self.width
        self.image = pygame.Surface((width, 10))  # size of rect
        # pygame.draw.circle(self.image, self.color, (5,5), 5)

        percent = boss.hitpoints / boss.hitpointsfull
        # print(percent, boss.hitpoints, boss.hitpointsfull)
        w2 = int(width * percent)
        # moving inside filling
        #if boss.side == 1:
        #    c = (200, 0, 0)
        #elif boss.side == 2:
        #    c = (0, 0, 200)
        #else:
        #    c = (200, 200, 200)
        c = (0,0,200)
        pygame.draw.rect(self.image, c, (1, 1, w2, 8))
        # static outside border
        pygame.draw.rect(self.image, (200, 200, 200), (0, 0, width, 10), 1)
        self.image.set_colorkey((0, 0, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.image0 = self.image.copy()
        # self.rect.centerx = boss.rect.centerx
        # self.rect.centerx = boss.rect.centerx
        # self.rect.centery = boss.rect.centery - 100


class Bar(VectorSprite):
    
    def _overwrite_parameters(self):
        self._layer = 19
        self.ydistance = -37
        self.width = 50
        self.sticky_with_boss = True
        self.kill_with_boss = True
        self.always_create_image = True
        #print("ich bin bar, meine Nummmer, meine bossnumber:", self.number, self.bossnumber)
          
    def create_image(self):
        try:
            boss = VectorSprite.numbers[self.bossnumber]
        except:
            return
        width = self.width
        self.image = pygame.Surface((width,10)) # size of rect
        percent = boss.hitpoints / boss.hitpointsfull
        w2 = int(width * percent)
        # moving inside filling
        if boss.number == 0:
            c = (0,200,0)
        else:
            c = (200,200,200)
        pygame.draw.rect(self.image,c, (1,1,w2,8)) 
        # static outside border
        pygame.draw.rect(self.image, (200,200,200), (0,0,width,10),1)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect= self.image.get_rect()
        self.image0 = self.image.copy()
        #self.rect.centerx = boss.rect.centerx
        #self.rect.centerx = boss.rect.centerx
        #self.rect.centery = boss.rect.centery - 100
    
class Fireball(VectorSprite):
    
    def _overwrite_parameters(self):
        self.hitpoints = 1
        self.color = (255,0,255)
        
    def create_image(self):
        self.image = pygame.Surface((10,10))
        #self.image.fill(self.color)
        pygame.draw.circle(self.image, self.color, (5,5),5)
        #pygame.draw.rect(self.image, (0,0,0), (0,0,49,49),1)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        
        
class Wall(VectorSprite):
    
    def _overwrite_parameters(self):
        self.color = (139, 105, 20)
        self.hitpoints = 1
        
    def crack(self):
        # border point
        border = random.choice(("n","s","w","e"))
        if border == "n":
            x1 = random.randint(0, 50)
            y1 = 0
            x2 = random.randint(20,30)
            y2 = random.randint(15,25)
        if border == "s":
            x1 = random.randint(0, 50)
            y1 = 50
            x2 = random.randint(20,30)
            y2 = random.randint(25,35)
        if border == "w":
            x1 = 0
            y1 = random.randint(0, 50)
            x2 = random.randint(15,25)
            y2 = random.randint(20,30)
        if border == "e":
            x1 = 50
            y1 = random.randint(0, 50)
            x2 = random.randint(25,35)
            y2 = random.randint(20,30)
        # draw crackline
        thick = random.randint(1,3)
        pygame.draw.line(self.image, (0,0,0), (x1,y1), (x2, y2), thick)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
            
        
        
    def create_image(self):
        new = [0,0,0]
        for a in range(3):
            c = self.color[a] + random.randint(-20,20)
            c = min(c, 255)
            c = max(c, 0)
            new[a] = c
        self.color = new
        self.image = pygame.Surface((50,50))
        self.image.fill(self.color)
        pygame.draw.rect(self.image, (0,0,0), (0,0,49,49),1)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        #print(self.pos)
            
        
        
class WallBorder(Wall):
    
    def _overwrite_parameters(self):
        self.color = (255, 50, 50)
        self.hitpoints = 400
        
    def create_image(self):
        Wall.create_image(self)
        pygame.draw.line(self.image, (0,200,0), (0,0), 
                         (49,49), 5)
        pygame.draw.line(self.image, (0,200,0), (0,49), 
                         (49,0), 5)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
           
    def crack(self):
        pass # hahahaha, indestructable
        
    def update(self, seconds):
        VectorSprite.update(self, seconds)
        self.hitpoints = 400


class Monster(VectorSprite):
    
    def _overwrite_parameters(self):
        self.lookright = True
        self.attacktime = 0
        #self.movingtime = 0
        self._layer = 14
        self.attack = 5
        self.defense = 5
        self.hitpoints = 50
        self.imagenames = ["wizard", "wizard-a"]
        self.dx, self.dy = 0, 0
        self.sniffrange = 5
        self.state = NoneState()  # PatrolState() / SleepState()
        #self.state = SleepingState()

    def on_event(self, event):
        self.state = self.state.on_event(event)


    def run_to_player(self):
            playerpos = VectorSprite.numbers[1].pos
            dx, dy = 0, 0
            if self.pos.x < playerpos.x:
                dx = Viewer.tilesize
            elif self.pos.x > playerpos.x:
                dx = - Viewer.tilesize
            if self.pos.y < playerpos.y:
                dy = -Viewer.tilesize
            elif self.pos.y > playerpos.y:
                dy = Viewer.tilesize
            return dx, dy

    def ai(self):
        playerpos = VectorSprite.numbers[1].pos
        distance = (self.pos - playerpos ).length() // Viewer.tilesize
        if distance < self.sniffrange:
            dx, dy = self.run_to_player()
        else:
            dx, dy = random.choice([(0,0), (0,0), (0,0),
                                    (-Viewer.tilesize, -Viewer.tilesize),
                                    (-Viewer.tilesize, 0),
                                    (-Viewer.tilesize, Viewer.tilesize),
                                    (0, -Viewer.tilesize),
                                    (0, Viewer.tilesize),
                                    (Viewer.tilesize, -Viewer.tilesize),
                                    (Viewer.tilesize, 0),
                                    (Viewer.tilesize, Viewer.tilesize)])
        self.dx, self.dy = dx, dy
        # --- checking Patrol / SleepState
        if self.state.__str__()=="PatrolState":
           self.tired += random.randint(1, 10)
           if self.tired> 100:
               #self.state.on_event("sleepy")
               self.on_event("sleepy")
               self.tired = 99
        elif self.state.__str__()== "SleepState":
            Flytext(pos=pygame.math.Vector2(self.pos.x, self.pos.y),
                    text="z", move=pygame.math.Vector2(15,20), max_age=1)
            self.dx, self.dy = 0,0
            self.tired -= 1
            if self.tired <= 0:
                #self.state.on_event("wake up")
                self.on_event("wake up")
                self.tired = 0
        
        elif self.state.__str__() == "BerserkState":
            self.dx, self.dy = self.run_to_player()
            print("i am in berserk-state", self.dx, self.dy)
    
    def update(self, seconds):
        if self.age < self.attacktime:
            if self.lookright:
                self.image = self.image2
            else:
                self.image = self.image3
        #elif self.age < self.movingtime:
        #    if self.lookright:
        #        self.image = self.image4:
        #    else:
        #        self.image = self.image5
        else:
            if self.lookright:
                self.image = self.image0
            else:
                self.image = self.image1
        VectorSprite.update(self, seconds)
        
    #def moving_animation(self, duration=0.1):
    #    self.movingtime = self.age + duration
    #    #if self.lookright:
    #    #      self.image = self.image4
    #    #else:
    #    #      self.image = self.image5
        
    def attack_animation(self, duration=0.15):
        self.attacktime = self.age + duration
        #if self.lookright:
        #    self.image = self.image2 
        #else:
        #    self.image = self.image3
        
    
    def create_image(self):
        self.image=Viewer.images[self.imagenames[0]]   
        # stand normal, look right + left     
        self.image0 = self.image.copy()
        self.image1 = pygame.transform.flip(self.image, True, False)
        # attack, look right + left
        self.image2 = Viewer.images[self.imagenames[1]]
        self.image3 = pygame.transform.flip(self.image2, True, False)
        # move, look right + left 
        #print(Viewer.images)
        # self.image4 = Viewer.images[self.imagenames[2]]
        # self.image5 = pygame.transform.flip(self.image4, True, False)
        self.rect = self.image.get_rect()

class Wizard(Monster):
    
    def _overwrite_parameters(self):
        self.lookright = True
        self.attacktime = 0
        self._layer = 15
        self.attack = 7
        self.defense = 5
        self.hitpoints = 200
        self.hitpointsfull = 200
        self.imagenames = ["wizard", "wizard-a"]
        self.dx, self.dy = 0, 0
        self.sniffrange = 5
        #print("ich bin wizard", self.number)
        Bar(bossnumber=self.number)
        #Hitpointbar(bossnumber=self.number, kill_with_boss=True,
        #            sticky_with_boss=True, ydistance=0, width=50,
        #            always_create_image=True)
        self.gold = 0

class Lizard(Monster):
    
    def _overwrite_parameters(self):
        self.attack = 5
        self.defense = 2
        self.attacktime = 0
        self.lookright = True
        self.hitpoints = 50
        self.hitpointsfull = 200
        self.imagenames = ["reptile", "reptile-a"]
        self.dx, self.dy = 0, 0
        self.sniffrange = 5
        Bar(bossnumber=self.number)
        self.tired = 0
        self.state = PatrolState()
        self.bounty = 1
        
   

    
class Wolf(Monster):
    
    def _overwrite_parameters(self):
        self.lookright = True
        self.attacktime = 0
        self._layer = 15
        self.attack = 8
        self.defense = 3
        self.hitpoints = 30
        self.hitpointsfull = 200
        self.imagenames = ["wolf", "wolf-a"]
        self.dx, self.dy = 0, 0
        self.sniffrange = 5
        self.state = PatrolState()
        self.tired = 0
        Bar(bossnumber=self.number)
        self.bounty = 4

  
class Boss(Monster):
    
   def _overwrite_parameters(self):
        self.lookright = True
        self.attacktime = 0
        self._layer = 15
        self.attack = 10
        self.defense = 5
        self.hitpoints = 300
        self.hitpointsfull = 300
        self.imagenames = ["bosswolf", "bosswolf-a"]
        self.dx, self.dy = 0, 0
        self.sniffrange = 15
        self.state = BerserkState()
        self.tired = 0
        Bar(bossnumber=self.number)
        self.bounty = 20



class Chest(Monster):
    
    def _overwrite_parameters(self):
        self.lookright = True
        self.attacktime = 0
        self._layer = 15
        self.attack = 0
        self.defense = 0
        self.hitpoints = 1
        self.hitpointsfull = 1
        self.imagenames = ["chest", "chest-a"]
        self.dx, self.dy = 0, 0
        self.sniffrange = 0
        self.state = NoneState()
        self.tired = 500
        #Bar(bossnumber=self.number)
        self.bounty = random.randint(1,20)
    
    def ai(self):
        pass

    
   
class Shop(VectorSprite):
    
    def create_image(self):
        self.color = (0,0,222)
        self.image = pygame.Surface((50,50))
        self.image.fill(self.color)
        pygame.draw.rect(self.image, (0,0,0), (0,0,49,49),1)
        write(self.image, text="$", x=0,y=0,
              fontsize=64, color=(50,50,50))
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        #print(self.pos)
            
        
        
        





class Cannon(VectorSprite):
    def _overwrite_parameters(self):
        self.kill_on_edge = False
        self.survive_north = True
        #self.pos.y = -Viewer.height //2
        #self.pos.x = Viewer.width //2
       
        #self.imagenames = ["cannon"]
        self.speed  = 7
        self.turnspeed = 0.5
        self.ready_to_launch = 0
            
    def fire(self):
        for i in range(1):
            v = pygame.math.Vector2(200,0)
            v.rotate_ip(self.angle + i)
            Bullet(boss=self, mass=500,
                   pos=pygame.math.Vector2(self.pos.x, self.pos.y),
                   angle=self.angle+i, move = v+self.move, color=self.color)
        # --- recoil ----
        v = pygame.math.Vector2(50,0)
        v.rotate_ip(self.angle + 180)
        self.move += v
            
    def launch(self, enemy):
            if self.age < self.ready_to_launch:
                return # not yet ready, wait a bit
            self.ready_to_launch = self.age + 1.5 # wait that time
            v = pygame.math.Vector2(50,0)
            v.rotate_ip(self.angle)
            Rocket(boss=self, target=enemy, mass=50, max_age=7.4,
                   pos=pygame.math.Vector2(self.pos.x, self.pos.y),
                   angle=self.angle, move = v+self.move, color=self.color)
    
    def create_image(self):
        self.image=Viewer.images["cannon"]
        
        self.image0 = self.image.copy()
       # self.image0.set_colorkey((0,0,0))
       # self.image0.convert_alpha()
        self.rect = self.image.get_rect()

    def kill(self):
        Explosion(posvector=self.pos, red=200, red_delta=25, minsparks=500, maxsparks=600, maxlifetime=7)
        VectorSprite.kill(self)
   
   
    def update(self,seconds):
        VectorSprite.update(self,seconds)
        # - - - - - - go to mouse cursor ------ #
        target = mouseVector()
        dist =target - self.pos
        try:
            dist.normalize_ip() #schrupmft ihn zur länge 1
        except:
            print("Vector Error in line 833. i could not normalize", dist)
            return
        dist *= self.speed  
        rightvector = pygame.math.Vector2(1,0)
        angle = -dist.angle_to(rightvector)
        #print(angle)
        #if self.angle == round(angle, 0):
        if self.selected:
            self.move = dist
            self.set_angle(angle)
            pygame.draw.rect(self.image, (0,200,0), (0,0,self.rect.width, self.rect.height),1)



class Flytext(VectorSprite):
    
    def _overwrite_parameters(self):
        self._layer = 17  # order of sprite layers (before / behind other sprites)
        self.r, self.g, self.b = self.color
        
    def create_image(self):
        self.image = make_text(self.text, (self.r, self.g, self.b), self.fontsize)  # font 22
        self.rect = self.image.get_rect()
 
 
class Extra(VectorSprite):
    
    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True
        self.pos = pygame.math.Vector2(random.randint(0,Viewer.width),
                                       random.randint(-Viewer.height,0))
        v = pygame.math.Vector2(random.randint(10, 25), 0)
        v.rotate_ip(random.randint(0,360))
        self.move = v
                                              
    
    def create_image(self):
        self.image = pygame.Surface((30,30))
        pygame.draw.circle(self.image, (200,200,200), (15,15), 15)
        pygame.draw.circle(self.image, (200,100,200), (15,15), 12)
        pygame.draw.circle(self.image, (0,0,0), (15,15), 3)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect= self.image.get_rect()
        self.image0 = self.image.copy()                          
    
     
   
class Rocket(VectorSprite):
    
    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True
        self.trail = []
    
    def update(self, seconds):
        VectorSprite.update(self, seconds)
        diff = self.target.pos - self.pos
        r = pygame.math.Vector2(1,0)
        a = -diff.angle_to(r)
        # rotate the sprite
        self.set_angle(a)
        #self.move.rotate_ip(a)
        diff.normalize_ip() # diff has lenght 1 now
        self.move *= 0.8   # friction, reduce old move
        self.move += diff * 20  # add new move
        self.trail.insert(0,(self.pos.x, -self.pos.y))
        if len(self.trail) > 255:
            self.trail = self.trail[:256]
    
    def kill(self):
        #Explosion(posvector=self.pos, minsparks=50, maxsparks=150)
        VectorSprite.kill(self)
    
    def create_image(self):
        self.image = pygame.Surface((30,10))
        pygame.draw.circle(self.image, (1,1,1), (25,5), 5)
        pygame.draw.rect(self.image, self.color, (0,0,25,10))
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect= self.image.get_rect()
        self.image0 = self.image.copy()                          
    

class Bullet(VectorSprite):
    
    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True
        #self.color = (255,255,0) # yellow

    def create_image(self):
        r,g,b = self.color
        self.image = pygame.Surface((10,10))
        
        pygame.draw.circle(self.image, self.color, (5,5), 5)
        
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect= self.image.get_rect()
        self.image0 = self.image.copy()                          
    

class Gem(VectorSprite):

    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True

    def create_image(self):
        r = randomize_color(self.red, self.red_delta)
        g = randomize_color(self.green, self.green_delta)
        b = randomize_color(self.blue, self.blue_delta)
        self.image = pygame.Surface((10,10)) 
        pygame.draw.polygon(self.image, (r,g,b),
             [(5,0), (10,3), (10,7), (5,10), (0,7), (0,3)])
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect= self.image.get_rect()
        self.image0 = self.image.copy()                          
        
    

class Spark(VectorSprite):
    
    def _overwrite_parameters(self):
        self._layer = 9
        self.kill_on_edge = True
        
    def create_image(self):
        #r,g,b = self.color
        r = randomize_color(self.red, self.red_delta)
        g = randomize_color(self.green, self.green_delta)
        b = randomize_color(self.blue, self.blue_delta)
        self.image = pygame.Surface((10,10))
        pygame.draw.line(self.image, (r,g,b), 
                         (10,5), (5,5), 3)
        pygame.draw.line(self.image, (r,g,b),
                          (5,5), (2,5), 1)
        self.image.set_colorkey((0,0,0))
        self.image.convert_alpha()
        self.rect= self.image.get_rect()
        self.image0 = self.image.copy()                          
        

class Explosion():
    """emits a lot of sparks, for Explosion or Player engine"""
    def __init__(self, posvector, minangle=0, maxangle=360, maxlifetime=3,
                 minspeed=5, maxspeed=150, red=255, red_delta=0, 
                 green=225, green_delta=25, blue=0, blue_delta=0,
                 minsparks=5, maxsparks=20, 
                 shape="spark", gravity = None):
                     
                     
        for s in range(random.randint(minsparks,maxsparks)):
            v = pygame.math.Vector2(1,0) # vector aiming right (0°)
            a = random.randint(minangle,maxangle)
            v.rotate_ip(a)
            speed = random.randint(minspeed, maxspeed)
            duration = random.random() * maxlifetime # in seconds
            #red   = randomize_color(red, red_delta)
            #green = randomize_color(green, green_delta)
            #blue  = randomize_color(blue, blue_delta)
            
            if shape == "spark":
                Spark(pos=pygame.math.Vector2(posvector.x, posvector.y),
                      angle= a, move=v*speed, max_age = duration, 
                      red=red, green=green, blue=blue,
                      red_delta = red_delta, green_delta = green_delta, blue_delta=blue_delta,
                      kill_on_edge = True, gravity=gravity)
            elif shape == "gem":
                Gem(pos=pygame.math.Vector2(posvector.x, posvector.y),
                      angle= a, move=v*speed, max_age = duration, 
                      red=red, green=green, blue=blue,
                      red_delta = red_delta, green_delta = green_delta, blue_delta=blue_delta,
                      kill_on_edge = True, gravity=gravity)


        
    
    

class Viewer(object):
    width = 0
    dungeon = []
    log = []
    gold = 0
    height = 0
    images = {}
    sounds = {}
    #inventory = []
    history = ["main"]
    cursor = 0
    name = "main"
    tilesize = 50
    maxx = 100
    maxy = 100
    fullscreen = False
    gamemenu =  {"main":            ["resume", "use", "equip", "settings", "credits", "quit" ],
            #main
            # cheatmenu 
            "use" :      ["back",],
            "equip":     ["back",],
           
            "settings":        ["back", "video", "tile size", "max. tiles x", "max. tiles y" ],
            #settings
            "tile size":       ["back", "25x25", "50x50", "75x75", "100x100"],
            "max. tiles x":    ["back", "50", "100", "150", "200", "250"],
            "max. tiles y":    ["back", "50", "100", "150", "200", "250"],
            "video":           ["back", "resolution", "fullscreen"],
            #difficulty
           
    
            "fullscreen":      ["back", "true", "false"]
            }
    
    shopmenu = {"main": [ "resume", "earn money", "buy", "sell", "show inventory"],
                "earn money":      ["back", "plant tomatoes"],
                "show inventory":  ["back",] ,
                "buy":             ["back", 
                                    "wooden sword (10)",
                                    "old shield (15)",
                                    "ring mail (55)",
                                    "small health potion (1)",
                                    "medium health potion (5)",
                                    "big health potion (10)"],
                "sell":            ["back" ],
               
               }
    menu = gamemenu 
    #Viewer.menu["resolution"] = pygame.display.list_modes()
 

    def __init__(self, width=640, height=400, fps=60):
        """Initialize pygame, window, background, font,...
           default arguments """
        pygame.mixer.pre_init(44100,-16, 2, 2048)   
        pygame.init()
        Viewer.width = width    # make global readable
        Viewer.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.background.fill((255,255,255)) # fill background white
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.age = 0.0
        # -- menu --
        li = ["back"]
        for i in pygame.display.list_modes():
            # li is something like "(800, 600)"
            pair = str(i)
            comma = pair.find(",")
            x = pair[1:comma]
            y = pair[comma+2:-1]
            li.append(str(x)+"x"+str(y))
        Viewer.menu["resolution"] = li
        self.set_resolution()
        
        
        # ------ background images ------
        #self.backgroundfilenames = [] # every .jpg file in folder 'data'
        #try:
        #    for root, dirs, files in os.walk("data"):
        #        for file in files:
        #            if file[-4:] == ".jpg" or file[-5:] == ".jpeg":
        #                self.backgroundfilenames.append(file)
        #    random.shuffle(self.backgroundfilenames) # remix sort order
        #except:
        #    print("no folder 'data' or no jpg files in it")

        self.age = 0
        # ------ joysticks ----
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        for j in self.joysticks:
            j.init()
        self.prepare_sprites()
        self.loadbackground()
        #self.load_sounds()
        #self.world = World()
        #print(self.world)
        
        
    def load_sounds(self):
        pygame.mixer.music.load(os.path.join("data", "melody.ogg"))
        Viewer.sounds["click"]=  pygame.mixer.Sound(
                 os.path.join("data", "click1.wav"))
        Viewer.sounds["back"] =  pygame.mixer.Sound(
                 os.path.join("data", "click2.wav"))
        return
    
    
    def set_resolution(self):
        if Viewer.fullscreen:
             self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF|pygame.FULLSCREEN)
        else:
             self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.loadbackground()
    
    
    def loadbackground(self):
        
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.background.fill((64,64,64)) # fill background 
            
        self.background = pygame.transform.scale(self.background,
                          (Viewer.width,Viewer.height))
        self.background.convert()
        
    
  
    
    def load_sprites(self):
            """ all sprites that can rotate MUST look to the right. Edit Image files manually if necessary!"""
            print("loading sprites from 'data' folder....")
            #Viewer.images["catapult1"]= pygame.image.load(
            #     os.path.join("data", "catapultC1.png")).convert_alpha()
            
            ##self.create_selected("catapult1")
            
            #Viewer.images["cannon"] = pygame.image.load(os.path.join("data", "cannon.png"))
            Viewer.images["wizard"] = pygame.image.load(os.path.join(
                                      "data", "arch-mage.png"))
            Viewer.images["reptile"] = pygame.image.load(os.path.join(
                                       "data", "fighter.png"))
            Viewer.images["wizard-a"] = pygame.image.load(os.path.join(
                                      "data", "arch-mage-attack.png"))
            Viewer.images["reptile-a"] = pygame.image.load(os.path.join(
                                       "data", "fighter-attack.png"))
            Viewer.images["wolf"] = pygame.image.load(os.path.join(
                                        "data", "wolf.png"))
            Viewer.images["wolf-a"] = pygame.image.load(os.path.join(
                                        "data","wolf-attack.png"))
            Viewer.images["chest"] = pygame.image.load(os.path.join(
                                        "data", "chest-plain-closed.png"))
            Viewer.images["chest-a"] = pygame.image.load(os.path.join(
                                        "data", "chest-plain-open.png"))
            # --- boss images (scaled to be bigger) ---
            #Viewer.images["bosswolf"] = pygame.image.load(os.path.join(
            #                            "data", "bosswolf.png"))
            i = pygame.image.load(os.path.join(
                                        "data", "wolf.png"))
            Viewer.images["bosswolf"] = pygame.transform.scale(i, (150,150))
            i = pygame.image.load(os.path.join(
                                        "data","wolf-attack.png"))                                                    
            Viewer.images["bosswolf-a"] = pygame.transform.scale(i, (150,150))                                                    
                                    
            
     
    def prepare_sprites(self):
        """painting on the surface and create sprites"""
        self.load_sprites()
        self.allgroup =  pygame.sprite.LayeredUpdates() # for drawing
        self.flytextgroup = pygame.sprite.Group()
        #self.mousegroup = pygame.sprite.Group()
        
        self.bulletgroup = pygame.sprite.Group()
        self.playergroup = pygame.sprite.Group()
        self.rocketgroup = pygame.sprite.Group()
        self.enemygroup = pygame.sprite.Group()
        self.friendlygroup = pygame.sprite.Group()
        self.neutralgroup = pygame.sprite.Group()
        self.wallgroup = pygame.sprite.Group()
        self.missilegroup = pygame.sprite.Group()
        self.bargroup = pygame.sprite.Group()
        self.shopgroup = pygame.sprite.Group()
        VectorSprite.groups = self.allgroup
        Flytext.groups = self.allgroup, self.flytextgroup
        
        Shop.groups = self.allgroup, self.shopgroup
        #Cannon.groups = self.allgroup, self.playergroup
        #Bullet.groups = self.allgroup, self.bulletgroup
        #Rocket.groups = self.allgroup, self.rocketgroup
        Monster.groups = self.allgroup, self.enemygroup
        Wizard.groups = self.allgroup, self.friendlygroup
        #Wolf.groups = self.allgroup, self.enemygroup
        Wall.groups = self.allgroup, self.wallgroup
        Bar.groups = self.allgroup, self.bargroup
        Fireball.groups = self.allgroup, self.missilegroup
        #Catapult.groups = self.allgroup,
        #self.player1 =  Player(imagename="player1", warp_on_edge=True, pos=pygame.math.Vector2(Viewer.width/2-100,-Viewer.height/2))
        #self.player2 =  Player(imagename="player2", angle=180,warp_on_edge=True, pos=pygame.math.Vector2(Viewer.width/2+100,-Viewer.height/2))
        #self.cannon1 = Cannon(bounce_on_edge = True)
        #self.cannon2 = Cannon(bounce_on_edge = True)
        
        #self.enemy1 = Lizard(pos=pygame.math.Vector2(800,-250))
        #Lizard(pos=pygame.math.Vector2(300,-300))
   
    def menu_run(self):
        running = True
        pygame.mouse.set_visible(False)
        
        
        while running:
            
            #pygame.mixer.music.pause()
            milliseconds = self.clock.tick(self.fps) #
            seconds = milliseconds / 1000
            
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False # running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return True # running = False
                    
                    if event.key == pygame.K_d:
                        x = random.randint(0,Viewer.width)
                        y = random.randint(-Viewer.height, 0)
                        g = pygame.math.Vector2(0, -1.5)
                        #Gem(pos=pygame.math.Vector2(x,y),
                        #    max_age = 2)
                        Explosion(posvector=pygame.math.Vector2(x,y),
                                  shape="gem", gravity=g)
                        
                    
                    
                    if event.key == pygame.K_UP:
                        Viewer.cursor -= 1
                        Viewer.cursor = max(0, Viewer.cursor) # not < 0
                        #Viewer.menusound.play()
                        #Viewer.sounds["click"].play()
                    if event.key == pygame.K_DOWN:
                        Viewer.cursor += 1
                        Viewer.cursor = min(len(Viewer.menu[Viewer.name])-1,Viewer.cursor) # not > menu entries
                        #Viewer.menusound.play()
                        #Viewer.sounds["click"].play()
                    if event.key == pygame.K_RETURN:
                        text = Viewer.menu[Viewer.name][Viewer.cursor]
                        if text == "quit":
                            return False
                            #Viewer.menucommandsound.play()
                        elif text in Viewer.menu:
                            # changing to another menu
                            Viewer.history.append(text) 
                            Viewer.name = text
                            Viewer.cursor = 0
                            #Viewer.menuselectsound.play()
                        elif text == "resume":
                            return True
                            #Viewer.menucommandsound.play()
                            #pygame.mixer.music.unpause()
                        elif text == "back":
                            Viewer.history = Viewer.history[:-1] # remove last entry
                            Viewer.cursor = 0
                            Viewer.name = Viewer.history[-1] # get last entry
                            #Viewer.menucommandsound.play()
                            
                            # direct action
                        elif text == "credits":
                            Flytext(x=700, y=400, text="spielend-programmieren.at", fontsize = 100)  

                        elif text == "plant tomatoes":
                            #Viewer.gold += 1
                            # ----- Tomato Explosion ------
                            Explosion(red=0, green=220, blue=0, maxlifetime=5, maxspeed=250,
                                      green_delta=25, minangle=70, maxangle=110, gravity=pygame.math.Vector2(0,-5), 
                                      posvector=pygame.math.Vector2(random.randint(0, Viewer.width),-Viewer.height + 5)
                                      )
                        ### item to buy or sell. MUST have price in round brackets at the end, e.g. 'rusty sword (18)'
                        elif text[-1] == ")" and text.find("(") != -1:
                            pricepos = text.find("(")
                            try: 
                                price = int(text[pricepos+1:-1])
                                name = text[:pricepos]
                            except:
                                price is None
                            if price is not None:
                                if Viewer.name == "use":
                                   if "small health potion" in text:
                                       VectorSprite.numbers[1].hitpoints += 10
                                       Viewer.shopmenu["show inventory"].remove(text)
                                       Viewer.shopmenu["sell"].remove(text)
                                       Viewer.gamemenu["use"].remove(text)
                                   elif "medium health potion" in text:
                                       VectorSprite.numbers[1].hitpoints += 50
                                       Viewer.shopmenu["show inventory"].remove(text)
                                       Viewer.shopmenu["sell"].remove(text)
                                       Viewer.gamemenu["use"].remove(text)
                                   elif "big health potion" in text:
                                       VectorSprite.numbers[1].hitpoints += 100
                                       Viewer.shopmenu["show inventory"].remove(text)
                                       Viewer.shopmenu["sell"].remove(text)
                                       Viewer.gamemenu["use"].remove(text)
                                elif Viewer.name == "buy":
                                    if Viewer.gold < price:
                                        Flytext(text="not enough gold. You have {}. you need {}".format(Viewer.gold, price))
                                    else:
                                        Viewer.gold -= price
                                        Viewer.menu["show inventory"].append(text)
                                        Viewer.menu["sell"].append(text)
                                        if "potion" in text:
                                            Viewer.gamemenu["use"].append(text)
                                        else:
                                            Viewer.gamemenu["equip"].append(text)
                                elif Viewer.name == "sell":
                                    Viewer.gold += price
                                    Viewer.menu["show inventory"].remove(text)
                                    Viewer.menu["sell"].remove(text)
                                    if "potion" in text:
                                        Viewer.gamemenu["use"].remove(text)
                                    else:
                                        Viewer.gamemenu["equip"].remove(text)
                                    
                    
                        # ---------- submenus -------------
                        if Viewer.name == "resolution":
                            # text is something like '800x600'
                            t = text.find("x")
                            if t != -1:
                                x = int(text[:t])
                                y = int(text[t+1:])
                                Viewer.width = x
                                Viewer.height = y
                                self.set_resolution()
                                #Viewer.menucommandsound.play()
                        
                        elif Viewer.name == "tile size":
                            # text is something like "50x50"
                            t = text.find("x")
                            if t != -1:
                                x = int(text[:t])
                                y = int(text[t+1:])
                                if x == y:
                                    Viewer.tilesize = x
                                    print("setting grid size to ", x)
                                    # !!! Flytext als erstes Sprite....player soll erstes Sprite sein!
                                    #Flytext(text="set grid_size to {} x {}".format(Viewer.grid_size, Viewer.grid_size),
                                    #        max_age = 1)
                        
                        elif Viewer.name == "max. tiles x":
                            if text != Viewer.name:
                                print("text:", text)
                                Viewer.maxx = int(text)
                                print("setiing max. x tiles to", int(text))
                                
                        elif Viewer.name == "max. tiles y":
                            if text != Viewer.name:
                                Viewer.maxy = int(text)
                                print("setiing max. y tiles to", int(text))
                            
                        elif Viewer.name == "fullscreen":
                            if text == "true":
                                #Viewer.menucommandsound.play()
                                Viewer.fullscreen = True
                                self.set_resolution()
                            elif text == "false":
                                #Viewer.menucommandsound.play()
                                Viewer.fullscreen = False
                                self.set_resolution()
                        
            # ------delete everything on screen-------
            self.screen.blit(self.background, (0, 0))
            
            
         
            # -------------- UPDATE all sprites -------             
            #self.flytextgroup.update(seconds)
            self.allgroup.update(seconds)

            # ----------- clear, draw , update, flip -----------------
            self.allgroup.draw(self.screen)
            # --- paint gold ---
            write(self.screen, text="You have {} gold.".format(Viewer.gold),x=20, y=20, color=(200,200,0))
            # --- paint menu ----
            # ---- name of active menu and history ---
            write(self.screen, text="you are here:", x=200, y=50, color=(0,255,255))
            
            t = "main"
            for nr, i in enumerate(Viewer.history[1:]):
                #if nr > 0:
                t+=(" > ")
                t+=(i)
                #
            
            #t+=Viewer.name
            write(self.screen, text=t, x=200,y=70,color=(0,255,255))
            # --- menu items ---
            menu = Viewer.menu[Viewer.name]
            for y, item in enumerate(menu):
                write(self.screen, text=item, x=200, y=100+y*20, color=(255,255,255))
            # --- cursor ---
            write(self.screen, text="-->", x=100, y=100+ Viewer.cursor * 20, color=(255,255,255))
                        
                
            # -------- next frame -------------
            pygame.display.flip()
        #----------------------------------------------------- 
        return True 
    
    
    def paint_dungeon(self):
        # --- paint a 50 x 50 grid ----
        c = (128,128,128) # grey
        for x in range(0, Viewer.width+Viewer.tilesize, Viewer.tilesize):
            pygame.draw.line(self.screen, c, (x-Viewer.tilesize//2,0), (x-Viewer.tilesize//2, Viewer.height))
        for y in range(0, Viewer.height+Viewer.tilesize, Viewer.tilesize):
            pygame.draw.line(self.screen, c, (0, y-Viewer.tilesize//2), (Viewer.width, y-Viewer.tilesize//2))
        
    
  
    def create_level(self):
        # --- kill old walls ----
        for w in self.wallgroup:
            w.kill()
        # --- kill old shop ----
        for s in self.shopgroup:
            s.kill()
        # --- outer wall ---
        for x in range(0, Viewer.width, 50):
            WallBorder(pos=pygame.math.Vector2(x, 0))
        for y in range(50, Viewer.height, 50):
            WallBorder(pos=pygame.math.Vector2(0,-y))
        for x2 in range(0, x, 50):
            WallBorder(pos=pygame.math.Vector2(x2, -y-50))
        for y2 in range(0, Viewer.height, 50):
            WallBorder(pos=pygame.math.Vector2(x, -y2-50))
        # -------- random shop ------------
        sx = random.choice(range(50, Viewer.width-50,50))
        sy = random.choice(range(50, Viewer.height-50, 50))
        Shop(pos=pygame.math.Vector2(sx, -sy))
        
        # -------- random blocks ----------
        for x in range(50, Viewer.width-50, 50):
            for y in range(50, Viewer.height-50, 50):
                if x==sx and y == sy:
                    continue # no Wall on top of shop
                if random.random() < 0.15:
                    Wall(pos=pygame.math.Vector2(x,-y))
        
        # ---- create some random chests -----
        for x in range(50, Viewer.width-50, 50):
            for y in range(50, Viewer.height-50, 50):
                if random.random() < 0.05:
                    Chest(pos=pygame.math.Vector2(x, -y))
        
        # ---- create random enemies ------
        pool = ["wolf","wolf","wolf", "lizard"]
        for x in range(50, Viewer.width-50, 50):
            for y in range(50, Viewer.height-50, 50):
                # chance for a monster on this tile
                if x == -self.player1.pos.x and y == -self.player1.pos.y:
                    continue  # no monster on top of player
                if random.random() < 0.05:  # 5%
                    what = random.choice(pool)
                    if what=="wolf":
                        Wolf(pos=pygame.math.Vector2(x,-y))
                    if what=="lizard":
                        Lizard(pos=pygame.math.Vector2(x,-y))
        
        
        # --- no wall on players / enemies -----
        for w in self.wallgroup:
            if w.pos == self.player1.pos:
                w.kill()
            for e in self.enemygroup:
                if w.pos == e.pos:
                    w.kill()
    
    def run(self):
        """The mainloop"""
        
        running = True
        running = self.menu_run()
        self.player1 = Wizard(pos=pygame.math.Vector2(500,-200))
        #print("Wizard", self.player1.number)
        
        self.create_level()
        pygame.mouse.set_visible(True)
        oldleft, oldmiddle, oldright  = False, False, False
        loglines = 8
        turn = 0
        oldturn = 0
        self.level = 1
        self.boss_done = False
        
        #pygame.mixer.music.play(loops=-1)
        while running:
            #pygame.display.set_caption("player1 hp: {} player2 hp: {}".format(
            #                     self.player1.hitpoints, self.player2.hitpoints))
            
            if self.player1.hitpoints <= 0:
                running = False
            
            milliseconds = self.clock.tick(self.fps) #
            seconds = milliseconds / 1000
            self.age += seconds
            
            dx, dy = 0, 0
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        
                        #running = False
                        running = self.menu_run() 
                        
                    # --- spawn a boss -----
                    if event.key == pygame.K_e:
                        Boss(pos=pygame.math.Vector2(50,-50))
                    # --- move player 1 (wizard) -----
                  
                    if event.key == pygame.K_UP:
                        #self.player1.pos.y += 50
                        dy = 50
                        turn += 1
                        
                    elif event.key == pygame.K_DOWN:
                        #self.player1.pos.y -= 50
                        dy = -50
                        turn += 1
                        
                    elif event.key == pygame.K_RIGHT:
                        dx = 50
                        self.player1.lookright = True
                        turn += 1
                        
                        
                    elif event.key == pygame.K_LEFT:
                        dx = -50
                        self.player1.lookright = False
                        turn += 1
                    
                    
                    if event.key == pygame.K_f:
                        if self.player1.lookright:
                            x=50
                        else:
                            x=-50
                        self.player1.attack_animation()
                        Fireball(pos=pygame.math.Vector2(self.player1.pos.x, self.player1.pos.y),
                                 move=pygame.math.Vector2(x, 0))
                        turn += 1
                    
                    if event.key == pygame.K_b:
                        # --- create a block ----
                        if self.player1.lookright:
                            x=50
                        else:
                            x=-50
                        self.player1.attack_animation()
                        Wall(pos=pygame.math.Vector2(self.player1.pos.x + x,
                                                     self.player1.pos.y))
                        
                    
                    if event.key == pygame.K_PAGEUP:
                        loglines += 4
                    
                    if event.key == pygame.K_PAGEDOWN:
                        loglines -= 4
                        loglines = max(0, loglines) # not < 0
                    # --- attack for player1 -----
                    #if event.key == pygame.K_c:
                    #    self.player1.attack()
                        
                    # --- magic for player1 ----
                    if event.key == pygame.K_SPACE:
                        turn += 1
                        Flytext(pos=pygame.math.Vector2(self.player1.pos.x, self.player1.pos.y),
                                text="i wait a turn", move=pygame.math.Vector2(0,5), max_age=1)
                        
            # ---- check wall for moving player 1
            if dx != 0 or dy != 0:
                for w in self.wallgroup:
                    if w.pos.x == self.player1.pos.x + dx and w.pos.y==self.player1.pos.y + dy:
                        self.player1.attack_animation()
                        w.crack()
                        w.hitpoints -= random.randint(1,10)
                        direction = w.pos - self.player1.pos #- w.pos
                        direction.x *= -1 ## no idea why this is necessary, but it is
                        angle = direction.angle_to(pygame.math.Vector2(1,0))
                        # print("Angle:", angle)
                        Explosion(posvector = pygame.math.Vector2(
                                self.player1.pos.x + dx//2, self.player1.pos.y + dy//2),
                                red=w.color[0], green=w.color[1], blue=w.color[2],
                                minangle = angle-45, maxangle= angle+45)
                        dx , dy = 0, 0 # player must stop
                        break
                # ----- check enemy for moving player 1
                for s in self.shopgroup:
                    if (s.pos.x == self.player1.pos.x+dx and
                        s.pos.y == self.player1.pos.y + dy):
                        dx, dy =0, 0
                        #self.player1.hitpoints += 10
                        
                        Flytext(pos=pygame.math.Vector2(self.player1.pos.x,
                                    self.player1.pos.y),
                                move=pygame.math.Vector2(0,22),
                                text="shopping")
                        Viewer.menu = Viewer.shopmenu
                        Viewer.gold = VectorSprite.numbers[1].gold
                        running = self.menu_run() 
                        VectorSprite.numbers[1].gold = Viewer.gold
                        Viewer.menu = Viewer.gamemenu
                for e in self.enemygroup:
                    
                    if e.pos.x == self.player1.pos.x + dx and e.pos.y==self.player1.pos.y + dy:
                        
                        ## fight
                        e.on_event("attacked")
                        e.tired -= 20 
                        fight(self.player1, e)
                        Explosion(posvector = pygame.math.Vector2(
                                self.player1.pos.x + dx//2, self.player1.pos.y + dy//2))
                        dx , dy = 0, 0 # player must stop
                        break
                
                # ---- move the player -----
                self.player1.pos.x += dx
                self.player1.pos.y += dy
                        
            # ------------ move the (hostile) monsters -----
            if turn > oldturn:
                for e in self.enemygroup:
                    e.ai()
                    # wall ?
                    for w in self.wallgroup:
                       if e.pos.x + e.dx == w.pos.x and e.pos.y + e.dy == w.pos.y:
                           e.dx, e.dy = 0, 0
                           break
                    # other (hostile) monster ?
                    for e2 in self.enemygroup:
                        if e2.number == e.number:
                            continue
                        if e.pos.x + e.dx == e2.pos.x and e.pos.y + e.dy == e2.pos.y:
                            e.dx, e.dy = 0, 0
                            break 
                        # player ?
                    if e.pos.x + e.dx == self.player1.pos.x and e.pos.y + e.dy == self.player1.pos.y:
                        fight(e, self.player1)
                        e.dx, e.dy = 0, 0
                    # ---- move the monster ------
                    e.pos.x += e.dx
                    e.pos.y += e.dy
                        
                    
            # ---------------        
            oldturn = turn        
            # ------------ pressed keys ------
            pressed_keys = pygame.key.get_pressed()
            # -------- exit game with ctrl + q ? -------
            if pressed_keys[pygame.K_LCTRL] and pressed_keys[pygame.K_q]:
                running = False
        
            # ------ mouse handler ------
            left,middle,right = pygame.mouse.get_pressed()
            oldleft, oldmiddle, oldright = left, middle, right

            # ------ joystick handler -------
            for number, j in enumerate(self.joysticks):
                if number == 0:
                    player = self.cannon1
                else:
                    continue
                x = j.get_axis(0)
                y = j.get_axis(1)
                #if y > 0.2:
                #    player.forward(-1)
                #if y < -0.8:
                #    player.forward(15)
                #elif y < -0.5:
                #    player.forward(10)
                #elif y <  -0.2:
                #    player.forward(5)
                
                #if x > 0.2:
                #    player.rotate(-5)
                #if x < -0.2:
                #    player.rotate(5)
                
                buttons = j.get_numbuttons()
                for b in range(buttons):
                    pushed = j.get_button( b )
                    #if b == 0 and pushed:
                    #     player.fire()
                    #if b == 1 and pushed:
                    #    t = random.choice((self.cannon2,
                    #                       self.cannon3))
                    #    player.launch(t)
                
              
            # =========== delete everything on screen ==============
            self.screen.blit(self.background, (0, 0))
            self.paint_dungeon()
            # ----trails for rockets------
            #for r in self.rocketgroup:
            #    if len(r.trail) > 1:
            #        for rank, (x,y) in enumerate(r.trail):
            #            if rank > 0:
            #                pygame.draw.line(self.screen, r.color,
            #                   (x,y), (old[0], old[1]),(rank // 10))
            #            old = (x,y)
            
            ##self.paint_world()
                       
            # write text below sprites
           
            # ----- collision detection between fireball and wall---
            for w in self.wallgroup:
                if w.pos == pygame.math.Vector2(0,0):
                    continue # unnötige Borderwall
                crashgroup=pygame.sprite.spritecollide(w,
                           self.missilegroup, False, 
                           pygame.sprite.collide_rect)
                for o in crashgroup:
                    Explosion(posvector = o.pos)
                    o.kill()
            
            # ----- collision detection between fireball and wolf---
            for e in self.enemygroup:
                crashgroup=pygame.sprite.spritecollide(e,
                           self.missilegroup, False, 
                           pygame.sprite.collide_mask)
                for o in crashgroup:
                     #if o.boss.number == p.number:
                     #    continue
            #        #elastic_collision(o, p)
                     Explosion(posvector=o.pos)
                     o.kill()
                     e.hitpoints -= 1
            #        # p.hitpoints -= 1
            
                
            
           
            # ================ UPDATE all sprites =====================
            self.allgroup.update(seconds)
            # --- all enemys must look to player ----
            for e in self.enemygroup:
                if e.pos.x < self.player1.pos.x:
                    e.lookright = True
                elif e.pos.x > self.player1.pos.x:
                    e.lookright = False
            
            # ---- level finished ? ------
            #print("Monsters left:", len(self.enemygroup))
            if len(self.enemygroup) == 0:
                # -- time for a boss ? ----
                if not self.boss_done:
                    for y in range(self.level):
                        Boss(pos=pygame.math.Vector2(150,-100-50 * y))
                    self.boss_done = True
                else:
                    Flytext(pos=pygame.math.Vector2(Viewer.width//2, -Viewer.height),
                            move=pygame.math.Vector2(0, 25), text="level {} cleared".format(self.level),
                            fontsize = 128, max_lifetime=5)
                    # 5 sec pause
                    self.level += 1
                    self.create_level()
                    self.boss_done = False

            # ----------- clear, draw , update, flip -----------------
            self.allgroup.draw(self.screen)
            #print(self.allgroup)
            # ----- FPS -----
            write(self.screen, "FPS: {:8.3}".format(
                self.clock.get_fps() ), x=Viewer.width-200, y=10, color=(0,255,0), fontsize=12)
            
            write(self.screen, "gold: {}".format(
                  VectorSprite.numbers[1].gold), 
                  x=Viewer.width - 300, y=10, 
                  color=(255,255,0),
                  fontsize = 24)
            
            # ----- log ------
            for i in range(-loglines, 0):
                try:
                    textcolor, line = Viewer.log[i]
                except:
                    continue
                write(self.screen, line, x=Viewer.width // 2, y=Viewer.height + i*10, color=textcolor, fontsize=12)
            
           
                
            # -------- next frame -------------
            pygame.display.flip()
        #-----------------------------------------------------
        for line in Viewer.log:
            print(line[1])
        pygame.mouse.set_visible(True)    
        pygame.quit()

if __name__ == '__main__':
    Viewer(1430,800).run()
