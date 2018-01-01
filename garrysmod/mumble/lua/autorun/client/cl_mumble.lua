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

Msg("[client/cl_mumble.lua] Loading Mumble integration...\n")

local function showConfirmationDialog()
	local window = vgui.Create("DFrame")
	
	window:SetSize( 220, 100 )
	
	window:ShowCloseButton(false)
	window:Center()
	window:SetTitle("Mumble")
	window:SetVisible(true)
	window:MakePopup()

	local label1 = vgui.Create( "DLabel", window )
	label1:SetPos(10, 30)
	label1:SetSize(200, 10)
	label1:SetText("You should have received a four digit")
	local label2 = vgui.Create( "DLabel", window )
	label2:SetPos(10, 40)
	label2:SetSize(200, 10)
	label2:SetText("code in Mumble. Enter it to proceed:")
	
	local text = vgui.Create( "DTextEntry", window )
	text:SetText("Code")
	text.OnEnter = function()
		RunConsoleCommand("mumble_user_confirm", text:GetValue())
		window:Close()
	end
	text:SetSize(140, 20)
	text:SetPos(10, 60)
	
	local button = vgui.Create( "DButton", window )
	button:SetText("Confirm")
	button.DoClick = text.OnEnter
	button:SetSize(50, 20)
	button:SetPos(160, 60)
end

local function showRegisterDialog()
	local window = vgui.Create("DFrame")
	
	window:SetSize( 420, 110 )
	
	window:ShowCloseButton(false)
	window:Center()
	window:SetTitle("Mumble")
	window:SetVisible(true)
	window:MakePopup()

	local function createLabel(y, str)
		local label = vgui.Create( "DLabel", window )
		label:SetPos(10, 30 + y * 10)
		label:SetSize(400, 10)
		label:SetText(str)
	end
	createLabel(0, "Looks like you're not yet registered on the Mumble server.")
	createLabel(1, "You need to register so we can recognize you if you re-connect.")
	createLabel(2, "Registering is as simple as right-clicking on yourself in Mumble and selecting")
	createLabel(3, "\"Register\". Once you've registered, click \"OK\" and try again.")
	
	local button = vgui.Create( "DButton", window )
	button:SetText("OK")
	button.DoClick = function()
		RunConsoleCommand("mumble_show_selection")
		window:Close()
	end
	button:SetSize(50, 20)
	button:SetPos(210-50/2, 80)
end

local function showUserSelection(users)
	local window = vgui.Create("DFrame")
	
	window:SetSize( 640, 480 )
	
	window:ShowCloseButton(false)
	window:Center()
	window:SetTitle("Mumble")
	window:SetVisible(true)
	window:MakePopup()

	local label1 = vgui.Create( "DLabel", window )
	label1:SetPos(10, 30)
	label1:SetSize(600, 10)
	label1:SetText("This GMod server is linked to a Mumble server and you seem to be new here. Who are you?")
	local label2 = vgui.Create( "DLabel", window )
	label2:SetPos(10, 40)
	label2:SetSize(600, 10)
	label2:SetText("Not in the list? Make sure you are in the GMod channel, then hit \"Reload..\"")
	
	local x = 0
	local y = 0
	for user_id, user_name in pairs(users) do
		if 70+(y+1)*50 > 430 then
			y = 0
			x=x+1
		end
		local button = vgui.Create( "DButton", window )
		button:SetText(user_name)
		button.DoClick = function()
			window:Close()
			if user_id < 0 then
				showRegisterDialog()
			else
				RunConsoleCommand("mumble_user", user_id)
				showConfirmationDialog()
			end
		end
		button:SetSize(200, 40)
		button:SetPos(10+210*x, 70+50*y)
		y=y+1
	end
	local button = vgui.Create("DButton", window)
	button:SetText("Reload..")
	button.DoClick = function()
		RunConsoleCommand("mumble_show_selection")
		window:Close()
	end
	button:SetSize(200, 40)
	button:SetPos(10, 430)
end

net.Receive("mumble_show_user_selection", function(length)
     showUserSelection(net.ReadTable())
end)
