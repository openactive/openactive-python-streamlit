import openactive as oa
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title='OpenActive',
    page_icon='https://www.openactive.io/wp-content/themes/open-active-1_3/images/favicon.png',
    layout='wide',
    menu_items={
        'Get help': 'mailto:hello@openactive.io',
        'About': 'Copyright 2024 OpenActive',
    }
)

# Cache feeds to allow access across sessions
@st.cache_data
def get_feeds():
    return oa.get_feeds()

def go(feed_url=None):
    st.session_state.running = True

def clear():
    st.session_state.running = False
    st.session_state.dataset_url_name = None
    st.session_state.feed_url = None
    st.session_state.opportunities = None
    st.session_state.df = None
    st.session_state.df_edited = None

def disabled(default=False):
    return True if st.session_state.running else default

def set_time(datetime_isoformat):
    return datetime.fromisoformat(datetime_isoformat).strftime('%Y-%m-%d %H:%M') if len(datetime_isoformat)>0 else ''

def set_address(address_in):
    address_out = ''
    for address_part in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']:
        try: address_out += address_in[address_part] + ('\n' if address_part!='addressCountry' else '')
        except: pass
    return address_out

if ('initialised' not in st.session_state):
    st.session_state.initialised = False
    st.session_state.feeds = None
    st.session_state.providers = None
    clear()

with st.sidebar:
    st.image('https://openactive.io/brand-assets/openactive-logo-large.png')
    st.divider()
    st.selectbox(
        'Data Provider',
        st.session_state.providers or [],
        key='dataset_url_name',
        format_func=lambda x: x[1],
        index=None,
        placeholder='Choose a data provider',
        label_visibility='collapsed',
        disabled=disabled(),
    )
    st.selectbox(
        'Data Type',
        [feed['url'] for feed in st.session_state.feeds[st.session_state.dataset_url_name[0]]] if st.session_state.dataset_url_name else [],
        key='feed_url',
        format_func=lambda x: x.split('/')[-1],
        index=None,
        placeholder='Choose a data feed',
        label_visibility='collapsed',
        disabled=disabled(st.session_state.dataset_url_name==None),
    )
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        st.button(
            'Go',
            key='button_go',
            on_click=go,
            args=[st.session_state.feed_url],
            # type='primary', # Making this primary gives a little flicker when clicked due to the change in disabled state
            disabled=disabled(st.session_state.feed_url==None),
        )
    with col2:
        st.button(
            'Clear',
            key='button_clear',
            on_click=clear,
            disabled=st.session_state.dataset_url_name==None,
        )
    with col3:
        status = st.status('Complete' if st.session_state.initialised and not st.session_state.running else '', state='complete')

if (not st.session_state.initialised):
    status.update(label='Initialising', state='running')
    # st.session_state.feeds = {'a':[{'url':'1','publisherName':'A'}],'b':[{'url':'2','publisherName':'B'}],'c':[{'url':'3','publisherName':'C'}]}
    st.session_state.feeds = get_feeds()
    st.session_state.providers = [(dataset_url,feeds_dataset[0]['publisherName']) for dataset_url,feeds_dataset in st.session_state.feeds.items()]
    st.session_state.initialised = True
    st.rerun()

if (st.session_state.running):
    status.update(label='Running', state='running')
    # opportunities = json.load(open('opportunities-activeleeds-live-session-series.json', 'r'))
    st.session_state.opportunities = oa.get_opportunities(st.session_state.feed_url)
    num_items = len(st.session_state.opportunities['items'].keys())
    data = {
        'ID': st.session_state.opportunities['items'].keys(),
        'Super-event ID': [''] * num_items,
        'Name': [''] * num_items,
        'Time start': [''] * num_items,
        'Time end': [''] * num_items,
        'Address': [''] * num_items,
        'Coordinates': [''] * num_items,
        'Organizer name': [''] * num_items,
        'Organizer logo': [''] * num_items,
        'URL': [''] * num_items,
    }
    for item_idx,item in enumerate(st.session_state.opportunities['items'].values()):
        if ('data' in item.keys()):
            try: data['Super-event ID'][item_idx] = item['data']['superEvent'].split('/')[-1]
            except: pass
            try: data['Name'][item_idx] = item['data']['name']
            except: pass
            try: data['Time start'][item_idx] = item['data']['startDate']
            except: pass
            try: data['Time end'][item_idx] = item['data']['endDate']
            except: pass
            try: data['Address'][item_idx] = item['data']['location']['address']
            except: pass
            try: data['Coordinates'][item_idx] = '{:.5f}, {:.5f}'.format(item['data']['location']['geo']['latitude'], item['data']['location']['geo']['longitude']) # 5 decimal places gives accuracy at the metre level
            except: pass
            try: data['Organizer name'][item_idx] = item['data']['organizer']['name']
            except:
                try: data['Organizer name'][item_idx] = item['data']['superEvent']['organizer']['name']
                except: pass
            try: data['Organizer logo'][item_idx] = item['data']['organizer']['logo']['url']
            except:
                try: data['Organizer logo'][item_idx] = item['data']['superEvent']['organizer']['logo']['url']
                except: pass
            try: data['URL'][item_idx] = item['data']['url']
            except: pass
    st.session_state.df = pd.DataFrame(data)
    st.session_state.df['Time start'] = st.session_state.df['Time start'].apply(set_time)
    st.session_state.df['Time end'] = st.session_state.df['Time end'].apply(set_time)
    st.session_state.df['Address'] = st.session_state.df['Address'].apply(set_address)
    st.session_state.df.insert(0, 'JSON', pd.Series([True] + [False] * (len(st.session_state.df)-1)))
    del(data)
    st.session_state.running = False
    st.rerun()

if (not st.session_state.feed_url):
    st.session_state.opportunities = None

if (st.session_state.opportunities):
    st.write('{} rows'.format(len(st.session_state.df)))
    disabled_columns = list(st.session_state.df.columns)
    disabled_columns.remove('JSON')
    st.session_state.df_edited = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        disabled=disabled_columns,
        column_config={
            '_index': st.column_config.NumberColumn(label='Index'),
            'JSON': st.column_config.CheckboxColumn(),
            'Organizer logo': st.column_config.ImageColumn(),
            'URL': st.column_config.LinkColumn(),
        },
    )
    if (any(st.session_state.df_edited['JSON'])):
        selected_idxs = [str(idx) for idx in st.session_state.df_edited.index[st.session_state.df_edited['JSON']].values]
        selected_ids = st.session_state.df_edited['ID'][st.session_state.df_edited['JSON']].values
        for tab_idx,tab in enumerate(st.tabs(selected_idxs)):
            with tab:
                st.json(st.session_state.opportunities['items'][selected_ids[tab_idx]])

# today = datetime.datetime.now()
# filter_dates = st.date_input(
#     'Filter dates',
#     (today, today+datetime.timedelta(days=6)),
#     today,
#     format='DD.MM.YYYY',
#     disabled=True,
# )