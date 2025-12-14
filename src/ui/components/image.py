import streamlit as st
import src.ui.api_client as api_client

def display_img(column, path, final_data, name, available_colors):

    with column:
        with st.container():

            action = st.pills('', ['Flag', 'Relabel', 'Remove'], key=path + name, selection_mode='single')

            # Handle actions
            if action == 'Remove' and 'dataset_name' in st.session_state:
                with st.spinner('Removing...'):
                    result = api_client.delete_annotation(st.session_state['dataset_name'], path)
                    if result.get('success'):
                        st.success('Removed!')
                        st.rerun()
            elif action == 'Flag' and 'dataset_name' in st.session_state:
                # Update with flagged description
                current_label = final_data['label'].values[0]
                current_desc = final_data['description'].values[0]
                new_desc = f"[FLAGGED] {current_desc}" if not current_desc.startswith('[FLAGGED]') else current_desc
                api_client.update_annotation(st.session_state['dataset_name'], path, current_label, new_desc)
                st.warning('Flagged!')

            with st.popover('Image Path'):
                st.write(f'``{path}``')

            current_label = final_data['label'].values[0]
            current_patient = final_data['patient'].values[0]
            label_color = available_colors.get(current_label, 'gray')
            st.markdown(f"<span style='background-color:{label_color};padding:4px 8px;border-radius:4px;margin:2px'>{current_label}</span> | Patient: ``{current_patient}``", unsafe_allow_html=True)
            st.image(image=path, caption=final_data['description'].values[0])
