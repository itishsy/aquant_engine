# aquant_engine
aquant的engine
保留了 Linux 无头模式所需的 chromedriver、抓取代码改动和说明文档，同时把超大 Chrome 本体改成了项目内下载脚本 components/browser/linux64/download_linux_chrome.sh，这样既能在 Linux 上补齐浏览器，又不会撞上 GitHub 的 100MB 限制。你现在从 GitHub 拉代码后，在 Linux 上执行这个脚本即可下载官方 Chrome for Testing，然后 fetcher 会优先使用项目内的驱动和浏览器路径。
