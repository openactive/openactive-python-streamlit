import json
import openactive as oa
import streamlit as st

st.set_page_config(
    page_title='OpenActive',
    page_icon='https://www.openactive.io/wp-content/themes/open-active-1_3/images/favicon.png',
    layout='wide',
    menu_items={
        'Get help': 'mailto:hello@openactive.io',
        'About': 'Copyright 2024 OpenActive',
    }
)

if ('initialised' not in st.session_state):
    st.session_state.initialised = False
    st.session_state.running = False
    st.session_state.feeds = None
    st.session_state.providers = None
    st.session_state.opportunities = None

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

def disabled(default=False):
    return True if st.session_state.running else default

st.image('https://openactive.io/brand-assets/openactive-logo-large.png')
st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
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
with col2:
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
with col3:
    st.button(
        'Go',
        key='button_go',
        on_click=go,
        args=[st.session_state.feed_url],
        # type='primary', # Making this primary gives a little flicker when clicked due to the change in disabled state
        disabled=disabled(st.session_state.feed_url==None),
    )
with col4:
    st.button(
        'Clear',
        key='button_clear',
        on_click=clear,
        disabled=st.session_state.dataset_url_name==None,
    )
with col5:
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
    st.session_state.running = False
    st.rerun()

if (not st.session_state.feed_url):
    st.session_state.opportunities = None

if (st.session_state.opportunities):
    st.json(list(st.session_state.opportunities['items'].values())[0:10])

# today = datetime.datetime.now()
# filter_dates = st.date_input(
#     'Filter dates',
#     (today, today+datetime.timedelta(days=6)),
#     today,
#     format='DD.MM.YYYY',
#     disabled=True,
# )