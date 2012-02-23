#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2008-2011 Tobias Hieta <tobias@hieta.se>
#

import time
import urllib
from StringIO import StringIO

DEVICE_ID='plex-sc2-client'

TIMEFRAME_DAY='day'
TIMEFRAME_WEEK='week'
TIMEFRAME_MONTH='month'
TIMEFRAME_ALL='all'

SECTION_PLAYER='players'
SECTION_CASTER='casters'
SECTION_EVENT='events'
SECTION_MATCHUP='matchups'

SECTION_PLAYER_NUM=1
SECTION_CASTER_NUM=2
SECTION_EVENT_NUM=3
SECTION_MATCHUP_NUM=4

RACES = {
    1:'P',
    2:'T',
    3:'Z'
}

BASE_URL = 'http://sc2casts.com/services/plex/'

CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 10  minutes
CACHE_TIME_1DAY    = 60*60*24

def sectionByName(name):
    if name == SECTION_PLAYER: return SECTION_PLAYER_NUM
    if name == SECTION_CASTER: return SECTION_CASTER_NUM
    if name == SECTION_EVENT: return SECTION_EVENT_NUM
    if name == SECTION_MATCHUP: return SECTION_MATCHUP_NUM

def sc2request(method, args={}, cache=CACHE_TIME_SHORT):
    url = BASE_URL + method

    # filedate might be static, not sure
    args.update({"refdate":time.strftime('%d-%m-%Y'), "filedate":'30-05-2011', 'deviceid':DEVICE_ID})
    argstr = urllib.urlencode(args)
    url += '?%s' % argstr
    Log(url)

    data = HTTP.Request(url, cacheTime=cache).content
    data = data.replace('&', '&amp;');

    elm = XML.ElementFromString(data)
    
    return elm

def getCastDetails(cast):
    root = sc2request('view', {'series': cast.id})
    if root is None:
        return []
    fillFromNode(cast, root.xpath('/currentseries')[0])

def subnodeText(root, elm):
    try:
        return root.xpath('./%s' % elm)[0].text
    except:
        return None

def subnodeInt(root, elm):
    ret = subnodeText(root, elm)
    if ret:
        return int(ret)
    return 0

def fillFromNode(cast, node):
    cast.id = subnodeInt(node, 'seriesid')
    cast.caster = subnodeText(node, 'caster')
    cast.event = subnodeText(node, 'event')
    cast.bestof = subnodeText(node, 'bestof')
    cast.round = subnodeText(node, 'round')
    cast.bestofnum = subnodeInt(node, 'bestofnum')
    cast.rateup = subnodeInt(node, 'up')
    cast.ratedown = subnodeInt(node, 'down')
    datestr = subnodeText(node, 'date_added')
    cast.date_added = Datetime.ParseDate(datestr)

    for player in node.xpath("./*[substring(name(),1,6) = 'player']"):
        cast.players.append(player.text)

    for race in node.xpath("./*[substring(name(),1,4) = 'race']"):
        cast.races.append(race.text)

    for game in node.xpath(".//games/game"):
        partlist = []
        for p in game.xpath('.//part'):
            partlist.append(p.text)
        cast.games.append(partlist)


class SC2Cast:
    def __init__(self):
        self.id = 0
        self.players = []
        self.races = []
        self.games = []
        self.caster = None
        self.event = None
        self.date = None
        self.bestof = None
        self.bestofnum = 0
        self.round = None
        self.rateup = 0
        self.ratedown = 0

    def matchup(self):
        try:
            race1 = RACES[int(self.races[0][0:1])]
            race2 = RACES[int(self.races[1][0:1])]
        except:
            return 'TvZ'
        return race1+"v"+race2


class SC2CastsClient:
    def getRecentCasts(self):
        root = sc2request('recent')
        if root is None:
            return []
        periods = root.xpath('/periods/date_period')
        if not periods:
            return []

        ret = []
        for p in periods:
            date_name = p.xpath('./date_name')[0].text
            for s in p.xpath('.//series'):
                cast = SC2Cast()
                cast.date_name=date_name
                fillFromNode(cast,s)
                ret.append(cast)

        return ret

    def getTopCasts(self,timeframe=TIMEFRAME_DAY):
        root = sc2request('top', {timeframe:None})
        if root is None:
            return []
        ret = []
        for serie in root.xpath('//series'):
            cast = SC2Cast()
            fillFromNode(cast,serie)
            ret.append(cast)
        return ret
    
    def browse(self, section=SECTION_PLAYER):
        root = sc2request('browse', {section:None})
        if root is None:
            return []
        ret = []
        for item in root.xpath('//item'):
            ret.append((item.xpath('./name')[0].text, item.xpath('./id')[0].text))
        return ret

    def subBrowse(self, section, id):
        section_num = sectionByName(section)
        root = sc2request('browse', {'q':"%d_%d" %  (section_num, int(id))})
        if root is None:
            return []

        ret = []
        for serie in root.xpath('//series'):
            cast = SC2Cast()
            fillFromNode(cast,serie)
            ret.append(cast)
        return ret
        
    def search(self, query):
        root = sc2request('search', {'q':query})
        if root is None:
            return []
        ret = []
        for serie in root.xpath('//series'):
            cast = SC2Cast()
            fillFromNode(cast,serie)
            ret.append(cast)
        return ret
 

