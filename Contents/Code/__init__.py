#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2008-2011 Tobias Hieta <tobias@hieta.se>
#   Modified 2014 Andrew Cornforth

import sc2casts
import re
import cerealizer
import datetime
import time

TITLE = 'SC2Casts'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

TOP = 0
BROWSE = 1

BROWSE_EVENTS=0
BROWSE_PLAYERS=1
BROWSE_CASTERS=2
BROWSE_MATCHUPS=3

YTIMG_URL='http://i.ytimg.com/vi/%s/hqdefault.jpg'
YOUTUBE_VIDEO_PAGE = 'http://www.youtube.com/watch?v=%s'
YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]

USER_AGENT = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'

###################################################################################################

def Start():
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    
    ObjectContainer.title1 = TITLE
    ObjectContainer.view_group = 'List'
    ObjectContainer.art = R(ART)
    
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)
    
    HTTP.CacheTime = 3600
    HTTP.Headers['User-Agent'] = USER_AGENT

    cerealizer.register(sc2casts.SC2Cast)

###################################################################################################

@handler('/video/sc2casts2', TITLE, thumb = ICON, art = ART)
def MainMenu():
    oc = ObjectContainer()
    if ("RecentEvent1" in Dict):
        oc.add(DirectoryObject(key = Callback(RecentEventList), title = "Recently Watched Events"))
    oc.add(DirectoryObject(key = Callback(RecentList), title = "Recent Casts"))
    oc.add(DirectoryObject(key = Callback(SubMenuList, page = TOP), title = "Top Casts"))
    oc.add(DirectoryObject(key = Callback(SubMenuList, page = BROWSE), title = "Browse Casts"))
    oc.add(InputDirectoryObject(key = Callback(SearchList), title = "Search Casts", prompt = "Search Casts", thumb = R("icon-search.png")))
        
    return oc

###################################################################################################

def RecentEventList():
    cl = sc2casts.SC2CastsClient()
    oc = ObjectContainer()
    for i in range(1,6):
        keyName = ("RecentEvent%d" % (6-i))
        Log(keyName)
        if (keyName in Dict):
            oc.add(DirectoryObject(key = Callback(SubBrowseList, id=Dict[("RecentEventID%d" % (6-i))], title=Dict[keyName], section=sc2casts.SECTION_EVENT), title = Dict[keyName]))
    return oc

###################################################################################################

def RecentList():
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Recent casts', cl.getRecentCasts(), False)

###################################################################################################

def SubMenuList(page):
    oc = ObjectContainer()
    
    if page == TOP:
        oc.title2='Top casts'
        oc.add(DirectoryObject(key = Callback(TopList, page = sc2casts.TIMEFRAME_DAY), title = "Last 24 Hours"))
        oc.add(DirectoryObject(key = Callback(TopList, page = sc2casts.TIMEFRAME_WEEK), title = "This Week"))
        oc.add(DirectoryObject(key = Callback(TopList, page = sc2casts.TIMEFRAME_MONTH), title = "This Month"))
        oc.add(DirectoryObject(key = Callback(TopList, page = sc2casts.TIMEFRAME_ALL), title = "All Time"))
    if page == BROWSE:
        oc.title2='Browse'
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_TOP_EVENT, letter=None), title = "Prominent Events"))
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_TOP_PLAYER, letter=None), title = "Notable Players"))
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_TOP_CASTER, letter=None), title = "Prominent Casters"))
        oc.add(DirectoryObject(key = Callback(BrowseAlphabet, page = sc2casts.SECTION_EVENT), title = "Browse Events"))
        oc.add(DirectoryObject(key = Callback(BrowseAlphabet, page = sc2casts.SECTION_PLAYER), title = "Browse Players"))
        oc.add(DirectoryObject(key = Callback(BrowseAlphabet, page = sc2casts.SECTION_CASTER), title = "Browse Casters"))
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_MATCHUP, letter=""), title = "Browse Matchups"))
    
    return oc

###################################################################################################
                                               
def SearchList(query = 'the'):
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Search results', cl.search(query), True)
                                               
###################################################################################################

def TopList(page):
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Top casts', cl.getTopCasts(page), False)

###################################################################################################

def BrowseAlphabet(page):
    oc = ObjectContainer(title2 = 'Browse: ' + page)
    alphabet = "0abcdefghijklmnopqrstuvwxyz"
    for i in range(0, len(alphabet)):
        c = alphabet[i].upper()
        cd = c
        if cd=="0":
            cd = "0-9"
        oc.add(DirectoryObject(key = Callback(BrowseList, page = page, letter=c), title = cd))
    return oc

###################################################################################################

def BrowseList(page, letter):
    cl = sc2casts.SC2CastsClient()
    blist = cl.browse(page)
    oc = ObjectContainer(title2 = 'Browse: ' + page)
    for entry in blist:
        if page == sc2casts.SECTION_MATCHUP:
            oc.add(DirectoryObject(key = Callback(SubBrowseList, id = entry[0], section = page, title = entry[1]), title = entry[1], thumb = R("%s.png" % entry[1])))
        else:
            if letter==None or entry[1][0].upper()==letter:
                oc.add(DirectoryObject(key = Callback(SubBrowseList, id = entry[0], section = page, title = entry[1]), title = entry[1]))
    
    return oc

###################################################################################################

def SubBrowseList(id, section, title):
    cl = sc2casts.SC2CastsClient()
    if ((section==sc2casts.SECTION_EVENT) or (section==sc2casts.SECTION_TOP_EVENT)):
        insertIndex = 1
        found = -1
        if ("RecentEvent1" in Dict):
            for i in range(1, 6):
                keyName = "RecentEvent%d" % i
                keyNameID = "RecentEventID%d" % i
                if (keyName in Dict):
                    insertIndex = i+1
                    if (Dict[keyName]==title):
                        found = i
        if (found==-1):
            if (insertIndex==6):
                for i in range(1, 6):
                    keyName = "RecentEvent%d" % i
                    keyNameID = "RecentEventID%d" % i
                    keyNameNext = "RecentEvent%d" % (i+1)
                    keyNameNextID = "RecentEventID%d" % (i+1)
                    Dict[keyName] = Dict[keyNameNext]
                    Dict[keyNameID] = Dict[keyNameNextID]
                insertIndex = 5
        else:
            for i in range(found, 5):
                keyName = "RecentEvent%d" % (i)
                keyNameID = "RecentEventID%d" % (i)
                keyNameNext = "RecentEvent%d" % (i+1)
                keyNameNextID = "RecentEventID%d" % (i+1)
                Log("Moving - "+keyName)
                if (keyNameNext in Dict):
                    insertIndex = i+1
                    Dict[keyName] = Dict[keyNameNext]
                    Dict[keyNameID] = Dict[keyNameNextID]
        Log("Insert Index %d" % insertIndex)
        Dict["RecentEvent%d"%insertIndex] = title
        Dict["RecentEventID%d"%insertIndex] = id
        Dict.Save()
        gameList = cl.subBrowseGroups(id)
        return GroupList('Browse : '+title, gameList)
    else:
        gameList = cl.subBrowse(section,id)
        return SeriesList('Browse : ' + title, gameList, False)

###################################################################################################

def GroupList(title, listOfGroups):
    oc = ObjectContainer(view_group = 'InfoList', title2 = title, no_cache=True)
    for group in listOfGroups:
        oc.add(DirectoryObject(key = Callback(GroupListBrowse, group=group, title=title), title=group.name))
    return oc

###################################################################################################

def GroupListBrowse(group, title):
    cl = sc2casts.SC2CastsClient()
    return SeriesList(title+" : "+group.name, cl.subBrowseGroupList(group.eid, group.rid), True)
    
###################################################################################################

def SeriesList(title, listOfGames, reverse):
    oc = ObjectContainer(view_group = 'InfoList', title2 = title)
    if reverse:
        listOfGames.reverse()
    for game in listOfGames:
        title = "%s vs %s (%s)" % (game.players[0], game.players[1], game.bestof)
        summary = "%s - %s, casted by: %s" % (game.event, game.round, game.caster)
        oc.add(DirectoryObject(key = Callback(GameInfo, game = game),
                               title = title,
                               summary = summary,
                               tagline = summary,
                               thumb = R('%s.png' % game.matchup())))
    
    return oc

###################################################################################################

def GameInfo(game):
    sc2casts.getCastDetails(game)
    datestr = game.date_added.strftime("%d-%m-%Y")
    oc = ObjectContainer(view_group = 'InfoList', title2 = '%s vs %s (%s) Added: %s' % (game.players[0], game.players[1], game.bestof, datestr))

    gamenr = 1
    rating = 0.0
    summary = "%s - %s, casted by: %s" % (game.event, game.round, game.caster)

    if game.rateup:
        rating = (float(game.rateup) * 10.0) / (float(game.rateup) + float(game.ratedown))
    
    for p in game.games:
        
        if len(p) > 1:
            partnr = 1
            for part in p:
                title = "Game %d, part %d" % (gamenr, partnr)
                if Prefs["spoiler_thumbs"]:
                    oc.add(VideoClipObject(
                        url = YOUTUBE_VIDEO_PAGE % part,
                        title = title,
                        summary = summary,
                        rating = rating,
                        originally_available_at = game.date_added,
                        thumb = Callback(GetThumb, id = game.games[0][0])))
                else:
                    oc.add(VideoClipObject(
                        url = YOUTUBE_VIDEO_PAGE % part,
                        title = title,
                        summary = summary,
                        rating = rating,
                        originally_available_at = game.date_added,
                        thumb = Callback(GetThumb, id = part)))
                partnr+=1
        else:
            if Prefs["spoiler_thumbs"]:
                oc.add(VideoClipObject(
                    url = YOUTUBE_VIDEO_PAGE % p[0],
                    title = "Game %d" % gamenr,
                    summary = summary,
                    rating = rating,
                    originally_available_at = game.date_added,
                    thumb = Callback(GetThumb, id = game.games[0][0])))
            else:
                oc.add(VideoClipObject(
                    url = YOUTUBE_VIDEO_PAGE % p[0],
                    title = "Game %d" % gamenr,
                    summary = summary,
                    rating = rating,
                    originally_available_at = game.date_added,
                    thumb = Callback(GetThumb, id = p[0])))

        gamenr+=1
    

    Log("%d < %d" % (gamenr, game.bestofnum+1))
    if (gamenr < game.bestofnum+1):
        for i in range(gamenr, game.bestofnum+1):
             oc.add(VideoClipObject(
                url = YOUTUBE_VIDEO_PAGE % "dQw4w9WgXcQ",
                title = "Game %d" % i,
                summary = summary,
                rating = rating,
                originally_available_at = game.date_added,
                thumb = Callback(GetThumb, id = game.games[0][0])))


    return oc

###################################################################################################

def GetThumb(id):
    url = YTIMG_URL % id
    try:
        data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
        return DataObject(data, 'image/jpeg')
    except:
        return Redirect(R(THUMB))
