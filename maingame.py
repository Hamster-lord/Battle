"""
still not sure how collision should work in final (now main problem is when in melee combat and another unit can snuck in with rotate will finalised this after big map update 0.4+)
## Known problem
battalion sometimes go through enemy sprite to the pos center
Hitbox still behave weirdly in melee combat
Optimise list
maybe best remove all for loop in main and move them to update
remove index and change call to the sprite itself
"""
import ast
import csv
import glob
import os
import os.path
import random
import re
import datetime

import numpy as np
import pygame
import pygame.freetype
from pygame.locals import *
from pygame.transform import scale

from RTS import mainmenu
from RTS.script import gamesquad, gamebattalion, gameui, gameleader, gamemap, gamecamera, rangeattack, gamepopup, gamedrama, gamemenu, gamelongscript, gamelorebook, gameweather

config = mainmenu.config
SoundVolume = mainmenu.SoundVolume
SCREENRECT = mainmenu.SCREENRECT
main_dir = mainmenu.main_dir


def load_image(file, subfolder=""):
    """loads an image, prepares it for play"""
    file = os.path.join(main_dir, 'data', subfolder, file)
    try:
        surface = pygame.image.load(file).convert_alpha()
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pygame.get_error()))
    return surface.convert_alpha()


def load_images(subfolder=[], loadorder=True, returnorder=False):
    """loads all images(files) in folder using loadorder list file use only png file"""
    imgs = []
    dirpath = os.path.join(main_dir, 'data')
    if subfolder != []:
        for folder in subfolder:
            dirpath = os.path.join(dirpath, folder)
    if loadorder:
        loadorderfile = open(dirpath + "/load_order.txt", "r")
        loadorderfile = ast.literal_eval(loadorderfile.read())
        for file in loadorderfile:
            imgs.append(load_image(dirpath + "/" + file))
    else:
        loadorderfile = [f for f in os.listdir(dirpath) if f.endswith('.' + "png")]  ## read all file
        loadorderfile.sort(key=lambda var: [int(x) if x.isdigit() else x for x in re.findall(r'[^0-9]|[0-9]+', var)])
        for file in loadorderfile:
            imgs.append(load_image(dirpath + "/" + file))
    if returnorder == False:
        return imgs
    else:
        loadorderfile = [int(name.replace(".png", "")) for name in loadorderfile]
        return imgs, loadorderfile

def csv_read(file, subfolder=[], outputtype=0):
    """output type 0 = dict, 1 = list"""
    returnoutput = {}
    if outputtype == 1: returnoutput = []
    folderlist = ""
    for folder in subfolder:
        folderlist += "\\" + folder
    folderlist += "\\" + file
    with open(main_dir + folderlist, 'r') as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        for row in rd:
            for n, i in enumerate(row):
                if i.isdigit() or "-" in i:
                    row[n] = int(i)
            if outputtype == 0:
                returnoutput[row[0]] = row[1:]
            elif outputtype == 1:
                returnoutput.append(row)
        unitfile.close()
    return returnoutput

def load_sound(file):
    file = os.path.join(main_dir, "data/sound/", file)
    sound = pygame.mixer.Sound(file)
    return sound


def addarmy(squadlist, position, gameid, colour, imagesize, leader, leaderstat, unitstat, control, coa, command=False, startangle=0):
    squadlist = squadlist[~np.all(squadlist == 0, axis=1)]
    squadlist = squadlist[:, ~np.all(squadlist == 0, axis=0)]
    army = gamebattalion.Unitarmy(startposition=position, gameid=gameid,
                                  squadlist=squadlist, imgsize=imagesize,
                                  colour=colour, control=control, coa=coa, commander=command, startangle=startangle)
    army.hitbox = [gamebattalion.Hitbox(army, 0, army.rect.width - 10, 2),
                   gamebattalion.Hitbox(army, 1, 2, army.rect.height - 10),
                   gamebattalion.Hitbox(army, 2, 2, army.rect.height - 10),
                   gamebattalion.Hitbox(army, 3, army.rect.width - 10, 2)]
    army.leader = [gameleader.Leader(leader[0], leader[4], 0, army, leaderstat),
                   gameleader.Leader(leader[1], leader[5], 1, army, leaderstat),
                   gameleader.Leader(leader[2], leader[6], 2, army, leaderstat),
                   gameleader.Leader(leader[3], leader[7], 3, army, leaderstat)]
    return army


def unitsetup(playerarmy, enemyarmy, battle, imagewidth, imageheight, allweapon, allarmour, allleader, gameunitstat, coa, squad, inspectuipos,
              enactment=False):
    """squadindexlist is list of every squad index in the game for indexing the squad group"""
    # defaultarmy = np.array([[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]])
    letterboard = ("a", "b", "c", "d", "e", "f", "g", "h")
    numberboard = ("8", "7", "6", "5", "4", "3", "2", "1")
    boardpos = []
    for dd in numberboard:
        for ll in letterboard:
            boardpos.append(ll + dd)
    squadindexlist = []
    unitlist = []
    playercolour = (144, 167, 255)
    enemycolour = (255, 114, 114)
    """army num is list index for battalion in either player or enemy group"""
    playerstart, enemystart = 0, 0
    """squadindex is list index for all squad group"""
    squadindex = 0
    """firstsquad check if it the first ever in group"""
    squadgameid = 10000
    with open(main_dir + "\data" + "\map" + battle + "\\unit_pos.csv", 'r') as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        for row in rd:
            for n, i in enumerate(row):
                if i.isdigit():
                    row[n] = int(i)
                if n in range(1, 12):
                    row[n] = [int(item) if item.isdigit() else item for item in row[n].split(',')]
            if row[0] < 2000:
                if row[0] == 1:
                    """First player battalion as commander"""
                    army = addarmy(np.array([row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]), (row[9][0], row[9][1]), row[0],
                                   playercolour,
                                   (imagewidth, imageheight), row[10] + row[11], allleader, gameunitstat, True, coa[row[12]], True,
                                   startangle=row[13])
                else:
                    army = addarmy(np.array([row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]), (row[9][0], row[9][1]), row[0],
                                   playercolour, (imagewidth, imageheight), row[10] + row[11], allleader, gameunitstat, True, coa[row[12]],
                                   startangle=row[13])
                playerarmy.append(army)
                playerstart += 1
            elif row[0] >= 2000:
                if row[0] == 2000:
                    """First enemy battalion as commander"""
                    army = addarmy(np.array([row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]), (row[9][0], row[9][1]), row[0],
                                   enemycolour,
                                   (imagewidth, imageheight), row[10] + row[11], allleader, gameunitstat, enactment, coa[row[12]], True,
                                   startangle=row[13])
                elif row[0] > 2000:
                    army = addarmy(np.array([row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]), (row[9][0], row[9][1]), row[0],
                                   enemycolour,
                                   (imagewidth, imageheight), row[10] + row[11], allleader, gameunitstat, enactment, coa[row[12]], startangle=row[13])
                enemyarmy.append(army)
                enemystart += 1
            """armysquadindex is list index for squad list in a specific army"""
            armysquadindex = 0
            """Setup squad in army to squad group"""
            for squadnum in np.nditer(army.armysquad, op_flags=['readwrite'], order='C'):
                if squadnum != 0:
                    addsquad = gamesquad.Unitsquad(unitid=squadnum, gameid=squadgameid, weaponlist=allweapon, armourlist=allarmour,
                                                   statlist=gameunitstat,
                                                   battalion=army, position=army.squadpositionlist[armysquadindex], inspectuipos=inspectuipos)
                    squad.append(addsquad)
                    addsquad.boardpos = boardpos[armysquadindex]
                    squadnum[...] = squadgameid
                    army.squadsprite.append(addsquad)
                    squadindexlist.append(squadgameid)
                    squadgameid += 1
                    squadindex += 1
                armysquadindex += 1
    unitfile.close()
    return squadindexlist


class Battle():
    def __init__(self, winstyle):
        # Initialize pygame
        pygame.init()
        if pygame.mixer and not pygame.mixer.get_init():
            pygame.mixer = None
        # Set the display mode
        self.bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
        self.screen = pygame.display.set_mode(SCREENRECT.size, winstyle | pygame.RESIZABLE, self.bestdepth)
        # for when implement game and map camera
        # self.battle_surf = pygame.surface.Surface(width, height)
        # in your main loop
        # or however you draw your sprites
        # your_sprite_group.draw(game_surf)
        # then blit to screen
        # self.screen.blit(self.battle_surf, the_position)
        # Load images, assign to sprite classes
        # (do this before the classes are used, after screen setup)
        ## create game map
        featurelist = ["Grassland","Draught","Bushland","Forest","Inland Water","Road","Building","Farm","Pandemonium","Mana Flux","Creeping Rot","Mud","Savanna","Draught","Tropical Shrubland","Jungle","Inland Water","Road","Building","Farm","Pandemonium","Heat Mana","Creeping Rot","Mud","Volcanic Soil","Scorched Land","","","","Road","","Fertile Farm","Pandemonium","Fire Mana","Creeping Rot","","Desert Plain","Desert Sand","Desert Shrubland","Desert Forest","Oasis","Sand Road","Desert Dwelling","Desert Farm","Pandemonium","Earth Mana","Creeping Rot","Quicksand","Snow","Tundra","Arctic Shrubland","Arctic Forest","Frozen Water","Snow Road","Warm Shelter","Arctic Farm","Pandemonium","Ice Mana","Preserving Rot","Ice Ground","","","","","Poisoned Water","","","","Pandemonium","Poisoned Mana","Creeping Rot","","","Void","","","","","","","","Leyline","Creeping Rot","","","","","","","","","","Pandemonium","","Creeping Rot","","","","","","","","","","Pandemonium","","Rotten Land","","Lively Water","Empty Water","Marsh","Swamp","Water","Bridge","Swamp Building","Swamp Farm","Pandemonium","Cold Mana","Creeping Rot","","Sea","Ocean","Coral Reef","Underwater Forest","Fresh Water","Bridge","Sunken City","Fishery","Pandemonium","Water Mana","Creeping Rot",""]
        self.mapselected = "testmap"
        imgs = load_images(['map', self.mapselected],loadorder=False)
        gamemap.Basemap.images = [imgs[0]]
        gamemap.Mapfeature.images = [imgs[1]]
        gamemap.Mapheight.images = [imgs[2]]
        gamemap.Beautifulmap.placename = imgs[3]
        img = load_image('effect.png', 'map')
        gamemap.Beautifulmap.effectimage = img
        empty = load_image('empty.png', 'map/texture')
        maptexture = []
        loadtexturefolder = []
        for feature in featurelist:
            loadtexturefolder.append(feature.replace(" ", "").lower())
        loadtexturefolder = list(set(loadtexturefolder))
        loadtexturefolder = [item for item in loadtexturefolder if item != ""] ## For now remove terrain with no planned name/folder yet
        for index, texturefolder in enumerate(loadtexturefolder):
            imgs = load_images(['map','texture', texturefolder], loadorder=False)
            maptexture.append(imgs)
        gamemap.Beautifulmap.textureimages = maptexture
        gamemap.Beautifulmap.loadtexturelist = loadtexturefolder
        gamemap.Beautifulmap.emptyimage = empty
        ## create unit
        imgsold = load_images(['war', 'unit_ui'])
        imgs = []
        for img in imgsold:
            # x, y = img.get_width(), img.get_height()
            # img = pygame.transform.scale(img, (int(x),int(y/2)))
            imgs.append(img)
        gamesquad.Unitsquad.images = imgs
        self.imagewidth, self.imageheight = imgs[0].get_width(), imgs[0].get_height()
        imgs = []
        imgsold = load_images(['war', 'unit_ui', 'battalion'])
        for img in imgsold:
            imgs.append(img)
        gamebattalion.Unitarmy.images = imgs
        imgsold = load_images(['war', 'unit_ui', 'weapon'])
        imgs = []
        for img in imgsold:
            x, y = img.get_width(), img.get_height()
            img = pygame.transform.scale(img, (int(x / 1.7), int(y / 1.7)))
            imgs.append(img)
        self.allweapon = gamebattalion.Weaponstat(imgs)  ## create weapon class
        imgs = load_images(['ui','battlemenu_ui'],loadorder=False)
        gamemenu.Menubox.images = imgs ## Create ESC Menu box
        imgs = load_images(['war', 'unit_ui', 'armour'])
        self.allarmour = gamebattalion.Armourstat(imgs)  ## create armour class
        self.statusimgs = load_images(['ui', 'status_icon'], loadorder=False)
        self.roleimgs = load_images(['ui', 'role_icon'], loadorder=False)
        self.traitimgs = load_images(['ui', 'trait_icon'], loadorder=False)
        self.skillimgs = load_images(['ui', 'skill_icon'], loadorder=False)
        cooldown = pygame.Surface((self.skillimgs[0].get_width(), self.skillimgs[0].get_height()), pygame.SRCALPHA)
        cooldown.fill((230,70,80,200))
        activeskill = pygame.Surface((self.skillimgs[0].get_width(), self.skillimgs[0].get_height()), pygame.SRCALPHA)
        activeskill.fill((170,220,77,200))
        gameui.Skillcardicon.activeskill = activeskill
        gameui.Skillcardicon.cooldown = cooldown
        self.gameunitstat = gamebattalion.Unitstat()
        ## create leader list
        imgs, order = load_images(['leader', 'historic', 'portrait'],loadorder=False, returnorder=True)
        self.allleader = gameleader.Leaderdata(imgs, order, option="\historic")
        ## coa imagelist
        imgsold = load_images(['leader', 'historic', 'coa'])
        imgs = []
        for img in imgsold:
            imgs.append(img)
        self.coa = imgs
        ## Weather list
        self.allweather = csv_read('weather.csv', ['data','map','weather'])
        self.weathermatterimgs = []
        for weather in ('0','1','2','3'): ## Load weather matter sprite image
            imgs = load_images(['map','weather',weather],loadorder=False)
            self.weathermatterimgs.append(imgs)
        self.weathereffectimgs = []
        for weather in ('0','1','2','3'): ## Load weather effect sprite image
            imgsold = load_images(['map','weather','effect',weather],loadorder=False)
            imgs = []
            for img in imgsold:
                img = pygame.transform.scale(img, (int(SCREENRECT.width), SCREENRECT.height))
                imgs.append(img)
            self.weathereffectimgs.append(imgs)
        imgs = load_images(['map', 'weather', 'icon'], loadorder=False) ## Load weather icon
        gameweather.Weather.images = imgs
        ## Game Effect
        imgs = load_images(['effect'])
        # imgs = []
        # for img in imgsold:
            # x, y = img.get_width(), img.get_height()
            # img = pygame.transform.scale(img, (int(x ), int(y / 2)))
            # imgs.append(img)
        self.gameeffect = imgs
        rangeattack.Rangearrow.images = [self.gameeffect[0]]
        ## Popup Ui
        imgs =  load_images(['ui','popup_ui','terraincheck'], loadorder=False)
        gamepopup.Terrainpopup.images = imgs
        imgs = load_images(['ui', 'popup_ui', 'dramatext'], loadorder=False)
        gamedrama.Textdrama.images = imgs
        # decorate the game window
        # icon = load_image('sword.jpg')
        # icon = pygame.transform.scale(icon, (32, 32))
        # pygame.display.set_icon(icon)
        pygame.display.set_caption('Masendor RTS')
        pygame.mouse.set_visible(1)
        # #load the sound effects
        # boom_sound = load_sound('boom.wav')
        # shoot_sound = load_sound('car_door.wav')
        """Random music played from list"""
        if pygame.mixer:
            self.SONG_END = pygame.USEREVENT + 1
            # musiclist = os.path.join(main_dir, 'data/sound/')
            self.musiclist = glob.glob(main_dir + '/data/sound/*.mp3')
            self.pickmusic = random.randint(1, 1)
            pygame.mixer.music.set_endevent(self.SONG_END)
            pygame.mixer.music.load(self.musiclist[self.pickmusic])
            pygame.mixer.music.play(0)
        """Initialize Game Groups"""
        self.allcamera = pygame.sprite.LayeredUpdates() ## the layer is as followed 0 = terrain map, 1 = dead army, 2 = map special feature, 3 = hitbox, 4 = direction arrow, 5 = battalion, 6 = flying battalion, 7 = arrow/range, 8 = weather, 9 = weather matter, 10 = ui/button, 11 = squad inspect, 12 pop up
        self.allui = pygame.sprite.LayeredUpdates()
        self.unitupdater = pygame.sprite.Group()
        self.uiupdater = pygame.sprite.Group()
        self.weatherupdater = pygame.sprite.Group()
        self.effectupdater = pygame.sprite.Group()
        self.battlemap = pygame.sprite.Group()
        self.battlemapfeature = pygame.sprite.Group()
        self.battlemapheight = pygame.sprite.Group()
        self.showmap = pygame.sprite.Group()
        self.playerarmy = pygame.sprite.Group()
        self.enemyarmy = pygame.sprite.Group()
        self.squad = pygame.sprite.Group()
        self.armyleader = pygame.sprite.Group()
        self.hitboxs = pygame.sprite.Group()
        self.arrows = pygame.sprite.Group()
        self.directionarrows = pygame.sprite.Group()
        self.deadunit = pygame.sprite.Group()
        self.gameui = pygame.sprite.Group()
        self.minimap = pygame.sprite.Group()
        self.eventlog = pygame.sprite.Group()
        self.logscroll = pygame.sprite.Group()
        self.buttonui = pygame.sprite.Group()
        self.lorebuttonui = pygame.sprite.Group()
        self.squadselectedborder = pygame.sprite.Group()
        self.fpscount = pygame.sprite.Group()
        self.switchbuttonui = pygame.sprite.Group()
        self.terraincheck = pygame.sprite.Group()
        self.buttonnamepopup = pygame.sprite.Group()
        self.leaderpopup = pygame.sprite.Group()
        self.effectpopup = pygame.sprite.Group()
        self.traiticon = pygame.sprite.Group()
        self.skillicon = pygame.sprite.Group()
        self.effecticon = pygame.sprite.Group()
        self.textdrama = pygame.sprite.Group()
        self.battlemenu = pygame.sprite.Group()
        self.battlemenubutton = pygame.sprite.Group()
        self.optionmenubutton = pygame.sprite.Group()
        self.lorebook = pygame.sprite.Group()
        self.lorebookbutton = pygame.sprite.Group()
        self.slidermenu = pygame.sprite.Group()
        self.valuebox = pygame.sprite.Group()
        self.armyselector = pygame.sprite.Group()
        self.armyicon = pygame.sprite.Group()
        self.selectscroll = pygame.sprite.Group()
        self.timeui = pygame.sprite.Group()
        self.timenumber = pygame.sprite.Group()
        self.speednumber = pygame.sprite.Group()
        self.lorenamelist = pygame.sprite.Group()
        self.subsectionname = pygame.sprite.Group()
        self.weathermatter = pygame.sprite.Group()
        self.weathereffect = pygame.sprite.Group()
        """assign default groups"""
        gamemap.Basemap.containers = self.battlemap
        gamemap.Mapfeature.containers = self.battlemapfeature
        gamemap.Mapheight.containers = self.battlemapheight
        gamemap.Beautifulmap.containers = self.showmap, self.allcamera
        gamebattalion.Unitarmy.containers = self.playerarmy, self.enemyarmy, self.unitupdater, self.squad, self.allcamera
        gamesquad.Unitsquad.containers = self.playerarmy, self.enemyarmy, self.unitupdater, self.squad
        gamebattalion.Deadarmy.containers = self.deadunit, self.unitupdater, self.allcamera
        gamebattalion.Hitbox.containers = self.hitboxs, self.unitupdater, self.allcamera
        gameleader.Leader.containers = self.armyleader, self.unitupdater
        rangeattack.Rangearrow.containers = self.arrows, self.effectupdater, self.allcamera
        gamebattalion.Directionarrow.containers = self.directionarrows, self.effectupdater, self.allcamera
        gameui.Gameui.containers = self.gameui, self.uiupdater
        gameui.Minimap.containers = self.minimap, self.allui
        gameui.FPScount.containers = self.allui
        gameui.Uibutton.containers = self.buttonui, self.lorebuttonui
        gameui.Switchuibutton.containers = self.switchbuttonui, self.uiupdater
        gameui.Selectedsquad.containers = self.squadselectedborder
        gameui.Skillcardicon.containers = self.traiticon, self.skillicon, self.allui
        gameui.Effectcardicon.containers = self.effecticon, self.allui
        gameui.Eventlog.containers = self.eventlog, self.allui
        gameui.Uiscroller.containers = self.logscroll, self.selectscroll, self.allui
        gameui.Armyselect.containers = self.armyselector, self.allui
        gameui.Armyicon.containers = self.armyicon, self.allui
        gameui.Timeui.containers = self.timeui, self.allui
        gameui.Timer.containers = self.timenumber, self.allui
        gameui.Speednumber.containers = self.speednumber, self.allui
        gamepopup.Terrainpopup.containers = self.terraincheck
        gamepopup.Onelinepopup.containers = self.buttonnamepopup, self.leaderpopup
        gamepopup.Effecticonpopup.containers = self.effectpopup
        gamedrama.Textdrama.containers = self.textdrama
        gamemenu.Menubox.containers = self.battlemenu
        gamemenu.Menubutton.containers = self.battlemenubutton, self.optionmenubutton
        gamemenu.Slidermenu.containers = self.slidermenu
        gamemenu.Valuebox.containers = self.valuebox
        gamelorebook.Lorebook.containers = self.lorebook
        gamelorebook.Subsectionlist.containers = self.lorenamelist
        gamelorebook.Subsectionname.containers = self.subsectionname
        gameweather.Mattersprite.containers = self.weathermatter, self.allui, self.weatherupdater
        gameweather.Specialeffect.containers = self.weathereffect, self.allui, self.weatherupdater
        ## create the background map
        self.camerapos = pygame.Vector2(500,500) ## Camera pos at the current zoom
        self.basecamerapos = pygame.Vector2(500,500) ## Camera pos at furthest zoom for recalculate sprite pos after zoom
        self.camerascale = 1 ## Camera zoom
        self.battlemap = gamemap.Basemap(self.camerascale)
        self.battlemapfeature = gamemap.Mapfeature(self.camerascale)
        self.battlemapheight = gamemap.Mapheight(self.camerascale)
        self.showmap = gamemap.Beautifulmap(self.camerascale, self.battlemap, self.battlemapfeature, self.battlemapheight)
        del gamemap.Beautifulmap.textureimages ## remove texture image list to clear memory
        gamebattalion.Unitarmy.gamemap = self.battlemap ## add battle map to all battalion class
        gamebattalion.Unitarmy.gamemapfeature = self.battlemapfeature  ## add battle map to all battalion class
        gamebattalion.Unitarmy.gamemapheight = self.battlemapheight
        gamebattalion.Unitarmy.statuslist = self.gameunitstat.statuslist
        self.camera = gamecamera.Camera(self.camerapos, self.camerascale)
        self.background = pygame.Surface(SCREENRECT.size)
        self.background.fill((255,255,255))
        # pygame.display.flip()
        """Create Starting Values"""
        self.enactment = True
        self.gamestate = 1
        self.timer = 0
        self.uitimer = 0
        self.dramatimer = 0
        self.dt = 0 ## Used for in game calculation
        self.uidt = 0 ## Used for ui timer
        self.combattimer = 0
        self.clock = pygame.time.Clock()
        self.lastmouseover = 0
        self.gamespeed = 1
        self.gamespeedset = (0,0.5,1,2,4,6)
        self.clickcheck = 0  ## For checking if unit or ui is clicked
        self.clickcheck2 = 0  ##  For checking if another unit is clicked when inspect ui open"
        self.inspectui = 0
        self.lastselected = None
        self.mapviewmode = 0
        self.mapshown = self.showmap
        self.squadlastselected = None
        self.beforeselected = None
        self.splithappen = False
        self.splitbutton = False
        self.currentweather = None
        self.weatherscreenadjust = SCREENRECT.width / SCREENRECT.height
        self.splitunit = gamelongscript.splitunit
        self.die = gamelongscript.die
        self.leadernow = []
        self.rightcorner = SCREENRECT.width - 5
        self.bottomcorner = SCREENRECT.height - 5
        self.centerscreen = [SCREENRECT.width / 2, SCREENRECT.height / 2]
        self.battlemousepos = [0,0]
        """use same position as squad front index 0 = front, 1 = left, 2 = rear, 3 = right"""
        self.battlesidecal = [1, 0.5, 0.1, 0.5]
        """create game ui"""
        self.minimap = gameui.Minimap(SCREENRECT.width, SCREENRECT.height, self.showmap.trueimage, self.camera)
        topimage = load_images(['ui', 'battle_ui'])
        iconimage = load_images(['ui', 'battle_ui', 'topbar_icon'])
        self.armyselector = gameui.Armyselect((0,0), topimage[30])
        self.selectscroll = gameui.Uiscroller(self.armyselector.rect.topright, topimage[30].get_height(), self.armyselector.maxrowshow)
        self.gameui = [
            gameui.Gameui(screen=self.screen, X=SCREENRECT.width - topimage[0].get_size()[0] / 2, Y=topimage[0].get_size()[1] / 2, image=topimage[0],
                          icon=iconimage, uitype="topbar")]
        iconimage = load_images(['ui', 'battle_ui', 'commandbar_icon'])
        self.gameui.append(
            gameui.Gameui(screen=self.screen, X=topimage[1].get_size()[0] / 2, Y=(topimage[1].get_size()[1] / 2)+ self.armyselector.image.get_height(), image=topimage[1], icon=iconimage,
                          uitype="commandbar"))
        iconimage = load_images(['ui', 'battle_ui', 'unitcard_icon'])
        self.gameui.append(
            gameui.Gameui(screen=self.screen, X=SCREENRECT.width - topimage[2].get_size()[0] / 2, Y=SCREENRECT.height - 310, image=topimage[2],
                          icon="", uitype="unitcard"))
        self.gameui[2].featurelist = featurelist
        self.gameui.append(
            gameui.Gameui(screen=self.screen, X=SCREENRECT.width - topimage[5].get_size()[0] / 2, Y=topimage[0].get_size()[1] + 150,
                          image=topimage[5], icon="", uitype="armybox"))
        self.popgameui = self.gameui
        self.timeui = gameui.Timeui(self.armyselector.rect.topright, topimage[31])
        self.timenumber = gameui.Timer(self.timeui.rect.topleft)
        self.speednumber = gameui.Speednumber((self.timeui.rect.center[0]+40, self.timeui.rect.center[1]), self.gamespeed)
        self.buttonui = [gameui.Uibutton(self.gameui[2].X - 152, self.gameui[2].Y + 10, topimage[3], 0),
                         gameui.Uibutton(self.gameui[2].X - 152, self.gameui[2].Y - 70, topimage[4], 1),
                         gameui.Uibutton(self.gameui[2].X - 152, self.gameui[2].Y - 30, topimage[7], 2),
                         gameui.Uibutton(self.gameui[2].X - 152, self.gameui[2].Y + 50, topimage[22], 3),
                         gameui.Uibutton(self.gameui[0].X - 206, self.gameui[0].Y-1, topimage[6], 1),
                         gameui.Uibutton(self.gameui[1].X - 115, self.gameui[1].Y + 26, topimage[8], 0),
                         gameui.Uibutton(self.gameui[1].X - 115, self.gameui[1].Y + 56, topimage[9], 1),
                         gameui.Uibutton(self.gameui[1].X - 115, self.gameui[1].Y + 96, topimage[14], 1)]
        self.switchbuttonui = [gameui.Switchuibutton(self.gameui[1].X - 70, self.gameui[1].Y + 96, topimage[10:14]),
                               gameui.Switchuibutton(self.gameui[1].X - 30, self.gameui[1].Y + 96, topimage[15:17]),
                               gameui.Switchuibutton(self.gameui[1].X, self.gameui[1].Y + 96, topimage[17:20]),
                               gameui.Switchuibutton(self.gameui[1].X + 40, self.gameui[1].Y + 96, topimage[20:22])]
        self.eventlog = gameui.Eventlog(topimage[23], (0, SCREENRECT.height))
        self.logscroll = gameui.Uiscroller(self.eventlog.rect.topright, topimage[23].get_height(), self.eventlog.maxrowshow)
        self.eventlog.logscroll = self.logscroll ## Link scroller to ui since it is easier to do here with the current order
        ### Assign eventlog to unit class to broadcast event to the log
        gamesquad.Unitsquad.eventlog = self.eventlog
        ###
        self.buttonui.append(gameui.Uibutton(self.eventlog.pos[0] + (topimage[24].get_width()/2), self.eventlog.pos[1] - self.eventlog.image.get_height() - (topimage[24].get_height()/2), topimage[24], 0))
        self.buttonui += [gameui.Uibutton(self.buttonui[8].pos[0] + topimage[24].get_width(), self.buttonui[8].pos[1], topimage[25], 1),
                        gameui.Uibutton(self.buttonui[8].pos[0] + (topimage[24].get_width() * 2), self.buttonui[8].pos[1], topimage[26],2),
                        gameui.Uibutton(self.buttonui[8].pos[0] + (topimage[24].get_width() * 3), self.buttonui[8].pos[1], topimage[27],3),
                        gameui.Uibutton(self.buttonui[8].pos[0] + (topimage[24].get_width() * 5), self.buttonui[8].pos[1], topimage[28],4),
                        gameui.Uibutton(self.buttonui[8].pos[0] + (topimage[24].get_width() * 6), self.buttonui[8].pos[1], topimage[29],5),
                        gameui.Uibutton(self.timeui.rect.center[0] - 30 , self.timeui.rect.center[1], topimage[32],0),
                        gameui.Uibutton(self.timeui.rect.center[0], self.timeui.rect.center[1], topimage[33], 1),
                        gameui.Uibutton(self.timeui.rect.midright[0] - 60, self.timeui.rect.center[1], topimage[34],2)]
        self.allui.add(self.buttonui[8:17])
        self.screenbuttonlist = self.buttonui[8:17] ## List of button always on screen (for now just eventlog)
        self.squadselectedborder = gameui.Selectedsquad(topimage[-1])
        self.terraincheck = gamepopup.Terrainpopup()
        self.buttonnamepopup = gamepopup.Onelinepopup()
        self.leaderpopup = gamepopup.Onelinepopup()
        self.effectpopup = gamepopup.Effecticonpopup()
        self.textdrama = gamedrama.Textdrama()
        self.fpscount = gameui.FPScount()
        self.battlemenu = gamemenu.Menubox()
        gamelorebook.Lorebook.conceptlore = csv_read('concept_lore.csv', ['data','lore'])
        gamelorebook.Lorebook.factionlore = None
        gamelorebook.Lorebook.unitstat = self.gameunitstat.unitlist
        gamelorebook.Lorebook.unitlore = None
        gamelorebook.Lorebook.armourstat = self.allarmour.armourlist
        gamelorebook.Lorebook.weaponstat = self.allweapon.weaponlist
        gamelorebook.Lorebook.statusstat = self.gameunitstat.statuslist
        gamelorebook.Lorebook.skillstat = self.gameunitstat.abilitylist
        gamelorebook.Lorebook.traitstat = self.gameunitstat.traitlist
        gamelorebook.Lorebook.leaderstat = self.allleader.leaderlist
        gamelorebook.Lorebook.leaderlore = None
        gamelorebook.Lorebook.terrainstat = None
        gamelorebook.Lorebook.landmarkstat = None
        imgs = load_images(['ui','lorebook_ui'],loadorder=False)
        self.lorebook = gamelorebook.Lorebook(imgs[0])
        self.lorenamelist = gamelorebook.Subsectionlist(self.lorebook.rect.topleft, imgs[1])
        self.subsectionname
        imgs = load_images(['ui','lorebook_ui','button'],loadorder=False)
        self.lorebuttonui = [gameui.Uibutton(self.lorebook.rect.topleft[0] + imgs[0].get_width(), self.lorebook.rect.topleft[1] + (imgs[0].get_height()/2), imgs[0], 0, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5), self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[1], 1, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 2, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[2], 2, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 3, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[3], 3, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 4, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[4], 4, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 5, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[5], 5, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 6, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[6], 6, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 7, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[7], 7, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 8, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[8], 8, 10),
                             gameui.Uibutton(self.lorebook.rect.topleft[0] + (imgs[0].get_width()+5) * 9, self.lorebook.rect.topleft[1] - (imgs[0].get_height()/2),imgs[9], 9, 10)]
        buttonimage = load_images(['ui','battlemenu_ui','button'], loadorder=False)
        self.battlemenubutton = [gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0], self.battlemenu.rect.center[1] - 100), text="Resume", size=14),
                                 gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0], self.battlemenu.rect.center[1] - 50), text="Encyclopedia", size=14),
                                 gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0], self.battlemenu.rect.center[1]), text="Option", size=14),
                                 gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0], self.battlemenu.rect.center[1] + 50), text="Main Menu", size=14),
                                 gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0], self.battlemenu.rect.center[1] + 100), text="Desktop", size=14)]
        self.optionmenubutton = [gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0] - 50, self.battlemenu.rect.center[1] + 70), text="Confirm", size=14),
                                 gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0] + 50, self.battlemenu.rect.center[1] + 70), text="Apply", size=14),
                                 gamemenu.Menubutton(buttonimage, (self.battlemenu.rect.center[0] + 150, self.battlemenu.rect.center[1] + 70), text="Cancel", size=14)]
        sliderimage = load_images(['ui','battlemenu_ui','slider'], loadorder=False)
        self.slidermenu = [gamemenu.Slidermenu(sliderimage[0], sliderimage[1:3], (self.battlemenu.rect.center[0] * 1.1, self.battlemenu.rect.center[1]), SoundVolume, 0)]
        self.valuebox = [gamemenu.Valuebox(sliderimage[3], (self.battlemenu.rect.topright[0] * 1.2, self.battlemenu.rect.center[1]), SoundVolume)]
        """initialise starting unit sprites"""
        self.playerarmy, self.enemyarmy, self.squad = [], [], []
        self.inspectuipos = [self.gameui[0].rect.bottomleft[0] - self.imagewidth / 1.25,
                             self.gameui[0].rect.bottomleft[1] - self.imageheight / 3]
        self.squadindexlist = unitsetup(self.playerarmy, self.enemyarmy, '\\' + self.mapselected,
                                        self.imagewidth, self.imageheight, self.allweapon, self.allarmour, self.allleader,
                                        self.gameunitstat, self.coa, self.squad,
                                        self.inspectuipos, enactment=self.enactment)
        self.allunitlist = self.playerarmy.copy()
        self.allunitlist = self.allunitlist + self.enemyarmy
        self.allunitindex = [army.gameid for army in self.allunitlist]
        self.deadindex = 0
        self.playerposlist = {}
        self.enemyposlist = {}
        self.showingsquad = []

    def squadselectside(self, targetside, side, position):
        """side 0 is left 1 is right"""
        thisposition = position
        if side == 0:
            max = 0
            while targetside[thisposition] <= 1 and thisposition != max:
                thisposition -= 1
        else:
            max = 7
            while targetside[thisposition] <= 1 and thisposition != max:
                thisposition += 1
        if thisposition < 0:
            thisposition = 0
        elif thisposition > 7:
            thisposition = 7
        if targetside[thisposition] != 0:
            fronttarget = targetside[thisposition]
        else:
            fronttarget = 0
        return fronttarget

    def changecombatside(self, side, position):
        """position is attacker position against defender 0 = front 1 = left 2 = rear 3 = right"""
        """side is side of attack for rotating to find the correct side the defender got attack accordingly (e.g. left attack on right side is front)"""
        subposition = position
        if subposition == 2:
            subposition = 3
        elif subposition == 3:
            subposition = 2
        changepos = 1
        if subposition == 2:
            changepos = -1
        finalposition = subposition + changepos  ## right
        if side == 0: finalposition = subposition - changepos  ## left
        if finalposition == -1:
            finalposition = 3
        elif finalposition == 4:
            finalposition = 0
        return finalposition

    def combatpositioncal(self, sortmidfront, attacker, receiver, attackerside, receiverside, squadside):
        for thiswho in sortmidfront:
            if thiswho > 1:
                position = np.where(attacker.frontline[attackerside] == thiswho)[0][0]
                fronttarget = receiver.frontline[receiverside][position]
                """check if squad not already fighting if true skip picking new enemy """
                if any(battle > 1 for battle in self.squad[np.where(self.squadindexlist == thiswho)[0][0]].battleside) == False:
                    """get front of another battalion frontline to assign front combat if it 0 squad will find another unit on the left or right"""
                    if fronttarget > 1:
                        """only attack if the side is already free else just wait until it free"""
                        if self.squad[np.where(self.squadindexlist == fronttarget)[0][0]].battleside[squadside] in (-1, 0):
                            self.squad[np.where(self.squadindexlist == thiswho)[0][0]].battleside[attackerside] = fronttarget
                            self.squad[np.where(self.squadindexlist == fronttarget)[0][0]].battleside[squadside] = thiswho
                    else:
                        """pick flank attack if no enemy already fighting and not already fighting"""
                        chance = random.randint(0, 1)
                        secondpick = 0
                        if chance == 0: secondpick = 1
                        """attack left array side of the squad if get random 0, right if 1"""
                        truetargetside = self.changecombatside(chance, receiverside)
                        fronttarget = self.squadselectside(receiver.frontline[receiverside], chance, position)
                        """attack if the found defender at that side is free if not check other side"""
                        if fronttarget > 1:
                            if self.squad[np.where(self.squadindexlist == fronttarget)[0][0]].battleside[truetargetside] in (-1, 0):
                                self.squad[np.where(self.squadindexlist == thiswho)[0][0]].battleside[attackerside] = fronttarget
                                self.squad[np.where(self.squadindexlist == fronttarget)[0][0]].battleside[truetargetside] = thiswho
                        else:
                            """Switch to another side if above not found"""
                            truetargetside = self.changecombatside(secondpick, receiverside)
                            fronttarget = self.squadselectside(receiver.frontline[receiverside], secondpick, position)
                            if fronttarget > 1:
                                if self.squad[np.where(self.squadindexlist == fronttarget)[0][0]].battleside[truetargetside] in (-1, 0):
                                    self.squad[np.where(self.squadindexlist == thiswho)[0][0]].battleside[attackerside] = fronttarget
                                    self.squad[np.where(self.squadindexlist == fronttarget)[0][0]].battleside[truetargetside] = thiswho
                            else:
                                self.squad[np.where(self.squadindexlist == thiswho)[0][0]].battleside[receiverside] = 0

    def squadcombatcal(self, who, target, whoside, targetside):
        """calculate squad engagement using information after battalionengage who is player battalion, target is enemy battalion"""
        squadwhoside = [2 if whoside == 3 else 3 if whoside == 2 else 1 if whoside == 1 else 0][0]
        squadtargetside = [2 if targetside == 3 else 3 if targetside == 2 else 1 if targetside == 1 else 0][0]
        sortmidfront = [who.frontline[whoside][3], who.frontline[whoside][4], who.frontline[whoside][2], who.frontline[whoside][5],
                        who.frontline[whoside][1], who.frontline[whoside][6], who.frontline[whoside][0], who.frontline[whoside][7]]
        """only calculate if the attack is attack with the front side"""
        if whoside == 0:
            self.combatpositioncal(sortmidfront, who, target, whoside, targetside, squadtargetside)
        """only calculate if the target is attacked on the front side"""
        if targetside == 0:
            sortmidfront = [target.frontline[targetside][3], target.frontline[targetside][4],
                            target.frontline[targetside][2],
                            target.frontline[targetside][5], target.frontline[targetside][1],
                            target.frontline[targetside][6],
                            target.frontline[targetside][0], target.frontline[targetside][7]]
            self.combatpositioncal(sortmidfront, target, who, targetside, whoside, squadwhoside)

    def losscal(self, who, target, hit, defense, type):
        heightadventage = who.battalion.height - target.battalion.height
        if type == 1: heightadventage = int((who.battalion.height - target.battalion.height)/2)
        hit += heightadventage
        if hit < 0: hit = 0
        if defense < 0 or 30 in who.trait: defense = 0 ## Ignore def trait
        hitchance = hit - defense
        if hitchance > 80:
            combatscore = 1.5
        elif hitchance > 40:
            combatscore = 1
        elif hitchance > 20:
            combatscore = 0.5
        elif hitchance > 10:
            combatscore = 0.1
        elif hitchance <= 10:
            combatscore = 0
            if random.randint(0, 100) > 90: ## Final chence
                combatscore = 0.1
        leaderdmgbonus = 0
        if who.leader is not None: leaderdmgbonus = who.leader.combat * 10
        if type == 0:  ##melee dmg
            dmg = who.dmg
            """include charge in dmg if charging, ignore charge defense if have ignore trait"""
            if who.charging:
                if 29 not in who.trait:
                    dmg = round(dmg + (who.charge / 10) - (target.chargedef / 10))
                elif 29 in who.trait:
                    dmg = round(dmg + (who.charge / 10))
            leaderdmg = round((dmg * ((100 - (target.armour * ((100 - who.penetrate) / 100))) / 100) * combatscore) / 5)
            dmg = round(((leaderdmg * who.troopnumber) + leaderdmgbonus)/5)
            if target.state in (1, 2, 3, 4, 5, 6, 7, 8, 9): dmg = dmg * 5
        elif type == 1:  ##range dmg
            leaderdmg = round(who.rangedmg * ((100 - (target.armour * ((100 - who.rangepenetrate) / 100))) / 100) * combatscore)
            dmg = round((leaderdmg * who.troopnumber) + leaderdmgbonus)
        if (21 in who.trait and target.type in (1, 2)) or (23 in who.trait and target.type in (4, 5, 6, 7)):  ## Anti trait dmg bonus
            dmg = dmg * 1.25
        if dmg > target.unithealth:
            dmg = target.unithealth
        moraledmg = round(dmg / 100)
        return dmg, moraledmg, leaderdmg

    def applystatustoenemy(self, inflictstatus, receiver, attackerside):
        for status in inflictstatus.items():
            if status[1] == 1 and attackerside == 0:
                receiver.statuseffect[status[0]] = self.gameunitstat.statuslist[status[0]].copy()
            elif status[1] in (2, 3):
                receiver.statuseffect[status[0]] = self.gameunitstat.statuslist[status[0]].copy()
                if status[1] == 3:
                    for squad in receiver.nearbysquadlist[0:2]:
                        if squad != 0:
                            squad.statuseffect[status[0]] = self.gameunitstat.statuslist[status[0]].copy()
            elif status[1] == 4:
                for squad in receiver.battalion.spritearray.flat:
                    if squad.state != 100:
                        squad.statuseffect[status[0]] = self.gameunitstat.statuslist[status[0]].copy()

    def dmgcal(self, who, target, whoside, targetside):
        """target position 0 = Front, 1 = Side, 3 = Rear, whoside and targetside is the side attacking and defending respectively"""
        # print(target.gameid, target.battleside)
        wholuck = random.randint(-50, 50)
        targetluck = random.randint(-50, 50)
        whopercent = self.battlesidecal[whoside]
        """34 battlemaster no flanked penalty"""
        if 34 in who.trait or 91 in who.statuseffect: whopercent = 1
        targetpercent = self.battlesidecal[targetside]
        if 34 in target.trait or 91 in target.statuseffect: targetpercent = 1
        dmgeffect = who.frontdmgeffect
        targetdmgeffect = target.frontdmgeffect
        if whoside != 0 and whopercent != 1:  ## if attack or defend from side will use discipline to help reduce penalty a bit
            whopercent = self.battlesidecal[whoside] + (who.discipline / 300)
            dmgeffect = who.sidedmgeffect
            if whopercent > 1: whopercent = 1
        if targetside != 0 and targetpercent != 1:
            targetpercent = self.battlesidecal[targetside] + (target.discipline / 300)
            targetdmgeffect = target.sidedmgeffect
            if targetpercent > 1: targetpercent = 1
        whohit, whodefense = float(who.attack * whopercent) + wholuck, float(who.meleedef * whopercent) + wholuck
        """33 backstabber ignore def when atk rear, 55 Oblivious To Unexpected can't def from rear"""
        if (33 in target.trait and whoside == 2) or (55 in who.trait and whoside == 2) or (47 in who.trait and targetside in (1, 3)): whodefense = 0
        targethit, targetdefense = float(who.attack * targetpercent) + targetluck, float(target.meleedef * targetpercent) + targetluck
        if (33 in who.trait and targetside == 2) or (55 in target.trait and targetside == 2) or (
                47 in target.trait and whoside in (1, 3)): targetdefense = 0
        whodmg, whomoraledmg, wholeaderdmg = self.losscal(who, target, whohit, targetdefense, 0)
        targetdmg, targetmoraledmg, targetleaderdmg = self.losscal(target, who, targethit, whodefense, 0)
        who.unithealth -= round(targetdmg * (dmgeffect / 100))
        who.basemorale -= round(targetmoraledmg * (dmgeffect / 100))
        if target.elemrange not in (0, 5):  ## apply element effect if atk has element
            who.elemcount[target.elemrange - 1] += round((targetdmg * (dmgeffect / 100)) * (100 - who.elemresist[target.elemrange - 1]/100))
        target.basemorale += round((targetmoraledmg * (dmgeffect / 100) / 2))
        if who.leader is not None and who.leader.health > 0 and random.randint(0, 10) > 5:  ## dmg on who leader
            who.leader.health -= targetleaderdmg
            if who.leader.health <= 0:
                if who.leader.battalion.commander and who.leader.armyposition == 0:  ## reduce morale to whole army if commander die from the dmg (leader die cal is in gameleader.py)
                    self.textdrama.queue.append(str(who.leader.name) + " is dead")
                    self.eventlog.addlog([0, "Commander " + str(who.leader.name) + " is dead"], [0, 1, 2])
                    whicharmy = self.enemyarmy
                    if who.battalion.gameid < 2000:
                        whicharmy = self.playerarmy
                    for army in whicharmy:
                        for squad in army.squadsprite:
                            squad.basemorale -= 20
                else:
                    self.eventlog.addlog([0, str(who.leader.name) + " is dead"], [0, 2])
                self.setuparmyicon()
        target.unithealth -= round(whodmg * (targetdmgeffect / 100))
        target.basemorale -= round(whomoraledmg * (targetdmgeffect / 100))
        if who.elemrange not in (0, 5):  ## apply element effect if atk has element
            target.elemcount[who.elemrange - 1] += round(whodmg * (targetdmgeffect / 100) / 100 * target.elemresist[who.elemrange - 1])
        who.basemorale += round((whomoraledmg * (targetdmgeffect / 100) / 2))
        if target.leader is not None and target.leader.health > 0 and random.randint(0, 10) > 5:  ## dmg on target leader
            target.leader.health -= wholeaderdmg
            if target.leader.health <= 0:
                if target.leader.battalion.commander and target.leader.armyposition == 0:  ## reduce morale to whole army if commander die from the dmg
                    self.textdrama.queue.append(str(target.leader.name) + " is dead")
                    self.eventlog.addlog([0, "Commander " + str(target.leader.name) + " is dead"], [0, 1, 2])
                    whicharmy = self.enemyarmy
                    if target.battalion.gameid < 2000:
                        whicharmy = self.playerarmy
                    for army in whicharmy:
                        for squad in army.squadsprite:
                            squad.basemorale -= 30
                else:
                    self.eventlog.addlog([0, str(target.leader.name) + " is dead"], [0, 2])
                self.setuparmyicon()
        if who.corneratk:  ##attack corner (side) of self with aoe attack
            listloop = target.nearbysquadlist[2:4]
            if targetside in (0, 2): listloop = target.nearbysquadlist[0:2]
            for squad in listloop:
                if squad != 0 and squad.state != 100:
                    targethit, targetdefense = float(who.attack * targetpercent) + targetluck, float(squad.meleedef * targetpercent) + targetluck
                    whodmg, whomoraledmg = self.losscal(who, squad, whohit, targetdefense, 0)
                    squad.unithealth -= round(whodmg * (dmgeffect / 100))
                    squad.basemorale -= whomoraledmg
        """inflict status based on aoe 1 = front only 2 = all 4 side, 3 corner enemy unit, 4 entire battalion"""
        if who.inflictstatus != {}:
            self.applystatustoenemy(who.inflictstatus, target, whoside)
        if target.inflictstatus != {}:
            self.applystatustoenemy(target.inflictstatus, who, targetside)

    def setuparmyicon(self):
        row = 30
        startcolumn = 25
        column = startcolumn
        list = self.playerarmy
        if self.enactment == True:
            list = self.allunitlist
        currentindex = int(self.armyselector.currentrow * self.armyselector.maxcolumnshow)
        self.armyselector.logsize = len(list) / self.armyselector.maxcolumnshow
        if self.armyselector.logsize.is_integer() == False:
            self.armyselector.logsize = int(self.armyselector.logsize) + 1
        if self.armyselector.currentrow > self.armyselector.logsize - 1:
            self.armyselector.currentrow = self.armyselector.logsize - 1
            currentindex = int(self.armyselector.currentrow * self.armyselector.maxcolumnshow)
            self.selectscroll.changeimage(newrow=self.armyselector.currentrow)
        if len(self.armyicon) > 0: ## Remove all old icon first before making new list
            for icon in self.armyicon:
                icon.kill()
                del icon
        for index, army in enumerate(list[currentindex:]):
            self.armyicon.add(gameui.Armyicon((column, row), army))
            column += 40
            if column > 250:
                row += 50
                column = startcolumn
            if row > 100: break
        self.selectscroll.changeimage(logsize=self.armyselector.logsize)

    def checksplit(self, whoinput):
        if np.array_split(whoinput.armysquad, 2, axis=1)[0].size >= 10 and np.array_split(whoinput.armysquad, 2, axis=1)[1].size >= 10 and \
                whoinput.leader[1].name != "None":
            self.allui.add(self.buttonui[5])
        elif self.buttonui[5] in self.allui:
            self.buttonui[5].kill()
        if np.array_split(whoinput.armysquad, 2)[0].size >= 10 and np.array_split(whoinput.armysquad, 2)[1].size >= 10 and whoinput.leader[
            1].name != "None":
            self.allui.add(self.buttonui[6])
        elif self.buttonui[6] in self.allui:
            self.buttonui[6].kill()

    def traitskillblit(self):
        """For blitting skill and trait icon"""
        position = self.gameui[2].rect.topleft
        position = [position[0] + 70 , position[1] + 60]
        startrow = position[0]
        for icon in self.traiticon.sprites(): icon.kill()
        for trait in self.gameui[2].value2[0]:
            self.traiticon.add(gameui.Skillcardicon(self.traitimgs[0], (position[0], position[1]), 0, id = trait))  ## For now use placeholder image 0
            position[0] += 40
            if position[0] >= SCREENRECT.width:
                position[1] += 30
                position[0] = startrow
        position = self.gameui[2].rect.topleft
        position = [position[0] + 70, position[1] + 100]
        startrow = position[0]
        for skill in self.gameui[2].value2[1]:
            self.skillicon.add(gameui.Skillcardicon(self.skillimgs[0], (position[0], position[1]), 1, id = skill)) ## For now use placeholder image 0
            position[0] += 40
            if position[0] >= SCREENRECT.width:
                position[1] += 30
                position[0] = startrow

    def effecticonblit(self):
        """For blitting all status effect icon"""
        position = self.gameui[2].rect.topleft
        position = [position[0] + 70, position[1] + 140]
        startrow = position[0]
        for icon in self.effecticon.sprites(): icon.kill()
        for status in self.gameui[2].value2[4]:
            self.effecticon.add(gameui.Skillcardicon(self.statusimgs[0], (position[0], position[1]), 4, id = status))
            position[0] += 40
            if position[0] >= SCREENRECT.width:
                position[1] += 30
                position[0] = startrow

    def countdownskillicon(self):
        for skill in self.skillicon:
            cd = 0
            activetime = 0
            if skill.id in self.gameui[2].value2[2]:
                cd = int(self.gameui[2].value2[2][skill.id])
            if skill.id in self.gameui[2].value2[3]:
                activetime = int(self.gameui[2].value2[3][skill.id][3])
            skill.iconchange(cd, activetime)
        # for effect in self.effecticon:
        #     cd = 0
        #     if effect.id in self.gameui[2].value2[4]:
        #         cd = int(self.gameui[2].value2[4][effect.id][3])
        #     effect.iconchange(cd, 0)

    def uimouseover(self):
        for ui in self.gameui:
            if ui in self.allui and ui.rect.collidepoint(self.mousepos):
                if ui.uitype not in ("unitcard", 'armybox'):
                    self.clickcheck = 1
                    self.uicheck = 1  ## for avoiding clicking unit under ui
                    break
                else:
                    if self.inspectui == 1:
                        self.clickcheck = 1
                        self.uicheck = 1
                        break
        return self.clickcheck

    def armyiconmouseover(self, mouseup, mouseright):
        for icon in self.armyicon:
            if icon.rect.collidepoint(self.mousepos):
                self.clickcheck = 1
                self.uicheck = 1
                if mouseup:
                    self.lastselected = icon.army
                    for hitbox in self.lastselected.hitbox:
                        hitbox.clicked()
                    if self.beforeselected is not None and self.beforeselected != self.lastselected:
                        for hitbox in self.beforeselected.hitbox:
                            hitbox.release()
                if mouseright:
                    self.basecamerapos = pygame.Vector2(icon.army.basepos[0],icon.army.basepos[1])
                    self.camerapos = self.basecamerapos * self.camerascale
                break
        return self.clickcheck

    def buttonmouseover(self):
        for button in self.buttonui:
            if button in self.allui and button.rect.collidepoint(self.mousepos):
                self.clickcheck = 1
                self.uicheck = 1  ## for avoiding clicking unit under ui
                break
        return self.clickcheck

    def leadermouseover(self):
        leadermouseover = False
        for leader in self.leadernow:
            if leader.rect.collidepoint(self.mousepos):
                self.leaderpopup.pop(self.mousepos, leader.name)
                self.allui.add(self.leaderpopup)
                leadermouseover = True
                break
        return leadermouseover

    def effecticonmouseover(self, iconlist):
        effectmouseover = False
        for icon in iconlist:
            if icon.rect.collidepoint(self.mousepos):
                checkvalue = self.gameui[2].value2[icon.type]
                self.effectpopup.pop(self.mousepos, checkvalue[icon.id])
                self.allui.add(self.effectpopup)
                effectmouseover = True
                break
        return effectmouseover

    def convertweathertime(self):
        for index, item in enumerate(self.weatherevent):
            newtime = datetime.datetime.strptime(item[1], '%H:%M:%S').time()
            newtime = datetime.timedelta(hours=newtime.hour, minutes=newtime.minute, seconds=newtime.second)
            self.weatherevent[index] = [item[0], newtime, item[2]]

    def rungame(self):
        self.setuparmyicon()
        try:
            self.weatherevent = csv_read('weather.csv', ["data", "map", self.mapselected], 1)
            self.weatherevent = self.weatherevent[1:]
            self.convertweathertime()
        except:## If no weather found use default light sunny weather
            newtime = datetime.datetime.strptime("00:00:00", "%H:%M:%S").time()
            newtime = datetime.timedelta(hours=newtime.hour, minutes=newtime.minute, seconds=newtime.second)
            self.weatherevent = [4, newtime, 0]
        while True:
            self.fpscount.fpsshow(self.clock)
            keypress = None
            self.mousepos = pygame.mouse.get_pos()
            mouse_up = False
            mouse_down = False
            mouse_right = False
            double_mouse_right = False
            keystate = pygame.key.get_pressed()
            for event in pygame.event.get():  ## get event input
                if event.type == QUIT:
                    self.allui.clear(self.screen, self.background)
                    self.allcamera.clear(self.screen, self.background)
                    pygame.quit()
                    quit()
                if event.type == self.SONG_END:
                    # pygame.mixer.music.unload()
                    self.pickmusic = random.randint(1, 1)
                    pygame.mixer.music.load(self.musiclist[self.pickmusic])
                    pygame.mixer.music.play(0)
                if event.type == KEYDOWN and event.key == K_ESCAPE:
                    if self.gamestate == 1:
                        self.gamestate = 0
                        self.allui.add(self.battlemenu)
                        self.allui.add(*self.battlemenubutton)
                    else:
                        self.gamestate = 1
                        if self.battlemenu.mode == 2:
                            self.allui.remove(self.lorebook)
                            self.battlemenu.changemode(0)
                        else:
                            if self.battlemenu.mode == 1:
                                self.mixervolume = self.oldsetting
                                pygame.mixer.music.set_volume(self.mixervolume)
                                self.slidermenu[0].update(self.mixervolume, self.valuebox[0], forcedvalue=True)
                            self.battlemenu.changemode(0)
                            self.allui.remove(self.battlemenu)
                            self.allui.remove(*self.battlemenubutton)
                            self.allui.remove(*self.optionmenubutton)
                            self.allui.remove(*self.slidermenu)
                            self.allui.remove(*self.valuebox)
                if pygame.mouse.get_pressed()[0]: ## Hold left click
                    mouse_down = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: ## left click
                    mouse_up = True
                if self.gamestate == 1:
                    if event.type == pygame.MOUSEBUTTONUP:
                        # if event.button == 1:  ## left click
                        #     mouse_up = True
                        if event.button == 3:  ## Right Click
                            mouse_right = True
                            if self.timer == 0:
                                self.timer = 0.001  ##Start timer after first mouse click
                            elif self.timer < 0.3:
                                double_mouse_right = True
                                self.timer = 0
                        elif event.button == 4:
                            if self.eventlog.rect.collidepoint(self.mousepos): ## Scrolling when mouse at event log
                                self.eventlog.currentstartrow -= 1
                                if self.eventlog.currentstartrow < 0: self.eventlog.currentstartrow = 0
                                else:
                                    self.eventlog.recreateimage()
                                    self.logscroll.changeimage(newrow=self.eventlog.currentstartrow)
                            elif self.armyselector.rect.collidepoint(self.mousepos): ## Scrolling when mouse at event log
                                self.armyselector.currentrow -= 1
                                if self.armyselector.currentrow < 0: self.armyselector.currentrow = 0
                                else:
                                    self.setuparmyicon()
                                    self.selectscroll.changeimage(newrow=self.armyselector.currentrow)
                            else: ## Scrolling in game map to zoom
                                self.camerascale += 1
                                if self.camerascale > 10: self.camerascale = 10
                                else:
                                    self.camerapos[0] = self.basecamerapos[0] *  self.camerascale
                                    self.camerapos[1] = self.basecamerapos[1] *  self.camerascale
                                    self.mapshown.changescale(self.camerascale)
                        elif event.button == 5:
                            if self.eventlog.rect.collidepoint(self.mousepos): ## Scrolling when mouse at event log
                                self.eventlog.currentstartrow += 1
                                if self.eventlog.currentstartrow + self.eventlog.maxrowshow - 1 < self.eventlog.lencheck and self.eventlog.lencheck > 9:
                                    self.eventlog.recreateimage()
                                    self.logscroll.changeimage(newrow=self.eventlog.currentstartrow)
                                else:
                                    self.eventlog.currentstartrow -= 1
                            elif self.armyselector.rect.collidepoint(self.mousepos): ## Scrolling when mouse at event log
                                self.armyselector.currentrow += 1
                                if self.armyselector.currentrow < self.armyselector.logsize:
                                    self.setuparmyicon()
                                    self.selectscroll.changeimage(newrow=self.armyselector.currentrow)
                                else:
                                    self.armyselector.currentrow -= 1
                                    if self.armyselector.currentrow < 0:
                                        self.armyselector.currentrow = 0
                            else: ## Scrolling in game map to zoom
                                self.camerascale -= 1
                                if self.camerascale < 1: self.camerascale = 1
                                else:
                                    self.camerapos[0] = self.basecamerapos[0] *  self.camerascale
                                    self.camerapos[1] = self.basecamerapos[1] *  self.camerascale
                                    self.mapshown.changescale(self.camerascale)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_TAB:
                            if self.mapviewmode == 0: ## Currently in normal mode
                                self.mapviewmode = 1
                                self.showmap.changemode(self.mapviewmode)
                            else: ## Currently in height mode
                                self.mapviewmode = 0
                                self.showmap.changemode(self.mapviewmode)
                            self.mapshown.changescale(self.camerascale)
                        elif event.key == pygame.K_p:  ## Speed Pause Button
                            if self.gamespeed == 1:
                                self.gamespeed = 0
                            else:
                                self.gamespeed = 1
                        elif event.key == pygame.K_PAGEUP: ## Go to top of event log
                                self.eventlog.currentstartrow = 0
                                self.eventlog.recreateimage()
                                self.logscroll.changeimage(newrow=self.eventlog.currentstartrow)
                        elif event.key == pygame.K_PAGEDOWN: ## Go to bottom of event log
                            if self.eventlog.lencheck > self.eventlog.maxrowshow:
                                self.eventlog.currentstartrow = self.eventlog.lencheck - self.eventlog.maxrowshow
                                self.eventlog.recreateimage()
                                self.logscroll.changeimage(newrow=self.eventlog.currentstartrow)
                        elif event.key == pygame.K_SPACE and self.lastselected is not None:
                            whoinput.command(self.battlemousepos, mouse_up, mouse_right, double_mouse_right,
                                            self.lastmouseover, self.enemyposlist, keystate, othercommand=1)
                        ### FOR DEVELOPMENT DELETE LATER
                        elif event.key == pygame.K_1:
                            self.textdrama.queue.append('Hello and Welcome to the Update Video')
                        elif event.key == pygame.K_2:
                            self.textdrama.queue.append('Showcase: Game speed option and Weather system')
                        elif event.key == pygame.K_3:
                            self.textdrama.queue.append('Game speed can by adjusted at anytime in game')
                        elif event.key == pygame.K_4:
                            self.textdrama.queue.append('The weather effect will occur at set time')
                        elif event.key == pygame.K_5:
                            self.textdrama.queue.append('Weather effect affect the unit in many ways')
                        elif event.key == pygame.K_6:
                            self.textdrama.queue.append('Current special effect still need rework')
                        elif event.key == pygame.K_n and self.lastselected is not None:
                            if whoinput.gameid < 2000:
                                self.allunitindex = whoinput.switchfaction(self.playerarmy, self.enemyarmy, self.playerposlist, self.allunitindex, self.enactment)
                            else:
                                self.allunitindex = whoinput.switchfaction(self.enemyarmy, self.playerarmy, self.enemyposlist, self.allunitindex, self.enactment)
                        elif event.key == pygame.K_l and self.lastselected is not None:
                            for squad in whoinput.squadsprite:
                                squad.basemorale = 0
                        elif event.key == pygame.K_k and self.lastselected is not None:
                            for squad in self.lastselected.squadsprite:
                                squad.unithealth -= squad.unithealth
                        elif event.key == pygame.K_m and self.lastselected is not None:
                            self.lastselected.leader[0].health -= 1000
                        ###
                        else:
                            keypress = event.key
            self.allui.clear(self.screen, self.background)  ##clear sprite before update new one
            # self.screen.blit(self.background, self.camerapos)
            if self.gamestate == 1:
                self.uiupdater.update()  # update ui
                if keystate[K_s] or self.mousepos[1] >= self.bottomcorner:  ## down
                    self.basecamerapos[1] += 5 * abs(11 - self.camerascale)
                    self.camerapos[1] = self.basecamerapos[1] * self.camerascale
                elif keystate[K_w] or self.mousepos[1] <= 5:  ## up
                    self.basecamerapos[1] -= 5 * abs(11 - self.camerascale)
                    self.camerapos[1] = self.basecamerapos[1] * self.camerascale
                if keystate[K_a] or self.mousepos[0] <= 5:  ## left
                    self.basecamerapos[0] -= 5 * abs(11 - self.camerascale)
                    self.camerapos[0] = self.basecamerapos[0] * self.camerascale
                elif keystate[K_d] or self.mousepos[0] >= self.rightcorner:  ## right
                    self.basecamerapos[0] += 5 * abs(11 - self.camerascale)
                    self.camerapos[0] = self.basecamerapos[0] * self.camerascale
                if self.camerapos[0] > self.mapshown.image.get_width():
                    self.camerapos[0] = self.mapshown.image.get_width()
                elif self.camerapos[0] < 0:
                    self.camerapos[0] = 0
                if self.camerapos[1] > self.mapshown.image.get_height():
                    self.camerapos[1] = self.mapshown.image.get_height()
                elif self.camerapos[1] < 0:
                    self.camerapos[1] = 0
                if self.basecamerapos[0] > 1000:
                    self.basecamerapos[0] = 1000
                elif self.basecamerapos[0] < 0:
                    self.basecamerapos[0] = 0
                if self.basecamerapos[1] > 1000:
                    self.basecamerapos[1] = 1000
                elif self.basecamerapos[1] < 0:
                    self.basecamerapos[1] = 0
                self.cameraupcorner = (self.camerapos[0] - self.centerscreen[0], self.camerapos[1] - self.centerscreen[1])
                self.battlemousepos[0] = pygame.Vector2((self.mousepos[0] - self.centerscreen[0]) + self.camerapos[0],
                                                        self.mousepos[1] - self.centerscreen[1] + self.camerapos[1])
                self.battlemousepos[1] = self.battlemousepos[0] / self.camerascale
                if self.timer != 0:
                    self.timer += self.uidt
                    if self.timer >= 0.5:
                        self.timer = 0
                if self.dramatimer == 0 and len(self.textdrama.queue) != 0: ## Start timer and add to allui If there is event queue
                    self.allui.add(self.textdrama)
                    self.textdrama.processqueue()
                    self.dramatimer = 0.1
                elif self.dramatimer > 0:
                    self.textdrama.playanimation()
                    self.dramatimer += self.uidt
                    if self.dramatimer > 3:
                        self.dramatimer = 0
                        self.allui.remove(self.textdrama)
                self.lastmouseover = 0
                if self.terraincheck in self.allui and (self.terraincheck.pos != self.mousepos or keystate[K_s] or keystate[K_w] or keystate[K_a] or keystate[K_d]):
                    self.allui.remove(self.terraincheck)
                if mouse_up or mouse_right or mouse_down:
                    self.uicheck = 0
                    if mouse_up:
                        self.clickcheck = 0
                        self.clickcheck2 = 0
                    if self.minimap.rect.collidepoint(self.mousepos):
                        if mouse_up:
                            posmask = pygame.Vector2(int(self.mousepos[0] - self.minimap.rect.x), int(self.mousepos[1] - self.minimap.rect.y))
                            self.basecamerapos = posmask * 5
                            self.camerapos = self.basecamerapos * self.camerascale
                            self.clickcheck = 1
                        elif mouse_right and self.lastselected is not None:
                            self.uicheck = 1
                        elif mouse_right and self.lastselected is None:
                            pass
                    elif self.logscroll.rect.collidepoint(self.mousepos): ## Have to run logscroll before event log
                        if (mouse_down or mouse_up):
                            self.clickcheck = 1
                            self.uicheck = 1
                            newrow = self.logscroll.update(self.mousepos)
                            if self.eventlog.currentstartrow != newrow:
                                self.eventlog.currentstartrow = newrow
                                self.eventlog.recreateimage()
                        elif mouse_right:
                            self.clickcheck = 1
                            self.uicheck = 1
                    elif self.selectscroll.rect.collidepoint(self.mousepos): ## Have to run logscroll before event log
                        if (mouse_down or mouse_up):
                            # print(self.armyselector.logsize, self.selectscroll.logsize)
                            self.clickcheck = 1
                            self.uicheck = 1
                            newrow = self.selectscroll.update(self.mousepos)
                            if self.armyselector.currentrow != newrow:
                                self.armyselector.currentrow = newrow
                                self.setuparmyicon()
                        elif mouse_right:
                            self.clickcheck = 1
                            self.uicheck = 1
                    elif self.eventlog.rect.collidepoint(self.mousepos):
                        if mouse_up or mouse_right:
                            self.clickcheck = 1
                            self.uicheck = 1
                    elif self.armyselector.rect.collidepoint(self.mousepos):
                        if self.armyiconmouseover(mouse_up, mouse_right) == 1:
                            pass
                    elif self.uimouseover() == 1:
                        pass
                    elif self.buttonmouseover() == 1:
                        pass
                    elif mouse_right and self.lastselected is None and self.uicheck != 1:
                        if self.battlemousepos[1][0] >= 0 and self.battlemousepos[1][0] <= 1000 and self.battlemousepos[1][1] >= 0 and self.battlemousepos[1][1] <= 1000:
                            terrainpop, featurepop = self.battlemapfeature.getfeature(self.battlemousepos[1], self.battlemap)
                            featurepop = self.battlemapfeature.featuremod[featurepop]
                            self.terraincheck.pop(self.mousepos, featurepop)
                            self.allui.add(self.terraincheck)
                for index, button in enumerate(self.screenbuttonlist): ## Event log button and timer button click
                    if button.rect.collidepoint(self.mousepos):
                        if index in (0,1,2,3,4,5): ## eventlog button
                            if mouse_up:
                                if button.event in (0,1,2,3):
                                    self.eventlog.changemode(button.event)
                                elif button.event == 4:
                                    self.eventlog.cleartab()
                                elif button.event == 5:
                                   self.eventlog.cleartab(alltab=True)
                                self.uicheck = 1
                            elif mouse_right: self.uicheck = 1
                        elif index in (6,7,8): ## timer button
                            if mouse_up:
                                if button.event == 0:
                                    self.gamespeed = 0
                                elif button.event == 1:
                                    newindex = self.gamespeedset.index(self.gamespeed) - 1
                                    if newindex >= 0:
                                        self.gamespeed = self.gamespeedset[newindex]
                                elif button.event == 2:
                                    newindex = self.gamespeedset.index(self.gamespeed) + 1
                                    if newindex < len(self.gamespeedset):
                                        self.gamespeed = self.gamespeedset[newindex]
                                self.speednumber.speedupdate(self.gamespeed)
                            elif mouse_right: self.uicheck = 1
                        break
                for index, weather in enumerate(self.weatherevent): ## Weather system
                    if self.timenumber.timenum >= weather[1]:
                        del self.currentweather
                        if weather[0] != 0:
                            self.currentweather = gameweather.Weather(self.timeui, weather[0], weather[2], self.allweather)
                        else: ## Random weather
                            self.currentweather = gameweather.Weather(self.timeui, random.randint(0,11), random.randint(0,2), self.allweather)
                        self.weatherevent.pop(index)
                        break
                if self.currentweather.spawnrate > 0 and len(self.weathermatter) < self.currentweather.speed:
                    spawnnum = range(0,int(self.currentweather.spawnrate*self.dt*random.randint(0,10)))
                    for spawn in spawnnum:
                        truepos = (random.randint(10, SCREENRECT.width), 0)
                        target = (truepos[0], SCREENRECT.height)
                        if self.currentweather.spawnangle == 225:
                            startpos = random.randint(10, SCREENRECT.width*2)
                            truepos = (startpos,0)
                            if startpos >= SCREENRECT.width:
                                startpos = SCREENRECT.width
                                truepos = (startpos, random.randint(0,SCREENRECT.height))
                            if truepos[1] > 0: ## start position simulate from beyond top right of screen
                                target = (truepos[1]*self.weatherscreenadjust, SCREENRECT.height)
                            elif truepos[0] < SCREENRECT.width: ## start position inside screen width
                                target = (0, truepos[0]/self.weatherscreenadjust)
                        elif self.currentweather.spawnangle == 270:
                            truepos = (SCREENRECT.width, random.randint(0, SCREENRECT.height))
                            target = (0, truepos[1])
                        randompic = random.randint(0, len(self.weathermatterimgs[self.currentweather.type]) - 1)
                        self.weathermatter.add(gameweather.Mattersprite(truepos, target,
                                                                        self.currentweather.speed, self.weathermatterimgs[self.currentweather.type][randompic]))
                if self.currentweather.specialeffect > 0:
                    if len(self.weathereffect) == 0:
                        truepos = (SCREENRECT.width, SCREENRECT.height/2)
                        target = (-SCREENRECT.width, SCREENRECT.height/2)
                        self.weathereffect.add(gameweather.Specialeffect(truepos,target,self.currentweather.speed,self.weathereffectimgs[self.currentweather.type][self.currentweather.level]))
                    elif len(self.weathereffect) == 1:
                        for weathereffect in self.weathereffect:
                            if weathereffect.pos[0] <= 0:
                                truepos = (SCREENRECT.width, SCREENRECT.height / 2)
                                target = (-SCREENRECT.width, SCREENRECT.height / 2)
                                self.weathereffect.add(gameweather.Specialeffect(truepos, target, self.currentweather.speed,
                                                                                 self.weathereffectimgs[self.currentweather.type][
                                                                                     self.currentweather.level]))
                for army in self.allunitlist:
                    if army.gameid < 2000:
                        self.playerposlist[army.gameid] = army.basepos
                    else:
                        self.enemyposlist[army.gameid] = army.basepos
                    if army.basepos[0] < 0 or army.basepos[0] > 1000 or army.basepos[1] < 0 or army.basepos[
                        1] > 1000:  ## remove unit when it go out of battlemap
                        self.allunitindex.remove(army.gameid)
                        army.kill()
                        for hitbox in army.hitbox:
                            hitbox.kill()
                    if army.rect.collidepoint(self.battlemousepos[0]):
                        posmask = int(self.battlemousepos[0][0] - army.rect.x), int(self.battlemousepos[0][1] - army.rect.y)
                        try:
                            if army.mask.get_at(posmask) == 1:
                                army.mouse_over = True
                                self.lastmouseover = army
                                if mouse_up and self.uicheck == 0:
                                    self.lastselected = army
                                    for hitbox in self.lastselected.hitbox:
                                        hitbox.clicked()
                                    if self.beforeselected is not None and self.beforeselected != self.lastselected:
                                        for hitbox in self.beforeselected.hitbox:
                                            hitbox.release()
                                    self.clickcheck = 1
                        except:
                            army.mouse_over = False
                    else:
                        army.mouse_over = False
                    if army.changefaction:  ## change side via surrender or betrayal
                        if army.gameid < 2000:
                            self.allunitindex = army.switchfaction(self.playerarmy, self.enemyarmy, self.playerposlist, self.allunitindex, self.enactment)
                        else:
                            self.allunitindex = army.switchfaction(self.enemyarmy, self.playerarmy, self.enemyposlist, self.allunitindex, self.enactment)
                        army.changefaction = False
                        self.setuparmyicon()
                    if army.state == 100 and army.gotkilled == 0:
                        if army.gameid < 2000:
                            self.die(self, army, self.playerarmy, self.enemyarmy)
                            self.setuparmyicon()
                        else:
                            self.die(self, army, self.enemyarmy, self.playerarmy)
                            self.setuparmyicon()
                        self.eventlog.addlog([0, str(army.leader[0].name) + "'s battalion is destroyed"], [0, 1])
                if self.lastselected is not None and self.lastselected.state != 100:
                    """if not found in army class then it is in dead class"""
                    whoinput = self.lastselected
                    if (mouse_up or mouse_right) and self.uicheck == 0:
                        whoinput.command(self.battlemousepos, mouse_up, mouse_right, double_mouse_right,
                                         self.lastmouseover, self.enemyposlist, keystate)
                        # if whoinput.target != whoinput.pos and whoinput.rotateonly is False and whoinput.moverotate == 0 and whoinput.directionarrow is False:
                        #     gamebattalion.directionarrow(whoinput)
                    if self.beforeselected is None:  ## add back the pop up ui to group so it get shown when click unit with none selected before
                        self.gameui = self.popgameui
                        self.allui.add(*self.gameui[0:2])  ## add leader and top ui
                        self.allui.add(self.buttonui[4])  ## add inspection ui open/close button
                        self.allui.add(self.buttonui[7])  ## add decimation button
                        self.allui.add(*self.switchbuttonui[0:4])  ## add skill condition change, fire at will buttons
                        self.switchbuttonui[0].event = whoinput.useskillcond
                        self.switchbuttonui[1].event = whoinput.fireatwill
                        self.switchbuttonui[2].event = whoinput.hold
                        self.switchbuttonui[3].event = whoinput.useminrange
                        self.leadernow = whoinput.leader
                        self.allui.add(*self.leadernow)
                        if np.array_split(whoinput.armysquad, 2, axis=1)[0].size >= 10 and np.array_split(whoinput.armysquad, 2, axis=1)[1].size >= 10 and \
                                whoinput.leader[0].name != "None":
                            self.allui.add(self.buttonui[5])  ## add column split button
                        if np.array_split(whoinput.armysquad, 2)[0].size >= 10 and np.array_split(whoinput.armysquad, 2)[1].size >= 10 and \
                                whoinput.leader[0].name != "None":
                            self.allui.add(self.buttonui[6])  ## add row split button
                    elif self.beforeselected != self.lastselected:  ## change ui when click other battalion
                        if self.inspectui == 1:
                            self.clickcheck2 = 1
                            self.allui.remove(*self.showingsquad)
                            self.showingsquad = []
                        self.checksplit(whoinput)
                        self.allui.remove(*self.leadernow)
                        self.switchbuttonui[0].event = whoinput.useskillcond
                        self.switchbuttonui[1].event = whoinput.fireatwill
                        self.switchbuttonui[2].event = whoinput.hold
                        self.switchbuttonui[3].event = whoinput.useminrange
                        self.leadernow = whoinput.leader
                        self.allui.add(*self.leadernow)
                    self.gameui[0].valueinput(who=whoinput, leader=self.allleader, splithappen=self.splithappen)
                    self.gameui[1].valueinput(who=whoinput, leader=self.allleader, splithappen=self.splithappen)
                    self.splithappen = False
                    if self.buttonui[4].rect.collidepoint(self.mousepos) or (
                            mouse_up and self.inspectui == 1 and self.clickcheck2 == 1):
                        if self.buttonui[4].rect.collidepoint(self.mousepos):
                            self.buttonnamepopup.pop(self.mousepos, "Inspect Squad")
                            self.allui.add(self.buttonnamepopup)
                        if (mouse_up and self.inspectui == 0) or (
                                mouse_up and self.inspectui == 1 and self.clickcheck2 == 1):  ## Add army inspect ui when left click at ui button or when change unit with inspect open
                            self.inspectui = 1
                            self.allui.add(*self.gameui[2:4])
                            self.allui.add(*self.buttonui[0:4])
                            self.showingsquad = whoinput.squadsprite
                            self.squadlastselected = self.showingsquad[0]
                            self.squadselectedborder.pop(self.showingsquad[0].inspposition)
                            self.allui.add(self.squadselectedborder)
                        elif mouse_up and self.inspectui == 1:  ## Remove when click again and the ui already open
                            self.allui.remove(*self.showingsquad)
                            self.allui.remove(self.squadselectedborder)
                            self.showingsquad = []
                            for ui in self.gameui[2:4]: ui.kill()
                            for button in self.buttonui[0:4]: button.kill()
                            self.inspectui = 0
                            self.clickcheck2 = 0
                    elif self.switchbuttonui[0].rect.collidepoint(self.mousepos) or keypress == pygame.K_g:
                        if mouse_up or keypress == pygame.K_g:  ## rotate skill condition when clicked
                            whoinput.useskillcond += 1
                            if whoinput.useskillcond > 3:
                                whoinput.useskillcond = 0
                            self.switchbuttonui[0].event = whoinput.useskillcond
                        if self.switchbuttonui[0].rect.collidepoint(self.mousepos): ## popup name when mouse over
                            poptext = ("Free Skill Use", "Conserve 50% Stamina", "Conserve 25% stamina", "Forbid Skill")
                            self.buttonnamepopup.pop(self.mousepos, poptext[self.switchbuttonui[0].event])
                            self.allui.add(self.buttonnamepopup)
                    elif self.switchbuttonui[1].rect.collidepoint(self.mousepos) or keypress == pygame.K_f:
                        if mouse_up or keypress == pygame.K_f:  ## rotate fire at will condition when clicked
                            whoinput.fireatwill += 1
                            if whoinput.fireatwill > 1:
                                whoinput.fireatwill = 0
                            self.switchbuttonui[1].event = whoinput.fireatwill
                        if self.switchbuttonui[1].rect.collidepoint(self.mousepos): ## popup name when mouse over
                            poptext = ("Fire at will", "Hold fire until order")
                            self.buttonnamepopup.pop(self.mousepos, poptext[self.switchbuttonui[1].event])
                            self.allui.add(self.buttonnamepopup)
                    elif self.switchbuttonui[2].rect.collidepoint(self.mousepos) or keypress == pygame.K_h:
                        if mouse_up or keypress == pygame.K_h:  ## rotate hold condition when clicked
                            whoinput.hold += 1
                            if whoinput.hold > 2:
                                whoinput.hold = 0
                            self.switchbuttonui[2].event = whoinput.hold
                        if self.switchbuttonui[2].rect.collidepoint(self.mousepos):  ## popup name when mouse over
                            poptext = ("Aggressive", "Skirmish/Scout", "Hold Ground")
                            self.buttonnamepopup.pop(self.mousepos, poptext[self.switchbuttonui[2].event])
                            self.allui.add(self.buttonnamepopup)
                    elif self.switchbuttonui[3].rect.collidepoint(self.mousepos) or keypress == pygame.K_j:
                        if mouse_up or keypress == pygame.K_j:  ## rotate min range condition when clicked
                            whoinput.useminrange += 1
                            if whoinput.useminrange > 1:
                                whoinput.useminrange = 0
                            self.switchbuttonui[3].event = whoinput.useminrange
                        if self.switchbuttonui[3].rect.collidepoint(self.mousepos):  ## popup name when mouse over
                            poptext = ("Shoot from min range", "Shoot from max range")
                            self.buttonnamepopup.pop(self.mousepos, poptext[self.switchbuttonui[3].event])
                            self.allui.add(self.buttonnamepopup)
                    elif self.buttonui[5] in self.allui and self.buttonui[5].rect.collidepoint(self.mousepos):
                        self.buttonnamepopup.pop(self.mousepos, "Split by middle column")
                        self.allui.add(self.buttonnamepopup)
                        if mouse_up and whoinput.basepos.distance_to(list(whoinput.neartarget.values())[0]) > 50:
                            self.allunitindex = self.splitunit(self,whoinput, 1, gameleader)
                            self.splithappen = True
                            self.checksplit(whoinput)
                            self.allui.remove(*self.leadernow)
                            self.leadernow = whoinput.leader
                            self.allui.add(*self.leadernow)
                            self.setuparmyicon()
                    elif self.buttonui[6] in self.allui and self.buttonui[6].rect.collidepoint(self.mousepos):
                        self.buttonnamepopup.pop(self.mousepos, "Split by middle row")
                        self.allui.add(self.buttonnamepopup)
                        if mouse_up and whoinput.basepos.distance_to(list(whoinput.neartarget.values())[0]) > 50:
                            self.allunitindex = self.splitunit(whoinput, 0, gameleader)
                            self.splithappen = True
                            self.checksplit(whoinput)
                            self.allui.remove(*self.leadernow)
                            self.leadernow = whoinput.leader
                            self.allui.add(*self.leadernow)
                            self.setuparmyicon()
                    elif self.buttonui[7].rect.collidepoint(self.mousepos):  ## decimation effect
                        self.buttonnamepopup.pop(self.mousepos, "Decimation")
                        self.allui.add(self.buttonnamepopup)
                        if mouse_up and whoinput.state == 0:
                            for squad in whoinput.squadsprite:
                                squad.statuseffect[98] = self.gameunitstat.statuslist[98].copy()
                                squad.unithealth -= round(squad.unithealth * 0.1)
                    elif self.gameui[1] in self.allui and self.gameui[1].rect.collidepoint(self.mousepos) and self.leadermouseover():
                        pass
                    else:
                        self.allui.remove(self.leaderpopup)
                        self.allui.remove(self.buttonnamepopup) ## remove popup if no mouseover on any button
                    if self.inspectui == 1:
                        if self.splithappen:  ## change showing squad in inspectui if split happen
                            self.allui.remove(*self.showingsquad)
                            self.showingsquad = whoinput.squadsprite
                            # self.allui.add(*self.showingsquad)
                        self.allui.add(*self.showingsquad)
                        if mouse_up:  ## Change showing stat to the clicked squad one
                            for squad in self.showingsquad:
                                if squad.rect.collidepoint(self.mousepos):
                                    self.clickcheck = 1
                                    self.uicheck = 1
                                    squad.command(self.battlemousepos, mouse_up, mouse_right, self.squadlastselected.wholastselect)
                                    self.squadlastselected = squad
                                    self.squadselectedborder.pop(squad.inspposition)
                                    self.eventlog.addlog(
                                        [0, str(self.squadlastselected.boardpos) + " " + str(self.squadlastselected.name)  + " in " + self.squadlastselected.battalion.leader[0].name + "'s battalion is clicked"], [3])
                                    self.allui.add(self.squadselectedborder)
                                    self.gameui[2].valueinput(who=squad, weaponlist=self.allweapon, armourlist=self.allarmour, leader=self.allleader,
                                                              gameunitstat=self.gameunitstat, splithappen=self.splithappen)
                                    if self.gameui[2].option == 2:
                                        self.traitskillblit()
                                        self.effecticonblit()
                                        self.countdownskillicon()
                                    else:
                                        for icon in self.traiticon.sprites(): icon.kill()
                                        for icon in self.effecticon.sprites(): icon.kill()
                            for button in self.buttonui[0:4]:  ## Change unit card option based on button clicking
                                if button.rect.collidepoint(self.mousepos):
                                    self.clickcheck = 1
                                    self.uicheck = 1
                                    if self.gameui[2].option != button.event:
                                        self.gameui[2].option = button.event
                                        self.gameui[2].valueinput(who=self.squadlastselected, weaponlist=self.allweapon, armourlist=self.allarmour,
                                                                  leader=self.allleader, changeoption=1, gameunitstat=self.gameunitstat,
                                                                  splithappen=self.splithappen)
                                        if self.gameui[2].option == 2:
                                            self.traitskillblit()
                                            self.effecticonblit()
                                            self.countdownskillicon()
                                        else:
                                            for icon in self.traiticon.sprites(): icon.kill()
                                            for icon in self.effecticon.sprites(): icon.kill()
                                    break
                        if (self.squadlastselected is not None and self.uitimer >= 0.5 and self.gameui[2].option != 0) or self.beforeselected != self.lastselected:  ## Update value of the clicked squad
                            self.gameui[2].valueinput(who=self.squadlastselected, weaponlist=self.allweapon, armourlist=self.allarmour,
                                                      leader=self.allleader, gameunitstat=self.gameunitstat, splithappen=self.splithappen)
                            if self.gameui[2].option == 2:
                                self.countdownskillicon()
                                self.effecticonblit()
                                if self.beforeselected != self.lastselected:
                                    self.traitskillblit()
                                    self.countdownskillicon()
                            else:
                                for icon in self.traiticon.sprites(): icon.kill()
                                for icon in self.effecticon.sprites(): icon.kill()
                            self.uitimer = 0
                        if self.effecticonmouseover(self.traiticon):
                            pass
                        elif self.effecticonmouseover(self.skillicon):
                            pass
                        elif self.effecticonmouseover(self.effecticon):
                            pass
                        else: self.allui.remove(self.effectpopup)
                    else:
                        for icon in self.traiticon.sprites(): icon.kill()
                        for icon in self.effecticon.sprites(): icon.kill()
                    self.beforeselected = self.lastselected
                """remove the pop up ui when click at no group"""
                if self.clickcheck != 1:
                    if self.lastselected is not None:
                        for hitbox in self.lastselected.hitbox:
                            hitbox.release()
                        self.lastselected = None
                    self.gameui[2].option = 1
                    for ui in self.gameui: ui.kill()
                    for button in self.buttonui[0:8]: button.kill()
                    for icon in self.traiticon.sprites(): icon.kill()
                    for icon in self.effecticon.sprites(): icon.kill()
                    self.allui.remove(*self.switchbuttonui)
                    self.allui.remove(*self.showingsquad)
                    self.showingsquad = []
                    self.inspectui = 0
                    self.beforeselected = None
                    self.allui.remove(*self.leadernow)
                    self.squadlastselected = None
                    self.allui.remove(self.squadselectedborder)
                    self.leadernow = []
                # fight_sound.play()
                """Combat and unit update"""
                for hitbox in self.hitboxs:
                    collidelist = pygame.sprite.spritecollide(hitbox, self.hitboxs, dokill=False, collided=pygame.sprite.collide_mask)
                    for hitbox2 in collidelist:
                        if hitbox.who.gameid != hitbox2.who.gameid and hitbox.who.gameid < 2000 and hitbox2.who.gameid >= 2000:
                            # if pygame.sprite.collide_mask(hitbox, hitbox2) is not None:
                            hitbox.collide, hitbox2.collide = hitbox2.who.gameid, hitbox.who.gameid
                            """run combatprepare when combat start if army is the attacker"""
                            if hitbox.who.gameid not in hitbox.who.battleside:
                                hitbox.who.battleside[hitbox.side] = hitbox2.who.gameid
                                hitbox2.who.battleside[hitbox2.side] = hitbox.who.gameid
                                """set up army position to the enemyside"""
                                if hitbox.side == 0 and hitbox.who.state in (1, 2, 3, 4, 5, 6) and hitbox.who.combatpreparestate == 0:
                                    hitbox.who.combatprepare(hitbox2)
                                elif hitbox2.side == 0 and hitbox2.who.state in (1, 2, 3, 4, 5, 6) and hitbox2.who.combatpreparestate == 0:
                                    hitbox2.who.combatprepare(hitbox)
                                for battle in hitbox.who.battleside:
                                    if battle != 0:
                                        self.squadcombatcal(hitbox.who, hitbox2.who, hitbox.who.battleside.index(battle),
                                                            hitbox2.who.battleside.index(hitbox.who.gameid))
                            """Rotate army side to the enemyside"""
                            if hitbox.who.combatpreparestate == 1:
                                if hitbox.who.allsidepos != hitbox2.who.allsidepos:
                                    hitbox.who.setrotate(settarget=hitbox2.who.pos, instant=True)
                            if hitbox2.who.combatpreparestate == 1:
                                if hitbox.who.allsidepos != hitbox2.who.allsidepos:
                                    hitbox2.who.setrotate(settarget=hitbox.who.pos, instant=True)
                        elif hitbox.who.gameid != hitbox2.who.gameid and ((hitbox.who.gameid < 2000 and hitbox2.who.gameid < 2000)
                                                                          or (
                                                                                  hitbox.who.gameid >= 2000 and hitbox2.who.gameid >= 2000)):  ##colide battalion in same faction
                            hitbox.collide, hitbox2.collide = hitbox2.who.gameid, hitbox.who.gameid
                """Calculate squad combat dmg"""
                if self.combattimer >= 0.5:
                    for thissquad in self.squad:
                        if any(battle > 1 for battle in thissquad.battleside):
                            for index, combat in enumerate(thissquad.battleside):
                                if combat > 1:
                                    if thissquad.gameid not in self.squad[np.where(self.squadindexlist == combat)[0][0]].battleside:
                                        thissquad.battleside[index] = -1
                                    else:
                                        self.dmgcal(thissquad, self.squad[np.where(self.squadindexlist == combat)[0][0]], index,
                                                    self.squad[np.where(self.squadindexlist == combat)[0][0]].battleside.index(thissquad.gameid))
                        if thissquad.state in (11, 12, 13):
                            if type(thissquad.attacktarget) == int and thissquad.attacktarget != 0:
                                if thissquad.attacktarget in self.allunitindex:
                                    thissquad.attacktarget = self.allunitlist[self.allunitindex.index(thissquad.attacktarget)]
                                else:
                                    thissquad.attackpos = 0
                                    thissquad.attacktarget = 0
                                    for target in list(thissquad.battalion.neartarget.values()):
                                        if target in self.allunitindex:
                                            thissquad.attackpos = target[1]
                                            thissquad.attacktarget = target[1]
                                            thissquad.attacktarget = self.allunitlist[self.allunitindex.index(thissquad.attacktarget)]
                                            break
                            if thissquad.reloadtime >= thissquad.reload and (
                                    (thissquad.attacktarget == 0 and thissquad.attackpos != 0) or (thissquad.attacktarget != 0 and thissquad.attacktarget.state != 100)):
                                rangeattack.Rangearrow(thissquad, thissquad.combatpos.distance_to(thissquad.attackpos), thissquad.shootrange, self.camerascale)
                                thissquad.ammo -= 1
                                thissquad.reloadtime = 0
                            elif thissquad.attacktarget != 0 and thissquad.attacktarget.state == 100:
                                thissquad.battalion.rangecombatcheck, thissquad.battalion.attacktarget = 0, 0
                        self.combattimer = 0
                self.unitupdater.update(self.currentweather, self.squad, self.dt, self.camerascale, self.playerposlist, self.enemyposlist)
                self.effectupdater.update(self.playerarmy, self.enemyarmy, self.hitboxs, self.squad, self.squadindexlist, self.dt, self.camerascale)
                self.weatherupdater.update(self.dt)
                self.combattimer += self.dt
                self.uitimer += self.dt
                self.camera.update(self.camerapos, self.allcamera)
                self.minimap.update(self.camerascale, [self.camerapos, self.cameraupcorner],self.playerposlist,self.enemyposlist)
                self.clock.tick(60)
                self.dt = (self.clock.tick(60) / 500) * self.gamespeed
                self.timenumber.timerupdate(self.dt)
                self.uidt = self.dt
            else:
                if self.battlemenu.mode == 0:
                    for button in self.battlemenubutton:
                        if button.rect.collidepoint(self.mousepos):
                            button.image = button.images[1]
                            if mouse_up:
                                button.image = button.images[2]
                                if button.text == "Resume":
                                    self.gamestate = 1
                                    self.allui.remove(self.battlemenu, *self.battlemenubutton, *self.slidermenu, *self.valuebox)
                                elif button.text == "Encyclopedia":
                                    self.battlemenu.mode = 2
                                    self.allui.add(self.lorebook, self.lorenamelist, *self.lorebuttonui)
                                    self.lorebook.changesection(0)
                                elif button.text == "Option":
                                    self.battlemenu.changemode(1)
                                    self.allui.remove(*self.battlemenubutton)
                                    self.allui.add(*self.optionmenubutton,*self.slidermenu,*self.valuebox)
                                    self.oldsetting = self.slidermenu[0].value ## Save previous setting for in case of cancel
                                elif button.text == "Main Menu":
                                    self.allui.clear(self.screen, self.background)
                                    self.allcamera.clear(self.screen, self.background)
                                    return
                                elif button.text == "Desktop":
                                    self.allui.clear(self.screen, self.background)
                                    self.allcamera.clear(self.screen, self.background)
                                    quit()
                                break
                        else:
                            button.image = button.images[0]
                elif self.battlemenu.mode == 1:
                    for button in self.optionmenubutton:
                        if button.rect.collidepoint(self.mousepos):
                            button.image = button.images[1]
                            if mouse_up:
                                button.image = button.images[2]
                                if button.text == "Confirm":
                                    self.oldsetting = self.mixervolume
                                    pygame.mixer.music.set_volume(self.mixervolume)
                                    mainmenu.editconfig('DEFAULT', 'SoundVolume', str(slider.value), 'configuration.ini', config)
                                    self.battlemenu.changemode(0)
                                    self.allui.remove(*self.optionmenubutton,*self.slidermenu,*self.valuebox)
                                    self.allui.add(*self.battlemenubutton)
                                elif button.text == "Apply":
                                    self.oldsetting = self.mixervolume
                                    pygame.mixer.music.set_volume(self.mixervolume)
                                    mainmenu.editconfig('DEFAULT', 'SoundVolume', str(slider.value), 'configuration.ini', config)
                                elif button.text == "Cancel":
                                    self.mixervolume = self.oldsetting
                                    pygame.mixer.music.set_volume(self.mixervolume)
                                    self.slidermenu[0].update(self.mixervolume, self.valuebox[0], forcedvalue=True)
                                    self.battlemenu.changemode(0)
                                    self.allui.remove(*self.optionmenubutton,*self.slidermenu,*self.valuebox)
                                    self.allui.add(*self.battlemenubutton)
                        else:
                            button.image = button.images[0]
                    for slider in self.slidermenu:
                        if slider.rect.collidepoint(self.mousepos) and (mouse_down or mouse_up):
                            slider.update(self.mousepos, self.valuebox[0])
                            self.mixervolume = float(slider.value / 100)
                elif self.battlemenu.mode == 2:
                    if mouse_up == True:
                        for button in self.lorebuttonui:
                            if button.rect.collidepoint(self.mousepos):
                                self.lorebook.changesection(button.event)
                                break
            self.screen.blit(self.camera.image, (0,0)) ## Draw the game in camera
            self.allui.draw(self.screen)  ## Draw the UI
            # dirty = self.allui.draw(self.screen)
            pygame.display.update()
        if pygame.mixer:
            pygame.mixer.music.fadeout(1000)
        pygame.time.wait(1000)
        pygame.quit()


if __name__ == '__main__':
    main = Battle()
    main.rungame()
