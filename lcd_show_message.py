import time
from lcd_driver import LCD

# Initialize the LCD with specific parameters:
# Raspberry Pi revision, I2C address, and backlight status
# Using Raspberry Pi revision 2 and above, I2C address 0x3f, backlight enabled


# Display messages on the LCD
# name="1120418 CHUN-HSI LEE"

def lcd_show(user):
    lcd = LCD(2, 0x27, True)
    count=30
    while count>0:
        line_1=f'Welcome {user}'
        lcd.message(line_1, 1)
        line_2="Please connect to bluetooth"
        lcd.do(line_2, 2)
        time.sleep(0.2) # 每0.1 秒讀取一次
        count-=0.2
    lcd.clear()

def start():
    lcd = LCD(2, 0x27, True)
    lcd.clear()

def error():
    lcd = LCD(2, 0x27, True)
    lcd.message("Unauthorized", 1)
    lcd.message("user", 2)
    time.sleep(10) # 每0.1 秒讀取一次
    lcd.clear()

# Keep the messages displayed for 5 seconds
# time.sleep(5)

# Clear the LCD display
# if __name__==__main__:
#     lcd_show("asd")
