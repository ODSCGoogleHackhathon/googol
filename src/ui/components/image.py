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
            elif action == 'Relabel' and 'dataset_name' in st.session_state:
                # Manual annotation dialog
                with st.popover('✏️ Edit Annotation', use_container_width=True):
                    current_label = final_data['label'].values[0]
                    current_desc = final_data['description'].values[0]

                    st.write('**Manual Annotation**')

                    # Image Path
                    st.write('**Image Path:**')
                    st.code(path, language=None)

                    st.divider()

                    # Label selection
                    available_label_list = list(available_colors.keys())
                    current_index = available_label_list.index(current_label) if current_label in available_label_list else 0
                    new_label = st.selectbox('Label:', available_label_list, index=current_index, key=f'label_{path}_{name}')

                    # Description/findings
                    new_desc = st.text_area('Description/Findings:', value=current_desc, key=f'desc_{path}_{name}', height=100)

                    st.divider()

                    # Action buttons
                    col1, col2 = st.columns(2)

                    with col1:
                        # AI Analyze button
                        if st.button('🤖 AI Analyze', key=f'analyze_{path}_{name}', use_container_width=True):
                            with st.spinner('Analyzing with AI...'):
                                # Call analyze endpoint for single image
                                result = api_client.analyze_dataset(
                                    st.session_state['dataset_name'],
                                    prompt="Analyze this medical image and provide detailed findings",
                                    flagged=[path]
                                )
                                if result.get('success'):
                                    # Fetch updated annotations from backend
                                    cached_data = api_client.get_annotations(st.session_state['dataset_name'])
                                    if cached_data.get('total_annotations', 0) > 0:
                                        # Update local dataframe with fresh backend data
                                        path_to_annotation = {ann['path']: ann for ann in cached_data['annotations']}
                                        for idx, row in st.session_state['final_data_df'].iterrows():
                                            if row['path'] in path_to_annotation:
                                                cached = path_to_annotation[row['path']]
                                                st.session_state['final_data_df'].at[idx, 'label'] = cached.get('label', 'pending')
                                                st.session_state['final_data_df'].at[idx, 'description'] = cached.get('description', 'No description')
                                                st.session_state['final_data_df'].at[idx, 'patient'] = str(cached.get('patient_id', 'anonymous'))
                                    st.success('✅ AI analysis complete!')
                                    st.rerun()
                                else:
                                    st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

                    with col2:
                        # Manual Save button
                        if st.button('💾 Save Manual', key=f'save_{path}_{name}', use_container_width=True):
                            with st.spinner('Saving...'):
                                result = api_client.update_annotation(st.session_state['dataset_name'], path, new_label, new_desc)
                                if result.get('success'):
                                    # Update local dataframe
                                    st.session_state['final_data_df'].loc[st.session_state['final_data_df']['path'] == path, 'label'] = new_label
                                    st.session_state['final_data_df'].loc[st.session_state['final_data_df']['path'] == path, 'description'] = new_desc
                                    st.success('✅ Annotation updated!')
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to update: {result.get('error', 'Unknown error')}")

            current_label = final_data['label'].values[0]
            current_patient = final_data['patient'].values[0]
            label_color = available_colors.get(current_label, 'gray')
            st.markdown(f"<span style='background-color:{label_color};padding:4px 8px;border-radius:4px;margin:2px'>{current_label}</span> | Patient: ``{current_patient}``", unsafe_allow_html=True)
            st.image(image=path, caption=final_data['description'].values[0])
