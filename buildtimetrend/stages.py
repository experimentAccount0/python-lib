'''
vim: set expandtab sw=4 ts=4:

Reads timestamps.csv, calculates stage duration and saves the result
to an xml file

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

import csv
import os
from datetime import datetime
from lxml import etree


class Stages(object):
    '''
    Build stages object.
    It gathers timestamps from a csv file and calculates stage duration.
    Output stages in xml format.
    '''

    def __init__(self):
        self.stages = []
        self.started_at = None

    def read_csv(self, csv_filename):
        '''
        Gathers timestamps from a csv file and calculates stage duration.

        Parameters :
        - csv_filename : csv filename containing timestamps
        Returns false if file doesn't exist, true if it was read successfully.
        '''
        # load timestamps file
        if not os.path.isfile(csv_filename):
            print 'File doesn\'t exist : {0}'.format(csv_filename)
            return False

        # read timestamps, calculate stage duration
        with open(csv_filename, 'rb') as csv_data:
            timestamps = csv.reader(csv_data, delimiter=',', quotechar='"')
            previous_timestamp = 0
            event_name = None
            for row in timestamps:
                timestamp = int(row[1])
                if self.started_at is None:
                    started_datetime = datetime.fromtimestamp(timestamp)
                    self.started_at = started_datetime.isoformat()
                if event_name is not None:
                    if event_name == 'end':
                        break
                    duration = timestamp - previous_timestamp
                    print 'Duration {0} : {1}s'.format(event_name, duration)
                    # add stage duration to stages dict
                    self.stages.append({
                        "name": event_name,
                        "started_at":
                        datetime.fromtimestamp(previous_timestamp).isoformat(),
                        "finished_at":
                        datetime.fromtimestamp(timestamp).isoformat(),
                        "duration": duration})
                event_name = row[0]
                previous_timestamp = timestamp

        return True

    def total_duration(self):
        '''Calculate total duration of all stages'''
        total_duration = 0
        # calculate total duration
        for stage in self.stages:
            total_duration += stage["duration"]

        return total_duration

    def to_xml(self):
        '''Generates xml object from stages dictionary'''
        root = etree.Element("stages")

        for stage in self.stages:
            root.append(etree.Element(
                "stage", name=stage["name"],
                duration=str(stage["duration"])))

        return root

    def to_xml_string(self):
        '''Generates xml string from stages dictionary'''
        return etree.tostring(self.to_xml(), pretty_print=True)
