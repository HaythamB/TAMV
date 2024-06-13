# API template for TAMV interfaces
# MAIN CLASS NAME MUST BE "printerAPI" - do not change
# Search for "##############*** YOUR CUSTOM CODE #################" to find the sections that need to be modified.
#
# Not intended to be a gerneral purpose interface; instead, it contains methods
# to issue commands or return specific information. Feel free to extend with new
# methods for other information; please keep the abstraction for V2 V3 
#
# Copyright (C) 2020 Danal Estes all rights reserved.
# Copyright (C) 2022 Haytham Bennani
# Released under The MIT License. Full text available via https://opensource.org/licenses/MIT
#
# Requires Python3
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# shared import dependencies
import json
import time
# invoke parent (TAMV) _logger
_logger = logging.getLogger('TAMV.DuetWebAPI')

##############*** YOUR CUSTOM CODE #################
# Feel free to add whatever imports you may need to get this running in this section
##############*** YOUR CUSTOM CODE #################


#################################################################################################################################
#################################################################################################################################
# Main class for interface
# Rename this to whatever you want, and this needs to be the filename and the file called from TAMV
# For your custom TAMV tests, modify the following 2 statements in the TAMV_GUI.py file:
#   - "import DuetWebAPI as DWA"
#   - "self.printer = DWA.DuetWebAPI(self.printerURL)"

class printerAPI:
    # Max time to wait for toolchange before raising a timeout exception, in seconds
    _toolTimeout = 300
    # Max time to wait for HTTP requests to complete
    _requestTimeout = 2
    _responseTimeout = 10
    
    ##############*** YOUR CUSTOM CODE #################
    # Here's the section to add your class attributes
    ##############*** YOUR CUSTOM CODE #################

    #################################################################################################################################
    # Instantiate class and connect to controller
    # This is your main setup call, which will be returned
    # Parameters:
    #   - baseURL (string): full IP address (not FQDN or alias) in the format 'http://xxx.xxx.xxx.xxx' without trailing '/'
    #   - optional: nickname (string): short nickname for identifying machine (strictly for TAMV GUI)
    #
    # Returns: NONE
    # 
    # Raises: 
    #   - UnknownController: if fails to connect
    def __init__( self, baseURL, nickname='Default', password='reprap' ):
        _logger.debug('Starting API..')

        # Here are the required class attributes. These get saved to settings.json
        self._base_url = "whatever you want - this gets called from the dialog box when connecting - required"
        self._password = "password to connect to machine (if applicable) - can be empty string"
        self._name = "Printer name according to firmware (if applicable) - can be empty string"
        self._nickname = "Printer nickname - future use - can be empty string"
        self._firmwareName = "Firmware name - can be empty string"
        self._firmwareVersion = "Firmware version - can be empty string"
        # tools is an array of the Tool class located at the end of this file - read that first.
        self.tools = []

        try: 
            ##############*** YOUR CUSTOM CODE #################
            # add your code to connect to your controller in this section
            ##############*** YOUR CUSTOM CODE #################
            if( you_board_failed_to_connect ):
                # The board has failed to connect, return an error state
                raise UnknownController('Unknown controller detected.')
        except UnknownController as uc:
            _logger.critical( "Unknown controller at " + self._base_url )
            raise SystemExit(uc)
        except Exception as e:
            # Catastrophic error. Bail.
            _logger.critical( str(e) )
            raise SystemExit(e)
        _logger.info('  .. connected to '+ firmwareName + '- V'+ self._firmwareVersion + '..')
        return

    #################################################################################################################################
    # Get firmware version
    # Parameters: 
    # - NONE
    #
    # Returns: integer
    #   - returns either 2 or 3 depending on which RRF version is running on the controller
    #
    # Raises: NONE
    def getPrinterType( self ):
        _logger.debug('Called getPrinterType')
        ##############*** YOUR CUSTOM CODE #################
        ##############*** YOUR CUSTOM CODE #################
        return( some_integer )
    
    #################################################################################################################################
    # Get number of defined tools from machine
    # Parameters: 
    #   - NONE
    #
    # Returns: integer
    #   - Positive integer for number of defined tools on machine
    #
    # Raises: 
    #   - FailedToolDetection: when cannot determine number of tools on machine
    def getNumTools( self ):
        _logger.debug('Called getNumTools')
        ##############*** YOUR CUSTOM CODE #################
        ##############*** YOUR CUSTOM CODE #################
        return( some_integer )

    #################################################################################################################################
    # Get index of currently loaded tool
    # Tool numbering always starts as 0, 1, 2, ..
    # Parameters: 
    #   - NONE
    #
    # Returns: integer
    #   - Positive integer for index of current loaded tool
    #   - '-1' if no tool is loaded on the machine
    #
    # Raises: 
    #   - FailedToolDetection: when cannot determine number of tools on machine
    def getCurrentTool( self ):
        _logger.debug('Called getCurrentTool')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            
            # Unknown condition, raise error
            raise FailedToolDetection('Something failed. Baililng.')
        except ConnectionError as ce:
            _logger.critical('Connection error while polling for current tool')
            raise SystemExit(ce)
        except FailedToolDetection as fd:
            _logger.critical('Failed tool detection.')
            raise SystemExit(e1)
        except Exception as e1:
            _logger.critical('Unhandled exception in getCurrentTool: ' + str(e1))
            raise SystemExit(e1)

    #################################################################################################################################
    # Get currently defined offsets for tool referenced by index
    # Tool numbering always starts as 0, 1, 2, ..
    # Parameters:
    #   - toolIndex (integer): index of tool to get offsets for
    #
    # Returns: 
    #   - tuple of floats: { 'X': 0.000 , 'Y': 0.000 , 'Z': 0.000 }
    #
    # Raises: 
    #   - FailedOffsetCapture: when cannot determine number of tools on machine
    def getToolOffset( self, toolIndex=0 ):
        _logger.debug('Called getToolOffset')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            raise FailedOffsetCapture('getG10ToolOffset entered unhandled exception state.')
        except FailedOffsetCapture as fd:
            _logger.critical(str(fd))
            raise SystemExit(fd)
        except ConnectionError as ce:
            _logger.critical('Connection error in getToolOffset.')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in getToolOffset: ' + str(e1))
            raise SystemExit(e1)

    #################################################################################################################################
    # Get machine status, mapping any controller status output into 1 of 3 possible states
    # Parameters:
    #   - NONE
    #
    # Returns: string of following values ONLY
    #   - idle
    #   - processing
    #   - paused
    #
    # Raises: 
    #   - StatusException: when cannot determine machine status
    #   - StatusTimeoutException: when machine takes longer than _toolTimeout seconds to respond
    def getStatus( self ):
        _logger.debug('Called getStatus')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################

            # OUTPUT MAPPING LOGIC
            # Handle return mapping of status variable "_status"
            # Change the conditions as appropriate, but maintain the return values and logging please.
            if ( _status == "idle" or _status == "I"):
                _logger.debug("Machine is idle.")
                return ("idle")
            elif ( _status == "paused" or _status == "S" or _status == "pausing" or _status == "D"):
                _logger.debug("Machine is paused.")
                return ("paused")
            else:
                _logger.debug("Machine is busy processing something.")
                return ("processing")
            
            # unknown error raise exception
            raise StatusException('Unknown error getting machine status')
        except StatusException as se:
            _logger.critical(str(se))
            raise SystemExit(se)
        except ConnectionError as ce:
            _logger.critical('Connection error in getStatus')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in getStatus: ' + str(e1))
            raise SystemExit(e1)

    #################################################################################################################################
    # Get current tool coordinates from machine in XYZ space
    # Parameters:
    #   - NONE
    #
    # Returns: 
    #   - tuple of 3 decimal places precise floats: { 'X': 0.000 , 'Y': 0.000 , 'Z': 0.000 }
    #
    # Raises: 
    #   - CoordinatesException: when cannot determine machine status
    def getCoordinates( self ):
        _logger.debug('Called getCoordinates')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            if failed:
                raise CoordinatesException("Unknown duet controller.")
            else:
                # NOTE: round results to a maximum of 3 decimals places
                return( {'X': 0.000, 'Y': 0.000, 'Z': 0.000 } )
        except CoordinatesException as ce1:
            _logger.critical(str(ce1))
            raise SystemExit(ce1)
        except ConnectionError as ce:
            _logger.critical('Connection error in getCoordinates')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in getCoordinates: ' + str(e1))
            raise SystemExit(e1)

    #################################################################################################################################
    # Set tool offsets for indexed tool in X, Y, and Z
    # Parameters:
    #   - toolIndex (integer):
    #   - offsetX (float):
    #   - offsetY (float):
    #   - offsetZ (float):
    #
    # Returns: NONE
    #
    # Raises: 
    #   - SetOffsetException: when failed to set offsets in controller
    def setToolOffsets( self, tool=None, X=None, Y=None, Z=None ):
        _logger.debug('Called setToolOffsets')
        try:
            # Check for invalid tool index, raise exception if needed.
            if( tool is None ):
                raise SetOffsetException( "No tool index provided.")
            # Check that any valid offset has been passed as an argument
            elif( X is None and Y is None and Z is None ):
                raise SetOffsetException( "Invalid offsets provided." )
            else:
                ##############*** YOUR CUSTOM CODE #################
                ##############*** YOUR CUSTOM CODE #################
                _logger.debug( "Tool offsets applied.")
        except SetOffsetException as se:
            _logger.error(se)
            return
        except Exception as e:
            _logger.critical( "setToolOffsets unhandled exception: " + str(e) )
            raise SystemExit( "setToolOffsets unhandled exception: " + str(e) )

    #################################################################################################################################
    # Helper function to check if machine is idle or not
    # Parameters: NONE
    #
    # Returns: boolean
    def isIdle( self ):
        _logger.debug("Called isIdle")
        ##############*** YOUR CUSTOM CODE #################
        ##############*** YOUR CUSTOM CODE #################
        if( state == "idle" ):
            return True
        else:
            return False

    #################################################################################################################################
    # Helper function to check if machine is homed on all axes for motion
    # Parameters: NONE
    #
    # Returns: boolean
    def isHomed( self ):
        _logger.debug("Called isHomed")
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            if( homed ): 
                return True
            else:
                return False
        except Exception as e:
            _logger.critical( "Failed to check if machine is homed. " + str(e) )
            raise SystemExit("Failed to check if machine is homed. " + str(e))

    #################################################################################################################################
    # Load specified tool on machine, and wait until machine is idle
    # Tool numbering always starts as 0, 1, 2, ..
    # If the toolchange takes longer than the class attribute _toolTimeout, then raise a warning in the log and return.
    #
    # ATTENTION: 
    #       This assumes that your machine will not end up in an un-usable / unsteady state if the timeout occurs.
    #       You may change this behavior by modifying the exception handling for ToolTimeoutException.
    #
    # Parameters:
    #   - toolIndex (integer): index of tool to load
    #
    # Returns: NONE
    #
    # Raises: 
    #   - ToolTimeoutException: machine took too long to load the tool
    def loadTool( self, toolIndex = 0 ):
        _logger.debug('Called loadTool')
        # variable to hold current tool loading "virtual" timer
        toolchangeTimer = 0

        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            
            # Wait until machine is done loading tool and is idle
            while not self.isIdle() and toolchangeTimer <= self._toolTimeout:
                self._toolTimeout += 2
                time.sleep(2)
            if( toolchangeTimer > self._toolTimeout ):
                # Request for toolchange timeout, raise exception
                raise ToolTimeoutException( "Request to change to tool T" + str(toolIndex) + " timed out.")
            return
        except ToolTimeoutException as tte:
            _logger.warning(str(tte))
            return
        except ConnectionError as ce:
            _logger.critical('Connection error in loadTool.')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in loadTool: ' + str(e1))
            raise SystemExit(e1)

    #################################################################################################################################
    # Unload all tools from machine and wait until machine is idle
    # Tool numbering always starts as 0, 1, 2, ..
    # If the unload operation takes longer than the class attribute _toolTimeout, then raise a warning in the log and return.
    #
    # ATTENTION: 
    #       This assumes that your machine will not end up in an un-usable / unsteady state if the timeout occurs.
    #       You may change this behavior by modifying the exception handling for ToolTimeoutException.
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: 
    #   - ToolTimeoutException: machine took too long to load the tool
    def unloadTools( self ):
        _logger.debug('Called unloadTools')
        # variable to hold current tool loading "virtual" timer
        toolchangeTimer = 0
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################

            # Wait until machine is done loading tool and is idle
            while not self.isIdle() and toolchangeTimer <= self._toolTimeout:
                self._toolTimeout += 2
                time.sleep(2)
            if( toolchangeTimer > self._toolTimeout ):
                # Request for toolchange timeout, raise exception
                raise ToolTimeoutException( "Request to unload tools timed out!")
            return
        except ToolTimeoutException as tte:
            _logger.warning(str(tte))
            return
        except ConnectionError as ce:
            _logger.critical('Connection error in unloadTools')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in unloadTools: ' + str(e1))
            raise SystemExit(e1)

    #################################################################################################################################
    # Execute a relative positioning move (G91 in Duet Gcode), and return to absolute positioning.
    # You may specify if you want to execute a rapid move (G0 command), and set the move speed in feedrate/min.
    #
    # Parameters:
    #   - rapidMove (boolean): enable a G0 command at specified or max feedrate (in Duet CNC/Laser mode)
    #   - moveSpeed (float): speed at which to execute the move speed in feedrate/min (typically in mm/min)
    #   - X (float): requested X axis final position
    #   - Y (float): requested Y axis final position
    #   - Z (float): requested Z axis final position 
    #
    # Returns: NONE
    #
    # Raises:
    #   - HomingException: machine is not homed
    def moveRelative( self, rapidMove=False, moveSpeed=1000, X=None, Y=None, Z=None ):
        _logger.debug('Called moveRelative')
        try:
            # check if machine has been homed fully
            if( self.isHomed() is False ):
                raise HomingException("Machine axes have not been homed properly.")
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################

        except HomingException as he:
            _logger.error( he )
        except Exception as e:
            errorString = "Move failed to relative coordinates: ("
            if( X is not None ):
                errorString += " X" + str(X)
            if( Y is not None ):
                errorString += " Y" + str(Y)
            if( Z is not None ):
                errorString += " Z" + str(Z)
            errorString += ") at speed: " + str(moveSpeed)
            _logger.critical(errorString)
            raise SystemExit(errorString + "\n" + str(e))
        return

    #################################################################################################################################
    # Execute an absolute positioning move (G90 in Duet Gcode), and return to absolute positioning.
    # You may specify if you want to execute a rapid move (G0 command), and set the move speed in feedrate/min.
    #
    # Parameters:
    #   - rapidMove (boolean): enable a G0 command at specified or max feedrate (in Duet CNC/Laser mode)
    #   - moveSpeed (float): speed at which to execute the move speed in feedrate/min (typically in mm/min)
    #   - X (float): requested X axis final position
    #   - Y (float): requested Y axis final position
    #   - Z (float): requested Z axis final position 
    #
    # Returns: NONE
    #
    # Raises: NONE
    def moveAbsolute( self, rapidMove=False, moveSpeed=1000, X=None, Y=None, Z=None ):
        _logger.debug('Called moveAbsolute')
        try:
            # check if machine has been homed fully
            if( self.isHomed() is False ):
                raise HomingException("Machine axes have not been homed properly.")
            
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################

        except HomingException as he:
            _logger.error( he )
        except Exception as e:
            errorString = " move failed to absolute coordinates: ("
            if( X is not None ):
                errorString += " X" + str(X)
            if( Y is not None ):
                errorString += " Y" + str(Y)
            if( Z is not None ):
                errorString += " Z" + str(Z)
            errorString += ") at speed: " + str(moveSpeed)
            _logger.critical(errorString + str(e) )
            raise SystemExit(errorString + "\n" + str(e))
        return

    #################################################################################################################################
    # Limit machine movement to within predefined boundaries as per machine-specific configuration.
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: NONE
    def limitAxes( self ):
        _logger.debug('Called limitAxes')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            _logger.debug("Axes limits enforced successfully.")
        except Exception as e:
            _logger.error("Failed to limit axes movement: " + str(e))
            raise SystemExit("Failed to limit axes movement: " + str(e))
        return

    #################################################################################################################################
    # Flush controller movement buffer
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: NONE
    def flushMovementBuffer( self ):
        _logger.debug('Called flushMovementBuffer')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################

            _logger.debug("flushMovementBuffer ran successfully.")
        except Exception as e:
            _logger.error("Failed to flush movement buffer: " + str(e))
            raise SystemExit("Failed to flush movement buffer: " + str(e))
        return

    #################################################################################################################################
    # Save tool offsets to "firmware"
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: NONE
    def saveOffsetsToFirmware( self ):
        _logger.debug('Called saveOffsetsToFirmware')
        try:
            ##############*** YOUR CUSTOM CODE #################
            ##############*** YOUR CUSTOM CODE #################
            _logger.debug("Tool offsets saved to firmware.")
        except Exception as e:
            _logger.error("Failed to save offsets: " + str(e))
            raise SystemExit("Failed to save offsets: " + str(e))
        return

    #################################################################################################################################
    #################################################################################################################################
    # Core class functions
    #
    # These functions handle sending gcode commands to your controller:
    #   - gCode: send a single line of gcode
    #   - gCodeBatch: send an array of gcode strings to your controller and execute them sequentially 

    def gCode(self,command):
        _logger.debug('gCode called')
        ##############*** YOUR CUSTOM CODE #################
        ##############*** YOUR CUSTOM CODE #################
        if (ok):
            return 0
        else:
            _logger.error("Error running gCode command")
            raise SystemExit("Error running gCode command")
        return -1
    
    def gCodeBatch(self,commands):
        _logger.debug('gCode called')
        ##############*** YOUR CUSTOM CODE #################
        for command in commands:
            self.gCode(command)
        ##############*** YOUR CUSTOM CODE #################
        if (ok):
            return 0
        else:
            _logger.error("Error running gCode command")
            raise SystemExit("Error running gCode command")
        return -1

    ### DO NOT EDIT BEYOND THIS LINE ###
    #################################################################################################################################
    # Output JSON representation of printer
    #
    # Parameters: NONE
    #
    # Returns: JSON object for printer class
    #
    # Raises: NONE
    def getJSON( self ):
        printerJSON = { 
            'address': self._base_url,
            'password': self._password,
            'name': self._name,
            'nickname': self._nickname,
            'controller': self._firmwareName,
            'firmware': self._firmwareVersion,
            'tools': []
            }
        for i, currentTool in enumerate(self._tools):
            printerJSON['tools'].append(currentTool.getJSON())
        return( printerJSON )

    #################################################################################################################################
    #################################################################################################################################
    # ZTATP Core atomic class functions
    #
    # These are critical functions used by ZTATP to set up probes, check for odd RRF versions that have unique syntax requirements,
    # and are use to set/rest config file changes for the endstops to ensure correct operation of the ZTATP alignment scripts.

    def getFilenamed(self,filename):
        if (self.pt == 2):
            URL=(f'{self._base_url}'+'/rr_download?name='+filename)
        if (self.pt == 3):
            URL=(f'{self._base_url}'+'/machine/file/'+filename)
        r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout) )
        return(r.text.splitlines()) # replace('\n',str(chr(0x0a))).replace('\t','    '))
        
    def checkDuet2RRF3(self):
        if (self.pt == 2):
            URL=(f'{self._base_url}'+'/rr_status?type=2')
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout) )
            j = json.loads(r.text)
            s=j['firmwareVersion']
            
            # Send reply to clear buffer
            replyURL = (f'{self._base_url}'+'/rr_reply')
            r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout) )

            if s == "3.2":
                return True
            else:
                return False

    #################################################################################################################################
    # The following methods provide services built on the ZTATP Core atomimc class functions. 

    # _nilEndStop
    # Given a line from config g that defines an endstop (N574) or Z probe (M558),
    # Return a line that will define the same thing to a "nil" pin, i.e. undefine it
    def _nilEndstop(self,configLine):
        ret = ''
        for each in [word for word in configLine.split()]: 
            ret = ret + (each if (not (('P' in each[0]) or ('p' in each[0]))) else 'P"nil"') + ' '
        return(ret)

    def clearEndstops(self):
        c = self.getFilenamed('/sys/config.g')
        commandBuffer = []
        for each in [line for line in c if (('M574 ' in line) or ('M558 ' in line)                   )]:
            commandBuffer.append(self._nilEndstop(each))
        self.gCodeBatch(commandBuffer)

    def resetEndstops(self):
        c = self.getFilenamed('/sys/config.g')
        commandBuffer = []
        for each in [line for line in c if (('M574 ' in line) or ('M558 ' in line)                    )]:
            commandBuffer.append(self._nilEndstop(each))
        for each in [line for line in c if (('M574 ' in line) or ('M558 ' in line) or ('G31 ' in line))]:
            commandBuffer.append(each)
        self.gCodeBatch(commandBuffer)

    def resetAxisLimits(self):
        c = self.getFilenamed('/sys/config.g')
        commandBuffer = []
        for each in [line for line in c if 'M208 ' in line]:
            commandBuffer.append(each)
        self.gCodeBatch(commandBuffer)

    def resetG10(self):
        c = self.getFilenamed('/sys/config.g')
        commandBuffer = []
        for each in [line for line in c if 'G10 ' in line]:
            commandBuffer.append(each)
        self.gCodeBatch(commandBuffer)

    def resetAdvancedMovement(self):
        c = self.getFilenamed('/sys/config.g')
        commandBuffer = []
        for each in [line for line in c if (('M566 ' in line) or ('M201 ' in line) or ('M204 ' in line) or ('M203 ' in line))]:
            commandBuffer.append(each)
        self.gCodeBatch(commandBuffer)

    def getTriggerHeight(self):
        _errCode = 0
        _errMsg = ''
        triggerHeight = 0
        if (self.pt == 2):
            if not self._rrf2:
                #RRF 3 on a Duet Ethernet/Wifi board, apply buffer checking
                sessionURL = (f'{self._base_url}'+'/rr_connect?password=reprap')
                r = self.session.get(sessionURL, timeout=(self._requestTimeout,self._responseTimeout) )
                rawdata = r.json()
                rawdata = json.dumps(rawdata)
                _logger.debug( 'Response from connect: ' + rawdata )
                buffer_size = 0
                # while buffer_size < 150:
                #     bufferURL = (f'{self._base_url}'+'/rr_gcode')
                #     buffer_request = self.session.get(bufferURL, timeout=(self._requestTimeout,self._responseTimeout) )
                #     try:
                #         buffer_response = buffer_request.json()
                #         buffer_size = int(buffer_response['buff'])
                #     except:
                #         buffer_size = 149
                #     if buffer_size < 150:
                #         _logger.debug('Buffer low - adding 0.6s delay before next call: ' + str(buffer_size))
                #         time.sleep(0.6)
            URL=(f'{self._base_url}'+'/rr_gcode?gcode=G31')
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout) )
            replyURL = (f'{self._base_url}'+'/rr_reply')
            reply = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout) )
            # Reply is of the format:
            # "Z probe 0: current reading 0, threshold 500, trigger height 0.000, offsets X0.0 Y0.0 U0.0"
            start = reply.find('trigger height')
            triggerHeight = reply[start+15:]
            triggerHeight = float(triggerHeight[:triggerHeight.find(',')])
            if not self._rrf2:
                #RRF 3 on a Duet Ethernet/Wifi board, apply buffer checking
                endsessionURL = (f'{self._base_url}'+'/rr_disconnect')
                r2 = self.session.get(endsessionURL, timeout=(self._requestTimeout,self._responseTimeout) )
        if (self.pt == 3):
            URL=(f'{self._base_url}'+'/machine/code/')
            r = self.requests.post(URL, data='G31')
            # Reply is of the format:
            # "Z probe 0: current reading 0, threshold 500, trigger height 0.000, offsets X0.0 Y0.0"
            reply = r.text
            start = reply.find('trigger height')
            triggerHeight = reply[start+15:]
            triggerHeight = float(triggerHeight[:triggerHeight.find(',')])
        if (r.ok):
           return (_errCode, _errMsg, triggerHeight )
        else:
            _errCode = float(r.status_code)
            _errMsg = r.reason
            _logger.error("Bad resposne in getTriggerHeight: " + str(r.status_code) + ' - ' + str(r.reason))
            return (_errCode, _errMsg, None )
    
    #################################################################################################################################
#################################################################################################################################
# Exception Classes
# Do not change this
class Error(Exception):
    """Base class for other exceptions"""
    pass
class UnknownController(Error):
    pass
class FailedToolDetection(Error):
    pass
class FailedOffsetCapture(Error):
    pass
class StatusException(Error):
    pass
class CoordinatesException(Error):
    pass
class SetOffsetException(Error):
    pass
class ToolTimeoutException(Error):
    pass
class HomingException(Error):
    pass

#################################################################################################################################
#################################################################################################################################
# helper class for tool definition
# Do not change this
class Tool:
    # class attributes
    _number = 0
    _name = "Tool"
    _nozzleSize = 0.4
    _offsets = {"X":0, "Y": 0, "Z": 0}
    
    def __init__( self, number=0, name="Tool", nozzleSize=0.4, offsets={"X":0, "Y": 0, "Z": 0} ):
        self._number = number
        self._name = name
        self._nozzleSize = nozzleSize
        self._offsets = offsets

    def getJSON( self ):
        return( {
            "number": self._number,
            "name": self._name, 
            "nozzleSize": self._nozzleSize,
            "offsets": [ self._offsets["X"], self._offsets["Y"], self._offsets["Z"] ]
        } )
