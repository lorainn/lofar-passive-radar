#!/usr/bin/env python


import datetime
import ephem
import numpy

import time
import os

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
    


def select_range(start_time,obs_place,obs_obj):
    obs_place.date=start_time
    obs_obj.compute(obs_place)
    

    return obs_obj.rise_time,obs_obj.set_time
     
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

def make_beam(sat,time_0,subbands):
    pkin.date = time_0 + (-23.0)/24.0/3600
    timestamp = time.mktime(pkin.date.datetime().timetuple())
    print("# wait to %s"%datetime.datetime.fromtimestamp(timestamp))
    print("rspctl --bitmode=16")
    print("while [ $(date +%s)"+" -le %d ]; do date;sleep 1 ;done"%(timestamp))
    print('killall beamctl')
    print('sleep 2')


    borowiec.date=time_0
    sat.compute(borowiec)
    alt0 = sat.alt
    az0 = sat.az
    rn = sat.range
    pkin.date = time_0
    sat.compute(pkin)


       
  
    print("# %s %f %f %f %f %.2f"%(pkin.date.datetime(),numpy.rad2deg(sat.alt),numpy.rad2deg(sat.az),numpy.rad2deg(alt0),numpy.rad2deg(az0),rn/1000))
    print("beamctl --antennaset=HBA_JOINED --subbands=%s --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190 --anadir=%f,%f,AZELGEO --beamlets=0:9 &"%(subbands,az0,alt0,az0,alt0))

           

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
    #print dir(x)
    
    x.lon=lon
    x.lat=lat
    x.elevation=elevation
    x.pressure = 0.0
    return x
def make_sat(line1,line2,line3):
    x=ephem.readtle(line1 ,line2, line3)
    return x

if __name__ == '__main__':
    test_mode = False #False ###
    print_command = True

    borowiec = make_place0(57.553494, 21.854917) # to jest ibene
    pkin = make_place0(52.231718736894,21.006047888954)

    tle_file = open('starlink_tle.txt')
    name_in = 'STARLINK-33977'
    name_in = sys.argv[1]
    while True:
        name = tle_file.readline()[:-1]
        line2 = tle_file.readline()[:-1]
        line3 = tle_file.readline()[:-1]
        
        if  name.strip() == name_in.strip():
            sat = ephem.readtle(name ,line2, line3)
            break
    #    print(n,name)
   
    #from envisat_tle import sat_info
    #from iss_tle import sat_info
    #sat = make_sat(sat_info['name'],sat_info['line1'],sat_info['line2'])
   
    
    
    set_time = ephem.Date(datetime.datetime(2026,3,7,16,40,0))

    points  = []
    # znajd najblizy przelot
   
    #rise_time,set_time = select_range(set_time,pkin,sat)
    rise_time,pass_time,set_time = get_pass(set_time,borowiec,sat)
    rise_time = rise_time.datetime()
    pass_time = pass_time.datetime().replace(microsecond=0)
    set_time = set_time.datetime()
    time_step_int = 30
    time_step = datetime.timedelta(seconds=time_step_int)
    n_befor= int((pass_time-rise_time).total_seconds()/time_step_int+1.0)
    n_after = int((set_time-pass_time).total_seconds()/time_step_int+1.0)+2
   # print(rise_time,n_befor,n_after)
    start_time = pass_time - time_step*n_befor
    stop_time = pass_time + time_step*n_after

    current_time = start_time.replace(second=0)
    #print(current_time)
    #exit()
    beam_no = 0
    commands = {}
    commands[current_time - datetime.timedelta(seconds=41)]='rspctl --bitmode=16'
    commands[current_time - datetime.timedelta(seconds=40)]='rm %s_%s_beam.log'%(start_time.isoformat(),name_in)


    

    cut_commands = []
    subbands =    "36:50,76:102,115:129" #"13:62,118:128"# '448:487'# '423,424,425,426,427,428,429,430,431,432'
    data_cut_file = open('%s_%s_times.log'%(start_time.isoformat(),name_in),'w')

    
    
    while current_time <= stop_time:
        beam_start = current_time - datetime.timedelta(seconds=15+7)
        rsp_time = current_time - datetime.timedelta(seconds=3)
        pointing_time = current_time - datetime.timedelta(seconds=0)
     #   print(beam_start,rsp_time,current_time)
      
        borowiec.date=ephem.Date(pointing_time)
        sat.compute(borowiec)
        alt = sat.alt
        az = sat.az
        rn = sat.range
        alt0 = alt
        az0 = az
        beam = beam_no%6
        if True:
            anadir =  "--anadir=%f,%f,AZELGEO"%(az,alt)
            rsp_comm_str = ""
        else:
            anadir = ''
            rsp_comm_str = "rsp"
        
        delta = numpy.deg2rad(1.8)
        beam_comm_str="killall beamctl ; beamctl  --antennaset=HBA_JOINED --subbands=423,424,425,426,427,428,429,430,431,432,387,388,389,390,391,392,393,394,395,396,415,416,417,418,419,420,421,422,423,424,460,461,462,463,464,465,466,467,468,469  --digdir=%f,%f,AZELGEO --rcus=0:179,182:191 --band=110_190 %s --beamlets=0:39 &  "%(az,alt,anadir)
        #delta_time = rn/1000.0*numpy.deg2rad(1)/7.0
        delta_time = 2.0
        #if True:
        #print(rn/1000,delta_time)
        #current_time += time_step
        #continue
        if False:
        #for tn,time_delta in enumerate(numpy.array([-2,2,-4,4])*delta_time):
            pointing_time_mod = pointing_time + datetime.timedelta(seconds=time_delta)
            borowiec.date=ephem.Date(pointing_time_mod)
            sat.compute(borowiec)
            alt = sat.alt
            az = sat.az
            rn = sat.range
            #print(tn,numpy.rad2deg(ephem.separation((az0,alt0),(az,alt))),numpy.rad2deg(alt),'zzzzzzzzzzzzzzzzzzzzzz')
            if tn == 0:
                beam_comm_str += "killall beamctl1; beamctl1  --antennaset=HBA_JOINED --subbands=423,424,425,426,427,428,429,430,431,432,387,388,389,390,391,392,393,394,395,396,415,416,417,418,419,420,421,422,423,424  --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190  --beamlets=30:59 &  "%(az,alt)
            
            if tn == 1:
                beam_comm_str += "killall beamctl2; beamctl2  --antennaset=HBA_JOINED --subbands=423,424,425,426,427,428,429,430,431,432,387,388,389,390,391,392,393,394,395,396,415,416,417,418,419,420,421,422,423,424  --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190  --beamlets=61:90 &  "%(az,alt)


            if tn == 2:
                beam_comm_str += "killall beamctl3; beamctl3  --antennaset=HBA_JOINED --subbands=423,424,425,426,427,428,429,430,431,432,387,388,389,390,391,392,393,394,395,396,415,416,417,418,419,420,421,422,423,424  --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190  --beamlets=91:120 &  "%(az,alt)

            if tn == 3:
                beam_comm_str += "killall beamctl4; beamctl4  --antennaset=HBA_JOINED --subbands=423,424,425,426,427,428,429,430,431,432,387,388,389,390,391,392,393,394,395,396,415,416,417,418,419,420,421,422,423,424  --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190  --beamlets=122:151 &  "%(az,alt)



         #   rsp_comm_str = "#"
        #else:
        #beam_comm_str="killall beamctl %d;beamctl%d --antennaset=HBA_JOINED --subbands=%s --digdir=%f,%f,AZELGEO --rcus=0:191 --band=110_190 --beamlets=%d:%d &"%(beam,beam,subbands,az,alt,beam*10,beam*10+9)
          #  rsp_comm_str = "rsp"
        commands[beam_start] = beam_comm_str
        if rsp_comm_str != "":
            commands[rsp_time] = rsp_comm_str
        commands[pointing_time] = '# %s %2.2f %2.2f %2.2f %f %f'%(pointing_time.isoformat(),numpy.rad2deg(alt),numpy.rad2deg(az),rn/1000.,az,alt)
        commands[pointing_time+datetime.timedelta(seconds=1)] = 'date >> %s_beam.log ; ps x | grep beamct[l] >> %s_%s_beam.log'%(start_time.isoformat(),start_time.isoformat(),name_in)
        cut_comm_str = '%s %d\n'%(pointing_time.isoformat(),time.mktime(pointing_time.timetuple()))
        data_cut_file.write(cut_comm_str)
        print(cut_comm_str)
        #exit()
        cut_commands.append(cut_comm_str)
        current_time += time_step
        beam_no += 1
   
    if print_command == True:
         for c in sorted(commands):
             print( c.isoformat(),commands[c])
    #exit()
    for c in sorted(commands):
    
        comm_timestamp = time.mktime(c.timetuple())
        if test_mode == True:
            comm_timestamp = int(time.time()+12)
        time_now  = time.time()
        to_wait =  comm_timestamp-time_now
        while time.time() < comm_timestamp-0.2:
            time_now  = time.time()
            to_wait =  comm_timestamp-time_now
            # print(to_wait)
            print('wait: ',datetime.datetime.now().isoformat(),datetime.datetime.fromtimestamp(comm_timestamp).isoformat(),to_wait)
            if to_wait > 3:
                to_wait = 3
            time.sleep(to_wait)

        print(datetime.datetime.now().isoformat())
        print(c,commands[c])
        os.system(commands[c])
       
    
