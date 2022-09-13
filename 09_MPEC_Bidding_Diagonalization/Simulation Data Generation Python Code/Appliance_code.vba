'    Domestic Appliance Model - Simulation Example Code
'
'    Copyright (C) 2009 Ian Richardson, Murray Thomson
'    CREST (Centre for Renewable Energy Systems Technology),
'    Department of Electronic and Electrical Engineering
'    Loughborough University, Leicestershire LE11 3TU, UK
'    Tel. +44 1509 635326. Email address: I.W.Richardson@lboro.ac.uk

'    This program is free software: you can redistribute it and/or modify
'    it under the terms of the GNU General Public License as published by
'    the Free Software Foundation, either version 3 of the License, or
'    (at your option) any later version.

'    This program is distributed in the hope that it will be useful,
'    but WITHOUT ANY WARRANTY; without even the implied warranty of
'    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
'    GNU General Public License for more details.

'    You should have received a copy of the GNU General Public License
'    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Option Explicit

' Create a collection to store the activity statisitics
Dim oActivityStatistics As Collection

' Declare an object to store activity statistics
Dim oActivityStatsItem As ProbabilityModifier

' Declare the appliance description variables
Dim sApplianceType As String
Dim iMeanCycleLength As Integer
Dim iCyclesPerYear As Integer
Dim iStandbyPower As Integer
Dim iRatedPower As Integer
Dim dCalibration As Double
Dim dOwnership As Double
Dim iTargetAveragekWhYear As Integer
Dim sUseProfile As String
Dim iRestartDelay As Integer
Dim bHasAppliance As Boolean

' Declare timing counter and current power use variables
Dim iCycleTimeLeft As Integer
Dim iRestartDelayTimeLeft As Integer
Dim iPower As Integer

Public Sub RunApplianceSimulation()

    ' Declare variables
    Dim iMonth As Integer
    Dim dRan As Double
    Dim dActivityProbability As Double
    Dim iTenMinuteCount As Integer
    Dim iAppliance As Integer
    Dim bWeekend As Boolean
    Dim iMinute As Integer
    Dim iActiveOccupants As Integer
    Dim sKey As String
    Dim sCell As String
    Dim iApplianceSourceCellOffsetY As Integer
    Dim iApplianceTargetCellOffsetX As Integer
    
    ' Declare an array to store an annual temperature profile (used for heating appliances)
    Dim oMonthlyRelativeTemperatureModifier As Variant
    
    ' Define the relative monthly temperatures
    ' Data derived from MetOffice temperature data for the Midlands in 2007 (http://www.metoffice.gov.uk/climate/uk/2007/) Crown Copyright
    oMonthlyRelativeTemperatureModifier = Array(0, 1.63, 1.821, 1.595, 0.867, 0.763, 0.191, 0.156, 0.087, 0.399, 0.936, 1.561, 1.994)
    
    ' Define the cell count offsets
    iApplianceSourceCellOffsetY = 12
    iApplianceTargetCellOffsetX = 7
    
    ' Load the activity statistics into a collection
    LoadActivityStatistics
    
    ' Declare an array to store the simulation data
    Dim vSimulationArray(1 To 1442, 1 To 33) As Variant
    
    ' For each of the appliances
    For iAppliance = 1 To 33
    
        ' Initialisation
        iCycleTimeLeft = 0
        iRestartDelayTimeLeft = 0
    
        ' Get the appliance details
        sApplianceType = Range("'appliances'!T" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        iMeanCycleLength = Range("'appliances'!H" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        iCyclesPerYear = Range("'appliances'!G" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        iStandbyPower = Range("'appliances'!J" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        iRatedPower = Range("'appliances'!I" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        dCalibration = Range("'appliances'!W" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        dOwnership = Range("'appliances'!E" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        iTargetAveragekWhYear = Range("'appliances'!Z" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        sUseProfile = Range("'appliances'!U" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        iRestartDelay = Range("'appliances'!K" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value
        bHasAppliance = IIf(Range("'appliances'!D" + CStr(iAppliance + iApplianceSourceCellOffsetY)).Value = "YES", True, False)
        
        ' Get the month
        iMonth = Range("main!K6").Value
        
        ' Write the appliance type into the target sheet header
        vSimulationArray(1, iAppliance) = sApplianceType
        
        ' Write the units
        vSimulationArray(2, iAppliance) = "(W)"
            
        ' Check if this appliance is assigned to this dwelling
        If (Not bHasAppliance) Then
        
            ' This appliance is not applicable, so write zeros to the power demand
            Dim iCount As Integer
            For iCount = 3 To 1442
                vSimulationArray(iCount, iAppliance) = 0
            Next iCount
                        
        Else
         
            ' Randomly delay the start of appliances that have a restart delay (e.g. cold appliances with more regular intervals)
            iRestartDelayTimeLeft = Rnd() * iRestartDelay * 2 ' Weighting is 2 just to provide some diversity
        
            ' Make the rated power variable over a normal distribution to provide some variation
            iRatedPower = Lighting_Model.GetMonteCarloNormalDistGuess(Val(iRatedPower), iRatedPower / 10)
    
            ' Get the weekday or weekend flag
            bWeekend = IIf(Range("K5").Value = "wd", False, True)
             
            ' Loop through each minute of the day
            iMinute = 1
            Do While (iMinute <= 1440)
                
                ' Set the default (standby) power demand at this time step
                iPower = iStandbyPower
            
                ' Get the ten minute period count
                iTenMinuteCount = ((iMinute - 1) \ 10)
            
                ' Get the number of current active occupants for this minute
                ' Convert from 10 minute to 1 minute resolution
                iActiveOccupants = Range("occ_sim_data!C" + CStr(11 + ((iMinute - 1) \ 10))).Value
    
                ' Now generate a key to get the activity statistics
                sKey = IIf(bWeekend, "1", "0") + "_" + CStr(iActiveOccupants) + "_" + sUseProfile
    
                ' If this appliance is off having completed a cycle (ie. a restart delay)
                If (iCycleTimeLeft <= 0) And (iRestartDelayTimeLeft > 0) Then
    
                    ' Decrement the cycle time left
                    iRestartDelayTimeLeft = iRestartDelayTimeLeft - 1
                            
                ' Else if this appliance is off
                ElseIf iCycleTimeLeft <= 0 Then
    
                    ' There must be active occupants, or the profile must not depend on occupancy for a start event to occur
                    If (iActiveOccupants > 0 And sUseProfile <> "CUSTOM") Or (sUseProfile = "LEVEL") Then
    
                        ' Variable to store the event probability (default to 1)
                        dActivityProbability = 1
                        
                        ' For appliances that depend on activity profiles and is not a custom profile ...
                        If (sUseProfile <> "LEVEL") And (sUseProfile <> "ACTIVE_OCC") And (sUseProfile <> "CUSTOM") Then
                        
                            ' Get the activity statistics for this profile
                            Set oActivityStatsItem = oActivityStatistics.Item(sKey)
    
                            ' Get the probability for this activity profile for this time step
                            dActivityProbability = oActivityStatistics(sKey).Modifiers(iTenMinuteCount)
                        
                        ' For electric space heaters ... (excluding night storage heaters)
                        ElseIf (sApplianceType = "ELEC_SPACE_HEATING") Then
                            
                            ' If this appliance is an electric space heater, then then activity probability is a function of the month of the year
                            dActivityProbability = oMonthlyRelativeTemperatureModifier(iMonth)
                        
                        End If
    
                        ' Check the probability of a start event
                        If (Rnd() < (dCalibration * dActivityProbability)) Then
                        
                            ' This is a start event
                            StartAppliance
                            
                        End If
                    
                    ' Custom appliance handler: storage heaters have a simple representation
                    ElseIf (sUseProfile = "CUSTOM" And sApplianceType = "STORAGE_HEATER") Then
                            
                        ' The number of cycles (one per day) set out in the calibration sheet
                        ' is used to determine whether the storage heater is used
                        
                        ' This model does not account for the changes in the Economy 7 time
                        ' It assumes that the time starts at 00:30 each day
                        If (iTenMinuteCount = 4) Then ' ie. 00:30 - 00:40
                        
                            ' Assume January 14th is the coldest day of the year
                            Dim oDate, oDateOn, oDateOff As Date
                            Dim iMonthOn, iMonthOff As Integer
                            oDate = #1/14/1997#
                            
                            ' Get the month and day when the storage heaters are turned on and off, using the number of cycles per year
                            oDateOff = DateAdd("d", iCyclesPerYear / 2, oDate)
                            oDateOn = DateAdd("d", 0 - iCyclesPerYear / 2, oDate)
                            iMonthOff = DatePart("m", oDateOff)
                            iMonthOn = DatePart("m", oDateOn)
                            
                            ' Declare a probability of use variable
                            Dim dProbability As Double
                            
                            ' If this is a month in which the appliance is turned on of off
                            If (iMonth = iMonthOff) Or (iMonth = iMonthOn) Then
                                ' Pick a 50% chance since this month has only a month of year resolution
                                dProbability = 0.5 / 10  ' (since there are 10 minutes in this period)
                            ElseIf (iMonth > iMonthOff) And (iMonth < iMonthOn) Then
                                ' The appliance is not used in summer
                                dProbability = 0
                            Else
                                ' The appliance is used in winter
                                dProbability = 1
                            End If
                                                      
                            ' Determine if a start event occurs
                            If (Rnd() <= dProbability) Then
                            
                                ' This is a start event
                                StartAppliance
                                
                            End If
                        End If
                    End If
                Else
                    ' The appliance is on - if the occupants become inactive, switch off the appliance
                    If (iActiveOccupants = 0) And (sUseProfile <> "LEVEL") And (sUseProfile <> "ACT_LAUNDRY") And (sUseProfile <> "CUSTOM") Then
                             
                        ' Do nothing. The activity will be completed upon the return of the active occupancy.
                        ' Note that LEVEL means that the appliance use is not related to active occupancy.
                        ' Note also that laundry appliances do not switch off upon a transition to inactive occupancy.
                    Else
    
                        ' Set the power
                        iPower = GetPowerUsage(iCycleTimeLeft)
                        
                        ' Decrement the cycle time left
                        iCycleTimeLeft = iCycleTimeLeft - 1
                        
                    End If
                End If
    
                ' Set the appliance power at this time step
                vSimulationArray(2 + iMinute, iAppliance) = iPower
            
                ' Increment the time
                iMinute = iMinute + 1
                
            Loop
        End If
    Next iAppliance
    
    ' Write the data back to the simulation sheet
    Range("appliance_sim_data!H10:AN1451") = vSimulationArray
    
End Sub

Private Function CycleLength() As Integer
    
    ' Set the value to that provided in the configuration
    CycleLength = iMeanCycleLength
    
    ' Use the TV watching length data approximation, derived from the TUS data
    If (sApplianceType = "TV1") Or (sApplianceType = "TV2") Or (sApplianceType = "TV3") Then
    
        ' The cycle length is approximated by the following function
        ' The avergage viewing time is approximately 73 minutes
        CycleLength = CInt(70 * ((0 - Log(1 - Rnd())) ^ 1.1))
        
    ElseIf (sApplianceType = "STORAGE_HEATER") Or (sApplianceType = "ELEC_SPACE_HEATING") Then
    
        ' Provide some variation on the cycle length of heating appliances
        CycleLength = Lighting_Model.GetMonteCarloNormalDistGuess(CDbl(iMeanCycleLength), iMeanCycleLength / 10)
    
    End If
        
End Function

Private Function GetPowerUsage(ByVal iCycleTimeLeft As Integer) As Integer

    ' Set the return power to the rated power
    GetPowerUsage = iRatedPower

    ' Some appliances have a custom (variable) power profile depending on the time left
    Select Case sApplianceType
    
        Case "WASHING_MACHINE", "WASHER_DRYER":
        
            ' Declare the total cycle time variable
            Dim iTotalCycleTime As Integer
        
            ' Calculate the washing cycle time
            If (sApplianceType = "WASHING_MACHINE") Then iTotalCycleTime = 138
            If (sApplianceType = "WASHER_DRYER") Then iTotalCycleTime = 198
        
            ' This is an example power profile for an example washing machine
            ' This simplistic model is based upon data from personal communication with a major washing maching manufacturer
            Select Case (iTotalCycleTime - iCycleTimeLeft + 1)
            
                Case 1 To 8: GetPowerUsage = 73         ' Start-up and fill
                Case 9 To 29: GetPowerUsage = 2056     ' Heating
                Case 30 To 81: GetPowerUsage = 73       ' Wash and drain
                Case 82 To 92: GetPowerUsage = 73       ' Spin
                Case 93 To 94: GetPowerUsage = 250      ' Rinse
                Case 95 To 105: GetPowerUsage = 73      ' Spin
                Case 106 To 107: GetPowerUsage = 250    ' Rinse
                Case 108 To 118: GetPowerUsage = 73     ' Spin
                Case 119 To 120: GetPowerUsage = 250    ' Rinse
                Case 121 To 131: GetPowerUsage = 73     ' Spin
                Case 132 To 133: GetPowerUsage = 250    ' Rinse
                Case 134 To 138: GetPowerUsage = 568    ' Fast spin
                Case 139 To 198: GetPowerUsage = 2500   ' Drying cycle
                Case Else: GetPowerUsage = iStandbyPower
            
            End Select
                            
    End Select

End Function


' Load the activity statistics into a collection
Private Sub LoadActivityStatistics()

    ' Declare the variables
    Dim i, j As Integer
    Dim sKey As String
    Dim sCell As String
    
    Set oActivityStatistics = New Collection
    
    ' Load the activity statistics into probability modifiers objects
    For i = 7 To 78
    
        ' Create a new probability modifier
        Set oActivityStatsItem = New ProbabilityModifier
    
        ' Read in the data
        oActivityStatsItem.IsWeekend = IIf(Range("'activity_stats'!B" + CStr(i)).Value = 1, True, False)
        oActivityStatsItem.ActiveOccupantCount = Range("'activity_stats'!C" + CStr(i)).Value
        oActivityStatsItem.ID = Range("'activity_stats'!D" + CStr(i)).Value
        
        ' Get the hourly modifiers
        For j = 0 To 143
        
            ' Get the column reference
            sCell = Cells(i, j + 5).Address(True, False, xlA1)
        
            ' Read the values
            oActivityStatsItem.Modifiers(j) = Range("'activity_stats'!" + sCell).Value
            
        Next j

        ' Now generate a key
        sKey = IIf(oActivityStatsItem.IsWeekend, "1", "0") + "_" + CStr(oActivityStatsItem.ActiveOccupantCount) + "_" + oActivityStatsItem.ID
        
        ' Add this object to the collection
        oActivityStatistics.Add Item:=oActivityStatsItem, Key:=sKey
    
    Next i

End Sub

Public Sub ConfigureAppliancesInDwelling()

    ' Variables
    Dim i As Integer
    Dim iOffset As Integer
    Dim dRan As Double
    Dim dProportion As Double

    ' Vertical offset
    iOffset = 12
    
    ' For each appliance
    For i = 1 To 33
    
        ' Get a random number
        dRan = Rnd()
        
        ' Get the proportion of houses with this appliance
        dProportion = Range("appliances!E" + CStr(i + iOffset))
        
        ' Determine if this simulated house has this appliance
        Range("appliances!D" + CStr(i + iOffset)).Value = IIf(dRan < dProportion, "YES", "NO")
    
    Next i

End Sub

' Start a cycle for the current appliance
Private Sub StartAppliance()

    ' Determine how long this appliance is going to be on for
    iCycleTimeLeft = CycleLength()
    
    ' Determine if this appliance has a delay after the cycle before it can restart
    iRestartDelayTimeLeft = iRestartDelay
    
    ' Set the power
    iPower = GetPowerUsage(iCycleTimeLeft)
    
    ' Decrement the cycle time left
    iCycleTimeLeft = iCycleTimeLeft - 1
                            
End Sub

