import streamlit as st
import os


# HEAD ------------------------------------------------------------------------------------------------------

data_context = None
available_labels = {
    'label 1': 'red',
    'label 2': 'green',
    'label 3': 'yellow'
}

imgs = []

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
        iterator = os.walk(folder_path)
        data = next(iterator, None)
        while data is not None:
            dirpath, dirnames, filenames = data

            for filename in filenames:
                # Check if file format is appropriate
                if filename.endswith(ALLOWED_EXTENSIONS):
                    imgs.append(os.path.join(dirpath, filename))

            data = next(iterator, None)
        print('Data collected: ', imgs)

# MAIN AREA (Where Images are Displayed) -------------------------------------------------------------

columns = st.columns(3)


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
        '# AI Assistance'
        with st.chat_message('ai'):
            'Hello! How can I help you with labeling this dataset?'

        with st.chat_message('user'):
            user_input = st.text_input('You:', placeholder='Can you label these images according to anomalies found?')