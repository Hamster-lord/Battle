import csv
import datetime
import random
import ast
import re
import numpy as np
import pygame
import pygame.freetype
import os
import math

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

"""This file contains fuctions of various purposes"""

## Default game mechanic value

battlesidecal = (1, 0.5, 0.1, 0.5)  # battlesidecal is for melee combat side modifier,

## Data Loading gamescript


def makebarlist(listtodo, menuimage):
    """Make a drop down bar list option button"""
    from gamescript import gameprepare
    barlist = []
    img = load_image('bar_normal.jpg', 'ui\mainmenu_ui')
    img2 = load_image('bar_mouse.jpg', 'ui\mainmenu_ui')
    img3 = img2
    for index, bar in enumerate(listtodo):
        barimage = (img.copy(), img2.copy(), img3.copy())
        bar = gameprepare.Menubutton(images=barimage, pos=(menuimage.pos[0], menuimage.pos[1] + img.get_height() * (index + 1)), text=bar)
        barlist.append(bar)
    return barlist

def load_base_button():
    img = load_image('idle_button.png', 'ui\mainmenu_ui')
    img2 = load_image('mouse_button.png', 'ui\mainmenu_ui')
    img3 = load_image('click_button.png', 'ui\mainmenu_ui')
    return [img, img2, img3]


def text_objects(text, font):
    textSurface = font.render(text, True, (200, 200, 200))
    return textSurface, textSurface.get_rect()


def game_intro(screen, clock, introoption):
    intro = introoption
    if introoption:
        intro = True
    timer = 0
    # quote = ["Those attacker fail to learn from the mistakes of their predecessors are destined to repeat them. George Santayana", "It is more important to outhink your enemy, than to outfight him, Sun Tzu"]
    while intro:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                intro = False
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        largeText = pygame.font.Font('freesansbold.ttf', 115)
        TextSurf, TextRect = text_objects("Test Intro", largeText)
        TextRect.center = (700, 600)
        screen.blit(TextSurf, TextRect)
        pygame.display.update()
        clock.tick(60)
        timer += 1
        if timer == 1000: intro = False

def load_image(file, subfolder=""):
    """loads an image, prepares it for play"""
    import main
    main_dir = main.main_dir
    thisfile = os.path.join(main_dir, 'data', subfolder, file)
    try:
        surface = pygame.image.load(thisfile).convert_alpha()
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s' % (thisfile, pygame.get_error()))
    return surface.convert_alpha()

def load_images(subfolder=[], loadorder=True, returnorder=False):
    """loads all images(files) in folder using loadorder list file use only png file"""
    import main
    main_dir = main.main_dir
    imgs = []
    dirpath = os.path.join(main_dir, 'data')
    if subfolder != []:
        for folder in subfolder:
            dirpath = os.path.join(dirpath, folder)

    if loadorder: # load in the order of load_order file
        loadorderfile = open(dirpath + "/load_order.txt", "r")
        loadorderfile = ast.literal_eval(loadorderfile.read())
        for file in loadorderfile:
            imgs.append(load_image(dirpath + "/" + file))
    else: # load every file
        loadorderfile = [f for f in os.listdir(dirpath) if f.endswith('.' + "png")]  ## read all file
        loadorderfile.sort(key=lambda var: [int(x) if x.isdigit() else x for x in re.findall(r'[^0-9]|[0-9]+', var)])
        for file in loadorderfile:
            imgs.append(load_image(dirpath + "/" + file))

    if returnorder is False:
        return imgs
    else: # return order of the file as list
        loadorderfile = [int(name.replace(".png", "")) for name in loadorderfile]
        return imgs, loadorderfile

def loadgamedata(game):
    """Load various game data and encyclopedia object"""
    import main
    import csv
    from pathlib import Path

    main_dir = main.main_dir
    SCREENRECT = main.SCREENRECT
    Soundvolume = main.Soundvolume
    from gamescript import gameleader, gamemap, gamelongscript, gamelorebook, gameweather, gamefaction, \
        gameunitstat, gameui, gamefaction, gameunit, gamesubunit, rangeattack, gamemenu, gamepopup, gamedrama, gameprepare, gameunitedit

    #v Craete feature terrain modifier
    game.featuremod = {}
    with open(main_dir + "/data/map" + "/unit_terrainbonus.csv", encoding="utf-8", mode = "r") as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        run = 0  # for skipping the first row
        for row in rd:
            for n, i in enumerate(row):
                if run != 0:
                    if n == 12:  # effect list is at column 12
                        if "," in i:
                            row[n] = [int(item) if item.isdigit() else item for item in row[n].split(',')]
                        elif i.isdigit():
                            row[n] = [int(i)]

                    elif n in (2, 3, 4, 5, 6, 7):  # other modifer column
                        if i != "":
                            row[n] = float(i) / 100
                        else:  # empty row assign 1.0 default
                            i = 1.0

                    elif i.isdigit() or "-" in i:  # modifer bonus (including negative) in other column
                        row[n] = int(i)

            run += 1
            game.featuremod[row[0]] = row[1:]
    unitfile.close()
    #^ End feature terrain mod

    # v Create weather related class
    game.allweather = csv_read('weather.csv', ['data', 'map', 'weather'])
    weatherlist = [item[0] for item in game.allweather.values()][2:]
    strengthlist = ['Light ', 'Normal ', 'Strong ']
    game.weatherlist = []
    for item in weatherlist:
        for strength in strengthlist:
            game.weatherlist.append(strength+item)
    game.weathermatterimgs = []

    for weather in ('0', '1', '2', '3'):  # Load weather matter sprite image
        imgs = load_images(['map', 'weather', weather], loadorder=False)
        game.weathermatterimgs.append(imgs)

    game.weathereffectimgs = []
    for weather in ('0', '1', '2', '3', '4', '5', '6', '7'):  # Load weather effect sprite image
        imgs = load_images(['map', 'weather', 'effect', weather], loadorder=False)
        # imgs = []
        # for img in imgsold:
        #     img = pygame.transform.scale(img, (SCREENRECT.width, SCREENRECT.height))
        #     imgs.append(img)
        game.weathereffectimgs.append(imgs)

    imgs = load_images(['map', 'weather', 'icon'], loadorder=False)  # Load weather icon
    gameweather.Weather.images = imgs
    # ^ End weather

    #v Faction class
    gamefaction.Factiondata.main_dir = main_dir
    game.allfaction = gamefaction.Factiondata(option=game.rulesetfolder)
    imgsold = load_images(['ruleset', game.rulesetfolder.strip("/"), 'faction', 'coa'], loadorder=False)  # coa imagelist
    imgs = []
    for img in imgsold:
        imgs.append(img)
    game.coa = imgs
    game.faction_list = [item[0] for item in game.allfaction.faction_list.values()][1:]
    # ^ End faction

    # v create game map texture and their default variables
    game.featurelist = []
    with open(main_dir + "/data/map" + "/unit_terrainbonus.csv", encoding="utf-8", mode = "r") as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        for row in rd:
            game.featurelist.append(row[1])  # get terrain feature combination name for folder
    unitfile.close()
    game.featurelist = game.featurelist[1:]

    gamemap.Mapfeature.main_dir = main_dir
    gamemap.Mapfeature.featuremod = game.featuremod
    gamemap.Beautifulmap.main_dir = main_dir

    game.battlemap_base = gamemap.Basemap(1)  # create base terrain map
    game.battlemap_feature = gamemap.Mapfeature(1)  # create terrain feature map
    game.battlemap_height = gamemap.Mapheight(1)  # create height map
    game.showmap = gamemap.Beautifulmap(1)

    emptyimage = load_image('empty.png', 'map/texture')  # empty texture image
    maptexture = []
    loadtexturefolder = []
    for feature in game.featurelist:
        loadtexturefolder.append(feature.replace(" ", "").lower())  # convert terrain feature list to lower case with no space
    loadtexturefolder = list(set(loadtexturefolder))  # list of terrian folder to load
    loadtexturefolder = [item for item in loadtexturefolder if item != ""]  # For now remove terrain with no planned name/folder yet
    for index, texturefolder in enumerate(loadtexturefolder):
        imgs = load_images(['map', 'texture', texturefolder], loadorder=False)
        maptexture.append(imgs)
    gamemap.Beautifulmap.textureimages = maptexture
    gamemap.Beautifulmap.loadtexturelist = loadtexturefolder
    gamemap.Beautifulmap.emptyimage = emptyimage
    # ^ End game map

    #v Load map list
    mapfolder = Path(main_dir + '/data/ruleset/' + game.rulesetfolder + '/map')
    subdirectories = [x for x in mapfolder.iterdir() if x.is_dir()]

    for index, map in enumerate(subdirectories):
        if "custom" in str(map): # remove custom from this folder list to load
            subdirectories.pop(index)
            break

    game.maplist = [] # map name list for map selection list
    game.mapfoldername = [] # folder for reading later

    for map in subdirectories:
        game.mapfoldername.append(str(map).split("\\")[-1])
        with open(str(map) + "/info.csv", encoding="utf-8", mode = "r") as unitfile:
            rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
            for row in rd:
                if row[0] != "name":
                    game.maplist.append(row[0])
        unitfile.close()
    #^ End load map list

    #v Load custom map list
    mapfolder = Path(main_dir + "/data/ruleset/" + game.rulesetfolder + "/map/custom/")
    subdirectories = [x for x in mapfolder.iterdir() if x.is_dir()]

    game.mapcustomlist = []
    game.mapcustomfoldername = []

    for map in subdirectories:
        game.mapcustomfoldername.append(str(map).split("\\")[-1])
        with open(str(map) + "/info.csv", encoding="utf-8", mode = "r") as unitfile:
            rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
            for row in rd:
                if row[0] != "name":
                    game.mapcustomlist.append(row[0])
        unitfile.close()
    #^ End load custom map list

    game.statetext = {0: "Idle", 1: "Walking", 2: "Running", 3: "Walk (M)", 4: "Run (M)", 5: "Walk (R)", 6: "Run (R)",
                      7: "Walk (F)", 8: "Run (F)", 10: "Fighting", 11: "shooting", 65: "Sleeping", 66: "Camping", 67: "Resting", 68: "Dancing",
                      69: "Partying",95:"Disobey", 96: "Retreating", 97: "Collapse", 98: "Retreating", 99: "Broken", 100: "Destroyed"}

    # v create subunit related class
    imgsold = load_images(['ui', 'unit_ui', 'weapon'])
    imgs = []
    for img in imgsold:
        x, y = img.get_width(), img.get_height()
        img = pygame.transform.scale(img, (int(x / 1.7), int(y / 1.7)))  # scale 1.7 seem to be most fitting as a placeholder
        imgs.append(img)
    game.allweapon = gameunitstat.Weaponstat(main_dir, imgs, game.ruleset)  # Create weapon class

    imgs = load_images(['ui', 'unit_ui', 'armour'])
    game.allarmour = gameunitstat.Armourstat(main_dir, imgs, game.ruleset)  # Create armour class

    game.statusimgs = load_images(['ui', 'status_icon'], loadorder=False)
    game.roleimgs = load_images(['ui', 'role_icon'], loadorder=False)
    game.traitimgs = load_images(['ui', 'trait_icon'], loadorder=False)
    game.skillimgs = load_images(['ui', 'skill_icon'], loadorder=False)

    cooldown = pygame.Surface((game.skillimgs[0].get_width(), game.skillimgs[0].get_height()), pygame.SRCALPHA)
    cooldown.fill((230, 70, 80, 200))  # red colour filter for skill cooldown timer
    gameui.Skillcardicon.cooldown = cooldown

    activeskill = pygame.Surface((game.skillimgs[0].get_width(), game.skillimgs[0].get_height()), pygame.SRCALPHA)
    activeskill.fill((170, 220, 77, 200))  # green colour filter for skill active timer
    gameui.Skillcardicon.activeskill = activeskill

    game.gameunitstat = gameunitstat.Unitstat(main_dir, game.ruleset, game.rulesetfolder)

    gameunit.Unitarmy.status_list = game.gameunitstat.status_list
    rangeattack.Rangearrow.gamemapheight = game.battlemap_height

    imgs = load_images(['ui', 'unit_ui'])
    gamesubunit.Subunit.images = imgs
    gamesubunit.Subunit.gamemap = game.battlemap_base  # add battle map to all parentunit class
    gamesubunit.Subunit.gamemapfeature = game.battlemap_feature  # add battle map to all parentunit class
    gamesubunit.Subunit.gamemapheight = game.battlemap_height
    gamesubunit.Subunit.weapon_list = game.allweapon
    gamesubunit.Subunit.armour_list = game.allarmour
    gamesubunit.Subunit.stat_list = game.gameunitstat
    gameunitedit.Armybuildslot.images = imgs
    gameunitedit.Armybuildslot.weapon_list = game.allweapon
    gameunitedit.Armybuildslot.armour_list = game.allarmour
    gameunitedit.Armybuildslot.stat_list = game.gameunitstat

    game.squadwidth, game.squadheight = imgs[0].get_width(), imgs[0].get_height()  # size of subnit image at closest zoom
    #^ End subunit class

    #v create leader list
    imgs, order = load_images(['ruleset', game.rulesetfolder.strip("/"), 'leader', 'portrait'], loadorder=False, returnorder=True)
    game.leader_stat = gameunitstat.Leaderstat(main_dir, imgs, order, option=game.rulesetfolder)
    #^ End leader

    # v Game Effect related class
    imgs = load_images(['effect'])
    # imgs = []
    # for img in imgsold:
    # x, y = img.get_width(), img.get_height()
    # img = pygame.transform.scale(img, (int(x ), int(y / 2)))
    # imgs.append(img)
    rangeattack.Rangearrow.images = [imgs[0]]
    # ^ End game effect

    #v Encyclopedia related objects
    gamelorebook.Lorebook.concept_stat = csv_read('concept_stat.csv', ['data', 'ruleset', game.rulesetfolder.strip("/"), 'lore'])
    gamelorebook.Lorebook.concept_lore = csv_read('concept_lore.csv', ['data', 'ruleset', game.rulesetfolder.strip("/"), 'lore'])
    gamelorebook.Lorebook.history_stat = csv_read('history_stat.csv', ['data', 'ruleset', game.rulesetfolder.strip("/"), 'lore'])
    gamelorebook.Lorebook.history_lore = csv_read('history_lore.csv', ['data', 'ruleset', game.rulesetfolder.strip("/"), 'lore'])

    gamelorebook.Lorebook.faction_lore = game.allfaction.faction_list
    gamelorebook.Lorebook.unit_stat = game.gameunitstat.unit_list
    gamelorebook.Lorebook.unit_lore = game.gameunitstat.unit_lore
    gamelorebook.Lorebook.armour_stat = game.allarmour.armour_list
    gamelorebook.Lorebook.weapon_stat = game.allweapon.weapon_list
    gamelorebook.Lorebook.mount_stat = game.gameunitstat.mount_list
    gamelorebook.Lorebook.mount_armour_stat = game.gameunitstat.mount_armour_list
    gamelorebook.Lorebook.status_stat = game.gameunitstat.status_list
    gamelorebook.Lorebook.skillstat = game.gameunitstat.ability_list
    gamelorebook.Lorebook.trait_stat = game.gameunitstat.trait_list
    gamelorebook.Lorebook.leader = game.leader_stat
    gamelorebook.Lorebook.leader_lore = game.leader_stat.leader_lore
    gamelorebook.Lorebook.terrain_stat = game.featuremod
    gamelorebook.Lorebook.weather_stat = game.allweather
    gamelorebook.Lorebook.landmark_stat = None
    gamelorebook.Lorebook.unit_grade_stat = game.gameunitstat.grade_list
    gamelorebook.Lorebook.unit_class_list = game.gameunitstat.role
    gamelorebook.Lorebook.leader_class_list = game.leader_stat.leader_class
    gamelorebook.Lorebook.mount_grade_stat = game.gameunitstat.mount_grade_list
    gamelorebook.Lorebook.race_list = game.gameunitstat.race_list
    gamelorebook.Lorebook.SCREENRECT = SCREENRECT
    gamelorebook.Lorebook.main_dir = main_dir
    gamelorebook.Lorebook.statetext = game.statetext

    imgs = load_images(['ui', 'lorebook_ui'], loadorder=False)
    game.lorebook = gamelorebook.Lorebook(imgs[0]) # encyclopedia sprite
    game.lorenamelist = gamelorebook.Subsection_list(game.lorebook.rect.topleft, imgs[1])

    imgs = load_images(['ui', 'lorebook_ui', 'button'], loadorder=False)
    for index, img in enumerate(imgs):
        imgs[index] = pygame.transform.scale(img, (int(img.get_width() * game.widthadjust),
                                                    int(img.get_height() * game.heightadjust)))
    game.lorebuttonui = [
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5), game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[0], 0, 13),  # concept section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 2,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[1], 1, 13),  # history section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 3,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[2], 2, 13),  # faction section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 4,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[3], 3, 13),  # troop section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 5,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[4], 4, 13),  # troop equipment section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 6,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[5], 5, 13),  # troop status section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 7,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[6], 6, 13),  # troop ability section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 8,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[7], 7, 13),  # troop property section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 9,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2),
                        imgs[8], 8, 13),  # leader section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 10,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2), imgs[9], 9, 13),  # terrain section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 11,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2), imgs[10], 10, 13),  # weather section button
        gameui.Uibutton(game.lorebook.rect.topleft[0] + (imgs[0].get_width() + 5) * 13,
                        game.lorebook.rect.topleft[1] - (imgs[0].get_height() / 2), imgs[12], 19, 13),  # close button
        gameui.Uibutton(game.lorebook.rect.bottomleft[0] + (imgs[13].get_width()), game.lorebook.rect.bottomleft[1] - imgs[13].get_height(),
                        imgs[13], 20, 13),  # previous page button
        gameui.Uibutton(game.lorebook.rect.bottomright[0] - (imgs[14].get_width()), game.lorebook.rect.bottomright[1] - imgs[14].get_height(),
                        imgs[14], 21, 13)]  # next page button
    game.pagebutton = (game.lorebuttonui[12], game.lorebuttonui[13])
    game.lorescroll = gameui.Uiscroller(game.lorenamelist.rect.topright, game.lorenamelist.image.get_height(),
                                        game.lorebook.max_subsection_show, layer=25)  # add subsection list scroller
    #^ End encyclopedia objects

    # v Create battle game ui objects
    game.minimap = gameui.Minimap((SCREENRECT.width, SCREENRECT.height))

    #Popup Ui
    imgs = load_images(['ui', 'popup_ui', 'terraincheck'], loadorder=False)
    gamepopup.Terrainpopup.images = imgs
    gamepopup.Terrainpopup.SCREENRECT = SCREENRECT
    imgs = load_images(['ui', 'popup_ui', 'dramatext'], loadorder=False)
    gamedrama.Textdrama.images = imgs

    #Load all image of ui and icon from folder
    topimage = load_images(['ui', 'battle_ui'])
    iconimage = load_images(['ui', 'battle_ui', 'topbar_icon'])

    #Army select list ui
    game.armyselector = gameui.Armyselect((0, 0), topimage[30])
    game.selectscroll = gameui.Uiscroller(game.armyselector.rect.topright, topimage[30].get_height(),
                                          game.armyselector.max_row_show)  # scroller for army select ui

    #Right top bar ui that show rough information of selected battalions
    game.gameui = [
        gameui.Gameui(X=SCREENRECT.width - topimage[0].get_size()[0] / 2, Y=topimage[0].get_size()[1] / 2, image=topimage[0],
                      icon=iconimage, uitype="topbar")]
    game.gameui[0].options1 = game.statetext

    game.inspectuipos = [game.gameui[0].rect.bottomleft[0] - game.squadwidth / 1.25,
                         game.gameui[0].rect.bottomleft[1] - game.squadheight / 3]

    #Left top command ui with leader and parentunit behavious button
    iconimage = load_images(['ui', 'battle_ui', 'commandbar_icon'])
    game.gameui.append(gameui.Gameui(X=topimage[1].get_size()[0] / 2, Y=(topimage[1].get_size()[1] / 2) + game.armyselector.image.get_height(),
                                     image=topimage[1], icon=iconimage,
                                     uitype="commandbar"))

    #Subunit information card ui
    game.gameui.append(
        gameui.Gameui(X=SCREENRECT.width - topimage[2].get_size()[0] / 2, Y=(topimage[0].get_size()[1] * 2.5) + topimage[5].get_size()[1],
                      image=topimage[2], icon="", uitype="unitcard"))
    game.gameui[2].featurelist = game.featurelist  # add terrain feature list name to subunit card

    game.gameui.append(gameui.Gameui(X=SCREENRECT.width - topimage[5].get_size()[0] / 2, Y=topimage[0].get_size()[1] * 4,
                                     image=topimage[5], icon="", uitype="armybox"))  # inspect ui that show subnit in selected parentunit
    #v Subunit shown in inspect ui
    width, height = game.inspectuipos[0], game.inspectuipos[1]
    subunitnum = 0  # Number of subnit based on the position in row and column
    imgsize = (game.squadwidth, game.squadheight)
    game.inspectsubunit = []
    for subnit in list(range(0,64)):
        width += imgsize[0]
        game.inspectsubunit.append(gameui.Inspectsubunit((width, height)))
        subunitnum += 1
        if subunitnum == 8:  # Reach the last subnit in the row, go to the next one
            width = game.inspectuipos[0]
            height += imgsize[1]
            subunitnum = 0
    #^ End subunit shown

    #Time bar ui
    game.timeui = gameui.Timeui(game.armyselector.rect.topright, topimage[31])
    game.timenumber = gameui.Timer(game.timeui.rect.topleft)  # time number on time ui
    game.speednumber = gameui.Speednumber((game.timeui.rect.center[0] + 40, game.timeui.rect.center[1]),
                                          1)  # game speed number on the time ui

    image = pygame.Surface((topimage[31].get_width(), 15))
    game.scaleui = gameui.Scaleui(game.timeui.rect.bottomleft, image)

    #Button related to subunit card and command
    game.buttonui = [gameui.Uibutton(game.gameui[2].X - 152, game.gameui[2].Y + 10, topimage[3], 0),  # subunit card description button
                     gameui.Uibutton(game.gameui[2].X - 152, game.gameui[2].Y - 70, topimage[4], 1),  # subunit card stat button
                     gameui.Uibutton(game.gameui[2].X - 152, game.gameui[2].Y - 30, topimage[7], 2),  # subunit card skill button
                     gameui.Uibutton(game.gameui[2].X - 152, game.gameui[2].Y + 50, topimage[22], 3),  # subunit card equipment button
                     gameui.Uibutton(game.gameui[0].X - 206, game.gameui[0].Y - 1, topimage[6], 1),  # army inspect open/close button
                     gameui.Uibutton(game.gameui[1].X - 115, game.gameui[1].Y + 26, topimage[8], 0),  # split by middle coloumn button
                     gameui.Uibutton(game.gameui[1].X - 115, game.gameui[1].Y + 56, topimage[9], 1),  # split by middle row button
                     gameui.Uibutton(game.gameui[1].X + 100, game.gameui[1].Y + 56, topimage[14], 1)]  # decimation button

    #Behaviour button that once click switch to other mode for subunit behaviour
    game.switch_button = [gameui.Switchuibutton(game.gameui[1].X - 40, game.gameui[1].Y + 96, topimage[10:14]),  # skill condition button
                          gameui.Switchuibutton(game.gameui[1].X - 80, game.gameui[1].Y + 96, topimage[15:17]),  # fire at will button
                          gameui.Switchuibutton(game.gameui[1].X, game.gameui[1].Y + 96, topimage[17:20]),  # behaviour button
                          gameui.Switchuibutton(game.gameui[1].X + 40, game.gameui[1].Y + 96, topimage[20:22]),  # shoot range button
                          gameui.Switchuibutton(game.gameui[1].X - 125, game.gameui[1].Y + 96, topimage[35:38]),  # arcshot button
                          gameui.Switchuibutton(game.gameui[1].X + 80, game.gameui[1].Y + 96, topimage[38:40]),  # toggle run button
                          gameui.Switchuibutton(game.gameui[1].X + 120, game.gameui[1].Y + 96, topimage[40:43])]  # toggle melee mode

    game.eventlog = gameui.Eventlog(topimage[23], (0, SCREENRECT.height))

    game.logscroll = gameui.Uiscroller(game.eventlog.rect.topright, topimage[23].get_height(), game.eventlog.max_row_show)  # event log scroller
    game.eventlog.logscroll = game.logscroll  # Link scroller to ui since it is easier to do here with the current order
    gamesubunit.Subunit.eventlog = game.eventlog  # Assign eventlog to subunit class to broadcast event to the log

    game.buttonui.append(gameui.Uibutton(game.eventlog.pos[0] + (topimage[24].get_width() / 2),
                                         game.eventlog.pos[1] - game.eventlog.image.get_height() - (topimage[24].get_height() / 2), topimage[24],
                                         0))  # war tab log button

    game.buttonui += [gameui.Uibutton(game.buttonui[8].pos[0] + topimage[24].get_width(), game.buttonui[8].pos[1], topimage[25], 1),
                      # army tab log button
                      gameui.Uibutton(game.buttonui[8].pos[0] + (topimage[24].get_width() * 2), game.buttonui[8].pos[1], topimage[26], 2),
                      # leader tab log button
                      gameui.Uibutton(game.buttonui[8].pos[0] + (topimage[24].get_width() * 3), game.buttonui[8].pos[1], topimage[27], 3),
                      # subunit tab log button
                      gameui.Uibutton(game.buttonui[8].pos[0] + (topimage[24].get_width() * 5), game.buttonui[8].pos[1], topimage[28], 4),
                      # delete current tab log button
                      gameui.Uibutton(game.buttonui[8].pos[0] + (topimage[24].get_width() * 6), game.buttonui[8].pos[1], topimage[29], 5),
                      # delete all log button
                      gameui.Uibutton(game.timeui.rect.center[0] - 30, game.timeui.rect.center[1], topimage[32], 0),  # time pause button
                      gameui.Uibutton(game.timeui.rect.center[0], game.timeui.rect.center[1], topimage[33], 1),  # time decrease button
                      gameui.Uibutton(game.timeui.rect.midright[0] - 60, game.timeui.rect.center[1], topimage[34], 2)]  # time increase button

    game.screenbuttonlist = game.buttonui[8:17]
    game.unitcardbutton = game.buttonui[0:4]
    game.inspectbutton = game.buttonui[4]
    game.col_split_button = game.buttonui[5]  # parentunit split by column button
    game.rowsplitbutton = game.buttonui[6]  # parentunit split by row button

    game.timebutton = game.buttonui[14:17]
    game.battleui.add(game.buttonui[8:17])
    game.battleui.add(game.logscroll, game.selectscroll)

    gameui.Selectedsquad.image = topimage[-1] # squad border image always the last one
    game.inspectselectedborder = gameui.Selectedsquad((15000, 15000)) #yellow border on selected subnit in inspect ui
    game.mainui.remove(game.inspectselectedborder) #remove subnit border sprite from main menu drawer
    game.terraincheck = gamepopup.Terrainpopup() #popup box that show terrain information when right click on map
    game.button_name_popup = gamepopup.Onelinepopup() #popup box that show button name when mouse over
    game.leaderpopup = gamepopup.Onelinepopup() #popup box that show leader name when mouse over
    game.effectpopup = gamepopup.Effecticonpopup() #popup box that show skill/trait/status name when mouse over

    gamedrama.Textdrama.SCREENRECT = SCREENRECT
    game.textdrama = gamedrama.Textdrama() #messege at the top of screen that show up for important event

    game.fpscount = gameui.FPScount() #FPS number counter
    # ^ End game ui

    # v Esc menu related objects
    imgs = load_images(['ui', 'battlemenu_ui'], loadorder=False)
    gamemenu.Escbox.images = imgs  # Create ESC Menu box
    gamemenu.Escbox.SCREENRECT = SCREENRECT
    game.battle_menu = gamemenu.Escbox()

    buttonimage = load_images(['ui', 'battlemenu_ui', 'button'], loadorder=False)
    menurectcenter0 = game.battle_menu.rect.center[0]
    menurectcenter1 = game.battle_menu.rect.center[1]

    game.battle_menu_button = [
        gamemenu.Escbutton(buttonimage, (menurectcenter0, menurectcenter1 - 100), text="Resume", size=14),
        gamemenu.Escbutton(buttonimage, (menurectcenter0, menurectcenter1 - 50), text="Encyclopedia", size=14),
        gamemenu.Escbutton(buttonimage, (menurectcenter0, menurectcenter1), text="Option", size=14),
        gamemenu.Escbutton(buttonimage, (menurectcenter0, menurectcenter1 + 50), text="Main Menu", size=14),
        gamemenu.Escbutton(buttonimage, (menurectcenter0, menurectcenter1 + 100), text="Desktop", size=14)]

    game.escoption_menu_button = [
        gamemenu.Escbutton(buttonimage, (menurectcenter0 - 50, menurectcenter1 + 70), text="Confirm", size=14),
        gamemenu.Escbutton(buttonimage, (menurectcenter0 + 50, menurectcenter1 + 70), text="Apply", size=14),
        gamemenu.Escbutton(buttonimage, (menurectcenter0 + 150, menurectcenter1 + 70), text="Cancel", size=14)]

    sliderimage = load_images(['ui', 'battlemenu_ui', 'slider'], loadorder=False)
    game.escslidermenu = [
        gamemenu.Escslidermenu(sliderimage[0], sliderimage[1:3], (menurectcenter0 * 1.1, menurectcenter1), Soundvolume,
                               0)]
    game.escvaluebox = [gamemenu.Escvaluebox(sliderimage[3], (game.battle_menu.rect.topright[0] * 1.2, menurectcenter1), Soundvolume)]
    # ^ End esc menu objects

def create_troop_stat(self, team, stat, unitscale, starthp, startstamina):
    """Setup subunit troop stat"""
    self.name = stat[0]  # name according to the preset
    self.unitclass = stat[1]  # used to determine whether to use melee or range weapon as icon
    self.grade = stat[2]  # training level/class grade
    self.race = stat[3]  # creature race
    self.trait = stat[4]  # trait list from preset
    self.trait = self.trait + self.stat_list.grade_list[self.grade][-1]  # add trait from grade
    skill = stat[5]  # skill list according to the preset
    self.skill_cooldown = {}
    self.cost = stat[6]
    self.base_attack = round(stat[8] + int(self.stat_list.grade_list[self.grade][1]), 0)  # base melee attack with grade bonus
    self.base_meleedef = round(stat[9] + int(self.stat_list.grade_list[self.grade][2]), 0)  # base melee defence with grade bonus
    self.base_rangedef = round(stat[10] + int(self.stat_list.grade_list[self.grade][2]), 0)  # base range defence with grade bonus
    self.armourgear = stat[11]  # armour equipement
    self.base_armour = self.armour_list.armour_list[self.armourgear[0]][1] \
                       * self.armour_list.quality[self.armourgear[1]]  # Armour stat is cal from based armour * quality
    self.base_accuracy = stat[12] + int(self.stat_list.grade_list[self.grade][4])
    self.basesight = stat[13]  # base sight range
    self.ammo = stat[14]  # amount of ammunition
    self.base_reload = stat[15] + int(self.stat_list.grade_list[self.grade][5])
    self.reloadtime = 0  # Unit can only refill magazine when reloadtime is equal or more than reload stat
    self.base_charge = stat[16]
    self.base_chargedef = 50  # All infantry subunit has default 50 charge defence
    self.chargeskill = stat[17]  # For easier reference to check what charge skill this subunit has
    self.attacking = False  # For checking if parentunit in attacking state or not for using charge skill
    skill = [self.chargeskill] + skill  # Add charge skill as first item in the list
    self.skill = {x: self.stat_list.ability_list[x].copy() for x in skill if x != 0 and x in self.stat_list.ability_list}  # grab skill stat into dict
    self.troophealth = round(stat[18] * self.stat_list.grade_list[self.grade][7])  # Health of each troop
    self.stamina = int(stat[19] * self.stat_list.grade_list[self.grade][8] * (startstamina / 100))  # starting stamina with grade
    self.mana = stat[20]  # Resource for magic skill

    # v Weapon stat
    self.meleeweapon = stat[21]  # melee weapon equipment
    self.rangeweapon = stat[22]  # range weapon equipment
    self.dmg = self.weapon_list.weapon_list[self.meleeweapon[0]][1] * self.weapon_list.quality[self.meleeweapon[1]]  # damage for melee
    self.penetrate = 1 - (self.weapon_list.weapon_list[self.meleeweapon[0]][2] * self.weapon_list.quality[
        self.meleeweapon[1]] / 100)  # the lower the number the less effectiveness of enemy armour
    if self.penetrate > 1:
        self.penetrate = 1  # melee penetrate cannot be higher than 1
    elif self.penetrate < 0:
        self.penetrate = 0  # melee penetrate cannot be lower than 0
    self.rangedmg = self.weapon_list.weapon_list[self.rangeweapon[0]][1] * self.weapon_list.quality[self.rangeweapon[1]]  # damage for range
    self.rangepenetrate = 1 - (self.weapon_list.weapon_list[self.rangeweapon[0]][2] * self.weapon_list.quality[self.rangeweapon[1]] / 100)
    self.magazinesize = self.weapon_list.weapon_list[self.rangeweapon[0]][6] # can shoot how many time before have to reload
    self.base_range = int(self.weapon_list.weapon_list[self.rangeweapon[0]][7] * self.weapon_list.quality[self.rangeweapon[1]]) # base weapon range depend on weapon range stat and quality
    self.arrowspeed = self.weapon_list.weapon_list[self.rangeweapon[0]][8] # travel speed of range attack
    self.trait = self.trait + self.weapon_list.weapon_list[self.meleeweapon[0]][4]  # apply trait from range weapon
    self.trait = self.trait + self.weapon_list.weapon_list[self.rangeweapon[0]][4]  # apply trait from melee weapon
    if self.rangepenetrate > 1:
        self.rangepenetrate = 1  # range penetrate cannot be higher than 1
    elif self.rangepenetrate < 0:
        self.rangepenetrate = 0  # range penetrate cannot be lower than 0
    # ^ End weapon stat

    self.base_morale = int(stat[23] + int(self.stat_list.grade_list[self.grade][9]))  # morale with grade bonus
    self.base_discipline = int(stat[24] + int(self.stat_list.grade_list[self.grade][10]))  # discilpline with grade bonus
    self.mental = stat[25] + int(self.stat_list.grade_list[self.grade][11]) # mental resistance from morale damage and mental status effect
    self.troopnumber = int(stat[27] * unitscale[team - 1] * starthp / 100)  # number of starting troop, team -1 to become list index
    self.base_speed = 50  # All infantry has base speed at 50
    self.unit_type = stat[28] - 1  # 0 is melee infantry and 1 is range for command buff
    self.featuremod = 1  # the starting column in unit_terrainbonus of infantry

    # v Mount stat
    self.mount = self.stat_list.mount_list[stat[29][0]]  # mount this subunit use
    self.mountgrade = self.stat_list.mount_grade_list[stat[29][1]]
    self.mountarmour = self.stat_list.mount_armour_list[stat[29][2]]
    if stat[29][0] != 1:  # have mount, add mount stat with its grade to subunit stat
        self.base_chargedef = 25  # charge defence only 25 for cav
        self.base_speed = (self.mount[1] + self.mountgrade[1])  # use mount base speed instead
        self.troophealth += (self.mount[2] * self.mountgrade[3]) + self.mountarmour[1]  # Add mount health to the troop health
        self.base_charge += (self.mount[3] + self.mountgrade[2])  # Add charge power of mount to troop
        self.stamina += self.mount[4]
        self.trait = self.trait + self.mount[6]  # Apply mount trait to subunit
        self.unit_type = 2  # If subunit has mount, count as cav for command buff
        self.featuremod = 4  # the starting column in unit_terrainbonus of cavalry
    # ^ End mount stat

    self.weight = self.weapon_list.weapon_list[stat[21][0]][3] + self.weapon_list.weapon_list[stat[22][0]][3] + \
                  self.armour_list.armour_list[stat[11][0]][2] + self.mountarmour[2]  # Weight from both melee and range weapon and armour
    if self.unit_type == 2: # cavalry has half weight penalty
        self.weight = self.weight/2

    self.trait = self.trait + self.armour_list.armour_list[stat[11][0]][4]  # Apply armour trait to subunit
    self.base_speed = round((self.base_speed * ((100 - self.weight) / 100)) + int(self.stat_list.grade_list[self.grade][3]),
                            0)  # finalise base speed with weight and grade bonus
    self.description = stat[-1]  # subunit description for inspect ui
    # if self.hidden

    # v Elemental stat
    self.base_elemmelee = 0  # start with physical element for melee weapon
    self.base_elemrange = 0  # start with physical for range weapon
    self.elem_count = [0, 0, 0, 0, 0]  # Elemental threshold count in this order fire,water,air,earth,poison
    self.temp_count = 0  # Temperature threshold count
    fire_res = 0  # resistance to fire, will be combine into list
    water_res = 0  # resistance to water, will be combine into list
    air_res = 0  # resistance to air, will be combine into list
    earth_res = 0  # resistance to earth, will be combine into list
    self.magic_res = 0  # Resistance to any magic
    self.heat_res = 0  # Resistance to heat temperature
    self.cold_res = 0  # Resistance to cold temperature
    poison_res = 0  # resistance to poison, will be combine into list
    # ^ End elemental

    self.crit_effect = 1  # critical extra modifier
    self.front_dmg_effect = 1  # Some skill affect only frontal combat damage
    self.side_dmg_effect = 1  # Some skill affect damage for side combat as well (AOE)
    self.corner_atk = False  # Check if subunit can attack corner enemy or not
    self.flankbonus = 1  # Combat bonus when flanking
    self.base_auth_penalty = 0.1  # penalty to authority when bad event happen
    self.bonus_morale_dmg = 0  # extra morale damage
    self.bonus_stamina_dmg = 0  # extra stamina damage
    self.auth_penalty = 0.1  # authority penalty for certain activities/order
    self.base_hpregen = 0  # hp regeneration modifier, will not resurrect dead troop by default
    self.base_staminaregen = 2  # stamina regeneration modifier
    self.moraleregen = 2  # morale regeneration modifier
    self.status_effect = {}  # list of current status effect
    self.skill_effect = {}  # list of activate skill effect
    self.base_inflictstatus = {}  # list of status that this subunit will inflict to enemy when attack
    self.specialstatus = []

    # v Set up trait variable
    self.arcshot = False
    self.anti_inf = False
    self.anti_cav = False
    self.shootmove = False
    self.agileaim = False
    self.no_range_penal = False
    self.long_range_acc = False
    self.ignore_chargedef = False
    self.ignore_def = False
    self.fulldef = False
    self.temp_fulldef = False
    self.backstab = False
    self.oblivious = False
    self.flanker = False
    self.unbreakable = False
    self.temp_unbraekable = False
    self.stationplace = False
    # ^ End setup trait variable

    # v Add trait to base stat
    self.trait = list(set([trait for trait in self.trait if trait != 0]))
    if len(self.trait) > 0:
        self.trait = {x: self.stat_list.trait_list[x] for x in self.trait if
                      x in self.stat_list.trait_list}  # Any trait not available in ruleset will be ignored
        for trait in self.trait.values():  # add trait modifier to base stat
            self.base_attack *= trait[3]
            self.base_meleedef *= trait[4]
            self.base_rangedef *= trait[5]
            self.base_armour += trait[6]
            self.base_speed *= trait[7]
            self.base_accuracy *= trait[8]
            self.base_range *= trait[9]
            self.base_reload *= trait[10]
            self.base_charge *= trait[11]
            self.base_chargedef += trait[12]
            self.base_hpregen += trait[13]
            self.base_staminaregen += trait[14]
            self.base_morale += trait[15]
            self.base_discipline += trait[16]
            self.crit_effect += trait[17]
            fire_res += (trait[21] / 100)  # percentage, 1 mean perfect resistance, 0 mean none
            water_res += (trait[22] / 100)
            air_res += (trait[23] / 100)
            earth_res += (trait[24] / 100)
            self.magic_res += (trait[25] / 100)
            self.heat_res += (trait[26] / 100)
            self.cold_res += (trait[27] / 100)
            poison_res += (trait[28] / 100)
            self.mental += trait[31]
            if trait[32] != [0]:
                for effect in trait[32]:
                    self.base_inflictstatus[effect] = trait[1]
            # self.base_elemmelee =
            # self.base_elemrange =

        if 3 in self.trait:  # Varied training
            self.base_attack *= (random.randint(80, 120) / 100)
            self.base_meleedef *= (random.randint(80, 120) / 100)
            self.base_rangedef *= (random.randint(80, 120) / 100)
            # self.base_armour *= (random.randint(80, 120) / 100)
            self.base_speed *= (random.randint(80, 120) / 100)
            self.base_accuracy *= (random.randint(80, 120) / 100)
            # self.base_range *= (random.randint(80, 120) / 100)
            self.base_reload *= (random.randint(80, 120) / 100)
            self.base_charge *= (random.randint(80, 120) / 100)
            self.base_chargedef *= (random.randint(80, 120) / 100)
            self.base_morale += random.randint(-10, 10)
            self.base_discipline += random.randint(-10, 10)
            self.mental += random.randint(-10, 10)

        if 149 in self.trait:  # Impetuous
            self.base_auth_penalty += 0.5

        # v Change trait variable
        if 16 in self.trait: self.arcshot = True  # can shoot in arc
        if 17 in self.trait: self.agileaim = True  # gain bonus accuracy when shoot while moving
        if 18 in self.trait: self.shootmove = True  # can shoot and move at same time
        if 29 in self.trait: self.ignore_chargedef = True  # ignore charge defence completely
        if 30 in self.trait: self.ignore_def = True  # ignore defence completely
        if 34 in self.trait: self.fulldef = True  # full effective defence for all side
        if 33 in self.trait: self.backstab = True  # bonus on rear attack
        if 47 in self.trait: self.flanker = True  # bonus on flank attack
        if 55 in self.trait: self.oblivious = True  # more penalty on flank/rear defend
        if 73 in self.trait: self.no_range_penal = True  # no range penalty
        if 74 in self.trait: self.long_range_acc = True  # less range penalty

        if 111 in self.trait:
            self.unbreakable = True  # always unbreakable
            self.temp_unbraekable = True
        # ^ End change trait variable
    # ^ End add trait to stat

    # self.loyalty
    self.elem_res = (fire_res, water_res, air_res, earth_res, poison_res)  # list of elemental resistance
    self.maxstamina, self.stamina75, self.stamina50, self.stamina25, = self.stamina, round(self.stamina * 0.75), round(
        self.stamina * 0.5), round(self.stamina * 0.25)
    self.unit_health = self.troophealth * self.troopnumber  # Total health of subunit from all troop
    self.last_health_state = 4  # state start at full
    self.last_stamina_state = 4

    self.base_reload = self.weapon_list.weapon_list[self.rangeweapon[0]][5] + \
                       ((self.base_reload - 50) * self.weapon_list.weapon_list[self.rangeweapon[0]][5] / 100) # final reload speed from weapon and skill

    # v Stat variable after receive modifier effect from various sources, used for activity and effect calculation
    self.maxmorale = self.base_morale
    self.attack = self.base_attack
    self.meleedef = self.base_meleedef
    self.rangedef = self.base_rangedef
    self.armour = self.base_armour
    self.speed = self.base_speed
    self.accuracy = self.base_accuracy
    self.reload = self.base_reload
    self.morale = self.base_morale
    self.discipline = self.base_discipline
    self.shootrange = self.base_range
    self.charge = self.base_charge
    self.chargedef = self.base_chargedef
    # ^ End stat for status effect

    if self.mental < 0: # cannot be negative
        self.mental = 0
    elif self.mental > 200: # cannot exceed 100
        self.mental = 200
    self.mentaltext = int(self.mental - 100)
    self.mental = (200 - self.mental) / 100 # convert to percentage

    self.elemmelee = self.base_elemmelee
    self.elemrange = self.base_elemrange
    self.maxhealth, self.health75, self.health50, self.health25, = self.unit_health, round(self.unit_health * 0.75), round(
        self.unit_health * 0.5), round(self.unit_health * 0.25)  # health percentage
    self.oldlasthealth, self.old_last_stamina = self.unit_health, self.stamina  # save previous health and stamina in previous update
    self.maxtroop = self.troopnumber  # max number of troop at the start
    self.moralestate = round(self.base_morale / self.maxmorale)  # turn into percentage
    self.staminastate = round((self.stamina * 100) / self.maxstamina)  # turn into percentage
    self.staminastate_cal = self.staminastate / 100  # for using as modifer on stat

def csv_read(file, subfolder=[], outputtype=0, defaultmaindir=True):
    """output type 0 = dict, 1 = list"""
    import main
    main_dir = ""
    if defaultmaindir:
        main_dir = main.main_dir
    returnoutput = {}
    if outputtype == 1: returnoutput = []

    folderlist = ""
    for folder in subfolder:
        folderlist += "/" + folder
    folderlist += "/" + file
    with open(main_dir + folderlist, encoding="utf-8", mode = "r") as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        for row in rd:
            for n, i in enumerate(row):
                if i.isdigit() or ("-" in i and re.search("[a-zA-Z]", i) is None):
                    row[n] = int(i)
            if outputtype == 0:
                returnoutput[row[0]] = row[1:]
            elif outputtype == 1:
                returnoutput.append(row)
        unitfile.close()
    return returnoutput


def load_sound(file):
    import main
    main_dir = main.main_dir
    file = os.path.join(main_dir, "data/sound/", file)
    sound = pygame.mixer.Sound(file)
    return sound

def editconfig(section, option, value, filename, config):
    config.set(section, option, value)
    with open(filename, 'w') as configfile:
        config.write(configfile)

## mainmenu related script


## Other battle gamescript

def convertweathertime(weatherevent):
    for index, item in enumerate(weatherevent):
        newtime = datetime.datetime.strptime(item[1], "%H:%M:%S").time()
        newtime = datetime.timedelta(hours=newtime.hour, minutes=newtime.minute, seconds=newtime.second)
        weatherevent[index] = [item[0], newtime, item[2]]

def traitskillblit(self):
    from gamescript import gameui
    import main
    SCREENRECT = main.SCREENRECT

    """For blitting skill and trait icon into subunit info ui"""
    position = self.gameui[2].rect.topleft
    position = [position[0] + 70, position[1] + 60] # start position
    startrow = position[0]

    for icon in self.skill_icon.sprites():
        icon.kill()

    for trait in self.gameui[2].value2[0]:
        self.skill_icon.add(gameui.Skillcardicon(self.traitimgs[0], (position[0], position[1]), 0, id=trait))  # For now use placeholder image 0
        position[0] += 40
        if position[0] >= SCREENRECT.width:
            position[1] += 30
            position[0] = startrow

    position = self.gameui[2].rect.topleft
    position = [position[0] + 70, position[1] + 100]
    startrow = position[0]

    for skill in self.gameui[2].value2[1]:
        self.skill_icon.add(gameui.Skillcardicon(self.skillimgs[0], (position[0], position[1]), 1, id=skill))  # For now use placeholder image 0
        position[0] += 40
        if position[0] >= SCREENRECT.width:
            position[1] += 30
            position[0] = startrow

def effecticonblit(self):
    """For blitting all status effect icon"""
    from gamescript import gameui
    import main
    SCREENRECT = main.SCREENRECT

    position = self.gameui[2].rect.topleft
    position = [position[0] + 70, position[1] + 140]
    startrow = position[0]

    for icon in self.effect_icon.sprites():
        icon.kill()

    for status in self.gameui[2].value2[4]:
        self.effect_icon.add(gameui.Skillcardicon(self.statusimgs[0], (position[0], position[1]), 4, id=status))
        position[0] += 40
        if position[0] >= SCREENRECT.width:
            position[1] += 30
            position[0] = startrow

def countdownskillicon(self):
    """count down timer on skill icon for activate and cooldown time"""
    for skill in self.skill_icon:
        if skill.type == 1: # only do skill icon not trait
            cd = 0
            activetime = 0
            if skill.gameid in self.gameui[2].value2[2]:
                cd = int(self.gameui[2].value2[2][skill.gameid])
            if skill.gameid in self.gameui[2].value2[3]:
                activetime = int(self.gameui[2].value2[3][skill.gameid][3])
            skill.iconchange(cd, activetime)
    # for effect in self.effect_icon:
    #     cd = 0
    #     if effect.id in self.gameui[2].value2[4]:
    #         cd = int(self.gameui[2].value2[4][effect.id][3])
    #     effect.iconchange(cd, 0)

## Battle Start related gamescript

def addarmy(squadlist, position, gameid, colour, leader, leaderstat, unitstat, control, coa, command, startangle,starthp,startstamina,team):
    """Create batalion object into the battle and leader of the parentunit"""
    from gamescript import gameunit, gameleader
    oldsquadlist = squadlist[~np.all(squadlist == 0, axis=1)] # remove whole empty column in subunit list
    squadlist = oldsquadlist[:, ~np.all(oldsquadlist == 0, axis=0)] # remove whole empty row in subunit list
    army = gameunit.Unitarmy(position, gameid, squadlist, colour, control, coa, command, abs(360 - startangle),starthp,startstamina,team)

    # add leader
    army.leader = [gameleader.Leader(leader[0], leader[4], 0, army, leaderstat),
                   gameleader.Leader(leader[1], leader[5], 1, army, leaderstat),
                   gameleader.Leader(leader[2], leader[6], 2, army, leaderstat),
                   gameleader.Leader(leader[3], leader[7], 3, army, leaderstat)]
    return army


def unitsetup(maingame):
    """read parentunit from unit_pos(source) file and create object with addarmy function"""
    import main
    main_dir = main.main_dir
    from gamescript import gamesubunit
    ## defaultarmy = np.array([[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],
                             # [0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]])
    letterboard = ("a", "b", "c", "d", "e", "f", "g", "h") # letter according to subunit position in inspect ui similar to chess board
    numberboard = ("8", "7", "6", "5", "4", "3", "2", "1") # same as above
    boardpos = []
    for dd in numberboard:
        for ll in letterboard:
            boardpos.append(ll + dd)
    squadindexlist = [] # squadindexlist is list of every subunit index in the game for indexing the subunit group
    squadindex = 0 #  squadindex is list index for all subunit group
    squadgameid = 10000
    teamstart = [0, 0, 0]
    teamcolour = maingame.teamcolour
    teamarmy = (maingame.team0army, maingame.team1army, maingame.team2army)

    with open(main_dir + "/data/ruleset" + maingame.rulesetfolder + "/map/" + maingame.mapselected + "/unit_pos" + maingame.source + ".csv", encoding="utf-8", mode = "r") as unitfile:
        rd = csv.reader(unitfile, quoting=csv.QUOTE_ALL)
        for row in rd:
            for n, i in enumerate(row):
                if i.isdigit():
                    row[n] = int(i)
                if n in range(1, 12):
                    row[n] = [int(item) if item.isdigit() else item for item in row[n].split(',')]
            control = False

            if maingame.playerteam == row[16] or maingame.enactment: # player can control only his team or both in enactment mode
                control = True
            colour =  teamcolour[row[16]]
            teamstart[row[16]] += 1
            whicharmy = teamarmy[row[16]]

            command = False # Not commander parentunit by default
            if len(whicharmy) == 0: # First parentunit is commander
                command = True
            coa = pygame.transform.scale(maingame.coa[row[12]], (60, 60)) # get coa image and scale smaller to fit ui

            army = addarmy(np.array([row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]), (row[9][0], row[9][1]), row[0],
                           colour, row[10] + row[11], maingame.leader_stat, maingame.gameunitstat, control,
                           coa, command, row[13], row[14], row[15], row[16])
            whicharmy.add(army)
            armysquadindex = 0 # armysquadindex is list index for subunit list in a specific army

            #v Setup subunit in army to subunit group
            row, column = 0, 0
            maxcolumn = len(army.armysubunit[0])
            for squadnum in np.nditer(army.armysubunit, op_flags=['readwrite'], order='C'):
                if squadnum != 0:
                    addsubunit = gamesubunit.Subunit(squadnum, squadgameid, army, army.subunit_position_list[armysquadindex],
                                                     army.starthp, army.startstamina, maingame.unitscale)
                    maingame.subunit.add(addsubunit)
                    addsubunit.board_pos = boardpos[armysquadindex]
                    squadnum[...] = squadgameid
                    army.subunit_sprite_array[row][column] = addsubunit
                    army.subunit_sprite.append(addsubunit)
                    squadindexlist.append(squadgameid)
                    squadgameid += 1
                    squadindex += 1
                else:
                    army.subunit_sprite_array[row][column] = None # replace numpy None with python None

                column += 1
                if column == maxcolumn:
                    column = 0
                    row += 1
                armysquadindex += 1
            #^ End subunit setup

    unitfile.close()

## Battle related gamescript

def setrotate(self, settarget=None):
    """set base_target and new angle for sprite rotation"""
    if settarget is None: # For auto chase rotate
        myradians = math.atan2(self.base_target[1] - self.base_pos[1], self.base_target[0] - self.base_pos[0])
    else: # Command move or rotate
        myradians = math.atan2(settarget[1] - self.base_pos[1], settarget[0] - self.base_pos[0])
    newangle = math.degrees(myradians)

    # """upper left -"""
    if newangle >= -180 and newangle <= -90:
        newangle = -newangle - 90

    # """upper right +"""
    elif newangle > -90 and newangle < 0:
        newangle = (-newangle) - 90

    # """lower right -"""
    elif newangle >= 0 and newangle <= 90:
        newangle = -(newangle + 90)

    # """lower left +"""
    elif newangle > 90 and newangle <= 180:
        newangle = 270 - newangle

    return round(newangle)

def rotationxy(self, origin, point, angle):
    ox, oy = origin
    px, py = point
    x = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    y = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return pygame.Vector2(x, y)

def combatpathfind(self):
    # v Pathfinding
    self.combat_move_queue = []
    movearray = self.maingame.subunitposarray.copy()
    intbasetarget = (int(self.close_target.base_pos[0]), int(self.close_target.base_pos[1]))
    for y in self.close_target.posrange[0]:
        for x in self.close_target.posrange[1]:
            movearray[x][y] = 100  # reset path in the enemy sprite position

    intbasepos = (int(self.base_pos[0]), int(self.base_pos[1]))
    for y in self.posrange[0]:
        for x in self.posrange[1]:
            movearray[x][y] = 100  # reset path for sub-unit sprite position

    startpoint = (min([max(0, intbasepos[0] - 5), max(0, intbasetarget[0] - 5)]),  # start point of new smaller array
                  min([max(0, intbasepos[1] - 5), max(0, intbasetarget[1] - 5)]))
    endpoint = (max([min(999, intbasepos[0] + 5), min(999, intbasetarget[0] + 5)]),  # end point of new array
                max([min(999, intbasepos[1] + 5), min(999, intbasetarget[1] + 5)]))

    movearray = movearray[startpoint[1]:endpoint[1]]  # cut 1000x1000 array into smaller one by row
    movearray = [thisarray[startpoint[0]:endpoint[0]] for thisarray in movearray]  # cut by column

    # if len(movearray) < 100 and len(movearray[0]) < 100: # if too big then skip combat pathfinding
    grid = Grid(matrix=movearray)
    grid.cleanup()

    start = grid.node(intbasepos[0] - startpoint[0], intbasepos[1] - startpoint[1])  # start point
    end = grid.node(intbasetarget[0] - startpoint[0], intbasetarget[1] - startpoint[1])  # end point

    finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
    path, runs = finder.find_path(start, end, grid)
    path = [(thispath[0] + startpoint[0], thispath[1] + startpoint[1]) for thispath in path]  # remake pos into actual map pos

    path = path[4:]  # remove some starting path that may clip with friendly sub-unit sprite

    self.combat_move_queue = path  # add path into combat movement queue
    if len(self.combat_move_queue) < 1: # simply try walk to target anyway if pathfinder return empty
        self.combat_move_queue = [self.close_target.base_pos]
    # if self.gameid == 10087:
    #     print('done', self.base_pos != self.base_target)
    # print('operations:', runs, 'path length:', len(path))
    # print(grid.grid_str(path=path, start=start, end=end))
    # print(self.combat_move_queue)
    # print(self.base_pos, self.close_target.base_pos, self.gameid, startpoint, intbasepos[0] - startpoint[0], intbasepos[1] - startpoint[1])
    # ^ End path finding

def losscal(attacker, defender, hit, defense, type, defside = None):
    """Calculate damage, type 0 is melee attack and will use attacker subunit stat,
    type that is not 0 will use object stat instead (mostly used for range attack)"""
    who = attacker
    target = defender

    heightadventage = who.height - target.height
    if type == 1: heightadventage = int(heightadventage / 2) # Range attack use less height advantage
    hit += heightadventage

    if defense < 0 or who.ignore_def: # Ignore def trait
        defense = 0

    hitchance = hit - defense
    if hitchance < 0: hitchance = 0
    elif hitchance > 80: # Critical hit
        hitchance *= who.crit_effect # modify with crit effect further
        if hitchance > 200:
            hitchance = 200

    combatscore = round(hitchance / 100, 1)
    if combatscore == 0 and random.randint(0, 10) > 9:  # Final chence to not miss
        combatscore = 0.1

    leaderdmgbonus = 0
    if who.leader is not None:
        leaderdmgbonus = who.leader.combat # Get extra damage from leader combat ability

    if type == 0:  # Melee damage
        dmg = who.dmg
        if who.chargeskill in who.skill_effect: # Include charge in dmg if attacking
            if who.ignore_chargedef is False: # Ignore charge defense if have ignore trait
                sidecal = battlesidecal[defside]
                if target.fulldef or target.temp_fulldef: # Defense all side
                    sidecal = 1
                dmg = dmg + (((who.charge) - (target.chargedef * sidecal)) * 2)
            else:
                dmg = dmg + (who.charge * 2)

        if target.chargeskill in target.skill_effect and target.ignore_chargedef is False: # Also include chargedef in dmg if enemy charging
            chargedefcal = who.chargedef - target.charge
            if chargedefcal < 0:
                chargedefcal = 0
            dmg = dmg + (chargedefcal * 2) # if charge def is higher than enemy charge then deal back addtional dmg

        dmg = dmg * ((100 - (target.armour * who.penetrate)) / 100) * combatscore

    else:  # Range Damage
        dmg = type.damage * ((100 - (target.armour * type.penetrate)) / 100) * combatscore

    leaderdmg = dmg
    unitdmg = (dmg * who.troopnumber) + leaderdmgbonus # damage on subunit is dmg multiply by troop number with addition from leader combat
    if (who.anti_inf and target.type in (1, 2)) or (who.anti_cav and target.type in (4, 5, 6, 7)):  # Anti trait dmg bonus
        unitdmg = unitdmg * 1.25
    # if type == 0: # melee do less damage per hit because the combat happen more frequently than range
    #     unitdmg = unitdmg / 20

    moraledmg = dmg / 50

    # Damage cannot be negative (it would heal instead), same for morale and leader damage
    if unitdmg < 0:
        unitdmg = 0
    if leaderdmg < 0:
        leaderdmg = 0
    if moraledmg < 0:
        moraledmg = 0

    return unitdmg, moraledmg, leaderdmg

def applystatustoenemy(statuslist, inflictstatus, receiver, attackerside, receiverside):
    """apply aoe status effect to enemy squads"""
    for status in inflictstatus.items():
        if status[1] == 1 and attackerside == 0: # only front enemy
            receiver.status_effect[status[0]] = statuslist[status[0]].copy()
        elif status[1] == 2: # aoe effect to side enemy
            receiver.status_effect[status[0]] = statuslist[status[0]].copy()
            if status[1] == 3: # apply to corner enemy subunit (left and right of self front enemy subunit)
                corner_enemy_apply = receiver.nearby_subunit_list[0:2]
                if receiverside in (1,2): # attack on left/right side means corner enemy would be from front and rear side of the enemy
                    corner_enemy_apply = [receiver.nearby_subunit_list[2], receiver.nearby_subunit_list[5]]
                for subunit in corner_enemy_apply:
                    if subunit != 0:
                        subunit.status_effect[status[0]] = statuslist[status[0]].copy()
        elif status[1] == 3: # whole parentunit aoe
            for subunit in receiver.parentunit.subunit_sprite:
                if subunit.state != 100:
                    subunit.status_effect[status[0]] = statuslist[status[0]].copy()

def complexdmg(attacker, receiver, dmg, moraledmg, leaderdmg, dmgeffect, timermod):
    final_dmg = round(dmg * dmgeffect * timermod)
    final_moraledmg = round(moraledmg * dmgeffect * timermod)
    if final_dmg > receiver.unit_health: # damage cannot be higher than remaining health
        final_dmg = receiver.unit_health

    receiver.unit_health -= final_dmg
    receiver.base_morale -= (final_moraledmg + attacker.bonus_morale_dmg) * receiver.mental
    receiver.stamina -= attacker.bonus_stamina_dmg

    # v Add red corner to indicate combat
    if receiver.red_corner is False:
        receiver.imageblock.blit(receiver.images[11], receiver.cornerimagerect)
        receiver.red_corner = True
    # ^ End red corner

    if attacker.elemmelee not in (0, 5):  # apply element effect if atk has element, except 0 physical, 5 magic
        receiver.elem_count[attacker.elemmelee - 1] += round(final_dmg * (100 - receiver.elem_res[attacker.elemmelee - 1] / 100))

    attacker.base_morale += round((final_moraledmg / 5)) # recover some morale when deal morale dmg to enemy

    if receiver.leader is not None and receiver.leader.health > 0 and random.randint(0, 10) > 9:  # dmg on subunit leader, only 10% chance
        finalleaderdmg = round(leaderdmg - (leaderdmg * receiver.leader.combat/101) * timermod)
        if finalleaderdmg > receiver.leader.health:
            finalleaderdmg = receiver.leader.health
        receiver.leader.health -= finalleaderdmg


def dmgcal(attacker, target, attackerside, targetside, statuslist, combattimer):
    """base_target position 0 = Front, 1 = Side, 3 = Rear, attackerside and targetside is the side attacking and defending respectively"""
    wholuck = random.randint(-50, 50) # attacker luck
    targetluck = random.randint(-50, 50) # defender luck
    whopercent = battlesidecal[attackerside] # attacker attack side modifier

    """34 battlemaster fulldef or 91 allrounddef status = no flanked penalty"""
    if attacker.fulldef or 91 in attacker.status_effect:
        whopercent = 1
    targetpercent = battlesidecal[targetside] # defender defend side

    if target.fulldef or 91 in target.status_effect:
        targetpercent = 1

    dmgeffect = attacker.front_dmg_effect
    targetdmgeffect = target.front_dmg_effect

    if attackerside != 0 and whopercent != 1:  # if attack or defend from side will use discipline to help reduce penalty a bit
        whopercent = battlesidecal[attackerside] + (attacker.discipline / 300)
        dmgeffect = attacker.side_dmg_effect # use side dmg effect as some skill boost only front dmg
        if whopercent > 1: whopercent = 1

    if targetside != 0 and targetpercent != 1: # same for the base_target defender
        targetpercent = battlesidecal[targetside] + (target.discipline / 300)
        targetdmgeffect = target.side_dmg_effect
        if targetpercent > 1: targetpercent = 1

    whohit = float(attacker.attack * whopercent) + wholuck
    whodefense = float(attacker.meleedef * whopercent) + wholuck
    targethit = float(attacker.attack * targetpercent) + targetluck
    targetdefense = float(target.meleedef * targetpercent) + targetluck

    """33 backstabber ignore def when attack rear side, 55 Oblivious To Unexpected can't defend from rear at all"""
    if (attacker.backstab and targetside == 2) or (target.oblivious and targetside == 2) or (
            target.flanker and attackerside in (1, 3)): # Apply only for attacker
        targetdefense = 0

    whodmg, whomoraledmg, wholeaderdmg = losscal(attacker, target, whohit, targetdefense, 0, targetside) # get dmg by attacker
    targetdmg, targetmoraledmg, targetleaderdmg = losscal(target, attacker, targethit, whodefense, 0, attackerside) # get dmg by defender

    timermod = combattimer / 0.5 # Since the update happen anytime more than 0.5 second, high speed that pass by longer than x1 speed will become inconsistent
    complexdmg(attacker, target, whodmg, whomoraledmg, wholeaderdmg, dmgeffect, timermod) # Inflict dmg to defender
    complexdmg(target, attacker, targetdmg, targetmoraledmg, targetleaderdmg, targetdmgeffect, timermod) # Inflict dmg to attacker

    #v Attack corner (side) of self with aoe attack
    if attacker.corner_atk:
        listloop = [target.nearby_subunit_list[2], target.nearby_subunit_list[5]] # Side attack get (2) front and (5) rear nearby subunit
        if targetside in (0, 2): listloop = target.nearby_subunit_list[0:2] # Front/rear attack get (0) left and (1) right nearbysquad
        for subunit in listloop:
            if subunit != 0 and subunit.state != 100:
                targethit, targetdefense = float(attacker.attack * targetpercent) + targetluck, float(subunit.meleedef * targetpercent) + targetluck
                whodmg, whomoraledmg = losscal(attacker, subunit, whohit, targetdefense, 0)
                complexdmg(attacker, subunit, whodmg, whomoraledmg, wholeaderdmg, dmgeffect, timermod)
    #^ End attack corner

    #v inflict status based on aoe 1 = front only 2 = all 4 side, 3 corner enemy subunit, 4 entire parentunit
    if attacker.inflictstatus != {}:
        applystatustoenemy(statuslist, attacker.inflictstatus, target, attackerside, targetside)
    if target.inflictstatus != {}:
        applystatustoenemy(statuslist, target.inflictstatus, attacker, targetside, attackerside)
    #^ End inflict status


def die(who, battle,moralehit=True):
    """remove subunit when it dies"""
    if who.team == 1:
        group = battle.team1army
        enemygroup = battle.team2army
        battle.team1poslist.pop(who.gameid)
    else:
        group = battle.team2army
        enemygroup = battle.team1army
        battle.team2poslist.pop(who.gameid)

    if moralehit:
        if who.commander:  # more morale penalty if the parentunit is a command parentunit
            for army in group:
                for subunit in army.subunit_sprite:
                    subunit.base_morale -= 30

        for thisarmy in enemygroup:  # get bonus authority to the another army
            thisarmy.authority += 5

        for thisarmy in group:  # morale dmg to every subunit in army when allied parentunit destroyed
            for subunit in thisarmy.subunit_sprite:
                subunit.base_morale -= 20

    battle.allunitlist.remove(who)
    battle.allunitindex.remove(who.gameid)
    group.remove(who)
    who.got_killed = True


def changeleader(self, type):
    """Leader change subunit or gone/die, type can be "die" or "broken" """
    checkstate = [100]
    if type == "broken":
        checkstate = [99,100]
    if self.leader is not None and self.leader.state != 100:  # Find new subunit for leader if there is one in this subunit
        for subunit in self.nearby_subunit_list:
            if subunit != 0 and subunit.state not in checkstate and subunit.leader == None:
                subunit.leader = self.leader
                self.leader.subunit = subunit
                for index, subunit in enumerate(self.parentunit.subunit_sprite):  # loop to find new subunit pos based on new subunit_sprite list
                    if subunit.gameid == self.leader.subunit.gameid:
                        subunit.leader.subunitpos = index
                        if self.unit_leader:  # set leader subunit to new one
                            self.parentunit.leadersubunit = subunit
                            subunit.unit_leader = True

                self.leader = None
                break

        if self.leader is not None:  # if can't find near subunit to move leader then find from first subunit to last place in parentunit
            for index, subunit in enumerate(self.parentunit.subunit_sprite):
                if subunit.state not in checkstate and subunit.leader is None:
                    subunit.leader = self.leader
                    self.leader.subunit = subunit
                    subunit.leader.subunitpos = index
                    self.leader = None
                    if self.unit_leader:  # set leader subunit to new one
                        self.parentunit.leadersubunit = subunit
                        subunit.unit_leader = True

                    break

            if self.leader is not None and type == "die":  # Still can't find new subunit so leader disappear with chance of different result
                self.leader.state = random.randint(97, 100)  # captured, retreated, wounded, dead
                self.leader.health = 0
                self.leader.gone()

        self.unit_leader = False


def addnewunitprocess(battle, who):
    from gamescript import gameunit
    # generate subunit sprite array for inspect ui
    who.subunit_sprite_array = np.empty((8, 8), dtype=object)  # array of subunit object(not index)
    foundcount = 0
    for row in range(0, 8):
        for column in range (0, 8):
            try:
                if who.armysubunit[row][column] != 0:
                    who.subunit_sprite_array[row][column] = who.subunit_sprite[foundcount]
                    foundcount += 1
                    who.subunit_sprite[foundcount].armypos = (who.subunit_position_list[foundcount][0] / 10, who.subunit_position_list[foundcount][1] / 10)  # position in parentunit sprite
                else:
                    who.subunit_sprite_array[row][column] = None
            except:
                pass
    #^ End generate subunit array

    for index, subunit in enumerate(who.subunit_sprite): # reset leader subunitpos
        if subunit.leader is not None:
            subunit.leader.subunitpos = index

    who.zoom = battle.camerascale
    who.new_angle = who.angle

    who.startset(battle.subunit)
    who.set_target()
    for subunit in who.subunit_sprite:
        subunit.gamestart(subunit.zoom)

    battle.allunitlist.append(who)
    battle.allunitindex.append(who.gameid)

    battle.troopnumbersprite.add(gameunit.Troopnumber(who))

def moveleadersubunit(leader, oldarmysubunit, newarmysubunit, alreadypick=[]):
    """oldarmysubunit is armysubunit list that the subunit currently in and need to be move out to the new one (newarmysubunit), alreadypick is list of position need to be skipped"""
    replace = [np.where(oldarmysubunit == leader.subunit.gameid)[0][0],
               np.where(oldarmysubunit == leader.subunit.gameid)[1][0]] # grab old array position of subunit
    newrow = int(len(newarmysubunit) / 2) # set up new row subunit will be place in at the middle at the start
    newplace = int(len(newarmysubunit[newrow]) / 2) # setup new column position
    placedone = False # finish finding slot to place yet
    newarmysubunitlen = len(newarmysubunit[newrow]) # get size of row in new armysubunit

    while placedone is False:
        if leader.subunit.parentunit.armysubunit.flat[(newrow * newarmysubunitlen) + newplace] != 0:
            for subunit in leader.subunit.parentunit.subunit_sprite:
                if subunit.gameid == leader.subunit.parentunit.armysubunit.flat[(newrow * newarmysubunitlen) + newplace]:
                    if subunit.leader is not None or (newrow,newplace) in alreadypick:
                        newplace += 1
                        if newplace > len(newarmysubunit[newrow])-1: # find new column
                            newplace = 0
                        elif newplace == int(len(newarmysubunit[newrow]) / 2): # find in new row when loop back to the first one
                            newrow += 1
                        placedone = False
                    else: # found slot to replace
                        placedone = True
                        break
        else:  # fill in the subunit if the slot is empty
            placedone = True

    oldarmysubunit[replace[0]][replace[1]] = newarmysubunit[newrow][newplace]
    newarmysubunit[newrow][newplace] = leader.subunit.gameid
    newpostion = (newplace, newrow)
    return oldarmysubunit, newarmysubunit, newpostion

def splitunit(battle, who, how):
    """split parentunit either by row or column into two seperate parentunit""" # TODO check split when moving
    from gamescript import gameunit, gameleader

    if how == 0:  # split by row
        newarmysubunit = np.array_split(who.armysubunit, 2)[1]
        who.armysubunit = np.array_split(who.armysubunit, 2)[0]
        newpos = pygame.Vector2(who.base_pos[0], who.base_pos[1] + (who.base_height_box / 2))
        who.base_pos = pygame.Vector2(who.base_pos[0], who.base_pos[1] - (who.base_height_box / 2)) # new position for original parentunit

    else:  # split by column
        newarmysubunit = np.array_split(who.armysubunit, 2, axis=1)[1]
        who.armysubunit = np.array_split(who.armysubunit, 2, axis=1)[0]
        newpos = pygame.Vector2(who.base_pos[0] + (who.base_width_box / 2), who.base_pos[1])
        who.base_pos =  pygame.Vector2(who.base_pos[0] - (who.base_width_box / 2), who.base_pos[1])

    if who.leader[1].subunit.gameid not in newarmysubunit.flat:  # move first sub-general leader subunit if it not in new one
        who.armysubunit, newarmysubunit, newposition = moveleadersubunit(who.leader[1], who.armysubunit, newarmysubunit)
        who.leader[1].subunitpos = newposition[0] + (newposition[1] * 8)

    alreadypick = []
    for leader in (who.leader[0], who.leader[2], who.leader[3]): # move other leader subunit to original one if they are in new one
        if leader.subunit.gameid not in who.armysubunit:
            newarmysubunit, who.armysubunit, newposition = moveleadersubunit(leader, newarmysubunit, who.armysubunit, alreadypick)
            alreadypick.append(newposition)

    newleader = [who.leader[1], gameleader.Leader(1, 0, 1, who, battle.leader_stat), gameleader.Leader(1, 0, 2, who, battle.leader_stat),
                 gameleader.Leader(1, 0, 3, who, battle.leader_stat)] # create new leader list for new parentunit

    who.subunit_position_list = []

    width, height = 0, 0
    squadnum = 0  # Number of subunit based on the position in row and column
    for subunit in who.armysubunit.flat:
        width += who.imgsize[0]
        who.subunit_position_list.append((width, height))
        squadnum += 1
        if squadnum >= len(who.armysubunit[0]):  # Reach the last subunit in the row, go to the next one
            width = 0
            height += who.imgsize[1]
            squadnum = 0

    subunitsprite = [subunit for subunit in who.subunit_sprite if subunit.gameid in newarmysubunit.flat]  # new list of sprite not sorted yet
    newsquadsprite = []

    #v Sort so the new leader subunit position match what set before
    for squad in subunitsprite:
        if squad.gameid in newarmysubunit.flat:
            newsquadsprite.append(squad)

    who.subunit_sprite = [subunit for subunit in who.subunit_sprite if subunit.gameid in who.armysubunit.flat]
    #^ End sort

    #v Reset position in inspectui for both parentunit
    for sprite in (who.subunit_sprite, newsquadsprite):
        width, height = 0, 0
        squadnum = 0
        for squad in sprite:
            width += battle.squadwidth

            if squadnum >= len(who.armysubunit[0]):
                width = 0
                width += battle.squadwidth
                height += battle.squadheight
                squadnum = 0

            squad.inspposition = (width + battle.inspectuipos[0], height + battle.inspectuipos[1])
            squad.rect = squad.image.get_rect(topleft=squad.inspposition)
            squad.pos = pygame.Vector2(squad.rect.centerx, squad.rect.centery)
            squadnum += 1
    #^ End reset position

    #v Change the original parentunit stat and sprite
    originalleader = [who.leader[0], who.leader[2], who.leader[3], gameleader.Leader(1, 0, 3, who, battle.leader_stat)]
    for index, leader in enumerate(originalleader):  # Also change army position of all leader in that parentunit
        leader.armyposition = index  # Change army position to new one
        leader.imgposition = leader.baseimgposition[leader.armyposition]
        leader.rect = leader.image.get_rect(center=leader.imgposition)
    teamcommander = who.teamcommander
    who.teamcommander = teamcommander
    who.leader = originalleader

    addnewunitprocess(battle, who)
    #^ End change original unit

    #v start making new parentunit
    if who.team == 1:
        whosearmy = battle.team1army
    else:
        whosearmy= battle.team2army
    newgameid = battle.allunitlist[-1].gameid + 1

    newarmy = gameunit.Unitarmy(startposition=newpos, gameid=newgameid,squadlist=newarmysubunit,colour=who.colour,
                                control=who.control, coa=who.coa, commander=False, startangle=who.angle, team=who.team)

    whosearmy.add(newarmy)
    newarmy.teamcommander = teamcommander
    newarmy.leader = newleader
    newarmy.subunit_sprite = newsquadsprite

    for subunit in newarmy.subunit_sprite:
        subunit.parentunit = newarmy

    for index, leader in enumerate(newarmy.leader):  # Change army position of all leader in new parentunit
        leader.parentunit = newarmy  # Set leader parentunit to new one
        leader.armyposition = index  # Change army position to new one
        leader.imgposition = leader.baseimgposition[leader.armyposition]  # Change image pos
        leader.rect = leader.image.get_rect(center=leader.imgposition)
        leader.poschangestat(leader)  # Change stat based on new army position

    addnewunitprocess(battle, newarmy)

    #^ End making new parentunit

## Other scripts

def playgif(imageset, framespeed = 100):
    """framespeed in millisecond"""
    animation = {}
    frames = ["image1.png","image2.png"]
