# Python Script containing a class to send commands to, and query specific information from,
#   Duet based printers running either Duet RepRap V2 or V3 firmware.
#
# Does NOT hold open the connection.  Use for low-volume requests.
# Does NOT, at this time, support Duet passwords.
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
# from csv import excel_tab
# from string import lower
from http.client import *


import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import ConnectTimeoutError
from urllib3.util.retry import Retry
from urllib3.exceptions import *
from urllib.parse import urlparse
import socket
# import dependencies
import json
import time

# invoke parent (TAMV) _logger
_logger = logging.getLogger('TAMV.DuetWebAPI')
# # enable HTTP requests logging
# import http.client
# http.client.HTTPConnection.debuglevel = 1

#################################################################################################################################
#################################################################################################################################
# Exception Classes
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
class DuetSBCHandler(Error):
    pass

#################################################################################################################################
#################################################################################################################################
# helper class for tool definition
class Tool:
    # class attributes
    _number = 0
    _name = "Tool"
    _nozzleSize = 0.4
    _offsets = {"X":0, "Y": 0, "Z": 0}
    
    def __init__(self, number=0, name="Tool", nozzleSize=0.4, offsets={"X":0, "Y": 0, "Z": 0}):
        self._number = number
        self._name = name
        self._nozzleSize = nozzleSize
        self._offsets = offsets

    def getJSON(self):
        return({
            "number": self._number,
            "name": self._name, 
            "nozzleSize": self._nozzleSize,
            "offsets": [ self._offsets["X"], self._offsets["Y"], self._offsets["Z"] ]
        })

#################################################################################################################################
#################################################################################################################################
# Main class for interface
class printerAPI:
    # Any unhandled/general exceptions raised will cause a system exit to prevent machine damage.

    #################################################################################################################################
    #################################################################################################################################
    # Class attributes
    # Duet hardware version (Duet 2 or Duet 3 controller)
    pt = 0
    # base URL to connect to machine
    _base_url = ''
    # Machine-specific attributes
    _nickname = 'Default'
    _firmwareName = 'RRF'
    _firmwareVersion = ''
    _password = 'reprap'
    # special internal flag to handle Duet 2 boards running RRF v3 firmware - only needed for Duet controllers
    # you may delete this variable if extending API to other boards
    _rrf2 = False
    # Max time to wait for toolchange before raising a timeout exception, in seconds
    _toolTimeout = 300
    # Max time to wait for HTTP requests to complete
    _requestTimeout = 2
    _responseTimeout = 5
    # flag to indicate if machine has been homed or not
    _homed = None
    # Tools
    _tools = []

    #################################################################################################################################
    # Instantiate class and connect to controller
    # Parameters:
    #   - baseURL (string): full IP address (not FQDN or alias) in the format 'http://xxx.xxx.xxx.xxx' without trailing '/'
    #   - nickname (string): short nickname for identifying machine (strictly for TAMV GUI)
    #
    # Returns: NONE
    # 
    # Raises: 
    #   - UnknownController: if fails to connect
    def __init__(self, baseURL, nickname='Default', password='reprap'):
        _logger.debug('Starting DuetWebAPI..')
        # parse input parameters

        # convert hostname into IP
        # fetch IP address
        u = urlparse(baseURL)
        hostIP = socket.gethostbyname(u.hostname)
        baseURL = u.scheme + '://' + hostIP
        if(u.port is not None):
            baseURL += ':' + str(u.port)

        # set base parameters
        self._base_url = baseURL
        self._password = password
        self._nickname = nickname
        self._tools = []
        # Name as defined in RRF config.g file
        self._name = 'My Duet'
        # set up session parameters
        self.session = requests.Session()
        self.retry = Retry(connect=3, backoff_factor=0.4)
        self.adapter = HTTPAdapter(max_retries=self.retry)
        self.session.mount('http://', self.adapter)
        try:
            # check if its a Duet 2 board
            # Set up session using password
            if(self._password != "reprap"):
                _logger.debug('Starting DuetWebAPI session..')
                URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
            
            URL=(f'{self._base_url}'+'/rr_status?type=2')
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
            if(r.ok):
                j = json.loads(r.text)
            else: 
                raise DuetSBCHandler

            # Send reply to clear buffer
            replyURL = (f'{self._base_url}'+'/rr_reply')
            r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))
            
            # Get machine name
            self._name = j['name']
            # Setup tool definitions
            toolData = j['tools']
            for inputTool in toolData:
                tempTool = Tool(
                    number = inputTool['number'],
                    name = inputTool['name'],
                    offsets={'X': inputTool['offsets'][0], 'Y': inputTool['offsets'][1], 'Z':inputTool['offsets'][2]})
                self._tools.append(tempTool)
                _logger.debug('Added tool: ' + str(tempTool.getJSON()))
            
            # Check for firmware version
            firmwareName = j['firmwareName']
            # fetch hardware board type from firmware name, character 24
            boardVersion = firmwareName[24]
            self._firmwareVersion = j['firmwareVersion']
            # set RRF version based on results
            if self._firmwareVersion[0] == "2":
                # Duet running RRF v2
                self._rrf2 = True
                self.pt = 2
            else: 
                # Duet 2 hardware running RRF v3
                self._rrf2 = False
                self.pt = 2
            _logger.info('  .. connected to '+ firmwareName + '- V'+ self._firmwareVersion + '..')
            return
        except DuetSBCHandler as sbc:
            # We're probably dealing with a Duet 3 controller, get required firmware info
            try:
                _logger.debug('Trying to connect to Duet 3 board..')
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }
                
                URL=(f'{self._base_url}'+'/machine/status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                _logger.debug('Got reply, parsing again..')
                j = json.loads(r.text)
                _=j
                firmwareName = j['boards'][0]['firmwareName']
                firmwareVersion = j['boards'][0]['firmwareVersion']
                self.pt = 3

                # Setup tool definitions
                toolData = j['tools']
                toolCounter = 0
                for inputTool in toolData:
                    # attempt to read tool number from config
                    # redirect exception to a default toolnumber based on the current index in the array
                    try:
                        toolNumber = inputTool['number']
                    except Exception as noNumber:
                        toolNumber = str(toolCounter)
                    
                    # attempt to read tool name from config
                    # redirect exception to a default toolname in the format Tx (where x is the tool number)
                    try:
                        toolName = inputTool['name']
                    except Exception as noname:
                        toolName = "T" + toolNumber
                    
                    # increment current tool number
                    toolCounter = toolCounter + 1

                    tempTool = Tool(
                        number = toolNumber,
                        name = toolName,
                        offsets={'X': inputTool['offsets'][0], 'Y': inputTool['offsets'][1], 'Z':inputTool['offsets'][2]})
                    self._tools.append(tempTool)
                
                _logger.debug('Duet 3 board detected')
                _logger.info('  .. connected to: '+ firmwareName + '- V'+firmwareVersion + '..')
                return
            except:
                # The board is neither a Duet 2 controller using RRF v2/3 nor a Duet 3 controller board, return an error state
                raise UnknownController('Unknown controller detected.')
        except UnknownController as uc:
            errorMsg = 'Unknown controller at " + self._base_url + " - does not appear to be an RRF2 or RRF3 printer'
            _logger.error(errorMsg)
            raise SystemExit(errorMsg)
        except requests.exceptions.ConnectTimeout:
            errorMsg = 'Connect operation: Connection timed out.'
            _logger.critical(errorMsg)
            raise Exception(errorMsg)
        # except HTTPException as ht:
        #     _logger.error('DuetWebAPIT init: Connection error.')
        except Exception as e:
            # Catastrophic error. Bail.
            _logger.critical('DuetWebAPI2 Init: ' + str(e))
            raise Exception('DuetWebAPI Init: ' + str(e))

    #################################################################################################################################
    # Get firmware version
    # Parameters: 
    # - NONE
    #
    # Returns: integer
    #   - returns either 2 or 3 depending on which RRF version is running on the controller
    #
    # Raises: NONE
    def getPrinterType(self):
        _logger.debug('Called getPrinterType')
        return(self.pt)
    
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
    def getNumTools(self):
        _logger.debug('Called getNumTools')
        
        # try:
        #     if (self.pt == 2):
        #         # Duet RRF v2
        #         URL=(f'{self._base_url}'+'/rr_status?type=2')
        #         r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
        #         j = json.loads(r.text)
        #         jc=j['tools']
        #         _logger.debug('Number of tools: ' + str(len(jc)))

        #         # Send reply to clear buffer
        #         replyURL = (f'{self._base_url}'+'/rr_reply')
        #         r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))

        #         return(len(jc))
        #     elif (self.pt == 3):
        #         # Duet RRF v3
        #         URL=(f'{self._base_url}'+'/machine/status')
        #         r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
        #         j = json.loads(r.text)
        #         if 'result' in j: j = j['result']
        #         _logger.debug('Number of tools: ' + str(len(j['tools'])))
        #         return(len(j['tools']))
        #     # failed to get tool data, raise exception
        #     raise FailedToolDetection('Cannot determine number of tools on machine')
        # except FailedToolDetection as ft:
        #     _logger.critical('Failed to detect number of tools on machine')
        #     raise Exception(ft)
        # except Exception as e:
        #     _logger.critical("Connection error: " + str(e))
        #     raise Exception(e)
        return(len(self._tools))

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
    def getCurrentTool(self):
        _logger.debug('Called getCurrentTool')
        try:
            if (self.pt == 2):
                # Start a connection
                if(self._password != "reprap"):
                    _logger.debug('Starting DuetWebAPI session..')
                    URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                    r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))

                # Wait for machine to be in idle state
                while self.getStatus() not in "idle":
                    _logger.debug('Machine not idle, sleeping 0.5 seconds.')
                    time.sleep(0.5)
                # Fetch machine data
                URL=(f'{self._base_url}'+'/rr_status?type=2')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                ret=j['currentTool']

                # Send reply to clear buffer
                replyURL = (f'{self._base_url}'+'/rr_reply')
                r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))

                _logger.debug('Found current tool: ' + str(ret))
                return(ret)
            elif (self.pt == 3):
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }

                URL=(f'{self._base_url}'+'/machine/status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                if 'result' in j: j = j['result']
                ret=j['state']['currentTool']
                _logger.debug('Found current tool: ' + str(ret))
                return(ret)
            else:
                # Unknown condition, raise error
                raise FailedToolDetection('Something failed. Baililng.')
        except ConnectTimeoutError:
            errorMsg = 'getCurrentTool: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except ConnectionError as ce:
            _logger.critical('Connection error while polling for current tool')
            raise Exception(ce)
        except FailedToolDetection as fd:
            _logger.critical('Failed tool detection.')
            raise Exception(e1)
        except Exception as e1:
            _logger.critical('Unhandled exception in getCurrentTool: ' + str(e1))
            raise Exception(e1)

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
    def getToolOffset(self, toolIndex=0):
        _logger.debug('Called getToolOffset: ' + str(toolIndex))
        try:
            if (self.pt == 3):
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }

                URL=(f'{self._base_url}'+'/machine/status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                if 'result' in j: j = j['result']
                ja=j['move']['axes']
                jt=j['tools']
                ret=json.loads('{}')
                to = jt[toolIndex]['offsets']
                for i in range(0,len(to)):
                    ret[ ja[i]['letter'] ] = to[i]
                _logger.debug('Tool offset for T' + str(toolIndex) +': ' + str(ret))
                return(ret)
            elif (self.pt == 2):
                # Start a connection
                if(self._password != "reprap"):
                    _logger.debug('Starting DuetWebAPI session..')
                    URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                    r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))

                URL=(f'{self._base_url}'+'/rr_status?type=2')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                ja=j['axisNames']
                jt=j['tools']
                ret=json.loads('{}')
                for currentTool in jt:
                    if(currentTool['number'] == int(toolIndex)):
                        ret['X'] = currentTool['offsets'][0]
                        ret['Y'] = currentTool['offsets'][1]
                        ret['Z'] = currentTool['offsets'][2]
                        ret['U'] = currentTool['offsets'][3]
                    else:
                        continue
                # to = jt[toolIndex]['offsets']
                # for i in range(0,len(to)):
                    # ret[ ja[i] ] = to[i]
                _logger.debug('Tool offset for T' + str(toolIndex) +': ' + str(ret))
                
                # Send reply to clear buffer
                replyURL = (f'{self._base_url}'+'/rr_reply')
                r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))

                return(ret)
            else:
                raise FailedOffsetCapture('getG10ToolOffset entered unhandled exception state.')
        except ConnectTimeoutError:
            errorMsg = 'getToolOffset: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except FailedOffsetCapture as fd:
            _logger.critical('DuetWebAPI getToolOffset: ' + str(fd))
            raise Exception(fd)
        except ConnectionError as ce:
            _logger.critical('Connection error in getToolOffset.')
            raise Exception(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in getToolOffset: ' + str(e1))
            raise Exception(e1)

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
    def getStatus(self):
        _logger.debug('Called getStatus')
        try:
            if (self.pt == 2):
                # Start a connection
                if(self._password != "reprap"):
                    _logger.debug('Starting DuetWebAPI session..')
                    URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                    r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))

                URL=(f'{self._base_url}'+'/rr_status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                _status=j['status']
            elif (self.pt == 3):
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }

                URL=(f'{self._base_url}'+'/machine/status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                if 'result' in j: 
                    j = j['result']
                _status = str(j['state']['status'])
                _status = _status.lower()
            else:
                # unknown error raise exception
                raise StatusException('Unknown error getting machine status')
            
            # Send reply to clear buffer
            # replyURL = (f'{self._base_url}'+'/rr_reply')
            # r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))

            # OUTPUT MAPPING LOGIC
            # Handle return mapping of status variable "_status"
            if (_status == "idle" or _status == "I"):
                _logger.debug("Machine is idle.")
                return ("idle")
            elif (_status == "paused" or _status == "S" or _status == "pausing" or _status == "D"):
                _logger.debug("Machine is paused.")
                return ("paused")
            else:
                _logger.debug("Machine is busy processing something.")
                return ("processing")
        except ConnectTimeoutError:
            errorMsg = 'getStatus: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except StatusException as se:
            _logger.critical('DuetWebAPI getStatus: ' + str(se))
            raise Exception(se)
        except ConnectionError as ce:
            _logger.critical('Connection error in getStatus')
            raise Exception(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in getStatus: ' + str(e1))
            raise Exception(e1)

    #################################################################################################################################
    # Get current tool coordinates from machine in XYZ space
    # Parameters:
    #   - NONE
    #
    # Returns: 
    #   - tuple of floats: { 'X': 0.000 , 'Y': 0.000 , 'Z': 0.000 }
    #
    # Raises: 
    #   - CoordinatesException: when cannot determine machine status
    def getCoordinates(self):
        _logger.debug('*** Called getCoordinates')
        try:
            if (self.pt == 2):
                # Start a connection
                if(self._password != "reprap"):
                    _logger.debug('Starting DuetWebAPI session..')
                    URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                    r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))

                # poll machine for coordinates
                while self.getStatus() not in "idle":
                    _logger.debug('moveAbsolute: sleeping 0.3 seconds..')
                    time.sleep(0.3)
                
                URL=(f'{self._base_url}'+'/rr_status?type=2')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                if not r.ok:
                    raise ConnectionError('Error in getCoordinates session 2: ' + str(r))
                j = json.loads(r.text)
                jc=j['coords']['xyz']
                an=j['axisNames']
                ret=json.loads('{}')
                for i in range(0,len(jc)):
                    ret[ an[i] ] = jc[i]
                
                # Send reply to clear buffer
                #replyURL = (f'{self._base_url}'+'/rr_reply')
                #r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))
                _logger.debug('*** exiting getCoordinates')
                return(ret)
            elif (self.pt == 3):
                while self.getStatus() not in "idle":
                    _logger.debug('XX - printer not idle _SLEEPING_')
                    time.sleep(0.5)
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }

                URL=(f'{self._base_url}'+'/machine/status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                if not r.ok:
                    raise ConnectionError('Error in getCoordinates session 3: ' + str(r))
                j = json.loads(r.text)
                if 'result' in j: j = j['result']
                ja=j['move']['axes']
                ret=json.loads('{}')
                for i in range(0,len(ja)):
                    ret[ ja[i]['letter'] ] = ja[i]['userPosition']
                _logger.debug('Returning coordinates: ' + str(ret))
                _logger.debug('*** exiting getCoordinates')
                return(ret)
            else:
                #unknown error, raise exception
                raise CoordinatesException("Unknown duet controller.")
        except ConnectTimeoutError:
            errorMsg = 'getCoordinates: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except CoordinatesException as ce1:
            _logger.critical('DuetWebAPI getCoordinates: ' + str(ce1))
            raise Exception(ce1)
        except ConnectionError as ce:
            _logger.critical('Connection error in getCoordinates')
            raise Exception(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in getCoordinates: ' + str(e1))
            raise Exception(e1)

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
    def setToolOffsets(self, tool=None, X=None, Y=None, Z=None):
        _logger.debug('Called setToolOffsets: ' + str(tool))
        try:
            # Check for invalid tool index, raise exception if needed.
            if(tool is None):
                raise SetOffsetException("No tool index provided.")
            # Check that any valid offset has been passed as an argument
            elif(X is None and Y is None and Z is None):
                raise SetOffsetException("Invalid offsets provided.")
            else:
                offsetCommand = "G10 P" + str(int(tool))
                if(X is not None):
                    offsetCommand += " X" + str(X)
                if(Y is not None):
                    offsetCommand += " Y" + str(Y)
                if(Z is not None):
                    offsetCommand += " Z" + str(Z)
                _logger.debug(offsetCommand)
                self.gCode(offsetCommand)
                _logger.debug("Tool offsets applied.")
        except ConnectTimeoutError:
            errorMsg = 'setToolOffsets: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except SetOffsetException as se:
            _logger.error('DuetWebAPI setToolOffsets: ' + str(se))
            return
        except Exception as e:
            _logger.critical("setToolOffsets unhandled exception: " + str(e))
            raise Exception("setToolOffsets unhandled exception: " + str(e))

    #################################################################################################################################
    # Helper function to check if machine is idle or not
    # Parameters: NONE
    #
    # Returns: boolean
    def isIdle(self):
        _logger.debug("Called isIdle")
        state = self.getStatus()
        if(state == "idle"):
            return True
        else:
            return False

    #################################################################################################################################
    # Helper function to check if machine is homed on all axes for motion
    # Parameters: NONE
    #
    # Returns: boolean
    def isHomed(self):
        _logger.debug("Called isHomed")
        if(self._homed is not None):
            return self._homed
        machineHomed = True
        try:
            if (self.pt == 2):
                # Duet RRF v2

                # Start a connection
                if(self._password != "reprap"):
                    _logger.debug('Starting DuetWebAPI session..')
                    URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                    r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))

                URL=(f'{self._base_url}'+'/rr_status?type=2')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                axesList=j['coords']['axesHomed']
                for axis in axesList:
                    if(axis == 0):
                        machineHomed = False
                    else:
                        pass
                # Send reply to clear buffer
                replyURL = (f'{self._base_url}'+'/rr_reply')
                r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))
            elif (self.pt == 3):
                # Duet RRF v3
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }

                URL=(f'{self._base_url}'+'/machine/status')
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                j = json.loads(r.text)
                axesList=j['move']['axes']
                for axis in axesList[0:3]:
                    if(axis['homed'] is False):
                        machineHomed = False
                    else:
                        pass

            self._homed = machineHomed
            return(self._homed)
        except ConnectTimeoutError:
            errorMsg = 'isHomed: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except Exception as e:
            _logger.critical("Failed to check if machine is homed. " + str(e))
            raise Exception("Failed to check if machine is homed. " + str(e))

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
    def loadTool(self, toolIndex = 0):
        _logger.debug('Called loadTool: ' + str(toolIndex)) 
        # variable to hold current tool loading "virtual" timer
        toolchangeTimer = 0
        try:
            # Send command to controller to load tool specified by parameter
            _requestedTool = int(toolIndex)
            self.gCode("T" + str(_requestedTool))
            # Wait until machine is done loading tool and is idle
            while not self.isIdle() and toolchangeTimer <= self._toolTimeout:
                self._toolTimeout += 2
                time.sleep(2)
            if(toolchangeTimer > self._toolTimeout):
                # Request for toolchange timeout, raise exception
                raise ToolTimeoutException("Request to change to tool T" + str(toolIndex) + " timed out.")
            return
        except ConnectTimeoutError:
            errorMsg = 'loadTool: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except ToolTimeoutException as tte:
            _logger.warning(str(tte))
            return
        except ConnectionError as ce:
            _logger.critical('Connection error in loadTool.')
            raise Exception(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in loadTool: ' + str(e1))
            raise Exception(e1)

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
    def unloadTools(self):
        _logger.debug('Called unloadTools')
        # variable to hold current tool loading "virtual" timer
        toolchangeTimer = 0
        try:
            # Send command to controller to unload all tools
            self.gCode("T-1")
            # Wait until machine is done loading tool and is idle
            while not self.isIdle() and toolchangeTimer <= self._toolTimeout:
                self._toolTimeout += 2
                time.sleep(2)
            if(toolchangeTimer > self._toolTimeout):
                # Request for toolchange timeout, raise exception
                raise ToolTimeoutException("Request to unload tools timed out!")
            return
        except ConnectTimeoutError:
            errorMsg = 'unloadTools: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except ToolTimeoutException as tte:
            _logger.warning(str(tte))
            return
        except ConnectionError as ce:
            _logger.critical('Connection error in unloadTools')
            raise Exception(ce)
        except Exception as e1:
            _logger.critical('Unhandled exception in unloadTools: ' + str(e1))
            raise Exception(e1)

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
    def moveRelative(self, rapidMove=False, moveSpeed=1000, X=None, Y=None, Z=None):
        _logger.debug('Called moveRelative')
        try:
            # check if machine has been homed fully
            if(self.isHomed() is False):
                raise HomingException("Machine axes have not been homed properly.")
            # Create gcode command, starting with rapid flag (G0 / G1)
            if(rapidMove is True):
                moveCommand = "G91 G0 "
            else:
                moveCommand = "G91 G1 "
            # Add each axis position according to passed arguments
            if(X is not None):
                moveCommand += " X" + str(X)
            if(Y is not None):
                moveCommand += " Y" + str(Y)
            if(Z is not None):
                moveCommand += " Z" + str(Z)

            # Add move speed to command
            moveCommand += " F" + str(moveSpeed) 
            # Add a return to absolute positioning to finish the command string creation
            moveCommand += " G90"
            _logger.debug(moveCommand)
            # Send command to machine
            self.gCode(moveCommand)
            while self.getStatus() not in "idle":
                _logger.debug('moveRelative: sleeping 0.3 seconds..')
                time.sleep(0.3)
        except ConnectTimeoutError:
            errorMsg = 'moveRelative: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except HomingException as he:
            _logger.error(he)
        except Exception as e:
            if(rapidMove is True):
                errorString = "G0 rapid "
            else:
                errorString = "G1 linear "
            errorString += " move failed to relative coordinates: ("
            if(X is not None):
                errorString += " X" + str(X)
            if(Y is not None):
                errorString += " Y" + str(Y)
            if(Z is not None):
                errorString += " Z" + str(Z)
            errorString += ") at speed: " + str(moveSpeed)
            _logger.critical('DuetWebAPI moveRelative: ' + errorString)
            raise Exception(errorString + "\n" + str(e))
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
    def moveAbsolute(self, rapidMove=False, moveSpeed=1000, X=None, Y=None, Z=None):
        _logger.debug('Called moveAbsolute')
        try:
            # check if machine has been homed fully
            if(self.isHomed() is False):
                raise HomingException("Machine axes have not been homed properly.")
            # Create gcode command, starting with rapid flag (G0 / G1)
            if(rapidMove is True):
                moveCommand = "G90 G0"
            else:
                moveCommand = "G90 G1"
            # Add each axis position according to passed arguments
            if(X is not None):
                moveCommand += " X" + str(X)
            if(Y is not None):
                moveCommand += " Y" + str(Y)
            if(Z is not None):
                moveCommand += " Z" + str(Z)

            # Add move speed to command
            moveCommand += " F" + str(moveSpeed) 
            # Add a return to absolute positioning to finish the command string creation
            moveCommand += " G90"
            _logger.debug(moveCommand)
            # Send command to machine
            self.gCode(moveCommand)
            while self.getStatus() not in "idle":
                _logger.debug('moveAbsolute: sleeping 0.3 seconds..')
                time.sleep(0.3)
        except ConnectTimeoutError:
            errorMsg = 'moveAbsolute: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except HomingException as he:
            _logger.error(he)
        except Exception as e:
            if(rapidMove is True):
                errorString = "G0 rapid "
            else:
                errorString = "G1 linear "
            errorString += " move failed to absolute coordinates: ("
            if(X is not None):
                errorString += " X" + str(X)
            if(Y is not None):
                errorString += " Y" + str(Y)
            if(Z is not None):
                errorString += " Z" + str(Z)
            errorString += ") at speed: " + str(moveSpeed)
            _logger.critical('DuetWebAPI moveAbsolute: ' + errorString + str(e))
            raise Exception(errorString + "\n" + str(e))
        return

    #################################################################################################################################
    # Limit machine movement to within predefined boundaries as per machine-specific configuration.
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: NONE
    def limitAxes(self):
        _logger.debug('Called limitAxes')
        try:
            self.gCode("M561 S1")
            _logger.debug("Axes limits enforced successfully.")
        except ConnectTimeoutError:
            errorMsg = 'limitAxes: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except Exception as e:
            _logger.error("Failed to limit axes movement")
            raise Exception("Failed to limit axes movement")
        return

    #################################################################################################################################
    # Flush controller movement buffer
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: NONE
    def flushMovementBuffer(self):
        _logger.debug('Called flushMovementBuffer')
        try:
            self.gCode("M400")
            _logger.debug("flushMovementBuffer ran successfully.")
        except ConnectTimeoutError:
            errorMsg = 'flushBuffer: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except Exception as e:
            _logger.error("Failed to flush movement buffer.")
            raise Exception("Failed to flush movement buffer")
        return

    #################################################################################################################################
    # Save tool offsets to "firmware"
    #
    # Parameters: NONE
    #
    # Returns: NONE
    #
    # Raises: NONE
    def saveOffsetsToFirmware(self):
        _logger.debug('Called saveOffsetsToFirmware')
        try:
            self.gCode("M500 P10")
            _logger.debug("Tool offsets saved to firmware.")
        except ConnectTimeoutError:
            errorMsg = 'saveOffsetsToFirmware: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except Exception as e:
            _logger.error("Failed to save offsets: " + str(e))
            raise Exception("Failed to save offsets: " + str(e))
        return

    #################################################################################################################################
    # Output JSON representation of printer
    #
    # Parameters: NONE
    #
    # Returns: JSON object for printer class
    #
    # Raises: NONE
    def getJSON(self):
        printerJSON = { 
            'address': self._base_url,
            'password': self._password,
            'name': self._name,
            'nickname': self._nickname,
            'controller': self._firmwareName,
            'version': self._firmwareVersion,
            'tools': []
            }
        for i, currentTool in enumerate(self._tools):
            printerJSON['tools'].append(currentTool.getJSON())

        return(printerJSON)

    #################################################################################################################################
    #################################################################################################################################
    # Core class functions
    #
    # These functions handle sending gcode commands to your controller:
    #   - gCode: send a single line of gcode
    #   - gCodeBatch: send an array of gcode strings to your controller and execute them sequentially 

    def gCode(self,command):
        _logger.debug('gCode called: ' + command)
        try:
            if (self.pt == 2):
                # Start a connection
                if(self._password != "reprap"):
                    _logger.debug('Starting DuetWebAPI session..')
                    URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
                    r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))

                URL=(f'{self._base_url}'+'/rr_gcode?gcode='+command)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                
                # Send reply to clear buffer
                replyURL = (f'{self._base_url}'+'/rr_reply')
                r2 = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))
            elif (self.pt == 3):
                # Set up session using password
                URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Get session key
                r_obj = json.loads(r.text)
                self._sessionKey = r_obj['sessionKey']
                self.session.headers = {'X-Session-Key': self._sessionKey }

                URL=(f'{self._base_url}'+'/machine/code/')
                r = self.session.post(URL, data=command)
            if (r.ok):
                return 0
            else:
                _logger.error("Error running gCode command: return code " + str(r.status_code) + ' - ' + str(r.reason))
                raise Exception("Error running gCode command: return code " + str(r.status_code) + ' - ' + str(r.reason))
        except ConnectTimeoutError:
            errorMsg = 'gCode: Connection timed out.'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        except SystemExit:
            errorMsg = 'Failure to run gcode'
            _logger.error(errorMsg)
            raise Exception(errorMsg)
        finally:
            return -1
    
    def gCodeBatch(self,commands):
        if(self.pt == 2): 
            # Start a connection
            _logger.debug('Starting DuetWebAPI session..')
            URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
        else:
            # Set up session using password
            URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
            # Get session key
            r_obj = json.loads(r.text)
            self._sessionKey = r_obj['sessionKey']
            self.session.headers = {'X-Session-Key': self._sessionKey }
        
        for command in commands:
            if (self.pt == 2):
                URL=(f'{self._base_url}'+'/rr_gcode?gcode='+command)
                r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
                # Send reply to clear buffer
                replyURL = (f'{self._base_url}'+'/rr_reply')
                r = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))
            if (self.pt == 3):
                URL=(f'{self._base_url}'+'/machine/code/')
                r = self.requests.post(URL, data=command)
            if not (r.ok):
                _logger.Error("Error in gCodeBatch command: " + str(r.status_code) + str(r.reason))

        if(self.pt == 2):
            #RRF 3 on a Duet Ethernet/Wifi board, apply buffer checking
            endsessionURL = (f'{self._base_url}'+'/rr_disconnect')
            r = self.session.get(endsessionURL, timeout=(self._requestTimeout,self._responseTimeout))

    #################################################################################################################################
    #################################################################################################################################
    # ZTATP Core atomimc class functions
    #
    # These are critical functions used by ZTATP to set up probes, check for odd RRF versions that have unique syntax requirements,
    # and are use to set/rest config file changes for the endstops to ensure correct operation of the ZTATP alignment scripts.

    def getFilenamed(self,filename):
        if (self.pt == 2):
            # Start a connection
            _logger.debug('Starting DuetWebAPI session..')
            URL=(f'{self._base_url}'+'/rr_connect?password=' + self._password)
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
        
            URL=(f'{self._base_url}'+'/rr_download?name='+filename)

        if (self.pt == 3):
            # Set up session using password
            URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
            # Get session key
            r_obj = json.loads(r.text)
            self._sessionKey = r_obj['sessionKey']
            self.session.headers = {'X-Session-Key': self._sessionKey }

            URL=(f'{self._base_url}'+'/machine/file/'+filename)
        
        r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
        return(r.text.splitlines()) # replace('\n',str(chr(0x0a))).replace('\t','    '))

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
        for each in [line for line in c if (('M574 ' in line) or ('M558 ' in line)                  )]:
            commandBuffer.append(self._nilEndstop(each))
        self.gCodeBatch(commandBuffer)

    def resetEndstops(self):
        c = self.getFilenamed('/sys/config.g')
        commandBuffer = []
        for each in [line for line in c if (('M574 ' in line) or ('M558 ' in line)                   )]:
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
                _logger.debug('Starting DuetWebAPI session..')
                sessionURL = (f'{self._base_url}'+'/rr_connect?password=' + self._password)
                r = self.session.get(sessionURL, timeout=(self._requestTimeout,self._responseTimeout))
                rawdata = r.json()
                rawdata = json.dumps(rawdata)
                _logger.debug('Response from connect: ' + rawdata)
                buffer_size = 0
                # while buffer_size < 150:
                #     bufferURL = (f'{self._base_url}'+'/rr_gcode')
                #     buffer_request = self.session.get(bufferURL, timeout=(self._requestTimeout,self._responseTimeout))
                #     try:
                #         buffer_response = buffer_request.json()
                #         buffer_size = int(buffer_response['buff'])
                #     except:
                #         buffer_size = 149
                #     if buffer_size < 150:
                #         _logger.debug('Buffer low - adding 0.6s delay before next call: ' + str(buffer_size))
                #         time.sleep(0.6)
            URL=(f'{self._base_url}'+'/rr_gcode?gcode=G31')
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
            replyURL = (f'{self._base_url}'+'/rr_reply')
            reply = self.session.get(replyURL, timeout=(self._requestTimeout,self._responseTimeout))
            # Reply is of the format:
            # "Z probe 0: current reading 0, threshold 500, trigger height 0.000, offsets X0.0 Y0.0 U0.0"
            start = reply.find('trigger height')
            triggerHeight = reply[start+15:]
            triggerHeight = float(triggerHeight[:triggerHeight.find(',')])
            if not self._rrf2:
                #RRF 3 on a Duet Ethernet/Wifi board, apply buffer checking
                endsessionURL = (f'{self._base_url}'+'/rr_disconnect')
                r2 = self.session.get(endsessionURL, timeout=(self._requestTimeout,self._responseTimeout))
        if (self.pt == 3):
            # Set up session using password
            URL=(f'{self._base_url}'+'/machine/connect?password=' + self._password)
            r = self.session.get(URL, timeout=(self._requestTimeout,self._responseTimeout))
            # Get session key
            r_obj = json.loads(r.text)
            self._sessionKey = r_obj['sessionKey']
            self.session.headers = {'X-Session-Key': self._sessionKey }

            URL=(f'{self._base_url}'+'/machine/code/')
            r = self.requests.post(URL, data='G31')
            # Reply is of the format:
            # "Z probe 0: current reading 0, threshold 500, trigger height 0.000, offsets X0.0 Y0.0"
            reply = r.text
            start = reply.find('trigger height')
            triggerHeight = reply[start+15:]
            triggerHeight = float(triggerHeight[:triggerHeight.find(',')])
        if (r.ok):
           return (_errCode, _errMsg, triggerHeight)
        else:
            _errCode = float(r.status_code)
            _errMsg = r.reason
            _logger.error("Bad resposne in getTriggerHeight: " + str(r.status_code) + ' - ' + str(r.reason))
            return (_errCode, _errMsg, None)
    