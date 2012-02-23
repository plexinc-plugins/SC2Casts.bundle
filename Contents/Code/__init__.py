#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2008-2011 Tobias Hieta <tobias@hieta.se>
#

import sc2casts
import re
import cerealizer

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

@handler('/video/sc2castscom', TITLE, thumb = ICON, art = ART)
def MainMenu():
    oc = ObjectContainer()
    
    oc.add(DirectoryObject(key = Callback(RecentList), title = "Recent Casts"))
    oc.add(DirectoryObject(key = Callback(SubMenuList, page = TOP), title = "Top Casts"))
    oc.add(DirectoryObject(key = Callback(SubMenuList, page = BROWSE), title = "Browse Casts"))
    oc.add(InputDirectoryObject(key = Callback(SearchList), title = "Search Casts", prompt = "Search Casts", thumb = R("icon-search.png")))
        
    return oc

###################################################################################################

def RecentList():
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Recent casts', cl.getRecentCasts())

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
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_EVENT), title = "Browse Events"))
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_PLAYER), title = "Browse Players"))
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_CASTER), title = "Browse Casters"))
        oc.add(DirectoryObject(key = Callback(BrowseList, page = sc2casts.SECTION_MATCHUP), title = "Browse Matchups"))
    
    return oc

###################################################################################################
                                               
def SearchList(query):
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Search results', cl.search(query))
                                               
###################################################################################################

def TopList(page):
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Top casts', cl.getTopCasts(page))

###################################################################################################

def BrowseList(page):
    cl = sc2casts.SC2CastsClient()
    blist = cl.browse(page)
    
    oc = ObjectContainer(title2 = 'Browse: ' + page)
    for entry in blist:
        if page == sc2casts.SECTION_MATCHUP:
            oc.add(DirectoryObject(key = Callback(SubBrowseList, id = entry[0], section = page), title = entry[1], thumb = R("%s.png" % entry[1])))
        else:
            oc.add(DirectoryObject(key = Callback(SubBrowseList, id = entry[0], section = page), title = entry[1]))
    
    return oc

###################################################################################################

def SubBrowseList(id, section):
    cl = sc2casts.SC2CastsClient()
    return SeriesList('Browse : ' + section, cl.subBrowse(section,id))

###################################################################################################

def SeriesList(title, listOfGames):
    oc = ObjectContainer(view_group = 'InfoList', title2 = title)
    
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
    oc = ObjectContainer(view_group = 'InfoList', title2 = '%s vs %s (%s)' % (game.players[0], game.players[1], game.bestof))

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
                oc.add(VideoClipObject(
                    url = YOUTUBE_VIDEO_PAGE % part,
                    title = title,
                    summary = summary,
                    rating = rating,
                    originally_available_at = game.date_added,
                    thumb = Callback(GetThumb, id = part)))

                partnr+=1
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
