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
    st.session_state.df_edited = None
    st.session_state.df_filtered = None
    st.session_state.unique_ids = []
    st.session_state.unique_superevent_ids = []
    st.session_state.unique_organizers = []
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
    return address_out

# --------------------------------------------------------------------------------------------------

def set_time(datetime_isoformat):
    return datetime.fromisoformat(datetime_isoformat).strftime('%Y-%m-%d %H:%M') if len(datetime_isoformat)>0 else ''

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

            data = {
                'ID': st.session_state.opportunities['items'].keys(),
                'Super-event ID': [''] * num_items,
                'Organizer name': [''] * num_items,
                'Organizer logo': [''] * num_items,
                'Name': [''] * num_items,
                'Address': [''] * num_items,
                'Coordinates': [''] * num_items,
                'Time start': [''] * num_items,
                'Time end': [''] * num_items,
                'URL': [''] * num_items,
            }

            for item_idx,item in enumerate(st.session_state.opportunities['items'].values()):
                if ('data' in item.keys()):
                    try: data['Super-event ID'][item_idx] = item['data']['superEvent'].split('/')[-1]
                    except: pass
                    try: data['Organizer name'][item_idx] = item['data']['organizer']['name']
                    except:
                        try: data['Organizer name'][item_idx] = item['data']['superEvent']['organizer']['name']
                        except: pass
                    try: data['Organizer logo'][item_idx] = item['data']['organizer']['logo']['url']
                    except:
                        try: data['Organizer logo'][item_idx] = item['data']['superEvent']['organizer']['logo']['url']
                        except: pass
                    try: data['Name'][item_idx] = item['data']['name']
                    except: pass
                    try: data['Address'][item_idx] = item['data']['location']['address']
                    except: pass
                    try: data['Coordinates'][item_idx] = '{:.5f}, {:.5f}'.format(item['data']['location']['geo']['latitude'], item['data']['location']['geo']['longitude']) # 5 decimal places gives accuracy at the metre level
                    except: pass
                    try: data['Time start'][item_idx] = item['data']['startDate']
                    except: pass
                    try: data['Time end'][item_idx] = item['data']['endDate']
                    except: pass
                    try: data['URL'][item_idx] = item['data']['url']
                    except: pass

            st.session_state.df = pd.DataFrame(data)
            del(data)
            st.session_state.df.insert(0, 'JSON', pd.Series([False] * len(st.session_state.df)))
            st.session_state.df.index = range(1, len(st.session_state.df)+1) # This must happen after manual insertion of a new column, or the new column will not contain the right number of elements
            st.session_state.df['Address'] = st.session_state.df['Address'].apply(set_address)
            st.session_state.df['Time start'] = st.session_state.df['Time start'].apply(set_time)
            st.session_state.df['Time end'] = st.session_state.df['Time end'].apply(set_time)

            st.session_state.unique_ids = [id.strip() for id in sorted(set(st.session_state.df['ID'])) if id.strip()]
            st.session_state.unique_superevent_ids = [superevent_id.strip() for superevent_id in sorted(set(st.session_state.df['Super-event ID'])) if superevent_id.strip()]
            st.session_state.unique_organizers = [organizer.strip() for organizer in sorted(set(st.session_state.df['Organizer name'])) if organizer.strip()]
            st.session_state.unique_names = [name.strip() for name in sorted(set(st.session_state.df['Name'])) if name.strip()]
            st.session_state.unique_addresses = [address.strip() for address in sorted(set(st.session_state.df['Address'])) if address.strip()]
            st.session_state.unique_times = [time.strip() for time in sorted(set(pd.concat([st.session_state.df['Time start'], st.session_state.df['Time end']]))) if time.strip()]
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
            st.session_state.unique_organizers,
            key='filtered_organizers',
            disabled=len(st.session_state.unique_organizers)==0,
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
            '_index': st.column_config.NumberColumn(label='Index'),
            'JSON': st.column_config.CheckboxColumn(),
            'Organizer logo': st.column_config.ImageColumn(),
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