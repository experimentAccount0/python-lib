'''
vim: set expandtab sw=4 ts=4:

Collection of tool functions

Copyright (C) 2014 Dieter Adriaenssens <ruleant@users.sourceforge.net>

This file is part of buildtime-trend
<https://github.com/ruleant/buildtime-trend/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import copy
from datetime import datetime


def format_timestamp(timestamp):
    '''
    Format a datetime timestamp (UTC) to ISO format (YYYY-MM-DDTHH:MM:SS)

    Parameters :
    - timestamp : timestamp, seconds since epoch
    '''
    timestamp_datetime = datetime.utcfromtimestamp(timestamp)
    return timestamp_datetime.isoformat()


def add_project_info(payload, schema_version=1):
    '''
    Adds project info to a dictonary
    Param payload: dictonary payload
    Param schema_version: version of schema used
    '''
    if payload is not None and type(payload) is dict:
        payload_as_dict = copy.deepcopy(payload)
    else:
        payload_as_dict = {}

    payload_as_dict["buildtime_trend"] = {
        "version": "0.1",
        "schema_version": str(schema_version)
    }

    return payload_as_dict
