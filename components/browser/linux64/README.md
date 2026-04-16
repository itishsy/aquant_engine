Official Linux browser bundle for Selenium headless scraping.

- Channel: Stable
- Version: 147.0.7727.57
- Source: https://googlechromelabs.github.io/chrome-for-testing/
- Browser download script: `components/browser/linux64/download_linux_chrome.sh`
- Browser binary after download: `components/browser/linux64/chrome-linux64/chrome`
- Driver binary: `components/browser/linux64/chromedriver-linux64/chromedriver`

Linux runtime notes:

- `ChromeDriver` prefers the bundled Linux binaries when they exist.
- Headless flags are applied automatically on Linux: `--headless=new`, `--no-sandbox`, `--disable-gpu`, `--disable-dev-shm-usage`.
- If `chrome-linux64/chrome` is missing, install Chrome with the script in this folder or point `CHROME_BINARY` to a system Chrome/Chromium.
- After downloading, make sure the host has the shared libraries required by Chrome. The bundled `deb.deps` file under `chrome-linux64` lists the common Debian/Ubuntu packages.

Quick start on Linux:

```bash
cd components/browser/linux64
chmod +x download_linux_chrome.sh
./download_linux_chrome.sh
```

Override paths if needed:

- `CHROME_BINARY=/abs/path/to/chrome`
- `CHROMEDRIVER=/abs/path/to/chromedriver`
