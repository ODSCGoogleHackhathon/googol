import streamlit as st
from components.image import display_img
import os


# HEAD ------------------------------------------------------------------------------------------------------

data_context = None
available_labels = {
    'default': 'red',
    'label 2': 'green',
    'label 3': 'yellow'
}

MAX_IMG_PER_PAGE=12
if 'imgs' not in st.session_state.keys():
   st.session_state['imgs'] = [[]]

if 'final_data' not in st.session_state.keys():
    st.session_state['final_data'] = {} # this object will store all data, such as imgs (keys) and their labels
    # each img in the dictionary consists in another dictionary with the following keys: 'label', 'description'.

if 'chat_history' not in st.session_state.keys():
   st.session_state['chat_history'] = [{'name': 'ai', 'content': 'Hello! How can I help you with labeling this dataset?'}]

st.set_page_config(layout='wide')

# HEADER --------------------------------------------------------------------------------------------------

st.header('Googol')

'---'
# FILE UPLOAD AREA ----------------------------------------------------------------------------------------

# imgs = st.file_uploader('Upload Dataset  Folder / Images', type=['jpg', 'jpeg', 'png', 'svg'], accept_multiple_files='directory')

with st.expander('# 📁 Add Files'):
    folder_path = st.text_input('Please choose a folder path:')
    confirmed = st.button('Confirm')
    ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'svg')
    if folder_path and confirmed:
        current_page = 0
        file_num = 0
        iterator = os.walk(folder_path)
        data = next(iterator, None)
        st.session_state['imgs'] = [[]]
        while data is not None:
            dirpath, dirnames, filenames = data

            for filename in filenames:
                # Check if file format is appropriate
                if filename.endswith(ALLOWED_EXTENSIONS):

                    # If there's no space in the current page, add a new page
                    if file_num == MAX_IMG_PER_PAGE:
                        current_page += 1
                        st.session_state['imgs'].append([])
                        file_num = 0
                    
                    # Add to current page
                    file_path = os.path.join(dirpath, filename)
                    st.session_state['imgs'][current_page].append(file_path)
                    st.session_state['final_data'][file_path] = {
                        'label': 'default',
                        'description': 'No description provided.'
                    }
                    file_num += 1

            data = next(iterator, None)
        print('Data collected: ', st.session_state['imgs'])

# MAIN AREA (Where Images are Displayed) -------------------------------------------------------------

columns = st.columns(3, gap='medium')
if 'page_num' not in st.session_state:
    st.session_state['page_num'] = 0
with st.container(key='imgs_page'):

    for i, img in enumerate(st.session_state['imgs'][st.session_state['page_num']]):
     display_img(columns[i % 3], img, st.session_state['final_data'][img], str(i))
    if len(st.session_state['imgs']) > 1:
        last_page = len(st.session_state['imgs'])
        st.session_state['page_num'] = st.select_slider('Page', options=range(last_page))

# SIDEBAR (Chatbot Zone) -----------------------------------------------------------------------------
with st.sidebar:

    with st.container(horizontal=True):
        for label in available_labels.keys():
            st.badge(label, color=available_labels[label])

    with st.form('context'):
        st.write('Write the medical context for your dataset:')
        data_context = st.text_input('context')
        submit_button = st.form_submit_button('Submit')

    if submit_button:
        print(data_context)

    with st.container(key='chat_area'):
        '---'
        '# AI Chat'

        for msg in st.session_state['chat_history']:
            with st.chat_message(msg['name']):
                st.write(msg['content'])
        
        with st.chat_message('user'):
            with st.form('user_msg_form', clear_on_submit=True):
                user_input = st.text_input('You:', placeholder='Can you label these images according to anomalies found?', value='')
                submit = st.form_submit_button('Send', icon='➡️')
            
                if submit:
                    st.session_state['chat_history'].append({'name': 'user', 'content': user_input})

                    # This is where the API call will take place
                    st.session_state['chat_history'].append({'name': 'ai', 'content': 'I\'m an AI reply'})
                    st.rerun()  