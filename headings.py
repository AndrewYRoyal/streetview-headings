import pandas as pd
import numpy as np
import googlemaps
import pyproj
import json
import argparse
import time
import sys

## Pricing:
          ## $0.007 per photo
          ## $0.005 per directions
          ## $0.012 total

parser = argparse.ArgumentParser('Find property headings for google street view')
address_path = 'input.csv'
with open('credentials.json') as f:
    credentials = json.load(f)

## Import Data
#============================================================
site_dat = pd.read_csv(address_path)
print(f'{site_dat.site.count()} properties')

## Reformat inputs
#============================================================
site_dat.set_index('site', inplace = True)
site_dat['origin'] = site_dat['address']
site_dat['destination'] = site_dat['address']

centroids = site_dat[['lon', 'lat']].T.to_dict()
streets = site_dat[['origin', 'destination']].T.to_dict()

## Calculate Headings
#============================================================
gmaps = googlemaps.Client(**credentials)
geodesic = pyproj.Geod(ellps='WGS84')
export_cols = ['address', 'street_lon', 'street_lat', 'heading']

counter_success = 0
counter_fail = 0
start_time = time.time()

for site, centroid in centroids.items():
    try:
        street_coord = gmaps.directions(**streets[site])[0]['legs'][0]['start_location']
        points = {
            'lats1': street_coord['lat'],
            'lons1': street_coord['lng'],
            'lats2': centroid['lat'],
            'lons2': centroid['lon']
        }
        heading = geodesic.inv(**points)[0]
        site_dat.loc[site, 'heading'] = heading
        site_dat.loc[site, 'street_lon'] = street_coord['lng']
        site_dat.loc[site, 'street_lat'] = street_coord['lat']
        counter_success += 1
    except:
        site_dat.loc[site, 'heading'] = np.nan
        print("Unexpected error:", sys.exc_info()[0])
        counter_fail += 1
    time.sleep(2)
    if((counter_success + counter_fail) % 50 == 0):
        print('{} successful, {} failed'.format(counter_success, counter_fail))
        time_elapsed = start_time - time.time()
        print(f'{time_elapsed} elapsed.')
        site_dat[export_cols].to_csv('last.csv')
print(f'{time_elapsed} elapsed.')
# ~1.7s per site

## Export
#============================================================
site_dat[export_cols].to_csv('output.csv')
