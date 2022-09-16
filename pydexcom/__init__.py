"""The pydexcom module for interacting with Dexcom Share API."""
import sys
import re
from ustimezones import Pacific

sys.path.append('/pydexcom')
sys.path.append('/')

import datetime

try:
    import urequests
except ModuleNotFoundError:
    import requests as urequests

import pydexcom.const


from pydexcom.const import (
    _LOGGER,
    ACCOUNT_ERROR_ACCOUNT_NOT_FOUND,
    ACCOUNT_ERROR_PASSWORD_INVALID,
    ACCOUNT_ERROR_PASSWORD_NULL_EMPTY,
    ACCOUNT_ERROR_MAX_ATTEMPTS,
    ACCOUNT_ERROR_UNKNOWN,
    ACCOUNT_ERROR_USERNAME_NULL_EMPTY,
    ARGUEMENT_ERROR_MAX_COUNT_INVALID,
    ARGUEMENT_ERROR_MINUTES_INVALID,
    ARGUEMENT_ERROR_SERIAL_NUMBER_NULL_EMPTY,
    DEFAULT_SESSION_ID,
    DEXCOM_APPLICATION_ID,
    DEXCOM_AUTHENTICATE_ENDPOINT,
    DEXCOM_BASE_URL,
    DEXCOM_BASE_URL_OUS,
    DEXCOM_GLUCOSE_READINGS_ENDPOINT,
    DEXCOM_LOGIN_ID_ENDPOINT,
    DEXCOM_TREND_ARROWS,
    DEXCOM_TREND_DESCRIPTIONS,
    DEXCOM_TREND_DIRECTIONS,
    DEXCOM_VERIFY_SERIAL_NUMBER_ENDPOINT,
    MMOL_L_CONVERTION_FACTOR,
    SESSION_ERROR_SESSION_ID_DEFAULT,
    SESSION_ERROR_SESSION_ID_NULL,
    SESSION_ERROR_ACCOUNT_ID_NULL_EMPTY,
    SESSION_ERROR_ACCOUNT_ID_DEFAULT,
    SESSION_ERROR_SESSION_NOT_FOUND,
    SESSION_ERROR_SESSION_NOT_VALID,
)

_LOGGER.setLevel(10)

import pydexcom.errors

from pydexcom.errors import AccountError, ArguementError, SessionError


class GlucoseReading:
    """Class for parsing glucose reading from Dexcom Share API."""

    def __init__(self, json_glucose_reading: dict):
        """Initialize with JSON glucose reading from Dexcom Share API."""
        self.value = json_glucose_reading["Value"]
        self.mg_dl = self.value
        self.mmol_l = round(self.value * MMOL_L_CONVERTION_FACTOR, 1)
        self.trend = json_glucose_reading["Trend"]
        if not isinstance(self.trend, int):
            self.trend = DEXCOM_TREND_DIRECTIONS.get(self.trend, 0)
        self.trend_description = DEXCOM_TREND_DESCRIPTIONS[self.trend]
        self.trend_arrow = DEXCOM_TREND_ARROWS[self.trend]
        tz = datetime.tzinfo()
        self.time = datetime.datetime.fromtimestamp(
            int(re.sub("[^0-9]", "", json_glucose_reading["WT"])) / 1000.0
        , Pacific)


class Dexcom:
    """Class for communicating with Dexcom Share API."""

    def __init__(self, username: str, password: str, ous: bool = False):
        """Initialize with JSON glucose reading from Dexcom Share API."""
        self.base_url = DEXCOM_BASE_URL_OUS if ous else DEXCOM_BASE_URL
        self.username = username
        self.password = password
        self.session_id = None
        self.account_id = None
        self.create_session()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        json: dict = {},
    ) -> dict:
        """Send request to Dexcom Share API."""
        try:
            method = method.upper()
            params = self._process_params(params)
            url = f"{self.base_url}/{endpoint}"
            _LOGGER.debug(f"{method} request to {endpoint}:")
            if params is not None:
                url = f"{url}{params}"
            _LOGGER.debug(f"url: {url}, json: {json}")
            r = urequests.request(
                method,
                url,
                json=json,
            )
            _LOGGER.debug(f"{method} request response {r.status_code}:")
            if r.status_code != 200:
                r.close()
                raise Exception
            _LOGGER.debug(f"json: {r.json()}")
            # r.raise_for_status()
            j = r.json()
            r.close()
            return j
        except:
            try:
                r
                r.json
            except:
                _LOGGER.error('Request failed.')
                return {}
            try:
                if r.status_code == 500:
                    _LOGGER.debug(f'{r.json()["Code"]}: {r.json()["Message"]}')
                    if r.json()["Code"] == "SessionNotValid":
                        raise SessionError(SESSION_ERROR_SESSION_NOT_VALID)
                    elif r.json()["Code"] == "SessionIdNotFound":
                        raise SessionError(SESSION_ERROR_SESSION_NOT_FOUND)
                    elif r.json()["Code"] == "SSO_AuthenticateAccountNotFound":
                        raise AccountError(ACCOUNT_ERROR_ACCOUNT_NOT_FOUND)
                    elif r.json()["Code"] == "AccountPasswordInvalid":
                        raise AccountError(ACCOUNT_ERROR_PASSWORD_INVALID)
                    elif r.json()["Code"] == "SSO_AuthenticateMaxAttemptsExceeed":
                        raise AccountError(ACCOUNT_ERROR_MAX_ATTEMPTS)
                    elif r.json()["Code"] == "InvalidArgument":
                        if "accountName" in r.json()["Message"]:
                            raise AccountError(ACCOUNT_ERROR_USERNAME_NULL_EMPTY)
                        if "password" in r.json()["Message"]:
                            raise AccountError(ACCOUNT_ERROR_PASSWORD_NULL_EMPTY)
                    else:
                        _LOGGER.error(f'{r.json()["Code"]}: {r.json()["Message"]}')
                else:
                    _LOGGER.error(f"{r.status_code}: {r.json()}")
            except KeyError:
                _LOGGER.error(r.status_code)
                _LOGGER.error("Unknown request error")
        return {}

    @staticmethod
    def _process_params(params):
        if params is None:
            return None
        string = '&'.join('='.join(str(e) for e in pair) for pair in params.items())
        return '?' + string
        

    def _validate_session_id(self):
        """Validate session id."""
        if not self.session_id:
            _LOGGER.error(SESSION_ERROR_SESSION_ID_NULL)
            raise SessionError(SESSION_ERROR_SESSION_ID_NULL)
        if self.session_id == DEFAULT_SESSION_ID:
            _LOGGER.error(SESSION_ERROR_SESSION_ID_DEFAULT)
            raise SessionError(SESSION_ERROR_SESSION_ID_DEFAULT)

    def _validate_account(self):
        """Validate credentials."""
        if not self.username:
            _LOGGER.error(ACCOUNT_ERROR_USERNAME_NULL_EMPTY)
            raise AccountError(ACCOUNT_ERROR_USERNAME_NULL_EMPTY)
        if not self.password:
            _LOGGER.error(ACCOUNT_ERROR_PASSWORD_NULL_EMPTY)
            raise AccountError(ACCOUNT_ERROR_PASSWORD_NULL_EMPTY)

    def _validate_account_id(self):
        """Validate account ID."""
        if not self.account_id:
            _LOGGER.error(SESSION_ERROR_ACCOUNT_ID_NULL_EMPTY)
            raise AccountError(SESSION_ERROR_ACCOUNT_ID_NULL_EMPTY)
        if self.account_id == DEFAULT_SESSION_ID:
            _LOGGER.error(SESSION_ERROR_ACCOUNT_ID_DEFAULT)
            raise AccountError(SESSION_ERROR_ACCOUNT_ID_DEFAULT)

    def create_session(self):
        """Create Dexcom Share API session by getting session id."""
        _LOGGER.debug("Get session ID")
        self._validate_account()

        json = {
            "accountName": self.username,
            "password": self.password,
            "applicationId": DEXCOM_APPLICATION_ID,
        }
        """
        The Dexcom Share API at DEXCOM_AUTHENTICATE_ENDPOINT
        returns the account ID if credentials are valid -- whether
        the username is a classic username or email. Using the
        account ID the DEXCOM_LOGIN_ID_ENDPOINT is used to fetch
        a session ID.
        """
        endpoint1 = DEXCOM_AUTHENTICATE_ENDPOINT
        endpoint2 = DEXCOM_LOGIN_ID_ENDPOINT

        print('Fetching accound ID.')        
        self.account_id = self._request("post", endpoint1, json=json)
        print(f'ACCOUND ID: {self.account_id}')
        try:
            self._validate_account_id()

            json = {
                "accountId": self.account_id,
                "password": self.password,
                "applicationId": DEXCOM_APPLICATION_ID,
            }

            self.session_id = self._request("post", endpoint2, json=json)
            self._validate_session_id()
        except SessionError:
            raise AccountError(ACCOUNT_ERROR_UNKNOWN)

    def verify_serial_number(self, serial_number: str) -> bool:
        """Verify if transmitter serial number is assigned to user."""
        self._validate_session_id()
        if not serial_number:
            _LOGGER.error(ARGUEMENT_ERROR_SERIAL_NUMBER_NULL_EMPTY)
            raise ArguementError(ARGUEMENT_ERROR_SERIAL_NUMBER_NULL_EMPTY)

        params = {"sessionId": self.session_id, "serialNumber": serial_number}
        try:
            r = self._request(
                "post", DEXCOM_VERIFY_SERIAL_NUMBER_ENDPOINT, params=params
            )
        except SessionError:
            _LOGGER.debug("Get new session ID")
            self.create_session()
            r = self._request(
                "post", DEXCOM_VERIFY_SERIAL_NUMBER_ENDPOINT, params=params
            )
        return r.json() == "AssignedToYou"

    def get_glucose_readings(
        self, minutes: int = 1440, max_count: int = 288
    ) -> [GlucoseReading]:
        """Get max_count glucose readings within specified minutes."""
        self._validate_session_id()
        if minutes < 1 or minutes > 1440:
            _LOGGER.error(ARGUEMENT_ERROR_MINUTES_INVALID)
            raise ArguementError(ARGUEMENT_ERROR_MINUTES_INVALID)
        if max_count < 1 or max_count > 288:
            _LOGGER.error(ARGUEMENT_ERROR_MAX_COUNT_INVALID)
            raise ArguementError(ARGUEMENT_ERROR_MAX_COUNT_INVALID)

        params = {
            "sessionId": self.session_id,
            "minutes": minutes,
            "maxCount": max_count,
        }
        try:
            json_glucose_readings = self._request(
                "post", DEXCOM_GLUCOSE_READINGS_ENDPOINT, params=params
            )
        except SessionError:
            self.create_session()

            params = {
                "sessionId": self.session_id,
                "minutes": minutes,
                "maxCount": max_count,
            }

            json_glucose_readings = self._request(
                "post", DEXCOM_GLUCOSE_READINGS_ENDPOINT, params=params
            )

        glucose_readings = []
        if not json_glucose_readings:
            return None
        for json_glucose_reading in json_glucose_readings:
            glucose_readings.append(GlucoseReading(json_glucose_reading))
        if not glucose_readings:
            return None
        return glucose_readings

    def get_latest_glucose_reading(self) -> GlucoseReading:
        """Get latest available glucose reading."""
        glucose_readings = self.get_glucose_readings(max_count=1)
        if not glucose_readings:
            return None
        return glucose_readings[0]

    def get_current_glucose_reading(self) -> GlucoseReading:
        """Get current available glucose reading."""
        glucose_readings = self.get_glucose_readings(minutes=10, max_count=1)
        if not glucose_readings:
            return None
        return glucose_readings[0]
