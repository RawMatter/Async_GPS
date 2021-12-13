from influxdb_client import InfluxDBClient

from datetime import datetime
from gps import Gps
import json
import asyncio
import serial_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def logger(gps_handler):
    gps = gps_handler
    BUCKET = os.environ['INFLUXDB_BUCKET']
    ORG = os.environ['INFLUX_ORG']
    db_client = InfluxDBClient(
            url="http://localhost:8086", 
            token=os.environ['INFLUX_TOKEN'], 
            org=ORG
        )

    write_client = db_client.write_api(write_options=SYNCHRONOUS)

    while True:
        asyncio.sleep(20)
        if int(gps.fix_indicator) > 1:
            lat = gps.latitude
            if gps.hemisphere == "N":
                lat /= 100
            else:
                lat /= -100
            long = gps.longitude
            if gps.half == "E":
                long /= 100
            else:
                long /= -100
            speed = gps.speed_kmh
            heading = gps.heading

            payload = {
                "measurement": "position",
                "tags": {"device":"rover"},
                "fields":{
                    "latitude": lat,
                    "longitude": long,
                    "speed(km/h)": speed,
                    "heading(deg)": heading,
                    "satelite_count": gps.satellite_count,
                    "altitrude(m)":gps.altitude
                }
            }
            write_client.write(BUCKET,ORG,payload)


async def main():
    print("main")
    loop = asyncio.get_event_loop()
    gps = serial_asyncio.create_serial_connection(loop, Gps,'/dev/ttyS0',baudrate=4800)
    log =  asyncio.create_task(logger(gps))

    await gps
    await log

asyncio.run(main())
