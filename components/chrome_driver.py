import os
import shutil
import stat
import requests
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
        self.driver = None
        options = Options()
        chrome_binary = self._find_chrome_binary()
        if chrome_binary is not None:
            options.binary_location = chrome_binary
        self._apply_runtime_options(options, port)
        if port is not None:
            if not self.check_port():
                self.driver = None
                return
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver_path = self._find_chromedriver()
        try:
            if driver_path:
                self._ensure_executable(driver_path)
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
        except Exception as ex:
            print("chrome driver unavailable:", ex)
            self.driver = None

    @staticmethod
    def _component_dir():
        return os.path.join(os.path.dirname(__file__), "browser", "linux64")

    @staticmethod
    def _apply_runtime_options(options, port):
        options.add_argument("--start-maximized")
        if os.name == "posix":
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
        elif port is not None:
            options.add_argument("--disable-dev-shm-usage")

    @staticmethod
    def _find_chrome_binary():
        candidates = [os.getenv("CHROME_BINARY")]
        if os.name == "posix":
            candidates.append(os.path.join(ChromeDriver._component_dir(), "chrome-linux64", "chrome"))
        else:
            candidates.extend([
                r"D:\Huangsy\chrome\chrome\chrome.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\Chromium\Application\chrome.exe",
                r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
            ])
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        commands = ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser") if os.name == "posix" else ("chrome", "chrome.exe")
        for cmd in commands:
            resolved = shutil.which(cmd)
            if resolved:
                return resolved
        return None

    @staticmethod
    def _find_chromedriver():
        candidates = [os.getenv("CHROMEDRIVER")]
        if os.name == "posix":
            candidates.append(os.path.join(ChromeDriver._component_dir(), "chromedriver-linux64", "chromedriver"))
        else:
            candidates.append(r"D:\Huangsy\chrome\chromedriver\chromedriver.exe")
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        commands = ("chromedriver",) if os.name == "posix" else ("chromedriver", "chromedriver.exe")
        for cmd in commands:
            resolved = shutil.which(cmd)
            if resolved:
                return resolved
        return None

    @staticmethod
    def _ensure_executable(path):
        if os.name != "posix" or not path or not os.path.exists(path):
            return
        mode = os.stat(path).st_mode
        os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

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
        if self.driver is None:
            return
        self.driver.get(url)
        time.sleep(wait)

    def element(self, xpath, timeout=20, parent=None):
        if self.driver is None:
            return None
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
        if self.driver is None:
            return None
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
        if self.driver is None:
            return ''
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
        if self.driver is None:
            if is_post:
                response = requests.post(url, json=post_json, timeout=15)
            else:
                response = requests.get(url, timeout=15)
            response.raise_for_status()
            json_data = response.json()
            return json_data[data] if data is not None else json_data

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
            text = self.text("//pre")
            json_data = json.loads(text) if text else {}
        return json_data[data]

    def quit(self):
        print("=====chrome driver quit=====")
        if self.driver is not None:
            self.driver.quit()

