from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.binary_location = "/usr/bin/chromium-browser"
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=640x480')

service = Service(executable_path="/usr/bin/chromedriver")

driver = webdriver.Chrome(service=service, options=options)
driver.get("http://223.194.166.205:5000/video_feed/")
driver.save_screenshot("screenshot.png")
driver.quit()
