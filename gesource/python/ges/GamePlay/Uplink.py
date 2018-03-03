from GamePlay import GEScenario
import GEEntity, GEPlayer, GEUtil, GEWeapon, GEMPGameRules, GEGlobal, GEGamePlay
from .Utils.GEWarmUp import GEWarmUp
from .Utils.GEPlayerTracker import GEPlayerTracker
from GEWeapon import CGEWeapon

USING_API = GEGlobal.API_VERSION_1_2_0

#       #       #       #       #
#           - UPLINK -          #
#      Created by Euphonic      #
# Made for GoldenEye:Source 5.0 #
#       #       #       #       #

#	* / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *
UplinkVersion = "^uUplink Version ^l5.0.0"
#	* / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *

class UplinkPoint( object ):
		"""Handles information about each Uplink"""
		
		def __init__( self, location, name, UID ):
			self.location = location
			self.name = name
			self.UID = UID
			
			self.owner = GEGlobal.TEAM_NONE
			
			self.numJanus = 0
			self.numMI6 = 0
			self.isContested = False	# Keeps track of whether both teams are attempting to capture the Uplink
			self.inProgress = False		# Keeps track of whether a team is attempting to capture the Uplink
			
			self.timerJanus = 0
			self.timerMI6 = 0
			
			self.pointTimer = 0			# Counts upward to award points when an Uplink is owned by a team
			
			self.playerList = []		# Keeps track of what players are inside of the capture zone
			self.playerTimers = {}		# Keeps track of player timers in non-teamplay	
		
		def updatePointTimer(self, timerMax):	# If the Uplink is owned by a team, counts upwards constantly. When enough time has passed, resets and gives a point to the team
			if self.owner != GEGlobal.TEAM_NONE:
				self.pointTimer += 1
				
				if self.pointTimer >= timerMax:
					self.pointTimer = 0
					GEMPGameRules.GetTeam( self.owner ).AddRoundScore( 1 )
			
		def updateUplinkTimer(self, timerMax):		# Handles the capture timers, adding time or removing time based on which players are on the Uplink
			if GEMPGameRules.IsTeamplay():
				if self.owner != GEGlobal.TEAM_MI6 and self.numMI6:
					if not self.numJanus:
						self.timerMI6 += 1 + self.numMI6
						if self.timerMI6 >= timerMax:
							self.timerMI6 = 0; self.timerJanus = 0
							self.pointTimer = 0
							return GEGlobal.TEAM_MI6
						elif self.timerJanus:
							self.timerJanus -= 5
							if self.timerJanus < 0:
								self.timerJanus = 0

				elif self.owner != GEGlobal.TEAM_JANUS and self.numJanus:
					if not self.numMI6:
						self.timerJanus += 1 + self.numJanus
						if self.timerJanus >= timerMax:
							self.timerMI6 = 0; self.timerJanus = 0
							self.pointTimer = 0
							return GEGlobal.TEAM_JANUS
						elif self.timerMI6:
							self.timerMI6 -= 5
							if self.timerMI6 < 0:
								self.timerMI6 = 0
			
				else:
					self.timerMI6 -= 2
					if self.timerMI6 < 0:
						self.timerMI6 = 0
						
					self.timerJanus -= 2
					if self.timerJanus < 0:
						self.timerJanus = 0
				
				return False
			else:
				temp_playerUIDlist = []
				for player in self.playerList:
					temp_playerUIDlist += [GEEntity.GetUID( player )]
				
				for playerUID in list(self.playerTimers):
					if playerUID not in temp_playerUIDlist:
						self.playerTimers[playerUID] -= 2
						if self.playerTimers[playerUID] < 0:
							del self.playerTimers[playerUID]
				
				if len(self.playerList) == 1:
					self.playerTimers[ GEEntity.GetUID( self.playerList[0] ) ] += 2
					if self.playerTimers[ GEEntity.GetUID( self.playerList[0] )] >= timerMax:
						return True
				return False
					
		def addPlayerList(self, player):
			if GEMPGameRules.IsTeamplay():
				self.playerList += [player]
				if player.GetTeamNumber() == GEGlobal.TEAM_JANUS:
					self.numJanus += 1
				elif player.GetTeamNumber() == GEGlobal.TEAM_MI6:
					self.numMI6 += 1
			else:
				self.playerList += [player]
				if not GEEntity.GetUID( player ) in self.playerTimers:
					GEUtil.ClientPrint(GEEntity.GetUID( player ), GEGlobal.HUD_PRINTTALK, str(self.playerTimers))
					self.playerTimers[GEEntity.GetUID( player )] = 0
				
		def removePlayerList(self, player):
			if player in self.playerList:
				self.playerList.remove(player)
				playerTeam = player.GetTeamNumber()			
				if playerTeam == GEGlobal.TEAM_JANUS:
					self.numJanus -= 1
					if self.numJanus < 0:
						self.numJanus = 0
				elif playerTeam == GEGlobal.TEAM_MI6:
					self.numMI6 -= 1
					if self.numMI6 < 0:
						self.numMI6 = 0
						
		def checkContestedChange(self):
			if GEMPGameRules.IsTeamplay():
				if self.numMI6 and self.numJanus and not self.isContested:
					self.isContested = True
					return True
				elif self.isContested and (not self.numMI6 or not self.numJanus):
					self.isContested = False
					return True
				else:
					return False
			else:
				if len(self.playerList) > 1 and not self.isContested:
					self.isContested = True
					return True
				elif self.isContested and  len(self.playerList) < 2:
					self.isContested = False
					return True
				else:
					return False
		
		def checkProgressChange(self):
			if GEMPGameRules.IsTeamplay():
				if not self.inProgress:
					if self.owner != GEGlobal.TEAM_JANUS and self.numJanus:
						self.inProgress = True
						return True
					elif self.owner != GEGlobal.TEAM_MI6 and self.numMI6:
						self.inProgress = True
						return True
				else:
					if self.owner == GEGlobal.TEAM_JANUS and not self.numMI6:
						self.inProgress = False
						return True
					elif self.owner == GEGlobal.TEAM_MI6 and not self.numJanus:
						self.inProgress = False
						return True
					elif self.owner == GEGlobal.TEAM_NONE and not self.numJanus and not self.numMI6:
						self.inProgress = False
						return True
					else:
						return False
			else:
				if not self.inProgress:
					if len(self.playerList) != 0:
						self.inProgress = True
					else:
						return False
				else:
					if len(self.playerList) == 0:
						self.inProgress = False
						return True
					else:
						return False

class Uplink( GEScenario ):
	
	def __init__( self ):
		super( Uplink, self ).__init__()
		
		self.warmupTimer = GEWarmUp( self )
		self.notice_WaitingForPlayers = 0
		self.WaitingForPlayers = True
		
		self.roundActive = False
		
#		>> Uplink data >>
		self.areaDictionary = {}		# Holds each Uplink's data (as a class object)
		self.fixDictionary = {}			# Holds player information before an Uplink is added to self.areaDictionary (e.g. an Uplink spawning on a player)

#		>> Uplink names >>
		self.uplinkNames = []			# List of unused Uplink names
		
#		>> Uplink variables >>
		self.pointRadius = 255.0						# Sets radius of each Uplink
		self.pointSeperation = 5 * self.pointRadius		# Sets minimum distance between Uplink points (changes with map size, see OnLoadGamePlay)
		self.uplinkTimerMax = None						# Sets amount of time to make an Uplink (changes depending on teamplay setting)
		self.uplinkTimerMaxSolo = 145					# Sets amount of time to make an Uplink in free-for-all mode
		self.uplinkTimerMaxTeam = 165					# Sets amount of time to make an Uplink in teamplay
		self.pointTimerMax = 150						# Sets amount of time between each point being awarded
		
		self.areaTotal = 3								# Sets the number of Uplinks to spawn
		
		self.skinNeutral = 0
		self.skinJanus = 2
		self.skinMI6 = 1
		
		self.uplinkReward = 2
		self.uplinkRewardSoloPoints = 2
		self.uplinkRewardSoloHP = 0.2
		
#		>> Ping effect variables >>
		self.pingTimerMax = 12 						# Sets how long between each "ping" effect on Uplinks
		self.pingTimer = self.pingTimerMax + 1		# Keeps track of how long since last "ping" effect on Uplinks
		
#		>> Color variables >>
		self.colorNeutral = GEUtil.CColor(255,255,255,255)
		self.colorNeutralPing = GEUtil.CColor(255,255,255,100)
		self.colorMI6 = GEUtil.CColor(0,150,255,255)
		self.colorMI6Ping = GEUtil.CColor(0,150,255,100)
		self.colorJanus = GEUtil.CColor(255,0,0,255)
		self.colorJanusPing = GEUtil.CColor(255,0,0,100)
		
#		>> Objective  color variables
		self.colorMI6_Hot = GEUtil.Color( 94, 171, 231, 235 )
		self.colorMI6_Cold = GEUtil.Color( 94, 171, 231, 120 )
		self.colorJanus_Hot = GEUtil.Color( 206, 43, 43, 235 )
		self.colorJanus_Cold = GEUtil.Color( 206, 43, 43, 120 )
		self.colorNeutral_Hot = GEUtil.Color( 231, 231, 231, 235 )
		self.colorNeutral_Cold = GEUtil.Color( 231, 231, 231, 120 )
		
#		>> Message & Progress Bar colors >>
		self.colorMsg = GEUtil.CColor(220,220,220,240)
		self.colorMsgContested = GEUtil.CColor(255,210,210,185)
		self.colorBarStandard = GEUtil.CColor(220,220,220,240)	# Color of progress bar when player is completing an Uplink
		
#		>> Killticker Message colors >>
		self.colorKilltickerJanus = "^r"
		self.colorKilltickerMI6 = "^i"
		self.colorKilltickerDefault = "^1"
		self.colorKilltickerNoTeam = "^1"

#		>> Scoreboard color variables >>
		self.scoreboardDefault = GEGlobal.SB_COLOR_NORMAL
		self.scoreboardOnPoint = GEGlobal.SB_COLOR_WHITE

#		>> Round Score Display Colors >>
		self.colorOwnershipJanus = "^r"					# Since Janus' score displays first, we don't add spaces
		self.colorOwnershipMI6 = "^c"					# Since MI6's score displays last, we add spaces...
		self.colorOwnershipNeutral = "    ^w:    "		# ...same for Neutral score, which is the second to display
		
#		>> Message & Progress Bar information >>
		self.barIndex = 0
		self.barTitle = "Uplink"								# Displays as the title of the progress bar when a player is capturing an Uplink
		self.completeMsg = "Uplink Established!"				# Displays when a player  finishes an Uplink
		self.ownedMsg = "Your team controls this Uplink"		# Displays when a player steps on an Uplink their team already owns
		self.contestedMsg = "Error: Uplink Blocked!"			# Displays when a player is making an Uplink and an opposing player enters the Uplink
		self.capturedPrintMsg = "^u established an Uplink"	# Displays in killticker when team make an Uplink
		self.capturedPrintMsgAnd = " ^1and "					# Displays before final player who helped complete an Uplink
		self.printMI6 = "MI6"
		self.printJanus = "Janus"
		self.helpMsg = "MI6 and Janus fight for control of key military satellites. Capture and control Uplinks while preventing your opponents from doing the same!\n\nEnter an Uplink to initiate capture and earn points. Team-controlled Uplinks generate points over time.\n\nTeamplay: Toggleable\n\nCreated by WNxEuphonic"

#		>> Uplink Distribution display >>
		self.distColorJanus = GEUtil.CColor(255,0,0,255)
		self.distColorMI6 = GEUtil.CColor(0,0,255,255)
		self.distColorNeutral = GEUtil.CColor(255,255,255,255)
	
	def GetPrintName( self ):
		return "Uplink"

	def GetScenarioHelp( self, help_obj ):
		help_obj.SetDescription( self.helpMsg )
			
		help_obj.SetInfo("Capture and Defend Uplinks", "http://forums.geshl2.com/index.php/topic,7275.new.html" )
		
		pane = help_obj.AddPane( "uplink1" )
		help_obj.AddHelp( pane, "up_goal", "Uplinks are marked by flags and glowing rings")
		help_obj.AddHelp( pane, "", "Enter an Uplink to initiate capture and earn points")
		help_obj.AddHelp( pane, "", "Team-controlled Uplinks generate points over time")
		
		help_obj.SetDefaultPane( pane )

	def GetGameDescription( self ):
			return "Uplink"

	def GetTeamPlay( self ):
		return GEGlobal.TEAMPLAY_TOGGLE

	def OnLoadGamePlay( self ):
		GEUtil.PrecacheModel( "models/weapons/tokens/w_flagtoken.mdl" )
		GEUtil.PrecacheSound( "GEGamePlay.Token_Grab" )
		GEUtil.PrecacheSound( "GEGamePlay.Token_Drop_Enemy" )
		GEUtil.PrecacheSound( "GEGamePlay.Token_Chime" )
		GEUtil.PrecacheSound( "Buttons.beep_denied" )
		
		GEMPGameRules.GetRadar().SetForceRadar( True )
		GEMPGameRules.SetAllowTeamSpawns( False )
				
		if GEMPGameRules.GetNumActivePlayers() >= 2:
			self.WaitingForPlayers = False
		
		self.CreateCVar( "up_warmup", "20", "The warm up time in seconds (Use 0 to disable warmup)" )
		self.CreateCVar( "up_points_override", "0", "Sets number of Uplinks to spawn to a maximum of 15. Set to 0 to use default amount. Takes effect on round end" )
		
	def OnRoundBegin(self):
		sizeScore = GEMPGameRules.GetMapMinPlayers() + GEMPGameRules.GetMapMaxPlayers()
		
		if sizeScore == 56:				# Default map size
			distanceMultiplier = 4.5
		
		elif sizeScore < 11:
			distanceMultiplier = 3.1
		elif sizeScore < 13:
			distanceMultiplier = 3.5
		elif sizeScore < 21:
			distanceMultiplier = 4.0
		elif sizeScore < 25:
			distanceMultiplier = 5.0
		else:
			distanceMultiplier = 6.0
		
		if GEMPGameRules.IsTeamplay():
			self.uplinkTimerMax = self.uplinkTimerMaxTeam
		else:
			self.uplinkTimerMax = self.uplinkTimerMaxSolo
			distanceMultiplier -= 1
		
		self.pointSeperation = distanceMultiplier * self.pointRadius
		
		GEMPGameRules.ResetAllPlayersScores()
		self.pointsJanus = 0; self.pointsMI6 = 0
		self.areaDictionary = {}
		self.fixDictionary = {}
		self.uplinkNames = []
		self.roundActive = True
		self.updateAreaTotal()
		if not self.WaitingForPlayers:
			self.createAreas()
	
	def OnRoundEnd(self):
		self.roundActive = False
		self.pointsMI6 = 0; self.pointsJanus = 0
		
		self.removeAreas()
		
		self.hideRoundScore(None)
	
	def CanPlayerChangeTeam( self, player, oldteam, newteam, wasforced ):
		if oldteam != newteam:
			self.removePlayerFromArea(player)
		return True
	
	def OnPlayerDisconnect( self, player ):
		self.removePlayerFromArea(player)
	
	def OnCaptureAreaSpawned( self, area ):
		name = GEMPGameRules.CGECaptureArea.GetGroupName(area)
		
		self.areaDictionary[ name ] = UplinkPoint(area.GetAbsOrigin(), name, area)
		
		GEMPGameRules.GetRadar().AddRadarContact( area, GEGlobal.RADAR_TYPE_OBJECTIVE, True, "sprites/hud/radar/capture_point", self.colorNeutral )
		self.createObjective( area, name, False )
		
		self.fixAreaDictionary()
	
	def OnCaptureAreaRemoved( self, area ):
		GEMPGameRules.GetRadar().DropRadarContact( area )
		
		areaName = GEMPGameRules.CGECaptureArea.GetGroupName(area)
		
		self.uplinkNames += [areaName]
		
		if areaName in self.areaDictionary:
			del self.areaDictionary[ areaName ]
		
		if area in self.fixDictionary:
			del self.fixDictionary[ area ]
	
	def OnCaptureAreaEntered( self, area, player, token ):
		if not GEMPGameRules.IsTeamplay():
			player.SetScoreBoardColor( self.scoreboardOnPoint )
		
		if not self.WaitingForPlayers and not self.warmupTimer.IsInWarmup():
			areaName = GEMPGameRules.CGECaptureArea.GetGroupName(area)
			if areaName in self.areaDictionary:
				self.addPlayerToArea(player, area, areaName)
			else:
				if area in self.fixDictionary:
					self.fixDictionary[area].append(player)
				else:
					self.fixDictionary[area] = [player]
	
	def OnCaptureAreaExited( self, area, player ):
		if not GEMPGameRules.IsTeamplay():
			try:
				player.SetScoreBoardColor( self.scoreboardDefault )
			except AttributeError:
				pass
		
		if not self.WaitingForPlayers and not self.warmupTimer.IsInWarmup():
			try:
				self.clearBars(player)
			except AttributeError:
				pass
			
			if self.roundActive:
				areaName = GEMPGameRules.CGECaptureArea.GetGroupName(area)
				if areaName in self.areaDictionary:
					self.areaDictionary[ areaName ].removePlayerList(player)
					
					if self.areaDictionary[ areaName ].checkContestedChange():
						self.changeContested( areaName, area, self.areaDictionary[ areaName ].isContested)
					
					if self.areaDictionary[ areaName ].checkProgressChange():
						self.createObjective( self.areaDictionary[ areaName ].UID, self.areaDictionary[ areaName ].name, self.areaDictionary[ areaName ].inProgress)
			
			if area in self.fixDictionary:
				if player in self.fixDictionary[area]:
					self.fixDictionary[name].remove(player)
	
	def OnPlayerSpawn( self, player ):
		if not self.WaitingForPlayers and not self.warmupTimer.IsInWarmup():
			if GEMPGameRules.IsTeamplay():
				self.showRoundScore( player )
		
			if not self.warmupTimer.IsInWarmup() and self.roundActive:
					self.updateAreaTotal()
					self.createAreas()
	
	def OnPlayerKilled( self, victim, killer, weapon ):
		victim.SetScoreBoardColor( self.scoreboardDefault )
		
		if self.warmupTimer.IsInWarmup() or not victim:
			return

		if not killer:
			victim.AddRoundScore( -1 )
			return
		
		if (GEMPGameRules.IsTeamplay() and victim.GetTeamNumber() == killer.GetTeamNumber()) or victim == killer:
			killer.AddRoundScore( -1 )

		else:
			killer.AddRoundScore( 1 )
	
	def OnPlayerSay(self, player, text):
		if text == "!version":
			GEUtil.ClientPrint(player, GEGlobal.HUD_PRINTTALK, UplinkVersion) 
		
	def OnThink(self):
		self.updateRings()
		
		if GEMPGameRules.GetNumActivePlayers() < 2:
			if not self.WaitingForPlayers:
				self.notice_WaitingForPlayers = 0
				GEMPGameRules.EndRound()
			elif GEUtil.GetTime() > self.notice_WaitingForPlayers:
				GEUtil.HudMessage( None, "#GES_GP_WAITING", -1, -1, GEUtil.Color( 255, 255, 255, 255 ), 2.5, 1 )
				self.notice_WaitingForPlayers = GEUtil.GetTime() + 12.5

			self.warmupTimer.Reset()
			self.WaitingForPlayers = True
			return

		elif self.WaitingForPlayers:
			self.WaitingForPlayers = False
			if not self.warmupTimer.HadWarmup():
				self.warmupTimer.StartWarmup( int( GEUtil.GetCVarValue( "up_warmup" ) ), True )
				GEUtil.EmitGameplayEvent( "up_startwarmup" )
			else:
				GEMPGameRules.EndRound( False )
		
		if not self.warmupTimer.IsInWarmup() and not self.WaitingForPlayers:
			if GEMPGameRules.IsTeamplay():
				scoreMI6 = GEMPGameRules.GetTeam( GEGlobal.TEAM_MI6 ).GetRoundScore()
				scoreJanus = GEMPGameRules.GetTeam( GEGlobal.TEAM_JANUS ).GetRoundScore()
			for uplinkPoint in list(self.areaDictionary):
				updated = self.areaDictionary[uplinkPoint].updateUplinkTimer( self.uplinkTimerMax )
				self.updateBar( self.areaDictionary[uplinkPoint].playerList, self.areaDictionary[uplinkPoint].name )
				if updated:
					self.uplinkCaptured( self.areaDictionary[uplinkPoint].name, self.areaDictionary[uplinkPoint].UID, updated )
				if GEMPGameRules.IsTeamplay():
					self.areaDictionary[uplinkPoint].updatePointTimer( self.pointTimerMax )
				
				if not updated and ((self.areaDictionary[ uplinkPoint ].timerJanus + self.areaDictionary[ uplinkPoint ].timerMI6) or len( self.areaDictionary[ uplinkPoint ].playerList )):
						self.createObjective( self.areaDictionary[ uplinkPoint ].UID, self.areaDictionary[ uplinkPoint ].name, self.areaDictionary[ uplinkPoint ].inProgress)
			if GEMPGameRules.IsTeamplay():
				if scoreMI6 != GEMPGameRules.GetTeam( GEGlobal.TEAM_MI6 ).GetRoundScore() or scoreJanus != GEMPGameRules.GetTeam( GEGlobal.TEAM_JANUS ).GetRoundScore():
					self.showRoundScore(None)



			####################					# # # # # # # # # # # # # # # # # #					   ####################
			#########################################         Custom Functions        #########################################
			####################					# # # # # # # # # # # # # # # # # #					   ####################


	def updateRings( self ):	# Draws the colored rings around Uplinks
		if self.pingTimer > self.pingTimerMax:
			ping = True; self.pingTimer = 0
		else:
			ping = False; self.pingTimer += 1
		
		for item in list(self.areaDictionary):
			area = self.areaDictionary[item].location
			area = GEUtil.Vector( area[0], area[1], area[2] + 3.0 )
			RingColor = self.getColor( self.areaDictionary[item].owner )
				
			GEUtil.CreateTempEnt( 0, origin = area, radius_start = self.pointRadius, radius_end = self.pointRadius + 0.1, framerate = 30, duration = 0.6, width = 3.0, amplitude = 0, color = RingColor, speed = 0 )
	
			if ping:	# Draws the "ping" effect around Uplinks
				PingColor = self.getColorPing(self.areaDictionary[item].owner)
				GEUtil.CreateTempEnt( 0, origin = area, framerate = 30, duration = 2, speed = 10, width=0.66, amplitude=0.00, radius_start=0, radius_end=self.pointRadius,  color=PingColor )

	def createAreas( self ):
		areaCount = len( self.areaDictionary.keys() )
		
		for curNum in range( self.areaTotal - areaCount ):
			if len(self.uplinkNames):
				curName = self.uplinkNames.pop()
			else:
				curName = "Uplink Zone #" + str(areaCount  + 1)
			
			areaCount += 1
				
			self.createCaptureZone( curName, self.skinNeutral, GEGlobal.TEAM_NONE )
	
	def removeAreas( self ):
		for uplinkPoint in list(self.areaDictionary):
			GEMPGameRules.GetTokenMgr().RemoveCaptureArea( uplinkPoint )
		return
	
	def updateAreaTotal( self ):
		players = GEMPGameRules.GetNumActivePlayers()
		
		override = int( GEUtil.GetCVarValue( "up_points_override" ) )
		if override > 0:
			if override > 15:
				override = 15
			self.areaTotal = override
		
		elif GEMPGameRules.IsTeamplay():
			if players < 6:
				self.areaTotal = 1
			elif players < 8:
				self.areaTotal = 2
			elif players < 10:
				self.areaTotal = 3
			elif players < 13:
				self.areaTotal = 4
			elif players < 17:
				self.areaTotal = 5
			else:
				self.areaTotal = 6
		
		else:
			if players < 7:
				self.areaTotal = 1
			elif players < 10:
				self.areaTotal = 2
			elif players < 14:
				self.areaTotal = 3
			elif players < 17:
				self.areaTotal = 4
			else:
				self.areaTotal = 5
	
	def getColor(self, owner):
		if owner == GEGlobal.TEAM_JANUS:
			return self.colorJanus
		elif owner == GEGlobal.TEAM_MI6:
			return self.colorMI6
		else:
			return self.colorNeutral
	
	def getObjColor(self, owner, capturing):
		if owner == GEGlobal.TEAM_JANUS:
			if capturing:
				return self.colorJanus_Hot
			else:
				return self.colorJanus_Cold
		elif owner == GEGlobal.TEAM_MI6:
			if capturing:
				return self.colorMI6_Hot
			else:
				return self.colorMI6_Cold
		else:
			if capturing:
				return self.colorNeutral_Hot
			else:
				return self.colorNeutral_Cold
			
	def getColorPing(self, owner):
		if owner == GEGlobal.TEAM_JANUS:
			return self.colorJanusPing
		elif owner == GEGlobal.TEAM_MI6:
			return self.colorMI6Ping
		else:
			return self.colorNeutralPing
	
	def createCaptureZone(self, name, skinType, team):
		GEMPGameRules.GetTokenMgr().SetupCaptureArea( name , model= "models/weapons/tokens/w_flagtoken.mdl", skin=skinType, limit=1, location=GEGlobal.SPAWN_TOKEN, radius=0.5*self.pointRadius, rqd_team = GEGlobal.TEAM_NONE, rqd_token= None, spread=self.pointSeperation)

	def createObjective(self, area, name, capturing):
		if capturing:
			if GEMPGameRules.IsTeamplay():
				title = str(int( (self.areaDictionary[ name ].timerJanus + self.areaDictionary[ name ].timerMI6) * (100.0 / self.uplinkTimerMax))) + "%%"
			else:
				if name in self.areaDictionary:
					tempList = []
					for player in self.areaDictionary[ name ].playerList:
						tempList += [self.areaDictionary[ name ].playerTimers[ GEEntity.GetUID( player ) ]]
					title = str( int( max(tempList) * 100.0 / self.uplinkTimerMax )) + "%%"
		else:
			title = ""
		color = self.getObjColor( self.areaDictionary[ name ].owner, capturing )
		GEMPGameRules.GetRadar().SetupObjective( area, GEGlobal.TEAM_NONE, "", title, color, int( 0.6 * self.pointRadius ), capturing )
	
	def printCapture(self, playerList, team):
		if GEMPGameRules.IsTeamplay():
			if team == GEGlobal.TEAM_MI6:
				color = self.colorKilltickerMI6
				name = self.printMI6
			else:
				color = self.colorKilltickerJanus
				name = self.printJanus
			if len( playerList ) == 1:
					msg = color + playerList[0] + self.capturedPrintMsg
			elif len( playerList ) == 2:
				msg = color + playerList[1] + self.capturedPrintMsgAnd + color + playerList[0] + self.capturedPrintMsg
			else:
				msg = color + name + self.capturedPrintMsg
		else:
			msg = self.colorKilltickerNoTeam + playerList[0] + self.capturedPrintMsg
			
		GEUtil.PostDeathMessage( msg )
	
	def showMsg(self, player, msg):
		GEUtil.InitHudProgressBar(player, self.barIndex, msg, GEGlobal.HUDPB_TITLEONLY, 0, -1, .75, 0, 0, self.colorMsg)
	
	def showBar(self, player):
		GEUtil.InitHudProgressBar(player, self.barIndex, self.barTitle, 1, float(self.uplinkTimerMax), -1, .75, 110, 12, self.colorBarStandard)
	
	def showContestedMsg(self, player, state):
		if state:
			GEUtil.InitHudProgressBar(player, self.barIndex, self.contestedMsg, GEGlobal.HUDPB_TITLEONLY, 0, -1, .75, 0, 0, self.colorMsgContested)
		else:
			self.showBar(player)
	
	def updateBar(self, playerList, areaName):
		for player in playerList:
			if GEMPGameRules.IsTeamplay():
				if player.GetTeamNumber() == GEGlobal.TEAM_MI6:
					num = self.areaDictionary[ areaName ].timerMI6
				else:
					num = self.areaDictionary[ areaName ].timerJanus
				GEUtil.UpdateHudProgressBar( player, self.barIndex, num )
			else:
				tempPlayerTimers = self.areaDictionary[ areaName ].playerTimers
				num = tempPlayerTimers[ GEEntity.GetUID(player) ]
				GEUtil.UpdateHudProgressBar( player, self.barIndex, num )

	def clearBars(self, player):
		GEUtil.RemoveHudProgressBar(player, self.barIndex)
	
	def changeContested(self, areaName, areaID, newState):
		for player in self.areaDictionary[ areaName ].playerList:
			if player.GetTeamNumber() != self.areaDictionary[ areaName ].owner or not GEMPGameRules.IsTeamplay():
				self.showContestedMsg(player, newState)
				if newState:
					GEUtil.PlaySoundToPlayer( player,"Buttons.beep_denied")
	
	def uplinkCaptured(self, areaName, areaID, newOwner):
		if GEMPGameRules.IsTeamplay():
			oldOwner = self.areaDictionary[ areaName ].owner
			self.areaDictionary[ areaName ].owner = newOwner
			self.areaDictionary[ areaName ].inProgress = False
			GEMPGameRules.GetRadar().AddRadarContact( areaID, GEGlobal.RADAR_TYPE_OBJECTIVE, True, "sprites/hud/radar/capture_point", self.getColor(newOwner) )
			self.createObjective(areaID, areaName, False)
			ringLocation = GEUtil.Vector( self.areaDictionary[areaName].location[0], self.areaDictionary[areaName].location[1], self.areaDictionary[areaName].location[2] + 3.0 )
			GEUtil.CreateTempEnt( 0, origin = ringLocation, framerate = 30, duration = 0.6, speed = 1, width=20, amplitude=5, radius_start=0, radius_end=self.pointRadius,  color=self.getColor(newOwner) )
			if newOwner == GEGlobal.TEAM_JANUS:
				GEUtil.PlaySoundToTeam( newOwner, "GEGamePlay.Token_Grab", True )
				GEUtil.PlaySoundToTeam( GEGlobal.TEAM_MI6, "GEGamePlay.Token_Drop_Enemy", True )
				self.createCaptureZone( areaName, self.skinJanus, GEGlobal.TEAM_JANUS )
				GEUtil.EmitGameplayEvent( "up_capture_team", "%i" % GEGlobal.TEAM_JANUS )
			elif newOwner == GEGlobal.TEAM_MI6:
				GEUtil.PlaySoundToTeam( newOwner, "GEGamePlay.Token_Grab", True )
				GEUtil.PlaySoundToTeam( GEGlobal.TEAM_JANUS, "GEGamePlay.Token_Drop_Enemy", True )
				self.createCaptureZone( areaName, self.skinMI6, GEGlobal.TEAM_MI6 )
				GEUtil.EmitGameplayEvent( "up_capture_team", "%i" % GEGlobal.TEAM_MI6 )
			GEMPGameRules.GetTeam( newOwner ).AddRoundScore( 1 )
			nameList = []
			for player in self.areaDictionary[ areaName ].playerList:
				self.clearBars( player )
				self.showMsg( player, self.completeMsg )
				player.AddRoundScore( self.uplinkReward )
				GEUtil.PlaySoundToPlayer( player, "GEGamePlay.Token_Chime", False )
				nameList += [player.GetCleanPlayerName()]
				if oldOwner == GEGlobal.TEAM_NONE:
					GEUtil.EmitGameplayEvent( "up_capture_neutral", "%i" % player.GetUserID() )
				else:
					GEUtil.EmitGameplayEvent( "up_capture_steal", "%i" % player.GetUserID() )
			self.printCapture(nameList, newOwner)
			
		else:
			ringLocation = GEUtil.Vector( self.areaDictionary[areaName].location[0], self.areaDictionary[areaName].location[1], self.areaDictionary[areaName].location[2] + 3.0 )
			GEUtil.CreateTempEnt( 0, origin = ringLocation, framerate = 30, duration = 0.6, speed = 1, width=20, amplitude=5, radius_start=0, radius_end=self.pointRadius,  color=self.colorNeutral )
			for player in self.areaDictionary[ areaName ].playerList:
				self.clearBars( player )
				player.SetScoreBoardColor( self.scoreboardDefault )
				player.AddRoundScore( self.uplinkRewardSoloPoints )
				GEUtil.PlaySoundToPlayer( player, "GEGamePlay.Token_Chime", False )
				GEUtil.EmitGameplayEvent( "up_capture_solo", "%i" % player.GetUserID() )
				self.printCapture([player.GetCleanPlayerName()], player)
				
				rewardHP = self.uplinkRewardSoloHP
				
				newHealth = float(player.GetHealth()) / float(player.GetMaxHealth()) + rewardHP
				if newHealth > 1.0:
					player.SetHealth(player.GetMaxHealth())
					newArmor = newHealth - 1.0 + float(player.GetArmor()) / float(player.GetMaxArmor())
					if newArmor > 1.0:
						newArmor = 1.0
					player.SetArmor(int(newArmor * player.GetMaxArmor()))
				else:
					player.SetHealth(int(newHealth * player.GetMaxHealth()))
				
			GEMPGameRules.GetTokenMgr().RemoveCaptureArea( areaName )
			
			self.updateAreaTotal()
			if len( self.areaDictionary.keys() ) < self.areaTotal:
				self.createCaptureZone( areaName, self.skinNeutral, GEGlobal.TEAM_NONE )

	def showRoundScore(self, target):
		scoreJanus = GEMPGameRules.GetTeam( GEGlobal.TEAM_JANUS ).GetRoundScore()
		scoreMI6 = GEMPGameRules.GetTeam( GEGlobal.TEAM_MI6 ).GetRoundScore()
		
		GEUtil.HudMessage( target, self.colorOwnershipJanus + str(scoreJanus) + self.colorOwnershipNeutral + self.colorOwnershipMI6 + str(scoreMI6), -1, 0.0, self.distColorNeutral, float('inf'), 1 )
	
	def hideRoundScore(self, target):
		GEUtil.HudMessage( target, "", 0.0, 0.0, self.distColorNeutral, 0, 1 )
	
	def fixAreaDictionary(self):
		if len( self.fixDictionary.keys() ) and not self.WaitingForPlayers and not self.warmupTimer.IsInWarmup():
			for area in list(self.fixDictionary):
				areaName = GEMPGameRules.CGECaptureArea.GetGroupName(area)
				if areaName in self.areaDictionary:
					for player in self.fixDictionary[area]:
						self.addPlayerToArea(player, area, areaName)
					del self.fixDictionary[area]
				else:
					continue

	def addPlayerToArea(self, player, area, areaName):
		self.areaDictionary[ areaName ].addPlayerList(player)
		if self.areaDictionary[ areaName ].owner == player.GetTeamNumber() and GEMPGameRules.IsTeamplay():
			self.showMsg( player, self.ownedMsg)
		elif self.areaDictionary[ areaName ].isContested:
			self.showContestedMsg(player, True)
		else:
			self.showBar( player )
		if self.areaDictionary[ areaName ].checkContestedChange():
			self.changeContested( areaName, area, self.areaDictionary[ areaName ].isContested )
		if self.areaDictionary[ areaName ].checkProgressChange():
			self.createObjective( self.areaDictionary[ areaName ].UID, self.areaDictionary[ areaName ].name, self.areaDictionary[ areaName ].inProgress)

	def removePlayerFromArea(self, player):
		for item in list(self.areaDictionary):
			if player in self.areaDictionary[ item ].playerList:
				self.areaDictionary[ item ].removePlayerList( player )
			else:
				continue