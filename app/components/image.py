import streamlit as st
import uuid

def display_img(column, path, final_data, name):

    with column:
        with st.container():

            st.pills('', ['Flag', 'Relabel', 'Remove'], key=path + name, selection_mode='single')
            with st.container(horizontal=True):
                with st.popover('Image Path'):
                    st.write(f'``{path}``')
                st.badge(final_data['label'].values[0], color='red')
            st.image(image=path, caption=final_data['description'].values[0])
