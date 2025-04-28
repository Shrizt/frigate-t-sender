import paho.mqtt.client as mqtt
import requests
import json
import os
import time
from logger import ulog
from datetime import datetime, timedelta
from config import load_config
from globals import *


config = load_config(CONFIG_FILE)

last_event_time = {}

def frigate_event_to_text(event_data):
    """Process incoming Frigate event and format a text message."""
    
    after_data = event_data.get("after", {})
    event_id = after_data.get("id", "N/A")
    camera = after_data.get("camera", "Unknown Camera")
    label = after_data.get("label", "Unknown Label")
    entered_zones = after_data.get("entered_zones", [])
    start_time = after_data.get("start_time", 0)
    
    # Convert timestamp to human-readable format
    start_datetime = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Formatting message
    message = (
        f"Event: {event_id}\n"
        f"Camera: {camera}\n"
        f"Start: {start_datetime}\n"
        f"Label(s): {label}\n"
        f"Zone(s): {', '.join(entered_zones) if entered_zones else 'None'}"
    )
    
    return message

def send_telegram_message(text, muted=False):
    """Send a message to Telegram"""
    url = f"https://api.telegram.org/bot{config.telegram.bot_token}/sendMessage"
    payload = {"chat_id": config.telegram.chat_id, "text": text, "disable_notification": muted}
    response = requests.post(url, json=payload)
    ulog.debug(f"Sent Telegram message (Silent:{muted}): {text} | Response: {response.status_code}")

def send_telegram_video(file_path, caption, muted=False):
    """Send a video file to Telegram"""
    url = f"https://api.telegram.org/bot{config.telegram.bot_token}/sendVideo"
    with open(file_path, "rb") as video:
        files = {"video": video}
        payload = {"chat_id": config.telegram.chat_id, "caption": caption, "disable_notification": muted}
        response = requests.post(url, data=payload, files=files)    
    if response.status_code != 200:
        send_telegram_message(f"Send Telegram video error: {file_path} | Response: {response.status_code} - {response.text}")
    else:
        ulog.debug(f"Sent Telegram video (Silent:{muted}): {file_path} | Response: {response.status_code} - {response.text}")   
        os.remove(file_path);
        


def download_file(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        file_size = os.path.getsize(filename)  # Get actual file size                
        ulog.debug(f"Downloaded file: {url} to {filename} \n Size: {file_size}")
        return file_size
    ulog.error(f"Failed to download video: {url} | Status: {response.status_code}")
    send_telegram_message(f"Failed to download video: {url} | Status: {response.status_code}")
    return -1


def download_content(event_id, camera):
    """Download video clip from Frigate API"""
    event_url = f"{config.frigate.frigate_api}/{event_id}/"   
    video_size = download_file(f"{event_url}clip.mp4",f"{CACHE_DIR}/{camera}.mp4")
    if video_size == 0:
        ulog.debug("file size is 0 - sleeping 5 seconds and retry...")
        time.sleep(5)
        video_size = download_file(f"{event_url}clip.mp4",f"{CACHE_DIR}/{camera}.mp4")        
        if video_size == 0:
            ulog.debug("still_zero_file, sleep 3 more second and second retry")
            time.sleep(3)
            video_size = download_file(f"{event_url}clip.mp4",f"{CACHE_DIR}/{camera}.mp4")        
            if video_size == 0:
                ulog.error("error_downloading_video after 3 attempts")

    download_file(f"{event_url}snapshot.jpg",f"{CACHE_DIR}/{camera}.jpg")    

def trim_video(input_path, output_path):
    """Trim the video to the specified duration"""
    cmd = f"ffmpeg -i {input_path} -t {config.storage.clip_duration} -c copy {output_path} -y"
    os.system(cmd)
    ulog.debug(f"Trimmed video: {output_path}")

def handle_event(event_data):
    """Process incoming Frigate event"""
    global last_event_time

    event_type = event_data.get("type")
    after_data = event_data.get("after", {})
    event_id = after_data.get("id")
    camera = after_data.get("camera")
    label = after_data.get("label")

    if event_type != "end":
        ulog.debug("Skipping event: Not a end event")
        return

    if config.frigate.event_zone not in after_data.get("entered_zones", []):
        ulog.debug("Skipping event: end event outside target zone")
        return

    ulog.debug(f"MQTT Message Received: {event_data}") #logging only after initial checks

    if not after_data.get("has_clip",False):
        ulog.debug("Skipping event: has_clip == False")
        return

    if camera not in config.frigate.camera_whitelist:
        ulog.debug(f"Skipping event: Camera '{camera}' not in whitelist")
        return

    now = time.time()
    last_trigger = last_event_time.get(camera, 0)
    if (now - last_trigger) < config.frigate.min_event_interval:
        ulog.debug(f"Skipping event: Rate limit active for camera '{camera}'")
        return
    last_event_time[camera] = now

    ulog.debug(f"Processing event: {event_id} | Camera: {camera} | Label: {label}")
    time.sleep(0.5) #sleep 0.5 sec - give frigate time to make clip
    download_content(event_id, camera)
    #if video_path:
        #trimmed_path = os.path.join(STORAGE_PATH, f"{TRIMMED_PREFIX}{camera}.mp4")
        #trim_video(video_path, trimmed_path)
        #send_telegram_video(trimmed_path, f"{label} detected on {camera}")  

    send_telegram_video(f"{CACHE_DIR}/{camera}.mp4", frigate_event_to_text(event_data), check_mute_state())

def load_state():
    """Load mute state from file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)
    return {}

def save_state(state):
    """Save state to file"""
    with open(STATE_FILE, "w") as file:
        json.dump(state, file)

def check_mute_state():
    """Check if notifications are muted"""
    state = load_state()
    mute_end = state.get("mute_until", 0)
    return time.time() < mute_end

def handle_telegram_command(command):
    """Process Telegram mute commands"""
    if command == "/muteshort":
        mute_until = time.time() + config.telegram.mute_durations["short"]
    elif command == "/mutelong":
        mute_until = time.time() + config.telegram.mute_durations["long"]
    else:
        return

    save_state({"mute_until": mute_until})
    ulog.debug(f"Notifications muted until {datetime.fromtimestamp(mute_until)}")

def on_connect(client, userdata, flags, reason_code, properties):
    ulog.info(f"Connected MQTT with reason code {reason_code}")
    client.subscribe(config.mqtt.mqtt_topic)

def on_message(client, userdata, msg):
    """MQTT message handler"""
    try:
        payload = json.loads(msg.payload.decode())        

        handle_event(payload)
    except Exception as e:
        ulog.error(f"Error processing MQTT message: {e}")

def main():
    """Main function to start the MQTT listener"""
    ulog.info("Starting Frigate Event Handler...")

    try: 
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,SCRIPT_ID)
        client.on_message = on_message
        client.on_connect = on_connect
        client.connect(config.mqtt.mqtt_broker, config.mqtt.mqtt_port, config.mqtt.mqtt_keepalive)        
        
        send_telegram_message(f"Video notify bot started - {SCRIPT_ID}",True)
        client.loop_forever()
        ulog.info("mqtt loop exited!")
    except Exception as e:
        client.disconnect()
        ulog.error(f"main func/mqtt error {e}")
        raise Exception(f"main func/mqtt error {e}")
if __name__ == "__main__":
    retry_times = 0
    last_retry = datetime.now()

    while True:
        try:
            main()
        except Exception as e:
            ulog.error(f"Main crashed: {e}")                                                
            
            if (last_retry-datetime.now())>timedelta(minutes=config.engine.retry_window): 
                retry_times = 0

            retry_times+=1
            last_retry = datetime.now()

            if retry_times > config.engine.retry_count:
                ulog.error(f"Exceeded {config.engine.retry_count} retries within {config.engine.retry_window}. Stopping.")
                break

            ulog.info(f"Retrying in 5 seconds... ({retry_times} retries in last hour)\n")
            time.sleep(5)
        else:
            ulog.info(f"Main func exited, restart in 5 sec...\n")
            time.sleep(5)
    send_telegram_message(f"Video notify bot finished - {SCRIPT_ID}",True)
    ulog.info("script end...")            


