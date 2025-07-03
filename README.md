# Streamlit-Analytics2

[![PyPi](https://img.shields.io/pypi/v/streamlit-analytics2)](https://pypi.org/project/streamlit-analytics2/)
[![PyPI Downloads](https://static.pepy.tech/badge/streamlit-analytics2)](https://pepy.tech/projects/streamlit-analytics2)
[![PyPI Downloads](https://static.pepy.tech/badge/streamlit-analytics2/month)](https://pepy.tech/projects/streamlit-analytics2)
![Build Status](https://github.com/444B/streamlit-analytics2/actions/workflows/release.yml/badge.svg)

[![CodeFactor](https://www.codefactor.io/repository/github/444b/streamlit-analytics2/badge)](https://www.codefactor.io/repository/github/444b/streamlit-analytics2)
![Coverage](https://codecov.io/gh/444B/streamlit-analytics2/branch/main/graph/badge.svg)

![Known Vulnerabilities](https://snyk.io/test/github/444B/streamlit-analytics2/badge.svg)
[![streamlit-analytics2](https://snyk.io/advisor/python/streamlit-analytics2/badge.svg)](https://snyk.io/advisor/python/streamlit-analytics2)


## Check it out here! [👉 Demo 👈](https://sa2analyticsdemo.streamlit.app/?analytics=on)

Streamlit Analytics2 is an actively maintained, powerful tool for tracking user interactions and gathering insights from your [Streamlit](https://streamlit.io/) applications. With just a few lines of code, you can gain insight into how your app is being used and making data-driven decisions to improve your app.

> [!Note]
> This fork is confirmed to fix the deprecation ```st.experimental_get_query_params``` alerts.    [Context](https://docs.streamlit.io/library/api-reference/utilities/st.experimental_get_query_params)  
> It also resolves 41 security issues that exist in the upstream dependencies (4 Critical, 13 High, 21 Moderate, 3 Low) as of Dec 29th 2024


## Getting Started

1. Install the package:
   ```
   pip install streamlit-analytics2
   ```

2. Import and initialize the tracker in your Streamlit script:
   ```python
   import streamlit as st
   import streamlit_analytics2 as streamlit_analytics

   with streamlit_analytics.track():
      st.write("Hello, World!")
      st.button("Click me")
   ```

3. Run your Streamlit app and append `?analytics=on` to the URL to view the analytics dashboard.


## Getting the most out of Streamlit Analytics2

Be sure to check out our [Wiki](https://github.com/444B/streamlit-analytics2/wiki) for even more ways to configure the application.
Some features include:
- Storing data to json, CSV or Firestore
- Gathering Session state details based on randomized UUIDs
- Setting passwords for your analytics dashboards
- Migration guides
We welcome contributions to the Wiki as well!


## Contributing

We're actively seeking additional maintainers to help improve Streamlit Analytics2. If you're interested in contributing, please check out our [Contributing Guidelines](https://github.com/444B/streamlit-analytics2/blob/main/.github/CONTRIBUTING.md) to get started. We welcome pull requests, bug reports, feature requests, and any other feedback.


## Upcoming Features

We're currently working on a major release that will introduce exciting new features and enhancements:

- Multi-page tracking: Monitor user interactions across multiple pages of your Streamlit app.
- Improved metrics accuracy: Get more precise and reliable usage metrics.
- Flexible data formats: Choose between CSV or JSON for storing and exporting analytics data.
- Customization screen: Easily configure and customize the analytics settings through a user-friendly interface.

Stay tuned for more updates and join our [community](https://github.com/444B/streamlit-analytics2/discussions) to be part of shaping the future of Streamlit Analytics2!


## Multipage tracking status:
|Method|Status|
|-|-|
|main.py|✅ (Works)|
|[pages/ directory](https://docs.streamlit.io/develop/concepts/multipage-apps/pages-directory)|❌ (Not Working)|
|[st.Page + st.navigation](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)|🤷 (Checking)|


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
