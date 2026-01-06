import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import subprocess
import json
import datetime
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import lcd_show_message
from gpiozero import LED

AWS_ENDPOINT = "a1gvp5jatx03n0-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "RPi_Smart_Lab"
TOPIC = "topic_1"
PATH_TO_ROOT = "certs/Amazon-Root-CA-1.pem"
PATH_TO_CERT = "certs/device.pem.crt"
PATH_TO_KEY = "certs/private.pem.key"\

bibi = LED(21)


def init_aws():
    if not os.path.exists(PATH_TO_ROOT) or not os.path.exists(PATH_TO_CERT) or not os.path.exists(PATH_TO_KEY):
        print("[錯誤] 憑證檔案路徑不正確，請檢查 certs 資料夾")
        return None

    client = AWSIoTMQTTClient(CLIENT_ID)
    client.configureEndpoint(AWS_ENDPOINT, 8883)
    client.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)

    client.configureAutoReconnectBackoffTime(1, 32, 20)
    client.configureOfflinePublishQueueing(-1)
    client.configureDrainingFrequency(2)
    client.configureConnectDisconnectTimeout(10)
    client.configureMQTTOperationTimeout(5)

    try:
        print("正在連線至 AWS...")
        client.connect()
        print("AWS 連線成功！")
        return client
    except Exception as e:
        print(f"AWS 連線失敗: {e}")
        return None


def upload_data(client, user_id, status_type):
    """
    status_type: "Check-in" 或 "Check-out"
    """
    if client is None:
        return

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    payload = {
        "time": current_time,
        "status": status_type,
        "user": user_id
    }

    try:
        client.publish(TOPIC, json.dumps(payload), 1)
        print(f"[AWS] 上傳成功: {payload}")
    except Exception as e:
        print(f"[AWS] 上傳失敗: {e}")


with open("data/source.json", "r") as file:
    data = json.load(file)

reader = SimpleMFRC522()
mqtt_client = init_aws()

print("---------------------------------")
print("程式已啟動，請將卡片靠近 RC522...")
print("按 Ctrl + C 可以結束程式")
print("---------------------------------")


def is_connected(user, mac_address):
    bibi.on()
    time.sleep(0.5)
    bibi.off()
    lcd_show_message.lcd_show(user)
    try:
        # 呼叫 bluetoothctl info 指令
        while 1:
            result = subprocess.run(
                ["bluetoothctl", "info", mac_address],
                capture_output=True,
                text=True
            )

            if "Connected: yes" in result.stdout:
                time.sleep(2)
                continue
            else:
                bibi.on()
                time.sleep(3)
                bibi.off()
                break

    except Exception as e:
        print(f"發生錯誤: {e}")
        return False

lcd_show_message.start()
try:
    while True:
        id, text = reader.read()
        user_id_str = str(id)

        print(f"讀取成功!")
        print(f"卡片 ID: {id}")

        if user_id_str in data:
            # 1. 驗證成功，上傳 Check-in
            print(f"歡迎 {user_id_str}，已 Check-in")
            upload_data(mqtt_client, data[user_id_str]["USER"], "Check-in")

            # 2. 進入藍牙監控
            is_connected(data[user_id_str]["USER"], data[user_id_str]["MAC"])

            # 3. 藍牙斷線後，程式執行到這裡，上傳 Check-out
            print(f"使用者 {user_id_str} 已離場，上傳 Check-out")
            upload_data(mqtt_client, data[user_id_str]["USER"], "Check-out")

            print("---------------------------------")
            print("等待下一位使用者...")
            time.sleep(2)

        else:
            print("---------------------------------")
            print("卡片未經授權，等待下一次讀取 (2秒後)...")
            bibi.on()
            time.sleep(1)
            bibi.off()
            lcd_show_message.error()

except KeyboardInterrupt:
    print("\n程式已停止")

finally:
    if mqtt_client:
        mqtt_client.disconnect()
    GPIO.cleanup()
