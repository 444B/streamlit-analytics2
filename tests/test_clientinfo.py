from streamlit_analytics2.clientinfo import browser_family, device_family, os_family

CHROME_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
SAFARI_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
EDGE_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
ANDROID_TABLET = "Mozilla/5.0 (Linux; Android 13; SM-X710) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def test_families():
    assert (
        browser_family(CHROME_MAC),
        os_family(CHROME_MAC),
        device_family(CHROME_MAC),
    ) == ("Chrome", "macOS", "Desktop")
    assert (
        browser_family(SAFARI_IPHONE),
        os_family(SAFARI_IPHONE),
        device_family(SAFARI_IPHONE),
    ) == ("Safari", "iOS", "Mobile")
    assert (browser_family(EDGE_WIN), os_family(EDGE_WIN)) == ("Edge", "Windows")
    assert (browser_family(FIREFOX_LINUX), os_family(FIREFOX_LINUX)) == (
        "Firefox",
        "Linux",
    )
    assert (os_family(ANDROID_TABLET), device_family(ANDROID_TABLET)) == (
        "Android",
        "Tablet",
    )
    assert browser_family("") == "Unknown"
    assert browser_family("Googlebot/2.1") == "Bot"
