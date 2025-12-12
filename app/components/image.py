import streamlit as st
import uuid

def display_img(column, path, name):

    with column:
        with st.container():
            column.write(f'``{path}``')
            column.badge('label 1', color='red')
            column.image(image=path, caption='## A medical image\n This photo reveals to us that...')
            column.pills('', ['Flag', 'Relabel', 'Remove'], key=path + name, selection_mode='single')
