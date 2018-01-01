-- Copyright (C) 2018 Jonas Herzig <me@johni0702.de>
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as
-- published by the Free Software Foundation, either version 3 of the
-- License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.
--
-- You should have received a copy of the GNU Affero General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.

Msg("[server/sv_mumble.lua] Loading Mumble integration...\n")

local CONFIG_FILE = "mumble.config.txt"

local API_URL = string.Split(file.Read(CONFIG_FILE), "\n")[1]

local function OpenUserSelection(ply)
	http.Fetch(string.format("%s/%s", API_URL, ply:UniqueID()), function(body)
		local response = util.JSONToTable(body)
		if not response.known then
			net.Start("mumble_show_user_selection")
			net.WriteTable(response)
			net.Send(ply)
		end
	end)
end
hook.Add("PlayerInitialSpawn", "mumble_init_spawn", OpenUserSelection)
concommand.Add("mumble_show_selection", OpenUserSelection)
util.AddNetworkString("mumble_show_user_selection")

local function RequestMumbleUser(ply, command, args)
	if not IsValid(ply) then return end
	local gmod = ply:UniqueID()
	local mumble = math.floor(args[1]) -- Make sure this is an integer
	http.Fetch(string.format("%s/%s/challenge/%d", API_URL, gmod, mumble))
end
concommand.Add("mumble_user", RequestMumbleUser)

local function TryConfirmMumbleUser(ply, command, args)
	if not IsValid(ply) then return end
	local gmod = ply:UniqueID()
	local solution = args[1]
	http.Fetch(string.format("%s/%s/challenge/solve/%s", API_URL, gmod, solution), function(body)
		if util.JSONToTable(body).valid then
			UpdateState()
		else
			OpenUserSelection(ply)
		end
	end)
end
concommand.Add("mumble_user_confirm", TryConfirmMumbleUser)

local function UpdateStateNow()
	state = {}
	local inGame = GetRoundState ~= nil and GetRoundState() == ROUND_ACTIVE
	for _, ply in pairs(player.GetAll()) do
		state[ply:UniqueID()] = inGame and not ply:Alive()
	end
	http.Post(string.format("%s/state", API_URL), {state = util.TableToJSON(state)})
	Msg(util.TableToJSON(state))
end

local function UpdateState()
	timer.Create("mumble_update_state", 0, 1, UpdateStateNow)
end


hook.Add("TTTEndRound", "mumble_update_state", UpdateState)
hook.Add("TTTBeginRound", "mumble_update_state", UpdateState)
hook.Add("PlayerDeath", "mumble_update_state", UpdateState)
hook.Add("PlayerSpawn", "mumble_update_state", UpdateState)
hook.Add("PlayerDisconnected", "mumble_player_spawn", UpdateState)

-- Initial update
UpdateState()
