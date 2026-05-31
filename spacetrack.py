import requests
import configparser
import os
from skyfield.api import EarthSatellite
import numpy as np
from skyfield.framelib import itrs

from lofarantpos.db import LofarAntennaDatabase
from astropy.coordinates import EarthLocation
from skyfield.api import wgs84, load, utc
import astropy.units as u
from datetime import datetime, timedelta

# from https://www.space-track.org/documentation#howto-api_python

def get_iss(start_date, end_date, recording_datetime):
    # See https://www.space-track.org/documentation for details on REST queries

    uriBase                = "https://www.space-track.org"
    requestLogin           = "/ajaxauth/login"
    requestCmdAction       = "/basicspacedata/query" 
    requestFindISS   = "/class/gp_history/EPOCH/{START_DATE}--{END_DATE}/NORAD_CAT_ID/25544/format/3le/orderby/EPOCH%20asc"


    # ACTION REQUIRED FOR YOU:
    #=========================
    # Provide a config file in the same directory as this file, called ISSTrack.ini, with this format (without the # signs)
    # [configuration]
    # username = XXX
    # password = YYY
    # output = ZZZ (optional)
    #
    # ... where XXX and YYY are your www.space-track.org credentials (https://www.space-track.org/auth/createAccount for free account)
    # ... and ZZZ is your Excel Output file - e.g. iss-track.xlsx (note: make it an .xlsx file)

    # Use configparser package to pull in the ini file (pip install configparser)
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(base_dir, "ISSTrack.ini")
    
    file_read = config.read(ini_path)
    if not file_read:
        print("ERROR: ISSTrack.ini not found.")
    elif not config.has_section("configuration"):
        print("ERROR: Header [configuration] not found in file.")
    else:
        configUsr = config.get("configuration","username")
        configPwd = config.get("configuration","password")
        
    siteCred = {'identity': configUsr, 'password': configPwd}


    # use requests package to drive the RESTful session with space-track.org
    with requests.Session() as session:
        # run the session in a with block to force session to close if we exit

        # need to log in first. note that we get a 200 to say the web site got the data, not that we are logged in
        resp = session.post(uriBase + requestLogin, data = siteCred)
        if resp.status_code != 200:
            print(f"Error {resp.status_code}. POST fail on login.")
            return ""

        # this query picks up ISS. Note - a 401 failure shows you have bad credentials 
        requestFindISS = requestFindISS.replace('{START_DATE}', start_date.replace(' ','%20'))
        requestFindISS = requestFindISS.replace('{END_DATE}', end_date.replace(' ','%20'))
                                                            
        resp = session.get(uriBase + requestCmdAction + requestFindISS)
        if resp.status_code != 200:
            print(resp)
            print(f"Error {resp.status_code}. GET fail on request for ISS satellites.")
            return ""
        else:
            print("Data downloaded, converting to Skyfield objects.")
            
            if recording_datetime is None:
                recording_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

            best_iss   = None
            best_l1    = best_l2 = None
            best_delta = float('inf')
            
            lines = resp.text.strip().splitlines()
            
            # TLE has 3 lines/satellite
            for i in range(0, len(lines) - 2, 3):
                try:
                    name = lines[i].strip()
                    l1 = lines[i+1]
                    l2 = lines[i+2]
                    iss = EarthSatellite(l1, l2, name)
                    
                    # Parse epoch from TLE line 1 columns 18-32: YYDDD.DDDDDDDD
                    epoch_str = l1[18:32].strip()
                    yr2 = int(epoch_str[:2])
                    year = 2000 + yr2 if yr2 < 57 else 1900 + yr2
                    doy = float(epoch_str[2:])
                    epoch_dt = datetime(year, 1, 1) + timedelta(days=doy - 1)
                    delta = abs((recording_datetime - epoch_dt).total_seconds())
                    
                    if delta < best_delta:
                        best_delta = delta
                        best_iss = iss
                        best_l1 = l1
                        best_l2 = l2

                except Exception:
                    continue 
                    
            return best_iss, best_l1, best_l2


def get_pointing_coords(iss, station_name, obstime_dt):
    db = LofarAntennaDatabase()
    st_el = EarthLocation.from_geocentric(*(db.phase_centres[station_name] * u.m))
    st_loc = wgs84.latlon(st_el.lat.deg, st_el.lon.deg, elevation_m=st_el.height.to(u.m).value)

    ts = load.timescale()
    t = ts.from_datetime(obstime_dt.replace(tzinfo=utc))

    difference = iss - st_loc
    topocentric = difference.at(t)
    alt, az, _ = topocentric.altaz()

    return alt.degrees, az.degrees

def bistatic_params(iss, t):
    # ISS TO CARTESIAN
    geocentric = iss.at(t)
    sat_xyz, vel_sat = geocentric.frame_xyz_and_velocity(itrs)

    sat_xyz = sat_xyz.m
    vel_sat = vel_sat.m_per_s

    # RX TO CARTESIAN POSITION
    # WGS84: lat +57.5575 N, lon 21.8557 E, elev 13.3 m
    rx_loc = EarthLocation(lat=57.5575*u.deg, lon=21.8557*u.deg, height=13.3*u.m)
    rx_xyz = np.array([rx_loc.x.value, rx_loc.y.value, rx_loc.z.value]) 

    # WGS84: lat 52.23167 N, lon 21.00639 E, elev 257 m
    tx_loc = EarthLocation(lat=52.23167*u.deg, lon=21.00639*u.deg, height=257*u.m)
    tx_xyz = np.array([tx_loc.x.value, tx_loc.y.value, tx_loc.z.value])

    # VECTORS (From antemnas to sat)
    vec_tx = sat_xyz - tx_xyz
    vec_rx = sat_xyz - rx_xyz

    #Distances
    r_tx_sat = np.linalg.norm(vec_tx)
    r_sat_rx = np.linalg.norm(vec_rx)

    R_abs = r_tx_sat + r_sat_rx

    # UNITARY VECTORS
    u_tx = vec_tx / r_tx_sat
    u_rx = vec_rx / r_sat_rx

    Vb = np.dot(vel_sat, u_tx) + np.dot(vel_sat, u_rx)

    return R_abs, Vb