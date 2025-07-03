# Streamlit-Analytics2 📊

[![PyPi](https://img.shields.io/pypi/v/streamlit-analytics2)](https://pypi.org/project/streamlit-analytics2/)
[![PyPI Downloads](https://static.pepy.tech/badge/streamlit-analytics2)](https://pepy.tech/projects/streamlit-analytics2)
[![PyPI Downloads](https://static.pepy.tech/badge/streamlit-analytics2/month)](https://pepy.tech/projects/streamlit-analytics2)
![Build Status](https://github.com/444B/streamlit-analytics2/actions/workflows/release.yml/badge.svg)
[![CodeFactor](https://www.codefactor.io/repository/github/444b/streamlit-analytics2/badge)](https://www.codefactor.io/repository/github/444b/streamlit-analytics2)
![Coverage](https://codecov.io/gh/444B/streamlit-analytics2/branch/main/graph/badge.svg)
![Known Vulnerabilities](https://snyk.io/test/github/444B/streamlit-analytics2/badge.svg)
[![streamlit-analytics2](https://snyk.io/advisor/python/streamlit-analytics2/badge.svg)](https://snyk.io/advisor/python/streamlit-analytics2)

**Track and visualize user interactions with your Streamlit apps** - no extra code required! 🚀

[**Live Demo**](https://sa2analyticsdemo.streamlit.app/?analytics=on) | [**Documentation**](https://github.com/444B/streamlit-analytics2/wiki) | [**PyPI**](https://pypi.org/project/streamlit-analytics2/)

## ✨ Features

- 📊 **Real-time Analytics** - Track pageviews, user interactions, and session duration
- 🔒 **Privacy-First** - All data stored locally, no external services required
- 📈 **Beautiful Dashboard** - View analytics with `?analytics=on` in your URL
- 💾 **Multiple Storage Options** - Save as JSON or CSV for easy analysis
- 🔐 **Password Protection** - Secure your analytics dashboard
- 🎯 **Zero Config** - Works out of the box with sensible defaults
- 🛠️ **Fully Customizable** - Configure tracking to your needs

## 🚀 Quick Start

### Installation

```bash
pip install streamlit-analytics2
```

### Basic Usage

Just wrap your Streamlit app with `track()`:

```python
import streamlit as st
import streamlit_analytics2 as streamlit_analytics

# Track analytics with just one line!
with streamlit_analytics.track():
    st.title("My Awesome App 🎈")
    
    name = st.text_input("Enter your name")
    if st.button("Say Hello"):
        st.write(f"Hello, {name}! 👋")
```

That's it! Your app now tracks:
- Page views and unique visitors
- Widget interactions (buttons, inputs, etc.)
- Time spent on the app
- User flow patterns

### View Your Analytics

Add `?analytics=on` to your app's URL:
```
http://localhost:8501/?analytics=on
```

## 📸 Screenshots

<details>
<summary>Analytics Dashboard</summary>

![Analytics Dashboard](https://github.com/444B/streamlit-analytics2/wiki/images/dashboard.png)

</details>

<details>
<summary>Setup Screen</summary>

![Setup Screen](https://github.com/444B/streamlit-analytics2/wiki/images/setup.png)

</details>

## 🎯 Examples

### Save Analytics as CSV

```python
# CSV format - great for Excel analysis!
with streamlit_analytics.track(save_to_json="analytics.csv"):
    # Your app code here
```

### Password Protection

```python
# Secure your analytics dashboard
with streamlit_analytics.track(unsafe_password="my_password"):
    # Your app code here
```

### Load Previous Data

```python
# Continue tracking from previous sessions
with streamlit_analytics.track(load_from_json="analytics.json"):
    # Your app code here
```

### Firestore Integration

```python
# Store analytics in Google Firestore
with streamlit_analytics.track(
    firestore_key_file="path/to/key.json",
    firestore_collection_name="analytics"
):
    # Your app code here
```

## ⚙️ Configuration

Streamlit-Analytics2 can be configured through:

1. **Function parameters** (shown above)
2. **Config file** at `.streamlit/analytics.toml`
3. **Environment variables**

### Config File Example

`.streamlit/analytics.toml`:
```toml
[streamlit_analytics2]
enabled = true

[storage]
save = true
type = "csv"  # or "json"
path = "sa2_data/analytics_data.csv"

[access]
password_hash = ""  # SHA256 hash of password
require_auth = true
```

## 📊 What Gets Tracked?

- **Page Metrics**
  - Total page views
  - Unique visitors
  - Session duration
  - Bounce rate

- **User Interactions**
  - Button clicks
  - Form submissions
  - Slider/input changes
  - File uploads

- **Session Data**
  - User journey through the app
  - Time spent on different sections
  - Most used features

## 🔒 Privacy & Security

- **Local Storage Only** - All data stays on your server
- **No External Services** - No data sent to third parties
- **Password Protection** - Secure your analytics dashboard
- **Anonymous Tracking** - No personal information collected
- **Open Source** - Audit the code yourself

## 🛠️ Advanced Features

### Real-time Metrics
```python
from streamlit_analytics2.state import data

# Display live metrics in your app
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Views", data.get('total_pageviews', 0))
with col2:
    st.metric("Active Users", len(data.get('active_users', {})))
with col3:
    st.metric("Total Interactions", data.get('total_script_runs', 0))
```

### Custom Events (Coming Soon)
```python
# Track custom events
streamlit_analytics.track_event("purchase_completed", value=99.99)
streamlit_analytics.track_event("feature_used", feature="advanced_search")
```

## 🔧 Troubleshooting

### Forgot Password?

If you've forgotten your analytics password:

**Option 1:** Delete the config file
```bash
rm .streamlit/analytics.toml
```

**Option 2:** Edit the config file
1. Open `.streamlit/analytics.toml`
2. Set `require_auth = false`
3. Restart your app
4. Set a new password from the config screen

### Common Issues

**Analytics not showing?**
- Make sure you added `?analytics=on` to the URL
- Check that tracking is wrapped around your app code
- Verify the app has write permissions for the data directory

**Data not persisting?**
- Ensure `save = true` in your config
- Check file permissions in the `sa2_data/` directory
- Verify the storage path is correct

## 🤝 Contributing

We love contributions! Whether it's:

- 🐛 Bug reports
- 💡 Feature requests
- 📖 Documentation improvements
- 🔧 Code contributions

Please check our [Contributing Guidelines](https://github.com/444B/streamlit-analytics2/blob/main/.github/CONTRIBUTING.md).

## 📈 Roadmap

- [ ] Custom event tracking
- [ ] Email reports
- [ ] Data export scheduler
- [ ] A/B testing support
- [ ] Funnel analysis
- [ ] Heatmaps
- [ ] Multi-page app support improvements

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built on top of the original [streamlit-analytics](https://github.com/jrieke/streamlit-analytics) by Johannes Rieke.

Special thanks to all [contributors](https://github.com/444B/streamlit-analytics2/graphs/contributors) who have helped improve this project!

---

<p align="center">
  Made with ❤️ by the Streamlit community
</p>

<p align="center">
  <a href="https://github.com/444B/streamlit-analytics2/wiki">📚 Documentation</a> •
  <a href="https://github.com/444B/streamlit-analytics2/issues">🐛 Report Bug</a> •
  <a href="https://github.com/444B/streamlit-analytics2/issues">✨ Request Feature</a>
</p>