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

def go(feed_url=None):
    st.session_state.running = True
    clear_outputs()

# --------------------------------------------------------------------------------------------------

def clear():
    st.session_state.running = False
    clear_inputs()
    clear_outputs()

# --------------------------------------------------------------------------------------------------

def clear_inputs():
    st.session_state.dataset_url_name = None
    st.session_state.feed_url = None

# --------------------------------------------------------------------------------------------------

def clear_outputs():
    st.session_state.opportunities = None
    st.session_state.df = None
    st.session_state.df_filtered = None
    st.session_state.df_edited = None
    st.session_state.unique_ids = []
    st.session_state.unique_superevent_ids = []
    st.session_state.unique_organizer_names = []
    st.session_state.unique_names = []
    st.session_state.unique_locations = []
    st.session_state.unique_dates = []
    st.session_state.unique_dates_range = ()
    clear_filters()

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
    return True if st.session_state.running else default

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

    return not filtered_multiselects_active and not filtered_dates_range_active

# --------------------------------------------------------------------------------------------------

def set_location(location_in):
    try: location_out = location_in['name'].strip()
    except: location_out = ''

    if ('address' in location_in.keys()):
        for address_part in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']:
            try: address_part_found = location_in['address'][address_part].strip()
            except: address_part_found = ''
            if (address_part_found):
                location_out += (',\n' if len(location_out)>0 else '') + address_part_found

    return location_out or None

# --------------------------------------------------------------------------------------------------

def set_datetime(datetime_isoformat):
    try: return datetime.fromisoformat(datetime_isoformat).strftime('%Y-%m-%d %H:%M')
    except: return None

# --------------------------------------------------------------------------------------------------

def set_date(datetime_isoformat):
    try: return datetime.fromisoformat(datetime_isoformat).date().strftime('%Y-%m-%d')
    except: return None

# --------------------------------------------------------------------------------------------------

def get_unique(datalist):
    return sorted(set([x for x in datalist if type(x)==str and x.strip()]))

# --------------------------------------------------------------------------------------------------

if ('initialised' not in st.session_state):
    st.session_state.initialised = False
    st.session_state.feeds = None
    st.session_state.providers = None
    clear()
elif (not st.session_state.feed_url):
    clear_outputs()

# --------------------------------------------------------------------------------------------------

with st.sidebar:
    st.image('https://openactive.io/brand-assets/openactive-logo-large.png')
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
            args=[st.session_state.feed_url],
            # type='primary', # Making this primary gives a little flicker when clicked due to the change in disabled state
            disabled=disable_input_controls(st.session_state.feed_url==None),
        )
    with col2:
        st.button(
            'Clear',
            key='button_clear_inputs',
            on_click=clear,
            disabled=st.session_state.dataset_url_name==None,
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

if (    st.session_state.running
    or  st.session_state.opportunities
):
    with st.sidebar:
        st.divider()
        st.write('Source')
        st.write(st.session_state.feed_url)

# --------------------------------------------------------------------------------------------------

if (st.session_state.running):
    with st.sidebar:
        with st.spinner(''):
            st.session_state.opportunities = oa.get_opportunities(st.session_state.feed_url)
            num_items = len(st.session_state.opportunities['items'].keys())

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
                    try: st.session_state.df.at[item_idx, 'Super-event ID'] = item['data']['superEvent'].split('/')[-1]
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Organizer name'] = item['data']['organizer']['name']
                    except:
                        try: st.session_state.df.at[item_idx, 'Organizer name'] = item['data']['superEvent']['organizer']['name']
                        except: pass
                    try: st.session_state.df.at[item_idx, 'Organizer logo'] = item['data']['organizer']['logo']['url']
                    except:
                        try: st.session_state.df.at[item_idx, 'Organizer logo'] = item['data']['superEvent']['organizer']['logo']['url']
                        except: pass
                    try: st.session_state.df.at[item_idx, 'Name'] = item['data']['name']
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Location'] = set_location(item['data']['location'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Lat'] = float(item['data']['location']['geo']['latitude'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Lon'] = float(item['data']['location']['geo']['longitude'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Date/time start'] = set_datetime(item['data']['startDate'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Date/time end'] = set_datetime(item['data']['endDate'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'URL'] = item['data']['url']
                    except: pass

            st.session_state.df.index = range(1, num_items+1)

            st.session_state.unique_ids = get_unique(st.session_state.df['ID'])
            st.session_state.unique_superevent_ids = get_unique(st.session_state.df['Super-event ID'])
            st.session_state.unique_organizer_names = get_unique(st.session_state.df['Organizer name'])
            st.session_state.unique_names = get_unique(st.session_state.df['Name'])
            st.session_state.unique_locations = get_unique(st.session_state.df['Location'])
            st.session_state.unique_dates = get_unique(pd.concat([st.session_state.df['Date/time start'].apply(set_date), st.session_state.df['Date/time end'].apply(set_date)]))
            st.session_state.unique_dates_range = (
                datetime.fromisoformat(st.session_state.unique_dates[0]).date(),
                datetime.fromisoformat(st.session_state.unique_dates[-1]).date()
            ) if st.session_state.unique_dates else ()
            st.session_state.filtered_dates_range = st.session_state.unique_dates_range # We need to initialise this here, for some reason it doesn't do it when the associated filter widget is created

            st.session_state.disabled_columns = ['_index'] + list(st.session_state.df.columns) # Index column editing is disabled by default, but for some reason becomes enabled when a filter selection is made, so we explicitly add it to the disabled list here to ensure against this
            st.session_state.disabled_columns.remove('JSON')

            st.session_state.running = False
            st.rerun()

# --------------------------------------------------------------------------------------------------

if (st.session_state.opportunities):
    with st.sidebar:
        st.divider()
        st.write('Filters')
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
            'Organizer',
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

    df_filtered = st.session_state.df
    if (st.session_state.filtered_ids):
        df_filtered = df_filtered.loc[df_filtered['ID'].isin(st.session_state.filtered_ids)]
    if (st.session_state.filtered_superevent_ids):
        df_filtered = df_filtered.loc[df_filtered['Super-event ID'].isin(st.session_state.filtered_superevent_ids)]
    if (st.session_state.filtered_organizers):
        df_filtered = df_filtered.loc[df_filtered['Organizer name'].isin(st.session_state.filtered_organizers)]
    if (st.session_state.filtered_names):
        df_filtered = df_filtered.loc[df_filtered['Name'].isin(st.session_state.filtered_names)]
    if (st.session_state.filtered_locations):
        df_filtered = df_filtered.loc[df_filtered['Location'].isin(st.session_state.filtered_locations)]
    if (st.session_state.filtered_dates_range):
        df_filtered = df_filtered.loc[
                (df_filtered['Date/time start'].apply(datetime.fromisoformat).apply(datetime.date) >= st.session_state.filtered_dates_range[0])
            &   (df_filtered['Date/time end'].apply(datetime.fromisoformat).apply(datetime.date) <= st.session_state.filtered_dates_range[len(st.session_state.filtered_dates_range)-1])
        ]
    if (len(df_filtered)>0):
        df_filtered.at[df_filtered.index[0], 'JSON'] = True

    container_map = st.container()

    st.subheader('Highlights')
    st.write('{} rows'.format(len(df_filtered)))
    st.session_state.df_edited = st.data_editor(
        df_filtered,
        use_container_width=True,
        disabled=st.session_state.disabled_columns,
        column_config={
            '_index': st.column_config.NumberColumn(label='Row'),
            'JSON': st.column_config.CheckboxColumn(),
            'Organizer logo': st.column_config.ImageColumn(),
            'Lat': st.column_config.NumberColumn(format='%.5f'), # 5 decimal places gives accuracy at the metre level
            'Lon': st.column_config.NumberColumn(format='%.5f'), # 5 decimal places gives accuracy at the metre level
            # It is simpler to leave the time columns as strings rather than convert to DateTime objects, which
            # has issues when the strings are empty, so the following lines aren't needed but are left here to
            # warn against a change that may take a while to figure out and ultimately lead to the same conclusion
            #   'Date/time start': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm'),
            #   'Date/time end': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm'),
            'URL': st.column_config.LinkColumn(),
        },
    )

    if (any(st.session_state.df_edited['JSON'])):
        st.subheader('JSON')
        selected_idxs = list(st.session_state.df_edited.index[st.session_state.df_edited['JSON']].values.astype(str))
        selected_ids = list(st.session_state.df_edited['ID'][st.session_state.df_edited['JSON']].values.astype(str))
        for tab_idx,tab in enumerate(st.tabs(selected_idxs)):
            with tab:
                st.json(st.session_state.opportunities['items'][selected_ids[tab_idx]])

    # We use [Lon,Lat] rather than [Lat,Lon] in all of the following map code, as this is the required
    # order for PyDeck, so just standardised in all cases of seeing these quantities
    map_data = st.session_state.df_edited.loc[
            st.session_state.df_edited['Lon'].notna()
        &   st.session_state.df_edited['Lat'].notna(),
        ['Lon', 'Lat', 'Location']
    ]

    if (len(map_data)!=0):
        with container_map:
            st.subheader('Geo')
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
            #     st.session_state.df_edited.loc[
            #             st.session_state.df_edited['Lon'].notna()
            #         &   st.session_state.df_edited['Lat'].notna(),
            #         ['Lon', 'Lat']
            #     ],
            #     use_container_width=True,
            #     longitude='Lon',
            #     latitude='Lat',
            #     size=200,
            #     color='#009ee3',
            # )
            st.divider()