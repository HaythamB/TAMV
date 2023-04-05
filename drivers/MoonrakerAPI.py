# Python Script containing a class to send commands to, and query specific information from,
#   Klipper based printers running Moonraker REST API
#
# Does NOT hold open the connection.  Use for low-volume requests.
# Does NOT, at this time, support authentication.
#
# Not intended to be a gerneral purpose interface; instead, it contains methods
# to issue commands or return specific information. Feel free to extend with new
# methods for other information; please keep the abstraction for V2 V3
#
# Copyright (C) 2022 Haytham Bennani
# Released under The MIT License. Full text available via https://opensource.org/licenses/MIT
#
# Requires Python3
from csv import excel_tab
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# shared import dependencies
import json
import time
import re
# invoke parent (TAMV) _logger
_logger = logging.getLogger('TAMV.MoonrakerAPI')

#################################################################################################################################
#################################################################################################################################
# Main class for interface


class printerAPI:
    # Max time to wait for toolchange before raising a timeout exception, in seconds
    _toolTimeout = 300
    # Max time to wait for moves (G0, G1) befroe raising a timeout exception, in seconds
    _moveTimeout = 5
    # Max time to wait for HTTP requests to complete
    _requestTimeout = 2
    _responseTimeout = 10

    #################################################################################################################################
    # G-Code Commands
    #
    G_CODE_SET_TOOL_OFFSET = "SET_TOOL_OFFSET TOOL=%s X=%f Y=%f"
    G_CODE_TOOL_UNLOAD = "T_1"
    G_CODE_TOOL_LOAD = "T%d"

    #################################################################################################################################
    # Data querying/parsing
    #
    OBJECT_TOOL_REGEX = "tool .+"  # extruder.+
    OBJECT_TOOL_NAME = "tool %d"  # extruder%d
    OBJECT_TOOLHEAD = "toollock"  # toolhead
    OBJECT_TOOLHEAD_TOOL_PROPERTY = "tool_current"  # extruder

    #################################################################################################################################
    # Instantiate class and connect to controller
    #
    # Parameters:
    #   - baseURL (string): full IP address (not FQDN or alias) in the format 'http://xxx.xxx.xxx.xxx' without trailing '/'
    #   - optional: nickname (string): short nickname for identifying machine (strictly for TAMV GUI)
    #
    # Returns: NONE
    #
    # Raises:
    #   - UnknownController: if fails to connect
    def __init__(self, baseURL, nickname='Default', password='none'):
        _logger.debug('Starting API..')

        self.session = requests.Session()
        self.retry = Retry(connect=3, backoff_factor=0.4)
        self.adapter = HTTPAdapter(max_retries=self.retry)
        self.session.mount('http://', self.adapter)

        # Here are the required class attributes. These get saved to settings.json
        self._base_url = baseURL
        self._name = 'My Klipper'
        self._nickname = nickname
        self._firmwareName = "klipper"
        self._firmwareVersion = ""
        # tools is an array of the Tool class located at the end of this file - read that first.
        self.tools = []

        try:
            state = self.getKlippyState()
            if (state != "ready"):
                # The board has failed to connect, return an error state
                raise UnknownController('Unknown controller detected.')

            # Setup tool definitions
            toolCount = self.getNumTools()
            for i in range(toolCount):
                toolOffset = self.getToolOffset(i)

                offsetX = round(float(toolOffset['X']), 3)
                offsetY = round(float(toolOffset['Y']), 3)
                offsetZ = round(float(toolOffset['Z']), 3)

                _logger.info("Adding tool %d with offsets %f, %f, %f" %
                             (i, offsetX, offsetY, offsetZ))

                tempTool = Tool(
                    number=i,
                    name=self.OBJECT_TOOL_NAME % (i),
                    offsets={'X': offsetX, 'Y': offsetY, 'Z': offsetZ})
                self.tools.append(tempTool)

        except UnknownController as uc:
            _logger.critical("Unknown controller at " + self._base_url)
            raise SystemExit(uc)
        except Exception as e:
            # Catastrophic error. Bail.
            _logger.critical(str(e))
            raise SystemExit(e)
        _logger.info('  .. connected to ' + self._firmwareName +
                     '- V' + self._firmwareVersion + '..')
        return

    def getKlippyState(self):
        j = self.query('/server/info')
        if 'error' in j:
            raise StatusException(j['error']['message'])
        elif 'result' in j:
            state = j['result']['klippy_state']
            return state

    def query(self, url):
        URL = (f'{self._base_url}' + url)
        r = self.session.get(URL, timeout=(
            self._requestTimeout, self._responseTimeout))
        j = json.loads(r.text)
        return j

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
        ##############*** YOUR CUSTOM CODE #################
        ##############*** YOUR CUSTOM CODE #################
        return (0)

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
        count = 0
        j = self.query('/printer/objects/list')
        if 'error' in j:
            raise FailedToolDetection(j['error']['message'])
        elif 'result' in j:
            for t in j['result']['objects']:
                if re.match(self.OBJECT_TOOL_REGEX, str.lower(t)):
                    count += 1
        return (count)

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
            j = self.query('/printer/objects/query?' + self.OBJECT_TOOLHEAD +
                           '=' + self.OBJECT_TOOLHEAD_TOOL_PROPERTY)
            if 'error' in j:
                raise FailedToolDetection(j['error']['message'])
            elif 'result' in j:
                return j['result']['status'][self.OBJECT_TOOLHEAD][self.OBJECT_TOOLHEAD_TOOL_PROPERTY]

            # Unknown condition, raise error
            raise FailedToolDetection('Something failed. Baililng.')
        except ConnectionError as ce:
            _logger.critical('Connection error while polling for current tool')
            raise SystemExit(ce)
        except FailedToolDetection as fd:
            _logger.critical('Failed tool detection.')
            raise SystemExit(e1)
        except Exception as e1:
            _logger.critical(
                'Unhandled exception in getCurrentTool: ' + str(e1))
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
    def getToolOffset(self, toolIndex=0):
        _logger.debug('Called getToolOffset')
        try:
            toolName = self.OBJECT_TOOL_NAME % (toolIndex)

            j = self.query("/printer/objects/query?" + toolName + "=offset")
            if 'error' in j:
                raise FailedOffsetCapture(j['error']['message'])
            elif 'result' in j:
                offsets = j['result']['status'][toolName]['offset']

            return ({
                'X': float(offsets[0]),
                'Y': float(offsets[1]),
                'Z': float(offsets[2])
            })
        except FailedOffsetCapture as fd:
            _logger.critical(str(fd))
            raise SystemExit(fd)
        except ConnectionError as ce:
            _logger.critical('Connection error in getToolOffset.')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical(
                'Unhandled exception in getToolOffset: ' + str(e1))
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
    def getStatus(self):
        _logger.debug('Called getStatus')
        try:
            j = self.query('/printer/info')
            if 'error' in j:
                raise StatusException(j['error']['message'])
            elif 'result' in j:
                _status = j['result']['state']

            if (_status == "idle" or _status == "ready"):
                _logger.debug("Machine is idle.")
                return ("idle")
            elif (_status == "paused"):
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
    #   - tuple of floats: { 'X': 0.000 , 'Y': 0.000 , 'Z': 0.000 }
    #
    # Raises:
    #   - CoordinatesException: when cannot determine machine status
    def getCoordinates(self):
        _logger.debug('Called getCoordinates')
        try:
            j = self.query('/printer/objects/query?gcode_move=gcode_position')
            if 'error' in j:
                raise CoordinatesException(j['error']['message'])
            elif 'result' in j:
                coords = j['result']['status']['gcode_move']['gcode_position']

            return ({
                'X': round(coords[0], 3),
                'Y': round(coords[1], 3),
                'Z': round(coords[2], 3)
            })
        except CoordinatesException as ce1:
            _logger.critical(str(ce1))
            raise SystemExit(ce1)
        except ConnectionError as ce:
            _logger.critical('Connection error in getCoordinates')
            raise SystemExit(ce)
        except Exception as e1:
            _logger.critical(
                'Unhandled exception in getCoordinates: ' + str(e1))
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
    def setToolOffsets(self, tool=None, X=None, Y=None, Z=None):
        _logger.debug('Called setToolOffsets')
        try:
            if len(self.G_CODE_SET_TOOL_OFFSET.strip()) == 0:
                _logger.info(
                    "No G_CODE_SET_TOOL_OFFSET configured, tool offset not set.")
                return
            # Check for invalid tool index, raise exception if needed.
            if (tool is None):
                raise SetOffsetException("No tool index provided.")
            # Check that any valid offset has been passed as an argument
            elif (X is None and Y is None):
                raise SetOffsetException("Invalid offsets provided.")
            else:
                self.gCode(self.G_CODE_SET_TOOL_OFFSET %
                           (str(tool), round(float(X), 3), round(float(Y), 3)))
                _logger.debug("Tool offsets applied.")
        except SetOffsetException as se:
            _logger.error(se)
            return
        except Exception as e:
            _logger.critical("setToolOffsets unhandled exception: " + str(e))
            raise SystemExit("setToolOffsets unhandled exception: " + str(e))

    #################################################################################################################################
    # Helper function to check if machine is idle or not
    # Parameters: NONE
    #
    # Returns: boolean
    def isIdle(self):
        _logger.debug("Called isIdle")
        state = self.getStatus()

        if (state == "idle"):
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
        try:
            homed = False

            j = self.query('/printer/objects/query?toolhead=homed_axes')
            if 'result' in j:
                homed_axes = j['result']['status']['toolhead']['homed_axes']
                homed = homed_axes == 'xyz'

            if (homed):
                return True
            else:
                return False
        except Exception as e:
            _logger.critical("Failed to check if machine is homed. " + str(e))
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
    def loadTool(self, toolIndex=0):
        _logger.debug('Called loadTool')
        # variable to hold current tool loading "virtual" timer
        toolchangeTimer = 0

        try:
            self.gCode(self.G_CODE_TOOL_LOAD % (toolIndex))

            # Wait until machine is done loading tool and is idle
            while not self.isIdle() and toolchangeTimer <= self._toolTimeout:
                toolchangeTimer += 2
                time.sleep(2)
            if (toolchangeTimer > self._toolTimeout):
                # Request for toolchange timeout, raise exception
                raise ToolTimeoutException(
                    "Request to change to tool T" + str(toolIndex) + " timed out.")
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
    def unloadTools(self):
        _logger.debug('Called unloadTools')
        # variable to hold current tool loading "virtual" timer
        toolchangeTimer = 0
        try:
            self.gCode(self.G_CODE_TOOL_UNLOAD)

            # Wait until machine is done loading tool and is idle
            while not self.isIdle() and toolchangeTimer <= self._toolTimeout:
                toolchangeTimer += 2
                time.sleep(2)
            if (toolchangeTimer > self._toolTimeout):
                # Request for toolchange timeout, raise exception
                raise ToolTimeoutException(
                    "Request to unload tools timed out!")
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
    def moveRelative(self, rapidMove=False, moveSpeed=1000, X=None, Y=None, Z=None):
        _logger.debug('Called moveRelative')
        try:
            # check if machine has been homed fully
            if (self.isHomed() is False):
                raise HomingException(
                    "Machine axes have not been homed properly.")

            commands = []
            commands.append('G91')
            # Create gcode command, starting with rapid flag (G0 / G1)
            if (rapidMove is True):
                moveCommand = "G0"
            else:
                moveCommand = "G1"
            # Add each axis position according to passed arguments
            if (X is not None):
                moveCommand += " X" + str(round(float(X), 3))
            if (Y is not None):
                moveCommand += " Y" + str(round(float(Y), 3))
            if (Z is not None):
                moveCommand += " Z" + str(round(float(Z), 3))

            # Add move speed to command
            moveCommand += " F" + str(moveSpeed)
            commands.append(moveCommand)
            # Add a return to absolute positioning to finish the command string creation
            commands.append("G90")

            moveTimer = 0

            # Send command to machine
            self.gCodeBatch(commands)

            while not self.isIdle() and moveTimer <= self._moveTimeout:
                moveTimer += 0.25
                time.sleep(0.25)
            if (moveTimer > self._moveTimeout):
                # Request for move timeout, raise exception
                raise MoveTimeoutException("Request to move timed out!")

        except HomingException as he:
            _logger.error(he)
        except Exception as e:
            errorString = "Move failed to relative coordinates: ("
            if (X is not None):
                errorString += " X" + str(X)
            if (Y is not None):
                errorString += " Y" + str(Y)
            if (Z is not None):
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
    def moveAbsolute(self, rapidMove=False, moveSpeed=1000, X=None, Y=None, Z=None):
        _logger.debug('Called moveAbsolute')
        try:
            # check if machine has been homed fully
            if (self.isHomed() is False):
                raise HomingException(
                    "Machine axes have not been homed properly.")

            commands = []
            commands.append('G90')
            # Create gcode command, starting with rapid flag (G0 / G1)
            if (rapidMove is True):
                moveCommand = "G0"
            else:
                moveCommand = "G1"
            # Add each axis position according to passed arguments
            if (X is not None):
                moveCommand += " X" + str(round(float(X), 3))
            if (Y is not None):
                moveCommand += " Y" + str(round(float(Y), 3))
            if (Z is not None):
                moveCommand += " Z" + str(round(float(Z), 3))

            # Add move speed to command
            moveCommand += " F" + str(moveSpeed)
            commands.append(moveCommand)
            # Add a return to absolute positioning to finish the command string creation
            commands.append("G90")
            _logger.debug(moveCommand)

            moveTimer = 0

            # Send command to machine
            self.gCodeBatch(commands)

            while not self.isIdle() and moveTimer <= self._moveTimeout:
                moveTimer += 0.25
                time.sleep(0.25)
            if (moveTimer > self._moveTimeout):
                # Request for move timeout, raise exception
                raise MoveTimeoutException("Request to move timed out!")

        except HomingException as he:
            _logger.error(he)
        except Exception as e:
            errorString = " move failed to absolute coordinates: ("
            if (X is not None):
                errorString += " X" + str(X)
            if (Y is not None):
                errorString += " Y" + str(Y)
            if (Z is not None):
                errorString += " Z" + str(Z)
            errorString += ") at speed: " + str(moveSpeed)
            _logger.critical(errorString + str(e))
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
    def limitAxes(self):
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
    def flushMovementBuffer(self):
        _logger.debug('Called flushMovementBuffer')
        try:
            self.gCode("M400")
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
    def saveOffsetsToFirmware(self):
        _logger.debug('Called saveOffsetsToFirmware')
        try:
            _logger.debug(
                "Saving tool offsets to Klipper firmware is not yet supported.")
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

    def gCode(self, command):
        _logger.debug('gCode called')

        j = self.query('/printer/gcode/script?script=' + command)
        ok = False
        if 'error' in j:
            raise SystemExit(j['error']['message'])
        elif 'result' in j:
            ok = j['result'] == "ok"

        if (ok):
            return 0
        else:
            _logger.error("Error running gCode command")
            raise SystemExit("Error running gCode command")

    def gCodeBatch(self, commands):
        _logger.debug('gCodeBatch called')

        for command in commands:
            self.gCode(command)

        return 0

    ### DO NOT EDIT BEYOND THIS LINE ###
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
            'name': self._name,
            'nickname': self._nickname,
            'controller': self._firmwareName,
            'version': self._firmwareVersion,
            'tools': []
        }
        for i, currentTool in enumerate(self.tools):
            printerJSON['tools'].append(currentTool.getJSON())
        return (printerJSON)

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


class MoveTimeoutException(Error):
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
    _offsets = {"X": 0, "Y": 0, "Z": 0}

    def __init__(self, number=0, name="Tool", nozzleSize=0.4, offsets={"X": 0, "Y": 0, "Z": 0}):
        self._number = number
        self._name = name
        self._nozzleSize = nozzleSize
        self._offsets = offsets

    def getJSON(self):
        return ({
            "number": self._number,
            "name": self._name,
            "nozzleSize": self._nozzleSize,
            "offsets": [self._offsets["X"], self._offsets["Y"], self._offsets["Z"]]
        })
