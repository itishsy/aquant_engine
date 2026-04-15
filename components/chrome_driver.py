import os
import shutil
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import json
import socket


class ChromeDriver:

    def __init__(self, port=None):
        print("=====chrome driver start=====")
        options = Options()
        chrome_binary = self._find_chrome_binary()
        if chrome_binary is not None:
            options.binary_location = chrome_binary
        options.add_argument("--start-maximized")
        if port is not None:
            if not self.check_port():
                self.driver = None
                return
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver_path = self._find_chromedriver()
        service = Service(driver_path) if driver_path else Service()
        self.driver = webdriver.Chrome(service=service, options=options)

    @staticmethod
    def _find_chrome_binary():
        candidates = [
            os.getenv("CHROME_BINARY"),
            r"D:\Huangsy\chrome\chrome\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Chromium\Application\chrome.exe",
            r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        for cmd in ("chrome", "chrome.exe"):
            resolved = shutil.which(cmd)
            if resolved:
                return resolved
        return None

    @staticmethod
    def _find_chromedriver():
        candidates = [
            os.getenv("CHROMEDRIVER"),
            r"D:\Huangsy\chrome\chromedriver\chromedriver.exe",
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        for cmd in ("chromedriver", "chromedriver.exe"):
            resolved = shutil.which(cmd)
            if resolved:
                return resolved
        return None

    @staticmethod
    def check_port(host="127.0.0.1", port=9222, timeout=5):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False
        except Exception as e:
            print(f"检查出错: {str(e)}")
            return False

    def access(self, url, wait=2):
        self.driver.get(url)
        time.sleep(wait)

    def element(self, xpath, timeout=20, parent=None):
        try:
            if parent is not None:
                xpath = self._xpath(parent) + xpath[1:] if xpath.startswith('.') else xpath

            el = WebDriverWait(self.driver, timeout).until(expected_conditions.presence_of_element_located(
                (By.XPATH, xpath)))
            return el
        except Exception as e:
            print('[Error]', str(e))
            return None

    def elements(self, xpath, timeout=20, parent=None):
        try:
            if parent is not None:
                xpath = self._xpath(parent) + xpath[1:] if xpath.startswith('.') else xpath

            el = WebDriverWait(self.driver, timeout).until(expected_conditions.presence_of_all_elements_located(
                (By.XPATH, xpath)))
            return el
        except Exception as e:
            print('[Error]', str(e))
            return None

    def _xpath(self, element):
        return self.driver.execute_script("""
            function generateXPath(elt) {
                let path = '';
                for (; elt && elt.nodeType === 1; elt = elt.parentNode) {
                    let idx = 1;
                    let sib = elt.previousSibling;
                    while (sib) {
                        if (sib.nodeType === 1 && sib.tagName === elt.tagName) idx++;
                        sib = sib.previousSibling;
                    }
                    path = '/' + elt.tagName.toLowerCase() + (idx > 1 ? `[${idx}]` : '') + path;
                }
                return path;
            }
            return generateXPath(arguments[0]);
        """, element)

    def text(self, xpath, timeout=20, wait=1, parent=None):
        el = self.element(xpath, timeout, parent=parent)
        if el is not None:
            time.sleep(wait)
            if el.text != '':
                return el.text
            else:
                return el.get_attribute("innerText")

    def click(self, xpath, timeout=20, wait=1, parent=None):
        el = self.element(xpath, timeout, parent=parent)
        if el is not None:
            time.sleep(wait)
            el.click()

    def input(self, xpath, value, timeout=20, wait=1, parent=None):
        el = self.element(xpath, timeout, parent=parent)
        if el is not None:
            time.sleep(wait)
            el.clear()
            el.send_keys(value)

    def is_present(self, xpath, parent=None):
        if parent is not None:
            xpath = self._xpath(parent) + xpath[1:] if xpath.startswith('.') else xpath
        ele = self.element(xpath, timeout=1)
        return ele is not None

    def fetch_data(self, url, data='data', is_post=False, post_json=None):
        if is_post:
            # 启用网络跟踪
            self.driver.execute_cdp_cmd("Network.enable", {})

            # 存储响应的字典
            responses = {}

            # 监听响应事件
            def response_listener(event):
                params = event.get("params", {})
                if "requestId" in params and "response" in params:
                    request_id = params["requestId"]
                    responses[request_id] = params["response"]

            # 注册事件监听器（通过性能日志）
            # self.driver.get_log('performance')  # 清除旧日志
            self.driver.execute_script("""
                window.addEventListener('load', function() {
                    console.log('Page loaded, ready for requests');
                });
            """)
            # 构建请求
            request_id = self.driver.execute_cdp_cmd("Network.send", {
                "method": "POST",
                "url": url,
                "headers": {
                    "Content-Type": "application/json"
                },
                "postData": json.dumps(post_json)
            })["requestId"]

            # 等待响应（最多5秒）
            start_time = time.time()
            while request_id not in responses and time.time() - start_time < 5:
                # 处理性能日志获取响应
                logs = self.driver.get_log('performance')
                for entry in logs:
                    try:
                        log = json.loads(entry['message'])
                        message = log.get('message', {})
                        if message.get('method') == 'Network.responseReceived':
                            event_params = message.get('params', {})
                            if event_params.get('requestId') == request_id:
                                responses[request_id] = event_params.get('response', {})
                    except:
                        continue

            # 获取响应体
            if request_id in responses:
                response = responses[request_id]
                try:
                    body = self.driver.execute_cdp_cmd("Network.getResponseBody",
                                                  {"requestId": request_id})
                    print("POST 响应状态码:", response.get("status", "N/A"))
                    print("响应头:", json.dumps(response.get("headers", {}), indent=2))
                    print("响应体:", body.get("body", "No body"))
                except Exception as e:
                    print(f"获取响应体失败: {str(e)}")
            else:
                print("未收到响应")
            json_data = {}
            # print(json_data)
        else:
            self.access(url)
            json_data = json.loads(self.text("//pre"))
        return json_data[data]

    def quit(self):
        print("=====chrome driver quit=====")
        if self.driver is not None:
            self.driver.quit()

