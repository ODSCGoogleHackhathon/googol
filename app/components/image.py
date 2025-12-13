import streamlit as st
import uuid

def display_img(column, path, final_data, name, available_colors):

    with column:
        with st.container():

            st.pills('', ['Flag', 'Relabel', 'Remove'], key=path + name, selection_mode='single')
            with st.popover('Image Path'):
                st.write(f'``{path}``')
            with st.container(horizontal=True):
                st.badge(final_data['label'].values[0], color=available_colors[final_data['label'].values[0]])
                #st.space()
                st.write(f'Patient ID: ``{final_data['patient'].values[0]}``')
            st.image(image=path, caption=final_data['description'].values[0])
