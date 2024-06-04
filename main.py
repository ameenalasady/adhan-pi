import requests
import schedule
import time
import os
import datetime
import traceback
import subprocess
import logging

# Setup logging
# Replace with your actual log file path
LOG_FILE_PATH = '/path/to/your/logfile.log'
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE_PATH,
                    filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_bluetooth_connection():
    device_mac = "XX:XX:XX:XX:XX:XX"  # Replace with your actual device MAC address
    try:
        process = subprocess.Popen(
            ['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.stdin.write(b'connect %s\n' % device_mac.encode())
        process.stdin.flush()

        time.sleep(5)  # Wait 5 seconds before quitting

        process.stdin.write(b'quit\n')
        process.stdin.flush()

        out, err = process.communicate()
        if err:
            logger.error(f"Error: {err.decode()}")
        else:
            logger.debug(f"Output: {out.decode()}")
    except Exception as e:
        logger.error(f"Error in connecting to Bluetooth device: {e}")


def play_empty_sound():
    try:
        logger.debug("Playing empty sound...")
        result = subprocess.run(
            ["aplay", "/path/to/your/silence.wav"], check=True, capture_output=True)  # Replace with your actual path to silence.wav
        logger.debug(
            f"Finished playing empty sound. Output: {result.stdout.decode()}, Error: {result.stderr.decode()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error playing empty sound: {e}")
        logger.error(e.output.decode())


def get_prayer_times():
    logger.debug("Getting prayer times...")
    url = "http://api.aladhan.com/v1/calendar"
    today = datetime.date.today()

    params = {
        "latitude": 0.0,  # Replace with your actual latitude
        "longitude": 0.0,  # Replace with your actual longitude
        "method": 2,
        "month": today.month,
        "year": today.year,
        "school": 1,
        "tune": "15,0,0,0,15,0",
    }

    for _ in range(5):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                logger.debug("Successfully got prayer times.")
                data = response.json()
                for day in data['data']:
                    if day['date']['gregorian']['date'] == today.strftime("%d-%m-%Y"):
                        logger.debug(
                            f"Prayer times for {today.strftime('%d-%m-%Y')}:")
                        for prayer, time in day['timings'].items():
                            if prayer in ['Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                                logger.debug(f"{prayer}: {time[:-6]}")
                        return day['timings']
            else:
                logger.error(
                    f"Failed to get prayer times: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            logger.error(traceback.format_exc())
        time.sleep(60)


def play_adhan(prayer, time):
    logger.debug(f"Scheduling {prayer} adhan at {time}...")
    schedule.every().day.at(time).do(play_adhan_at_scheduled_time, prayer=prayer)
    logger.debug(f"{prayer} adhan scheduled at {time}.")


def play_adhan_at_scheduled_time(prayer):
    try:
        logger.debug(f"Playing {prayer} adhan at scheduled time...")
        subprocess.run(
            ["aplay", "/path/to/your/output.wav"], check=True)  # Replace with your actual path to output.wav
        logger.debug(f"Finished playing {prayer} adhan.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error playing {prayer} adhan: {e}")
        logger.error(e.output)


def schedule_adhans():
    logger.debug("Scheduling adhans...")
    prayer_times = get_prayer_times()
    if prayer_times is not None:
        for prayer, time in prayer_times.items():
            if prayer in ['Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                play_adhan(prayer, time[:-6])


schedule.every().day.at("00:01").do(schedule_adhans)
schedule.every(1).minutes.do(check_bluetooth_connection)
schedule.every(5).minutes.do(play_empty_sound)

schedule_adhans()
check_bluetooth_connection()
play_empty_sound()

while True:
    schedule.run_pending()
    time.sleep(1)
