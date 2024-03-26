import openactive as oa
import pandas as pd
import pydeck as pdk
import streamlit as st
from datetime import datetime

# --------------------------------------------------------------------------------------------------

st.set_page_config(
    page_title='OpenActive',
    page_icon='https://www.openactive.io/wp-content/themes/open-active-1_3/images/favicon.png',
    layout='wide',
    menu_items={
        'Get help': 'mailto:hello@openactive.io',
        'About': 'Copyright 2024 OpenActive',
    }
)

# Custom styling
# st.markdown(
#     '''
#     <style>
#         [data-testid=stSidebar] {
#             background-color: #253882;
#         }
#     </style>
#     ''',
#     unsafe_allow_html=True
# )

# --------------------------------------------------------------------------------------------------

# Cache feeds to allow access across sessions i.e. different browser tabs
@st.cache_data
def get_feeds():
    return oa.get_feeds()

# --------------------------------------------------------------------------------------------------

def go():
    clear_outputs()
    st.session_state.started = True
    st.session_state.running = True

# --------------------------------------------------------------------------------------------------

def clear():
    clear_inputs()
    clear_outputs()

# --------------------------------------------------------------------------------------------------

def clear_inputs():
    st.session_state.dataset_url_name = None
    st.session_state.feed_url = None

# --------------------------------------------------------------------------------------------------

def clear_outputs():
    if (st.session_state.started):
        st.session_state.started = False
    if (st.session_state.running):
        st.session_state.running = False
    if (st.session_state.got_data):
        st.session_state.opportunities = None
        st.session_state.df = None
        st.session_state.unique_ids = []
        st.session_state.unique_superevent_ids = []
        st.session_state.unique_organizer_names = []
        st.session_state.unique_organizer_names_logos = []
        st.session_state.unique_names = []
        st.session_state.unique_locations = []
        st.session_state.unique_dates = []
        st.session_state.unique_dates_range = ()
        st.session_state.got_data = False
    if (st.session_state.got_filters):
        clear_filters()
        st.session_state.got_filters = False

# --------------------------------------------------------------------------------------------------

def clear_filters():
    st.session_state.filtered_ids = []
    st.session_state.filtered_superevent_ids = []
    st.session_state.filtered_organizers = []
    st.session_state.filtered_names = []
    st.session_state.filtered_locations = []
    st.session_state.filtered_dates_range = st.session_state.unique_dates_range

# --------------------------------------------------------------------------------------------------

def disable_input_controls(default=False):
    return st.session_state.running or default

# --------------------------------------------------------------------------------------------------

def disable_button_clear_filters():
    filtered_multiselects_active = len(
        st.session_state.filtered_ids +
        st.session_state.filtered_superevent_ids +
        st.session_state.filtered_organizers +
        st.session_state.filtered_names +
        st.session_state.filtered_locations
    ) > 0

    if (len(st.session_state.filtered_dates_range)==0):
        filtered_dates_range_active = False
    elif (len(st.session_state.filtered_dates_range)==1):
        filtered_dates_range_active = True
    elif (len(st.session_state.filtered_dates_range)==2):
        filtered_dates_range_active = \
            st.session_state.filtered_dates_range[0]!=st.session_state.unique_dates_range[0] \
        or  st.session_state.filtered_dates_range[1]!=st.session_state.unique_dates_range[1]

    return (not filtered_multiselects_active) and (not filtered_dates_range_active)

# --------------------------------------------------------------------------------------------------

def set_location(location_in):
    try: location_out = [location_in['name'].strip()]
    except: location_out = []

    if ('address' in location_in.keys()):
        for address_parts_type in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']:
            try: address_parts = location_in['address'][address_parts_type].strip().split(',')
            except: address_parts = []
            for address_part in address_parts:
                if (address_part not in location_out):
                    location_out.append(address_part)

    return ',\n'.join(location_out) or None

# --------------------------------------------------------------------------------------------------

def set_datetime(datetime_isoformat):
    try: return datetime.fromisoformat(datetime_isoformat)
    except: return None

# --------------------------------------------------------------------------------------------------

def get_unique(iterable):
    return sorted(set([x for x in iterable if x]))

# --------------------------------------------------------------------------------------------------

if ('initialised' not in st.session_state):
    st.session_state.initialised = False
    st.session_state.started = False
    st.session_state.running = False
    st.session_state.got_data = False
    st.session_state.got_filters = False
    st.session_state.feeds = None
    st.session_state.providers = None

# --------------------------------------------------------------------------------------------------

with st.sidebar:
    st.image('https://openactive.io/brand-assets/openactive-logo-large.png')
    show_info = st.toggle('Info', True)
    st.divider()
    st.selectbox(
        'Data Provider',
        st.session_state.providers or [],
        key='dataset_url_name',
        format_func=lambda x: x[1],
        index=None,
        on_change=clear_outputs,
        disabled=disable_input_controls(),
    )
    st.selectbox(
        'Data Type',
        [feed['url'] for feed in st.session_state.feeds[st.session_state.dataset_url_name[0]]] if st.session_state.dataset_url_name else [],
        key='feed_url',
        format_func=lambda x: x.split('/')[-1],
        index=None,
        on_change=clear_outputs,
        disabled=disable_input_controls(st.session_state.dataset_url_name==None),
    )
    col1, col2 = st.columns([1,4])
    with col1:
        st.button(
            'Go',
            key='button_go',
            on_click=go,
            # type='primary', # Making this primary gives a little flicker when clicked due to the change in disabled state
            disabled=disable_input_controls(st.session_state.feed_url==None),
        )
    with col2:
        st.button(
            'Clear',
            key='button_clear',
            on_click=clear,
            disabled=st.session_state.dataset_url_name==None,
        )

# --------------------------------------------------------------------------------------------------

if show_info:
    st.title('Welcome')
    st.markdown(
        '''
        *The following is extracted from the app [readme file](https://github.com/openactive/openactive-python-streamlit/blob/main/README.md), which contains further information if needed. Use the "Info" toggle in the sidebar to hide or show this message.*

        This [Streamlit](https://streamlit.io/) app is an experimental tool for familiarising all users with OpenActive data, and for helping Python users to get acquainted with the standalone OpenActive Python package, which is available at both [PyPI](https://pypi.org/project/openactive/) and [Conda-Forge](https://anaconda.org/conda-forge/openactive). It allows a user to select and read an OpenActive feed, and displays output in a map (if coordinate data are available), a table, and JSON. Filters are also included to select items based on ID, organiser, name, location and date.

        All code for both [the package](https://github.com/openactive/openactive-python/blob/main/src/openactive/openactive.py) and [this app](https://github.com/openactive/openactive-python-streamlit/blob/main/app.py) is open sourced under the MIT licence, so feel free to make a copy and modify as you like, ensuring that the original licence content is included in anything that you publish. The code has been intentionally kept minimal in order to be digestible, while still providing enough functionality to quickly get past common starting barriers.

        Want an idea for a project? How about taking this app and extending it to read and display a matched pair of feeds together i.e. a Session Series feed with its partner Scheduled Sessions feed. There should be enough information in the package [readme file](https://github.com/openactive/openactive-python/blob/main/README.md) to get you going. See the fully fledged live [OpenActive Visualiser](https://visualiser.openactive.io/) (a JavaScript app) for an idea of how something like this functions in practice.

        Note that it is not recommended to deploy this app on the Streamlit Community Cloud, unless the ingested data is heavily truncated. This is because there is often a lot of data in an OpenActive feed, which could rapidly saturate the memory quota of a cloud deployment, especially if you have multiple concurrent users. It is therefore best to keep this tool for download and use on individual machines using their own memory.

        It will take a couple of minutes to initialise the app with the current list of OpenActive feeds. You can open multiple windows or tabs at the same app location that all use the same base process, so they don't all need to be individually initialised. This allows you to read in and observe multiple datasets simultaneously, if needed.

        To use, simply choose a feed from the sidebar, which is separated into "Data Provider" and "Data Type" fields, and click the "Go" button. Note that the number of pages in a given feed is not known in advance, and so the time required to read all associated pages can vary greatly between one feed and another, from a number of seconds to a number of minutes. If a feed is taking too long to read and you would like to try something else, you can click the "Clear" button at any time to cancel the current task and start again.
        '''
    )

# --------------------------------------------------------------------------------------------------

if (not st.session_state.initialised):
    with st.sidebar:
        # Calling get_feeds() automatically includes a spinner
        st.session_state.feeds = get_feeds()
        st.session_state.providers = sorted(
            [(dataset_url,feeds_dataset[0]['publisherName'] or dataset_url) for dataset_url,feeds_dataset in st.session_state.feeds.items()],
            key=lambda x: x[1].lower()
        )
        st.session_state.initialised = True
        st.rerun()

# --------------------------------------------------------------------------------------------------

if (st.session_state.started):
    with st.sidebar:
        st.divider()
        st.markdown(
            'Feed URL',
            help='This is the location from which the displayed data is sourced. To obtain all of the data, this page and its chain of "next" pages are all visited in turn, until the final page with no further entries is met.'
        )
        st.markdown(st.session_state.feed_url)
        if (    (not st.session_state.running)
            and (not st.session_state.got_data)
        ):
            st.info('No data in this feed')

# --------------------------------------------------------------------------------------------------

if (st.session_state.running):
    with st.sidebar:
        with st.spinner(''):
            st.session_state.opportunities = oa.get_opportunities(st.session_state.feed_url)
            num_items = len(st.session_state.opportunities['items'].keys())

            if (num_items==0):
                st.session_state.running = False
                st.rerun()

            st.session_state.df = pd.DataFrame({
                'JSON': [False] * num_items,
                'ID': st.session_state.opportunities['items'].keys(),
                'Super-event ID': [None] * num_items,
                'Organizer name': [None] * num_items,
                'Organizer logo': [None] * num_items,
                'Name': [None] * num_items,
                'Location': [None] * num_items,
                'Lat': [None] * num_items,
                'Lon': [None] * num_items,
                'Date/time start': [None] * num_items,
                'Date/time end': [None] * num_items,
                'URL': [None] * num_items,
            })

            for item_idx,item in enumerate(st.session_state.opportunities['items'].values()):
                if ('data' in item.keys()):
                    try: st.session_state.df.at[item_idx, 'Super-event ID'] = item['data']['superEvent'].split('/')[-1] # This may be type str or dict, depending on context. We are currently only looking for the str version, and the dict version should be passed over.
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Organizer name'] = item['data']['organizer']['name'].strip()
                    except:
                        try: st.session_state.df.at[item_idx, 'Organizer name'] = item['data']['superEvent']['organizer']['name'].strip()
                        except: pass
                    try: st.session_state.df.at[item_idx, 'Organizer logo'] = item['data']['organizer']['logo']['url'].strip()
                    except:
                        try: st.session_state.df.at[item_idx, 'Organizer logo'] = item['data']['superEvent']['organizer']['logo']['url'].strip()
                        except: pass
                    try: st.session_state.df.at[item_idx, 'Name'] = item['data']['name'].strip()
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Location'] = set_location(item['data']['location'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Lat'] = float(item['data']['location']['geo']['latitude'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Lon'] = float(item['data']['location']['geo']['longitude'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Date/time start'] = set_datetime(item['data']['startDate'].strip())
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Date/time end'] = set_datetime(item['data']['endDate'].strip())
                    except: pass
                    try: st.session_state.df.at[item_idx, 'URL'] = item['data']['url'].strip()
                    except: pass

            st.session_state.df.index = range(1, num_items+1)

            st.session_state.unique_ids = get_unique(st.session_state.df['ID'])
            st.session_state.unique_superevent_ids = get_unique(st.session_state.df['Super-event ID'])
            st.session_state.unique_organizer_names = get_unique(st.session_state.df['Organizer name'])
            st.session_state.unique_organizer_names_logos = get_unique(zip(st.session_state.df['Organizer name'], st.session_state.df['Organizer logo']))
            st.session_state.unique_names = get_unique(st.session_state.df['Name'])
            st.session_state.unique_locations = get_unique(st.session_state.df['Location'])
            st.session_state.unique_dates = get_unique(pd.concat([
                (st.session_state.df['Date/time start'].loc[st.session_state.df['Date/time start'].notnull()]).apply(datetime.date),
                (st.session_state.df['Date/time end'].loc[st.session_state.df['Date/time end'].notnull()]).apply(datetime.date)
            ]))
            st.session_state.unique_dates_range = (
                st.session_state.unique_dates[0],
                st.session_state.unique_dates[-1]
            ) if st.session_state.unique_dates else ()

            st.session_state.df.rename(columns={'Organizer name': 'Organiser'}, inplace=True) # Note British English for display
            del(st.session_state.df['Organizer logo'])

            st.session_state.disabled_columns = ['_index'] + list(st.session_state.df.columns) # Index column editing is disabled by default, but for some reason becomes enabled when a filter selection is made, so we explicitly add it to the disabled list here to ensure against this
            st.session_state.disabled_columns.remove('JSON')

            st.session_state.running = False
            st.session_state.got_data = True
            st.rerun()

# --------------------------------------------------------------------------------------------------

if (st.session_state.got_data):
    with st.sidebar:
        st.divider()
        st.markdown(
            'Filters',
            help='This is intentionally not an adaptive filter system, so choosing one option from one filter will not restrict the other options in other filters, all options will remain with respect to the full dataset. If this wasn\'t so, then filter selection couldn\'t be easily adjusted after the initial selection.'
        )
        st.multiselect(
            'ID',
            st.session_state.unique_ids,
            key='filtered_ids',
            disabled=len(st.session_state.unique_ids)==0,
        )
        st.multiselect(
            'Super-event ID',
            st.session_state.unique_superevent_ids,
            key='filtered_superevent_ids',
            disabled=len(st.session_state.unique_superevent_ids)==0,
        )
        st.multiselect(
            'Organiser', # Note British English for display
            st.session_state.unique_organizer_names,
            key='filtered_organizers',
            disabled=len(st.session_state.unique_organizer_names)==0,
        )
        st.multiselect(
            'Name',
            st.session_state.unique_names,
            key='filtered_names',
            disabled=len(st.session_state.unique_names)==0,
        )
        st.multiselect(
            'Location',
            st.session_state.unique_locations,
            key='filtered_locations',
            disabled=len(st.session_state.unique_locations)==0,
        )
        st.date_input(
            'Date',
            value=st.session_state.unique_dates_range,
            min_value=st.session_state.unique_dates_range[0] if st.session_state.unique_dates_range else datetime.now().date(),
            max_value=st.session_state.unique_dates_range[1] if st.session_state.unique_dates_range else datetime.now().date(),
            key='filtered_dates_range',
            disabled=len(st.session_state.unique_dates_range)==0,
        )
        st.button(
            'Clear',
            key='button_clear_filters',
            on_click=clear_filters,
            disabled=disable_button_clear_filters(),
        )
        st.session_state.got_filters = True

    df_filtered = st.session_state.df
    if (st.session_state.filtered_ids):
        df_filtered = df_filtered.loc[df_filtered['ID'].isin(st.session_state.filtered_ids)]
    if (st.session_state.filtered_superevent_ids):
        df_filtered = df_filtered.loc[df_filtered['Super-event ID'].isin(st.session_state.filtered_superevent_ids)]
    if (st.session_state.filtered_organizers):
        df_filtered = df_filtered.loc[df_filtered['Organiser'].isin(st.session_state.filtered_organizers)]
    if (st.session_state.filtered_names):
        df_filtered = df_filtered.loc[df_filtered['Name'].isin(st.session_state.filtered_names)]
    if (st.session_state.filtered_locations):
        df_filtered = df_filtered.loc[df_filtered['Location'].isin(st.session_state.filtered_locations)]
    if (st.session_state.filtered_dates_range):
        df_filtered = df_filtered.loc[
                (df_filtered['Date/time start'].apply(datetime.date) >= st.session_state.filtered_dates_range[0])
            &   (df_filtered['Date/time end'].apply(datetime.date) <= st.session_state.filtered_dates_range[len(st.session_state.filtered_dates_range)-1])
        ]
    if (len(df_filtered)>0):
        df_filtered.at[df_filtered.index[0], 'JSON'] = True

    if (    len(st.session_state.unique_organizer_names_logos)==1
        and st.session_state.unique_organizer_names_logos[0][1]
    ):
        st.image(st.session_state.unique_organizer_names_logos[0][1], width=150)
        st.divider()

    container_map = st.container()

    st.subheader(
        'Highlights',
        help='This table shows a number of "highlight" fields from the full JSON data for each feed item. Some feeds will have no entries at all for certain table fields, but for consistency the table fields remain fixed for all feeds. Many feeds actually come in pairs, one for super-event data (e.g. Session Series) and one for sub-event data (e.g. Scheduled Sessions), and getting a full picture requires a read of both, as each feed will specialise in different table fields. This app does not allow for two feeds to be read simultaneously in one app session, but you can open another browser window or tab to run a parallel app session to read another feed if needed.'
    )
    st.markdown('{} rows'.format(len(df_filtered)))
    df_edited = st.data_editor(
        df_filtered,
        use_container_width=True,
        disabled=st.session_state.disabled_columns,
        column_config={
            '_index': st.column_config.NumberColumn(label='Row'),
            'JSON': st.column_config.CheckboxColumn(),
            'Lat': st.column_config.NumberColumn(format='%.5f'), # 5 decimal places gives accuracy at the metre level
            'Lon': st.column_config.NumberColumn(format='%.5f'), # 5 decimal places gives accuracy at the metre level
            'Date/time start': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm'),
            'Date/time end': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm'),
            'URL': st.column_config.LinkColumn(),
        },
    )

    if (any(df_edited['JSON'])):
        st.subheader(
            'JSON',
            help='These tabs correspond to the table rows which are selected in the "JSON" column, and they are labelled by table row number. They contain the full JSON data for their associated feed items, only a subset of which is seen in the table.'
        )
        selected_idxs = list(df_edited.index[df_edited['JSON']])
        selected_ids = list(df_edited['ID'][df_edited['JSON']])
        for tab_idx,tab in enumerate(st.tabs([str(x) for x in selected_idxs])):
            with tab:
                st.json(st.session_state.opportunities['items'][selected_ids[tab_idx]])

    # We use [Lon,Lat] rather than [Lat,Lon] in all of the following map code, as this is the required
    # order for PyDeck, so just standardised in all cases of seeing these quantities
    map_data = df_edited.loc[
            df_edited['Lon'].notna()
        &   df_edited['Lat'].notna(),
        ['Lon', 'Lat', 'Location']
    ]

    if (len(map_data)!=0):
        with container_map:
            st.subheader(
                'Geo',
                help='This map shows locations with coordinate data. Zoom in and out with your mouse scroll function, and hover over the pins to show pop-up boxes of the location names and addresses. Note that the initial zoom may not capture all pins that are actually present, so it\'s worth zooming out a bit to check for others that aren\'t initially seen.'
            )
            st.pydeck_chart(pdk.Deck(
                map_style='road',
                # This computed view doesn't create a fully encompassing bounding box for some reason, may need to
                # work something out manually
                initial_view_state=pdk.data_utils.viewport_helpers.compute_view(
                    map_data[['Lon', 'Lat']],
                ),
                # initial_view_state=pdk.ViewState(
                #     longitude=-3.0,
                #     latitude=54.5,
                #     zoom=4.4,
                #     pitch=30,
                # ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        map_data,
                        get_position=['Lon', 'Lat'],
                        pickable=True,
                        filled=True,
                        stroked=True,
                        radius_min_pixels=10,
                        radius_max_pixels=10,
                        line_width_min_pixels=1,
                        line_width_max_pixels=1,
                        get_fill_color=[0, 158, 277],
                        get_line_color=[3, 102, 175],
                        opacity=0.5,
                        elevation_scale=4,
                        elevation_range=[0, 1000],
                    ),
                ],
                tooltip={
                    'text': '{Location}',
                }
            ))
            # The dedicated map widget is just a simplified convenience wrapper around PyDeck, and doesn't have
            # tooltip functionality for e.g. showing location info over individual pins, hence not using this approach
            # st.map(
            #     df_edited.loc[
            #             df_edited['Lon'].notna()
            #         &   df_edited['Lat'].notna(),
            #         ['Lon', 'Lat']
            #     ],
            #     use_container_width=True,
            #     longitude='Lon',
            #     latitude='Lat',
            #     size=200,
            #     color='#009ee3',
            # )
            st.divider()