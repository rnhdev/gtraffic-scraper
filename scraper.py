#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os, calendar, time, random, sys, argparse, threading, datetime, math
from PIL import Image
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from io import BytesIO

options = argparse.ArgumentParser(description='Options')
options.add_argument('lat_start', type=float, help='Start latitude')
options.add_argument('lon_start', type=float, help='Start longitude')
options.add_argument('lat_end', type=float, help='End latitude')
options.add_argument('lon_end', type=float, help='End longitude')
options.add_argument('level', type=int, help='Zoom level (15 default)')
options.add_argument('time', type=int, help='Seconds int week (-1 for realtime)')

args = options.parse_args()

def coordinate_to_tile(lat, lon, zoom):
  lat_rad = lat * math.pi / 180.0;
  n = math.pow(2, zoom);
  x_tile = n * ((lon + 180) / 360.0);
  y_tile = n * (1-(math.log(math.tan(lat_rad) + 1/math.cos(lat_rad)) / math.pi)) / 2.0;

  return round(x_tile), round(y_tile);


def build_proxy_list():
    ua = UserAgent() 
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')
    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    proxy_list = []
    for row in proxies_table.tbody.find_all('tr'):
        proxy_list.append({
        'ip':   row.find_all('td')[0].string,
        'port': row.find_all('td')[1].string
        })
    return proxy_list

def build_tile_region(lat_start, lat_end, lon_start, lon_end, zoom):
    x_start,y_start = coordinate_to_tile(lat_start, lon_start, zoom)
    x_end,y_end = coordinate_to_tile(lat_end, lon_end, zoom)

    print([x_start,y_start])
    print([x_end,y_end])

    if x_end - x_start < 0:
        aux = x_end
        x_end = x_start
        x_start = aux        

    if y_end - y_start < 0:
        aux = y_end
        y_end = y_start
        y_start = aux        

    if x_start == x_end:
        x_end = x_end + 1

    if y_end == y_start:
        y_end = y_end + 1

    return {
        'x_start': x_start,
        'x_end': x_end,
        'y_start': y_start,
        'y_end': y_end
        }

def get_traffic_image(url, proxy):
    request = Request(url)
    request.set_proxy(proxy, 'http')
    image_data = urlopen(request, timeout=2).read()
    
    return Image.open(BytesIO(image_data))

def get_proxy(proxy_list):
  return proxy_list[random.randint(0, len(proxy_list) - 1)]

def scraper(proxy_list, time, zoom_level, region):
    output_file = os.path.dirname(os.path.realpath(__file__)) + "/traffic.png"
    w = region['x_end'] - region['x_start']
    h = region['y_end'] - region['y_start']


    url_template = ("http://mt1.google.com/vt?hl=es&lyrs=s,traffic|seconds_into_week:%i&x=%i&y=%i&z=%i&style=15")           
    image_out = Image.new('RGB', (256*w,256*h), color=(255,255,255))

    proxy = get_proxy(proxy_list)

    req = Request('http://icanhazip.com')
    req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

    for i in range(w):
        for j in range(h):
            while True:
                x = region['x_start'] + i
                y = region['y_start'] + j
                url = url_template % (time, x, y, zoom_level)
                proxy_host = proxy['ip'] + ':' + proxy['port']

                print(url)

                try:
                    im = get_traffic_image(url, proxy_host)                
                    break
                except Exception as err:
                    proxy = get_proxy(proxy_list)
                    continue            
            im = im.convert('RGBA')
            image_out.paste(im, (256*i, 256*j), im)         
        image_out.save(output_file)

def main():
    proxy_list = build_proxy_list()

    if len(proxy_list) < 1:
        print('Proxy list is empty')
        return -1

    region = build_tile_region(args.lat_start, args.lat_end, args.lon_start, args.lon_end, args.level)

    if region is None:
        print('Tile region is empty. Check coordinates input')
        return -1

    scraper(proxy_list, args.time, args.level, region)
if __name__ == '__main__':
  main()
