import openactive as oa
import pandas as pd
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

# Cache feeds to allow access across sessions
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
    st.session_state.unique_addresses = []
    st.session_state.unique_times = []
    st.session_state.unique_times_range = ()
    clear_filters()

# --------------------------------------------------------------------------------------------------

def clear_filters():
    st.session_state.filtered_ids = []
    st.session_state.filtered_superevent_ids = []
    st.session_state.filtered_organizers = []
    st.session_state.filtered_names = []
    st.session_state.filtered_addresses = []
    st.session_state.filtered_times_range = st.session_state.unique_times_range

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
        st.session_state.filtered_addresses
    ) > 0

    if (len(st.session_state.filtered_times_range)==0):
        filtered_times_range_active = False
    elif (len(st.session_state.filtered_times_range)==1):
        filtered_times_range_active = True
    elif (len(st.session_state.filtered_times_range)==2):
        filtered_times_range_active = \
            st.session_state.filtered_times_range[0]!=st.session_state.unique_times_range[0] \
        or  st.session_state.filtered_times_range[1]!=st.session_state.unique_times_range[1]

    return not filtered_multiselects_active and not filtered_times_range_active

# --------------------------------------------------------------------------------------------------

def set_address(address_in):
    address_out = ''
    for address_part in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']:
        try: address_out += address_in[address_part] + ('\n' if address_part!='addressCountry' else '')
        except: pass
    return address_out or None

# --------------------------------------------------------------------------------------------------

def set_time(datetime_isoformat):
    return datetime.fromisoformat(datetime_isoformat).strftime('%Y-%m-%d %H:%M') if len(datetime_isoformat)>0 else None

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
    col1, col2, col3 = st.columns([1,2,2])
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
    with col3:
        # Calling get_feeds() automatically includes a spinner
        # st.session_state.feeds = {'a':[{'url':'1','publisherName':'A'}],'b':[{'url':'2','publisherName':'B'}],'c':[{'url':'3','publisherName':'C'}]}
        st.session_state.feeds = get_feeds()
        st.session_state.providers = [(dataset_url,feeds_dataset[0]['publisherName']) for dataset_url,feeds_dataset in st.session_state.feeds.items()]
        st.session_state.initialised = True
        st.rerun()

# --------------------------------------------------------------------------------------------------

if (st.session_state.running):
    with col3:
        with st.spinner(''):
            # st.session_state.opportunities = json.load(open('opportunities-activeleeds-live-session-series.json', 'r'))
            st.session_state.opportunities = oa.get_opportunities(st.session_state.feed_url)
            num_items = len(st.session_state.opportunities['items'].keys())

            st.session_state.df = pd.DataFrame({
                'JSON': [False] * num_items,
                'ID': st.session_state.opportunities['items'].keys(),
                'Super-event ID': [None] * num_items,
                'Organizer name': [None] * num_items,
                'Organizer logo': [None] * num_items,
                'Name': [None] * num_items,
                'Address': [None] * num_items,
                'Lat': [None] * num_items,
                'Lon': [None] * num_items,
                'Time start': [None] * num_items,
                'Time end': [None] * num_items,
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
                    try: st.session_state.df.at[item_idx, 'Address'] = set_address(item['data']['location']['address'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Lat'] = float(item['data']['location']['geo']['latitude'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Lon'] = float(item['data']['location']['geo']['longitude'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Time start'] = set_time(item['data']['startDate'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'Time end'] = set_time(item['data']['endDate'])
                    except: pass
                    try: st.session_state.df.at[item_idx, 'URL'] = item['data']['url']
                    except: pass

            st.session_state.df.index = range(1, num_items+1)

            st.session_state.unique_ids = get_unique(st.session_state.df['ID'])
            st.session_state.unique_superevent_ids = get_unique(st.session_state.df['Super-event ID'])
            st.session_state.unique_organizer_names = get_unique(st.session_state.df['Organizer name'])
            st.session_state.unique_names = get_unique(st.session_state.df['Name'])
            st.session_state.unique_addresses = get_unique(st.session_state.df['Address'])
            st.session_state.unique_times = get_unique(pd.concat([st.session_state.df['Time start'], st.session_state.df['Time end']]))
            st.session_state.unique_times_range = (
                datetime.fromisoformat(st.session_state.unique_times[0]).date(),
                datetime.fromisoformat(st.session_state.unique_times[-1]).date()
            ) if st.session_state.unique_times else ()
            st.session_state.filtered_times_range = st.session_state.unique_times_range # We need to initialise this here, for some reason it doesn't do it when the associated filter widget is created

            st.session_state.disabled_columns = ['_index'] + list(st.session_state.df.columns) # The index column is not editable by default, but for some reason becomes editable when a filter selection is made, so we explicitly add it here to ensure against this
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
            'Address',
            st.session_state.unique_addresses,
            key='filtered_addresses',
            disabled=len(st.session_state.unique_addresses)==0,
        )
        st.date_input(
            'Time',
            value=st.session_state.unique_times_range,
            min_value=st.session_state.unique_times_range[0] if st.session_state.unique_times_range else datetime.now().date(),
            max_value=st.session_state.unique_times_range[1] if st.session_state.unique_times_range else datetime.now().date(),
            key='filtered_times_range',
            disabled=len(st.session_state.unique_times_range)==0,
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
    if (st.session_state.filtered_names):
        df_filtered = df_filtered.loc[df_filtered['Name'].isin(st.session_state.filtered_names)]
    if (st.session_state.filtered_addresses):
        df_filtered = df_filtered.loc[df_filtered['Address'].isin(st.session_state.filtered_addresses)]
    if (st.session_state.filtered_organizers):
        df_filtered = df_filtered.loc[df_filtered['Organizer name'].isin(st.session_state.filtered_organizers)]
    if (st.session_state.filtered_times_range):
        df_filtered = df_filtered.loc[
                (df_filtered['Time start'].apply(datetime.fromisoformat).apply(datetime.date) >= st.session_state.filtered_times_range[0])
            &   (df_filtered['Time end'].apply(datetime.fromisoformat).apply(datetime.date) <= st.session_state.filtered_times_range[len(st.session_state.filtered_times_range)-1])
        ]
    if (len(df_filtered)>0):
        df_filtered.at[df_filtered.index[0], 'JSON'] = True

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
            # warn against a change that may take a while to figure out and ultimately lead to the same conclusion.
            #   'Time start': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm'),
            #   'Time end': st.column_config.DatetimeColumn(format='YYYY-MM-DD HH:mm'),
            'URL': st.column_config.LinkColumn(),
        },
    )

    if (any(st.session_state.df_edited['JSON'])):
        selected_idxs = list(st.session_state.df_edited.index[st.session_state.df_edited['JSON']].values.astype(str))
        selected_ids = list(st.session_state.df_edited['ID'][st.session_state.df_edited['JSON']].values.astype(str))
        for tab_idx,tab in enumerate(st.tabs(selected_idxs)):
            with tab:
                st.json(st.session_state.opportunities['items'][selected_ids[tab_idx]])

# --------------------------------------------------------------------------------------------------

# today = datetime.datetime.now()
# filter_dates = st.date_input(
#     'Filter dates',
#     (today, today+datetime.timedelta(days=6)),
#     today,
#     format='DD.MM.YYYY',
#     disabled=True,
# )