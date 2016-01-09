# vim: set expandtab sw=4 ts=4:
"""
Interface to Keen IO.

Copyright (C) 2014-2016 Dieter Adriaenssens <ruleant@users.sourceforge.net>

This file is part of buildtimetrend/python-lib
<https://github.com/buildtimetrend/python-lib/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division
from builtins import str
import os
from buildtimetrend import logger
import copy
import keen
import requests
from keen import scoped_keys
from buildtimetrend.settings import Settings
from buildtimetrend.tools import check_dict
from buildtimetrend.tools import is_list
from buildtimetrend.tools import is_string
from buildtimetrend.buildjob import BuildJob


TIME_INTERVALS = {
    'week': {'name': 'week', 'timeframe': 'this_7_days', 'max_age': 600},
    'month': {'name': 'month', 'timeframe': 'this_30_days', 'max_age': 600},
    'year': {'name': 'year', 'timeframe': 'this_52_weeks', 'max_age': 1800}
}
KEEN_PROJECT_INFO_NAME = "buildtime_trend"


def keen_has_project_id():
    """Check if Keen.io project ID is set."""
    if "KEEN_PROJECT_ID" in os.environ or keen.project_id is not None:
        return True

    logger.warning("Keen.io Project ID is not set")
    return False


def keen_has_master_key():
    """Check if Keen.io Master API key is set."""
    if "KEEN_MASTER_KEY" in os.environ or keen.master_key is not None:
        return True

    logger.warning("Keen.io Master API Key is not set")
    return False


def keen_has_write_key():
    """Check if Keen.io Write Key is set."""
    if "KEEN_WRITE_KEY" in os.environ or keen.write_key is not None:
        return True

    logger.warning("Keen.io Write Key is not set")
    return False


def keen_has_read_key():
    """Check if Keen.io Read key is set."""
    if "KEEN_READ_KEY" in os.environ or keen.read_key is not None:
        return True

    logger.warning("Keen.io Read Key is not set")
    return False


def keen_is_writable():
    """Check if login keys for Keen IO API are set, to allow writing."""
    if keen_has_project_id() and keen_has_write_key():
        return True

    logger.warning("Keen.io Write Key is not set")
    return False


def keen_is_readable():
    """Check if login keys for Keen IO API are set, to allow reading."""
    if keen_has_project_id() and keen_has_read_key():
        return True

    logger.warning("Keen.io Read Key is not set")
    return False


def keen_io_generate_read_key(repo):
    """
    Create scoped key for reading only the build-stages related data.

    Param repo : github repository slug (fe. buildtimetrend/python-lib)
    """
    if not keen_has_master_key():
        logger.warning("Keen.io Read Key was not created,"
                       " keen.master_key is not defined.")
        return None

    master_key = keen.master_key or os.environ.get("KEEN_MASTER_KEY")

    privileges = {
        "allowed_operations": ["read"]
    }

    if repo is not None:
        privileges["filters"] = [get_repo_filter(repo)]

    logger.info("Keen.io Read Key is created for %s", repo)
    return scoped_keys.encrypt(master_key, privileges)


def keen_io_generate_write_key():
    """Create scoped key for write access to Keen.io database."""
    if not keen_has_master_key():
        logger.warning("Keen.io Write Key was not created,"
                       " keen.master_key is not defined.")
        return None

    master_key = keen.master_key or os.environ.get("KEEN_MASTER_KEY")

    privileges = {
        "allowed_operations": ["write"]
    }

    logger.info("Keen.io Write Key is created")
    return scoped_keys.encrypt(master_key, privileges)


def send_build_data(buildjob):
    """Send build data generated by client to keen.io."""
    if not isinstance(buildjob, BuildJob):
        raise TypeError("param buildjob should be a BuildJob instance")

    if keen_is_writable():
        logger.info("Sending client build job data to Keen.io")
        keen_add_event("build_jobs", {"job": buildjob.to_dict()})
        keen_add_events("build_stages", buildjob.stages_to_list())


def send_build_data_service(buildjob):
    """Send build data generated by service to keen.io."""
    if not isinstance(buildjob, BuildJob):
        raise TypeError("param buildjob should be a BuildJob instance")

    if keen_is_writable():
        logger.info("Sending service build job data to Keen.io")
        keen_add_event("build_jobs", {"job": buildjob.to_dict()})
        keen_add_events("build_substages", buildjob.stages_to_list())


def keen_add_event(event_collection, payload):
    """
    Wrapper for keen.add_event(), adds project info.

    Param event_collection : collection event data is submitted to
    Param payload : data that is submitted
    """
    # add project info to this event
    payload = add_project_info_dict(payload)

    # submit list of events to Keen.io
    keen.add_event(event_collection, payload)


def keen_add_events(event_collection, payload):
    """
    Wrapper for keen.add_events(), adds project info to each event.

    Param event_collection : collection event data is submitted to
    Param payload : array of events that is submitted
    """
    # add project info to each event
    payload = add_project_info_list(payload)

    # submit list of events to Keen.io
    keen.add_events({event_collection: payload})


def add_project_info_dict(payload):
    """
    Add project info to a dictonary.

    Param payload: dictonary payload
    """
    # check if payload is a dictionary, throws an exception if it isn't
    check_dict(payload, "payload")

    payload_as_dict = copy.deepcopy(payload)

    payload_as_dict[KEEN_PROJECT_INFO_NAME] = Settings().get_project_info()

    if "job" in payload:
        # override project_name, set to build_job repo
        if "repo" in payload["job"]:
            payload_as_dict[KEEN_PROJECT_INFO_NAME]["project_name"] = \
                payload["job"]["repo"]

        # override timestamp, set to finished_at timestamp
        if "finished_at" in payload["job"]:
            payload_as_dict["keen"] = {
                "timestamp": payload["job"]["finished_at"]["isotimestamp"]
            }

    return payload_as_dict


def add_project_info_list(payload):
    """
    Add project info to a list of dictionaries.

    Param payload: list of dictionaries
    """
    # check if payload is a list, throws an exception if it isn't
    is_list(payload, "payload")

    payload_as_list = []

    # loop over dicts in payload and add project info to each one
    for event_dict in payload:
        payload_as_list.append(add_project_info_dict(event_dict))

    return payload_as_list


def get_dashboard_keen_config(repo):
    """
    Generate the Keen.io settings for the configuration of the dashboard.

    The dashboard is Javascript powered HTML file that contains the
    graphs generated by Keen.io.
    """
    # initialise config settings
    keen_config = {}

    if not keen_has_project_id() or not keen_has_master_key():
        logger.warning("Keen.io related config settings could not be created,"
                       " keen.project_id and/or keen.master_key"
                       " are not defined.")
        return keen_config

    # set keen project ID
    if keen.project_id is None:
        keen_project_id = os.environ["KEEN_PROJECT_ID"]
    else:
        keen_project_id = keen.project_id
    keen_config['projectId'] = str(keen_project_id)

    # generate read key
    read_key = keen_io_generate_read_key(repo)
    if read_key is not None:
        # convert bytes to string
        if isinstance(read_key, bytes):
            read_key = read_key.decode('utf-8')

        keen_config['readKey'] = str(read_key)

    # return keen config settings
    return keen_config


def get_avg_buildtime(repo=None, interval=None):
    """
    Query Keen.io database and retrieve average build time.

    Parameters :
    - repo : repo name (fe. buildtimetrend/service)
    - interval : timeframe, possible values : 'week', 'month', 'year',
                 anything else defaults to 'week'
    """
    if repo is None or not keen_is_readable():
        return -1

    interval_data = check_time_interval(interval)

    try:
        return keen.average(
            "build_jobs",
            target_property="job.duration",
            timeframe=interval_data['timeframe'],
            max_age=interval_data['max_age'],
            filters=[get_repo_filter(repo)]
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        return -1
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.get_avg_buildtime() : " + str(msg))
        return -1


def get_total_build_jobs(repo=None, interval=None):
    """
    Query Keen.io database and retrieve total number of build jobs.

    Parameters :
    - repo : repo name (fe. buildtimetrend/service)
    - interval : timeframe, possible values : 'week', 'month', 'year',
                 anything else defaults to 'week'
    """
    if repo is None or not keen_is_readable():
        return -1

    interval_data = check_time_interval(interval)

    try:
        return keen.count_unique(
            "build_jobs",
            target_property="job.job",
            timeframe=interval_data['timeframe'],
            max_age=interval_data['max_age'],
            filters=[get_repo_filter(repo)]
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        return -1
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.get_total_build_jobs() : " + str(msg))
        return -1


def get_passed_build_jobs(repo=None, interval=None):
    """
    Query Keen.io database and retrieve total number of build jobs that passed.

    Parameters :
    - repo : repo name (fe. buildtimetrend/service)
    - interval : timeframe, possible values : 'week', 'month', 'year',
                 anything else defaults to 'week'
    """
    if repo is None or not keen_is_readable():
        return -1

    interval_data = check_time_interval(interval)

    try:
        return keen.count_unique(
            "build_jobs",
            target_property="job.job",
            timeframe=interval_data['timeframe'],
            max_age=interval_data['max_age'],
            filters=[
                get_repo_filter(repo),
                {
                    "property_name": "job.result",
                    "operator": "eq",
                    "property_value": "passed"
                }
            ]
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        return -1
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.get_passed_build_jobs() : " + str(msg))
        return -1


def get_pct_passed_build_jobs(repo=None, interval=None):
    """
    Calculate percentage of passed build jobs.

    Parameters :
    - repo : repo name (fe. buildtimetrend/service)
    - interval : timeframe, possible values : 'week', 'month', 'year',
                 anything else defaults to 'week'
    """
    total_jobs = get_total_build_jobs(repo, interval)
    passed_jobs = get_passed_build_jobs(repo, interval)

    logger.debug("passed/total build jobs : %d/%d", passed_jobs, total_jobs)

    # calculate percentage if at least one job was executed
    # passed is a valid number (not -1)
    if total_jobs > 0 and passed_jobs >= 0:
        return int(float(passed_jobs) / float(total_jobs) * 100.0)

    return -1


def get_result_color(value=0, ok_thershold=90, warning_thershold=70):
    """
    Get color code that corresponds to the result.

    Parameters:
    - value : value to check
    - ok_thershold : OK threshold value
    - warning_thershold : warning thershold value
    """
    if not(type(value) in (int, float) and
           type(ok_thershold) in (int, float) and
           type(warning_thershold) in (int, float)):
        return "lightgrey"

    # check thresholds
    if value >= ok_thershold:
        return "green"
    elif value >= warning_thershold:
        return "yellow"
    else:
        return "red"


def get_total_builds(repo=None, interval=None):
    """
    Query Keen.io database and retrieve total number of builds.

    Parameters :
    - repo : repo name (fe. buildtimetrend/service)
    - interval : timeframe, possible values : 'week', 'month', 'year',
                 anything else defaults to 'week'
    """
    if repo is None or not keen_is_readable():
        return -1

    interval_data = check_time_interval(interval)

    try:
        return keen.count_unique(
            "build_jobs",
            target_property="job.build",
            timeframe=interval_data['timeframe'],
            max_age=interval_data['max_age'],
            filters=[get_repo_filter(repo)]
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        return -1
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.get_total_builds() : " + str(msg))
        return -1


def get_latest_buildtime(repo=None):
    """
    Query Keen.io database and retrieve buildtime duration of last build.

    Parameters :
    - repo : repo name (fe. buildtimetrend/python-lib)
    """
    if repo is None or not keen_is_readable():
        return -1

    try:
        result = keen.extraction(
            "build_jobs",
            property_names="job.duration",
            latest=1,
            filters=[get_repo_filter(repo)]
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        return -1
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.get_latest_buildtime() : " + str(msg))
        return -1

    if is_list(result) and len(result) > 0 and \
            check_dict(result[0], None, ['job']) and \
            check_dict(result[0]['job'], None, ['duration']):
        return result[0]['job']['duration']

    return -1


def has_build_id(repo=None, build_id=None):
    """
    Check if build_id exists in Keen.io database.

    Parameters :
    - repo : repo name (fe. buildtimetrend/python-lib)
    - build_id : ID of the build
    """
    if repo is None or build_id is None:
        logger.error("Repo or build_id is not set")
        raise ValueError("Repo or build_id is not set")
    if not keen_is_readable():
        raise SystemError("Keen.io Project ID or API Read Key is not set")

    try:
        count = keen.count(
            "build_jobs",
            filters=[get_repo_filter(repo), {
                "property_name": "job.build",
                "operator": "eq",
                "property_value": str(build_id)}]
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        raise SystemError("Connection to Keen.io API failed")
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.has_build_id : " + str(msg))
        raise SystemError(msg)

    return count > 0


def get_all_projects():
    """Query Keen.io database and retrieve a list of all projects."""
    if not keen_is_readable():
        return []

    try:
        result = keen.select_unique(
            "build_jobs",
            "buildtime_trend.project_name",
            max_age=3600 * 24  # cache for 24 hours
        )
    except requests.ConnectionError:
        logger.error("Connection to Keen.io API failed")
        return []
    except keen.exceptions.KeenApiError as msg:
        logger.error("Error in keenio.get_all_projects() : " + str(msg))
        return []

    if type(result) is list:
        return result

    return []


def get_repo_filter(repo=None):
    """
    Return filter for analysis request.

    Parameters
    - repo : repo slug name, fe. buildtimetrend/python-lib
    """
    if repo is None:
        return None

    return {
        "property_name": "{}.project_name".format(KEEN_PROJECT_INFO_NAME),
        "operator": "eq",
        "property_value": str(repo)
    }


def check_time_interval(interval=None):
    """
    Check time interval and returns corresponding parameters.

    Parameters :
    - interval : timeframe, possible values : 'week', 'month', 'year',
                 anything else defaults to 'week'
    """
    if is_string(interval):
        # convert to lowercase
        interval = interval.lower()

        if interval in TIME_INTERVALS:
            return TIME_INTERVALS[interval]

    return TIME_INTERVALS['week']
