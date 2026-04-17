import os
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import urlparse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import json
import socket


class ChromeDriver:
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/147.0.7727.57 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    def __init__(self, port=None):
        print("=====chrome driver start=====")
        self.driver = None
        self.virtual_display = None
        self.user_data_dir = None
        self.headless = self._is_headless_enabled()
        if port is not None and not self.check_port():
            return

        driver_path = self._find_chromedriver()
        if driver_path:
            self._ensure_executable(driver_path)

        launch_plans = self._build_launch_plans()
        last_error = None
        for launch_plan in launch_plans:
            self._stop_virtual_display()
            self._cleanup_user_data_dir()
            options = self._build_options(
                port,
                use_legacy_headless=launch_plan["use_legacy_headless"],
                headless=launch_plan["headless"],
            )
            try:
                print("chrome launch mode:", self._describe_launch_plan(launch_plan))
                if launch_plan["use_virtual_display"]:
                    self._start_virtual_display()
                if driver_path:
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=options)
                else:
                    self.driver = webdriver.Chrome(options=options)
                self.driver.set_page_load_timeout(30)
                self.driver.set_script_timeout(20)
                self.access("data:,", wait=0)
                return
            except Exception as ex:
                last_error = ex
                if self.driver is not None:
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    self.driver = None
        self._stop_virtual_display()
        self._cleanup_user_data_dir()
        print("chrome driver unavailable:", last_error)

    @staticmethod
    def _component_dir():
        return os.path.join(os.path.dirname(__file__), "browser", "linux64")

    def _build_launch_plans(self):
        if os.name != "posix":
            return [{"headless": self.headless, "use_legacy_headless": False, "use_virtual_display": False}]

        plans = []
        if self.headless:
            plans.append({"headless": True, "use_legacy_headless": False, "use_virtual_display": False})
            plans.append({"headless": True, "use_legacy_headless": True, "use_virtual_display": False})
        if self._should_use_virtual_display():
            plans.append({"headless": False, "use_legacy_headless": False, "use_virtual_display": True})
        elif not self.headless:
            plans.append({"headless": False, "use_legacy_headless": False, "use_virtual_display": False})
        return plans

    @staticmethod
    def _describe_launch_plan(launch_plan):
        if launch_plan["use_virtual_display"]:
            return "xvfb-visible"
        if launch_plan["headless"]:
            return "legacy-headless" if launch_plan["use_legacy_headless"] else "headless-new"
        return "visible"

    def _build_options(self, port=None, use_legacy_headless=False, headless=True):
        options = Options()
        options.page_load_strategy = "eager"
        chrome_binary = ChromeDriver._find_chrome_binary()
        if chrome_binary is not None:
            options.binary_location = chrome_binary
        options.add_argument("--user-data-dir={}".format(self._make_user_data_dir()))
        ChromeDriver._apply_runtime_options(
            options,
            port,
            use_legacy_headless=use_legacy_headless,
            headless=headless
        )
        if port is not None:
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        return options

    @staticmethod
    def _apply_runtime_options(options, port, use_legacy_headless=False, headless=True):
        options.add_argument("--start-maximized")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-software-rasterizer")
        if os.name == "posix":
            if headless:
                options.add_argument("--headless" if use_legacy_headless else "--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
        elif port is not None:
            options.add_argument("--disable-dev-shm-usage")

    def _should_use_virtual_display(self):
        if os.name != "posix":
            return False
        if os.getenv("DISPLAY"):
            return False
        return shutil.which("Xvfb") is not None

    @staticmethod
    def _is_headless_enabled():
        value = os.getenv("CHROME_HEADLESS", "true").strip().lower()
        return value not in ("0", "false", "no", "off")

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

    def _make_user_data_dir(self):
        if self.user_data_dir is None:
            self.user_data_dir = tempfile.mkdtemp(prefix="aquant-chrome-")
        return self.user_data_dir

    def _cleanup_user_data_dir(self):
        if self.user_data_dir:
            shutil.rmtree(self.user_data_dir, ignore_errors=True)
            self.user_data_dir = None

    def _start_virtual_display(self):
        if self.virtual_display is not None:
            return
        xvfb = shutil.which("Xvfb")
        if not xvfb:
            raise RuntimeError("Xvfb not found for virtual display")

        last_error = None
        for display_num in range(99, 110):
            display = ":{}".format(display_num)
            env = os.environ.copy()
            env["DISPLAY"] = display
            try:
                self.virtual_display = subprocess.Popen(
                    [xvfb, display, "-screen", "0", "1920x1080x24", "-nolisten", "tcp"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env,
                )
                time.sleep(1)
                if self.virtual_display.poll() is None:
                    os.environ["DISPLAY"] = display
                    return
                last_error = RuntimeError("Xvfb exited immediately on {}".format(display))
            except Exception as ex:
                last_error = ex
        raise RuntimeError("Unable to start Xvfb: {}".format(last_error))

    def _stop_virtual_display(self):
        if self.virtual_display is not None:
            try:
                self.virtual_display.terminate()
                self.virtual_display.wait(timeout=5)
            except Exception:
                try:
                    self.virtual_display.kill()
                except Exception:
                    pass
            self.virtual_display = None

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
        self._ensure_driver()
        try:
            self.driver.get(url)
            time.sleep(wait)
        except TimeoutException:
            print("[Warn] page load timeout:", url)
            try:
                self.driver.execute_script("window.stop();")
            except WebDriverException:
                pass
        except WebDriverException as ex:
            print("[Error] browser access failed:", url, ex)
            raise

    def element(self, xpath, timeout=20, parent=None):
        self._ensure_driver()
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
        self._ensure_driver()
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
        self._ensure_driver()
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
        self._ensure_driver()
        self._ensure_context(url)
        method = "POST" if is_post else "GET"
        payload = self.driver.execute_async_script("""
            const url = arguments[0];
            const method = arguments[1];
            const body = arguments[2];
            const callback = arguments[3];
            const headers = {
                "Accept": "application/json,text/plain,*/*"
            };
            if (body !== null) {
                headers["Content-Type"] = "application/json";
            }

            fetch(url, {
                method,
                headers,
                credentials: "include",
                body: body === null ? undefined : JSON.stringify(body),
                redirect: "follow"
            }).then(async (response) => {
                const text = await response.text();
                callback({
                    ok: response.ok,
                    status: response.status,
                    statusText: response.statusText,
                    text
                });
            }).catch((error) => {
                callback({
                    ok: false,
                    error: String(error)
                });
            });
        """, url, method, post_json if is_post else None)

        if not payload.get("ok"):
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            raise RuntimeError("HTTP {} {}".format(payload.get("status"), payload.get("statusText", "")))

        json_data = json.loads(payload.get("text") or "{}")
        return json_data[data]

    @staticmethod
    def _context_url(url):
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if "10jqka.com.cn" in host:
            return "https://dq.10jqka.com.cn/"
        elif "cls.cn" in host:
            return "https://www.cls.cn/"
        elif "taoguba.com.cn" in host:
            return "https://www.taoguba.com.cn/"
        elif "xueqiu.com" in host:
            return "https://xueqiu.com/"
        return "{}://{}/".format(parsed.scheme, parsed.netloc)

    def _ensure_context(self, url):
        context_url = self._context_url(url)
        current = ""
        try:
            current = self.driver.current_url or ""
        except Exception:
            current = ""
        if not current.startswith(context_url):
            self.access(context_url, wait=1)

    def _ensure_driver(self):
        if self.driver is None:
            if os.name == "posix" and not os.getenv("DISPLAY") and not self.headless and not self._should_use_virtual_display():
                raise RuntimeError("Chrome driver unavailable: DISPLAY missing and Xvfb not installed")
            raise RuntimeError("Chrome driver unavailable")

    def quit(self):
        print("=====chrome driver quit=====")
        if self.driver is not None:
            try:
                self.driver.quit()
            finally:
                self.driver = None
        self._stop_virtual_display()
        self._cleanup_user_data_dir()

