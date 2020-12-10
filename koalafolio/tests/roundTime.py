# -*- coding: utf-8 -*-
"""
Created on 10.12.2020

@author: Martin
"""

import datetime

def roundTime(dt=None, roundToS=60):
    if dt == None: dt = datetime.datetime.now()
    if roundToS > 1:
        if roundToS < 10:
            dt = roundTime(dt, roundToS=1)
        seconds = (dt.replace(tzinfo=None) - dt.min).seconds
        rounding = (seconds+roundToS/2) // roundToS * roundToS
        return dt + datetime.timedelta(0, rounding-seconds, -dt.microsecond)
    else:
        roundTo = roundToS*1000000
        if dt == None : dt = datetime.datetime.now()
        microseconds = (dt.replace(tzinfo=None) - dt.min).microseconds
        rounding = (microseconds+roundTo/2) // roundTo * roundTo
        return dt + datetime.timedelta(0, 0, rounding-microseconds)

def roundTimeMin(dt=None):
    if dt == None: dt = datetime.datetime.now()
    dt = dt.replace(microsecond=0)
    dt = dt + datetime.timedelta(seconds=30)
    dt = dt.replace(second=0)
    return dt


times = []

times.append(datetime.datetime(year=2017, month=1, day=1, hour=0, minute=0, second=15, microsecond=45))
times.append(datetime.datetime(year=2018, month=1, day=1, hour=23, minute=59, second=30, microsecond=23))
times.append(datetime.datetime(year=2019, month=12, day=31, hour=0, minute=0, second=12, microsecond=45))
times.append(datetime.datetime(year=2020, month=12, day=31, hour=23, minute=59, second=30, microsecond=12))
times.append(datetime.datetime(year=2012, month=2, day=28, hour=23, minute=59, second=30, microsecond=11))
times.append(datetime.datetime(year=2018, month=5, day=31, hour=8, minute=34, second=38, microsecond=22))
times.append(datetime.datetime(year=2017, month=7, day=22, hour=8, minute=34, second=22, microsecond=45))

dts = []
roundTimes = []
rounddts = []
for time in times:
    dts.append(time.timestamp())
    roundTimes.append(roundTime(dt=time, roundToS=60))
    rounddts.append(roundTimes[-1].timestamp())

