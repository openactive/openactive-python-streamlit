<img src='https://openactive.io/brand-assets/openactive-logo-large.png' width='500'>

[![License](http://img.shields.io/:license-mit-blue.svg)](https://opensource.org/license/mit/)

This [Streamlit](https://streamlit.io/) app is an experimental tool for familiarising all users with OpenActive data, and for helping Python users to get acquainted with the standalone OpenActive Python package, which is available at both [PyPI](https://pypi.org/project/openactive/) and [Conda-Forge](https://anaconda.org/conda-forge/openactive). It allows a user to select and read an OpenActive feed, and displays output in a map (if coordinate data are available), a table, and JSON. Filters are also included to select items based on ID, organiser, name, location and date.

All code for both [the package](https://github.com/openactive/openactive-python/blob/main/src/openactive/openactive.py) and [this app](https://github.com/openactive/openactive-python-streamlit/blob/main/app.py) is open sourced under the MIT licence, so feel free to make a copy and modify as you like, ensuring that the original licence content is included in anything that you publish. The code has been intentionally kept minimal in order to be digestible, while still providing enough functionality to quickly get past common starting barriers.

Want an idea for a project? How about taking this app and extending it to read and display a matched pair of feeds together i.e. a Session Series feed with its partner Scheduled Sessions feed. There should be enough information in the package [readme file](https://github.com/openactive/openactive-python/blob/main/README.md) to get you going. See the fully fledged live [OpenActive Visualiser](https://visualiser.openactive.io/) (a JavaScript app) for an idea of how something like this functions in practice.

Note that it is not recommended to deploy this app on the Streamlit Community Cloud, unless the ingested data is heavily truncated. This is because there is often a lot of data in an OpenActive feed, which could rapidly saturate the memory quota of a cloud deployment, especially if you have multiple concurrent users. It is therefore best to keep this tool for download and use on individual machines using their own memory.

# Installation

It is recommended to first set up a virtual environment for your `openactive` project, to ensure that it's isolated from your base environment and runs as intended. The only thing that must be installed in your base environment is some package for generating virtual environments, such as `virtualenv`:

```
$ pip install virtualenv
```

Now clone this repo and change into the new project folder that will be created:

```
$ git clone https://github.com/openactive/openactive-python-streamlit.git
$ cd openactive-python-streamlit
```

Then, in this new project folder, create and initialise a new virtual environment as follows (`virt` and `venv` are typical names, but you can choose something else if needed):

```
$ virtualenv virt
$ source virt/bin/activate
(virt) $
```

Now install the app requirements in the virtual environment, and you're good to go:

```
(virt) $ pip install -r requirements.txt
```

When you're done working in the virtual environment, deactivate it by:

```
(virt) $ deactivate
```

# Usage

In an environment with the OpenActive Streamlit app requirements installed, run the app by:

```
(virt) $ streamlit run app.py
```

This should open a new window in your default web browser, but if not then open your browser and go to [http://localhost:8501/](http://localhost:8501/). It will take a couple of minutes to initialise the app with the current list of OpenActive feeds. You can open multiple windows or tabs at the same app location that all use the same base process, so they don't all need to be individually initialised. This allows you to read in and observe multiple datasets simultaneously, if needed.

To use, simply choose a feed from the sidebar, which is separated into "Data Provider" and "Data Type" fields, and click the "Go" button. Note that the number of pages in a given feed is not known in advance, and so the time required to read all associated pages can vary greatly between one feed and another, from a number of seconds to a number of minutes. If a feed is taking too long to read and you would like to try something else, you can click the "Clear" button at any time to cancel the current task and start again.

Upon a successful read of a selected feed, you will see something like the following:

![OpenActive Python Streamlit app running in a web browser](images/openactive-python-streamlit.png)

The exact sections that are seen will depend on the feed content. For example, if there is a single unique logo then a logo will be displayed, and if there is coordinate data then a map will be displayed. There will always be a table, which shows a number of "highlight" fields from the full JSON data for each feed item. The first row will be selected for full JSON display by default, and the JSON display section can be found below the table. Selecting more rows in the table will add more tabs to the JSON display section, labelled by table row number.

Some feeds will have no entries at all for certain table fields, but for consistency the table fields remain fixed for all feeds. Many feeds actually come in pairs, one for super-event data (e.g. Session Series) and one for sub-event data (e.g. Scheduled Sessions), and getting a full picture requires a read of both, as each feed will specialise in different table fields. This app does not allow for two feeds to be read simultaneously in one app session, but you can open another browser window or tab to run a parallel app session to read another feed if needed.

The table rows can be reordered by clicking on the column headings. Also, with your mouse pointer hovering over the table you will see three icons in the top-right, allowing you to: (1) download the data as CSV, (2) search for a particular term, and (3) expand the table to full screen.

If there is coordinate data in the selected feed and you see a map, then you can click and hold to pan, scroll to zoom, and hover over the pins to show pop-up boxes of the location names and addresses. Note that the initial zoom may not capture all pins that are actually present, so it's worth zooming out a bit to check for others that aren't initially seen.

To focus on feed items with certain characteristics from the table fields, select as many options from as many filters as you like in the sidebar. Filters are still shown but are disabled when they have no options. To change the selection, you can clear the filters individually or altogether with the "Clear" button.

When you're done working with the app, deactivate it by pressing Ctrl-c in the terminal where it's running.