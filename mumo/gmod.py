#!/usr/bin/env python2
# -*- coding: utf-8
#
# Copyright (C) 2018 Jonas Herzig <me@johni0702.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from mumo_module import commaSeperatedIntegers, MumoModule
from worker import local_thread_blocking
import pickle
import re
import os
from random import randint
from threading import Thread
from bottle import Bottle, run as runBottle, request, abort
import json

DEAD_GROUP = 'dead'
TRAITOR_GROUP = 'traitor'

class Game:
    def __init__(self, message_queue, server, lobbyChannelId, aliveChannelId, deadChannelId):
        self.message_queue = message_queue
        self._server = server
        self._lobbyChannelId = lobbyChannelId
        self._aliveChannelId = aliveChannelId
        self._deadChannelId = deadChannelId
        self._state = dict()
        self._gmodToMumble = dict()
        self._mumbleToGmod = dict()
        self._pendingUsers = dict()
        self._load()

    def setupBottle(self, bottle, secret):
        bottle.post('/%s/state' % secret)(self.updateState)
        bottle.route('/%s/<gmodUser>' % secret)(self.getUserOrList)
        bottle.route('/%s/<gmodUser>/challenge/<mumbleUser:int>' % secret)(self.challengeUser)
        bottle.route('/%s/<gmodUser>/challenge/solve/<solution>' % secret)(self.completeChallenge)

    def _save(self):
        with open('data/gmod/%d.%d' % (self._server.id(), self._lobbyChannelId), 'wb') as f:
            pickle.dump((self._gmodToMumble, self._mumbleToGmod, self._pendingUsers), f, 0)

    def _load(self):
        path = 'data/gmod/%d.%d' % (self._server.id(), self._lobbyChannelId)
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                (self._gmodToMumble, self._mumbleToGmod, self._pendingUsers) = pickle.load(f)

    def updateGModUser(self, userId, channel, traitor):
        self.updateMumbleUser(self._gmodToMumble[userId], channel, traitor)

    def updateMumbleUser(self, userId, channel, traitor):
        channelId = {
            'lobby': self._lobbyChannelId,
            'alive': self._aliveChannelId,
            'dead': self._deadChannelId
        }[channel]
        users = [u for u in self._server.getUsers().values() if u.userid == userId]
        if len(users) != 1: return # User offline
        user = users[0]
        session = user.session
        if channel in ['lobby', 'alive']:
            self._server.removeUserFromGroup(self._lobbyChannelId, session, DEAD_GROUP)
        else:
            self._server.addUserToGroup(self._lobbyChannelId, session, DEAD_GROUP)
        if user.channel in [self._lobbyChannelId, self._aliveChannelId, self._deadChannelId] \
           and user.channel != channelId:
            print('Moving %s to %s' % (user.name, channel))
            user.channel = channelId
            self._server.setState(user)
        if traitor:
            self._server.addUserToGroup(self._lobbyChannelId, session, TRAITOR_GROUP)
        else:
            self._server.removeUserFromGroup(self._lobbyChannelId, session, TRAITOR_GROUP)

    @local_thread_blocking
    def getUserOrList(self, gmodUser):
        if gmodUser in self._gmodToMumble:
            return dict(known = True)
        else:
            return self.listUsers()

    def listUsers(self):
        users = dict()
        for user in self._server.getUsers().values():
            if user.channel == self._lobbyChannelId:
                if user.userid > 0:
                    users[user.userid] = user.name
                else:
                    users[-user.session] = user.name
        return users

    def updateState(self):
        newState = request.params['state']
        newState = json.loads(newState)
        self._updateState(newState)

    @local_thread_blocking
    def _updateState(self, newState):
        # First find users that quit gmod
        for user, _ in self._state.iteritems():
            if user not in newState:
                if user in self._gmodToMumble:
                    self.updateGModUser(user, 'lobby', False)
        # then users that joined or were already online
        for user, state in newState.iteritems():
            if user not in self._gmodToMumble:
                continue
            dead = state['dead']
            traitor = state['traitor']
            self.updateGModUser(user, 'dead' if dead else 'alive', traitor)
        # Finally replace old state
        print(newState)
        self._state = newState


    @local_thread_blocking
    def challengeUser(self, gmodUser, mumbleUser):
        users = [u for u in self._server.getUsers().values() if u.userid == mumbleUser]
        if len(users) != 1: return # User offline
        session = users[0].session
        challenge = ''.join([str(randint(0, 9)) for i in range(4)])
        self._pendingUsers[gmodUser] = (mumbleUser, challenge)
        self._server.sendMessage(session, 'Enter "%s" in GMod to proceed.' % challenge)

    @local_thread_blocking
    def completeChallenge(self, gmodUser, solution):
        if gmodUser not in self._pendingUsers: abort(400, 'User not yet challenged')
        (mumbleUser, challenge) = self._pendingUsers[gmodUser]
        if challenge != solution: return dict(valid = False)
        self._gmodToMumble[gmodUser] = mumbleUser
        self._mumbleToGmod[mumbleUser] = gmodUser
        self._save()
        if gmodUser in self._state:
            state = self._state[gmodUser]
            dead = state['dead']
            traitor = state['traitor']
            self.updateMumbleUser(mumbleUser, 'dead' if dead else 'alive', traitor)
        return dict(valid = True)
    
    def userStateChanged(self, server, state):
        if state.channel != self._lobbyChannelId: return # not in lobby channel
        if not state.userid > 0: return # not a registered user
        mumbleUser = state.userid
        if mumbleUser not in self._mumbleToGmod: return # unknown user
        gmodUser = self._mumbleToGmod[mumbleUser]
        if gmodUser not in self._state: return # user not ingame
        state = self._state[gmodUser]
        dead = state['dead']
        traitor = state['traitor']
        self.updateMumbleUser(mumbleUser, 'dead' if dead else 'alive', traitor)


class gmod(MumoModule):
    default_config = {
        'gmod': (
            ('gmods', int, 0),
         ),
         lambda x: re.match('gmod_\d+', x): (
            ('secret', str, None),
            ('server', int, 1),
            ('lobbyChannel', int, 0),
            ('aliveChannel', int, 0),
            ('deadChannel', int, 0),
         )
    }
    
    def __init__(self, name, manager, configuration = None):
        MumoModule.__init__(self, name, manager, configuration)
        self._games = []
        self._bottle = Bottle()
        Thread(target=lambda: runBottle(self._bottle, host='localhost', port=8088)).start()

    def connected(self):
        manager = self.manager()

        self._games = []
        servers = set()
        for gmod in range(self.cfg().gmod.gmods):
            cfg = self.cfg()['gmod_%d' % gmod]
            server = manager.getMeta().getServer(cfg.server)
            game = Game(self.message_queue, server, cfg.lobbyChannel, cfg.aliveChannel, cfg.deadChannel)
            game.setupBottle(self._bottle, cfg.secret)
            self._games.append(game)
            servers.add(cfg.server)

        manager.subscribeServerCallbacks(self, list(servers))

    def disconnected(self): pass

    def userTextMessage(self, server, user, message, current=None): pass
    def userConnected(self, server, state, context = None):
        for game in self._games:
            game.userStateChanged(server, state)
    def userStateChanged(self, server, state, context = None):
        for game in self._games:
            game.userStateChanged(server, state)
    def channelCreated(self, server, state, context = None): pass
    def channelRemoved(self, server, state, context = None): pass
    def channelStateChanged(self, server, state, context = None): pass

