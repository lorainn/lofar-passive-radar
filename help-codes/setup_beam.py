#!/usr/bin/env python

import datetime
import ephem
import numpy

import time
import os
import argparse
from dateutil.parser import parse

import sys



import getopt
class azelv:
    time = 0.0
    az = 0.0
    alt = 0.0
    

def get_pass(start_time,obs_place,obs_obj):
    obs_place.date=start_time
    obs_obj.compute(obs_place)
   
    return obs_obj.rise_time,obs_obj.transit_time,obs_obj.set_time
    


     
def get_az_elv_dist(start_t, stop_t, nstep, obs_place, obs_obj):
   
    time = []

    s = start_t.datetime().replace(microsecond=0)
    while s < stop_t.datetime():
        s+=datetime.timedelta(microseconds=100000)
        time.append(s)
  
    time = numpy.array(time)
    alt=numpy.zeros( numpy.size( time ) )
    az=numpy.zeros( numpy.size( time ) )
    distance  = numpy.zeros( numpy.size( time ) )
    velocity = numpy.zeros( numpy.size( time ) )
    
    for k,t in enumerate(time):
        obs_place.date=ephem.Date(time[k])
        obs_obj.compute(obs_place)
        az[k]=obs_obj.az
        alt[k]=obs_obj.alt
        distance[k] = obs_obj.range
        velocity[k]= obs_obj.range_velocity
       
    x=azelv()
    x.time=time
    x.az=az
    x.alt=alt
    x.distance = distance
    x.velocity = velocity
    return x

           

def make_place0(lat,lon):
    """ Make observatory place from lat and lon  
    """
    x = ephem.Observer()
    #print dir(x)
    
    x.lon=str(lon)
    x.lat=str(lat)
    x.elevation=0.0
    x.pressure = 0.0
    return x


def make_place(lon,lat,elevation):
    """ Make observatory place from lat and lon  
    """
    x = ephem.Observer()
  
    
    x.lon=lon
    x.lat=lat
    x.elevation=elevation
    x.pressure = 0.0
    return x
def make_sat(line1,line2,line3):
    x=ephem.readtle(line1 ,line2, line3)
    return x



if __name__ == '__main__':
    test_mode = True
    print_command = True
    parser = argparse.ArgumentParser()
    borowiec = make_place0(52.275874, 17.074936)
    irbene = make_place0(57.557216, 21.855252)
    pkin = make_place0(52.231718736894, 21.006047888954)
    
   
   
    parser = argparse.ArgumentParser(description='Program to setup beam on LOFAR lcu. Is  needed to setup rawdata beam logging on datalogger with data port for lane1 example: dump_udp --verbose --compress --check --timeout 1 --ports 16102 --bufsize 1e9 --sock_bufsize 1e7 \
 Example use ./setup_beam.py --station irbene --pass 2025-03-02T04:09:13 --befor 2 --after 3  --ephemeris "1 25544U 98067A   25057.69551956  .00051272  00000-0  91556-3 0  9991/2 25544  51.6387 134.2889 0005831 315.8203 179.6729 15.49515680498024" --dummy' )
    parser.add_argument('-p','--pass',type=str,dest='pass_time',help='Pass time in format 2025-10-12T12:12:12')
    parser.add_argument('-s','--station',type=str,default='borowiec',dest='station',help='Station name: borowiec or irbene')
    parser.add_argument('-b','--before',type=int,default=10,dest='before',help='Number of obserwation before pass time')
    parser.add_argument('-a','--after',type=int,default=10,dest='after',help='Number of obserwation after pass time')
    parser.add_argument('-d','--dummy', action='store_true',dest='dummy',help='Dummy run without any action')
    parser.add_argument('-e','--ephemeris',dest='ephemeris')
    args = parser.parse_args()
    obs_time_utc =parse(args.pass_time)
    
    tle = args.ephemeris.split('/')
    
    sat_info = {u'name':'sv',u'line1':tle[0],u'line2':tle[1]}

    sat = make_sat(sat_info['name'],sat_info['line1'],sat_info['line2'])
    if  args.station == 'borowiec':
        station = borowiec

    if args.station == 'irbene':
        station = irbene

    points  = []
 
   
   
    pass_time = obs_time_utc
    obs_time = ephem.Date(obs_time_utc)
    
   
   
   
    time_step_int = 30
    time_step = datetime.timedelta(seconds=time_step_int)
    n_befor= args.before
    n_after = args.after
    start_time = pass_time - time_step*n_befor
    stop_time = pass_time + time_step*n_after

    current_time = start_time
    beam_no = 0
    commands = {}
    commands[start_time - datetime.timedelta(seconds=41)]='rspctl --bitmode=16'
    commands[start_time - datetime.timedelta(seconds=40)]='rm %s_beam.log'%(start_time.isoformat())
    cut_commands = []
  
    data_cut_file = open('%s_times.log'%(start_time.isoformat()),'w')

 
    while current_time <= stop_time:
        beam_start = current_time - datetime.timedelta(seconds=15+7) #subtract 22 secs (15+7) because of LOFAR's hardware processing time
        rsp_time = current_time - datetime.timedelta(seconds=3)
        pointing_time = current_time - datetime.timedelta(seconds=0)
       
        station.date=ephem.Date(pointing_time)
        sat.compute(station)
        alt = sat.alt
        az = sat.az
        rn = sat.range
       
        if True:
            anadir =  "--anadir=%f,%f,AZELGEO"%(az,alt)
            rsp_comm_str = ""
        else:
            anadir = ''
            rsp_comm_str = "rsp"
        

        beam_comm_str="killall beamctl ;beamctl  --antennaset=HBA_JOINED --subbands=423,424,425,426,427,428,429,430,431,432  --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190 %s --beamlets=0:9 &"%(az,alt,anadir)
        
        commands[beam_start] = beam_comm_str
        if rsp_comm_str != "":
            commands[rsp_time] = rsp_comm_str
        commands[pointing_time] = '# %s alt:%2.2f az:%2.2f range:%2.2f'%(pointing_time.isoformat(),numpy.rad2deg(alt),numpy.rad2deg(az),rn/1000.)
        commands[pointing_time+datetime.timedelta(seconds=1)] = 'date >> %s_beam.log ; ps x | grep beamct[l] >> %s_beam.log'%(start_time.isoformat(),start_time.isoformat())
        cut_comm_str = '%s %d\n'%(pointing_time.isoformat(),time.mktime(pointing_time.timetuple()))
        data_cut_file.write(cut_comm_str)
        #print(cut_comm_str)
        #exit()
        cut_commands.append(cut_comm_str)
        current_time += time_step
        beam_no += 1
   
    if print_command == True:
         for c in sorted(commands):
             print( c.isoformat(),commands[c])
   
    for c in sorted(commands):
    
        comm_timestamp = time.mktime(c.timetuple())
       
        time_now  = time.time()
        to_wait =  comm_timestamp-time_now
        while time.time() < comm_timestamp-0.2:
            time_now  = time.time()
            to_wait =  comm_timestamp-time_now
          
            print('wait %d seconds to next command'%to_wait)
            if to_wait > 3:
                to_wait = 3
            time.sleep(to_wait)

        
        print(c,commands[c])
        if args.dummy == False:
            os.system(commands[c])
        else:
            pass
       
    
