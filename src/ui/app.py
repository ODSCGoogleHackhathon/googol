import streamlit as st
from src.ui.components.image import display_img
import src.ui.api_client as api_client
import os
import pandas as pd
import json


# HEAD ------------------------------------------------------------------------------------------------------

data_context = None
colors = ["red", "green", "yellow", "violet", "orange", "blue", "gray"]
colors_i = 1
if "available_labels" not in st.session_state.keys():
    st.session_state["available_labels"] = {"default": "red"}

MAX_IMG_PER_PAGE = 12
if "imgs" not in st.session_state.keys():
    st.session_state["imgs"] = [[]]

if "chat_history" not in st.session_state.keys():
    st.session_state["chat_history"] = [
        {"name": "ai", "content": "Hello! How can I help you with labeling this dataset?"}
    ]

st.set_page_config(layout="wide")

# HEADER --------------------------------------------------------------------------------------------------

st.header("Googol")

"---"
# FILE UPLOAD AREA ----------------------------------------------------------------------------------------

# imgs = st.file_uploader('Upload Dataset  Folder / Images', type=['jpg', 'jpeg', 'png', 'svg'], accept_multiple_files='directory')

with st.expander("# 📁 Add Files", expanded=False):
    folder_path = st.text_input("Please choose a folder path:")
    consider_folder_as_patient = st.checkbox("Consider Subfolder As Patient ID")
    consider_folder_as_label = st.checkbox("Consider Subfolder As Label")
    confirmed = st.button("Confirm")
    ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "svg")
    df_data = {"label": [], "description": [], "path": [], "patient": []}
    if folder_path and confirmed:
        current_page = 0
        file_num = 0
        iterator = os.walk(folder_path)
        data = next(iterator, None)
        st.session_state["imgs"] = [[]]
        while data is not None:
            dirpath, dirnames, filenames = data

            folder_name = dirpath.split("/")[-1]

            for filename in filenames:
                # Check if file format is appropriate
                if filename.endswith(ALLOWED_EXTENSIONS):

                    # If there's no space in the current page, add a new page
                    if file_num == MAX_IMG_PER_PAGE:
                        current_page += 1
                        st.session_state["imgs"].append([])
                        file_num = 0

                    # Add to current page
                    file_path = os.path.join(dirpath, filename)
                    st.session_state["imgs"][current_page].append(file_path)

                    df_data["label"].append(folder_name if consider_folder_as_label else "default")
                    df_data["description"].append("No description provided.")
                    df_data["path"].append(file_path)
                    df_data["patient"].append(
                        folder_name if consider_folder_as_patient else "anonymous"
                    )
                    file_num += 1

            data = next(iterator, None)

        st.session_state["final_data_df"] = pd.DataFrame(df_data)

        # Setting labels
        for label in st.session_state["final_data_df"]["label"].unique():
            st.session_state["available_labels"][label] = colors[colors_i % len(colors)]
            colors_i += 1

        # NEW: Load dataset into backend
        dataset_name = folder_path.split("/")[-1] or "dataset"
        with st.spinner("Loading dataset into backend..."):
            result = api_client.load_dataset(dataset_name, df_data["path"])
            if result.get("success"):
                st.session_state["dataset_name"] = dataset_name
                message = result.get("message", "Dataset loaded")

                # Show appropriate message based on what happened
                if "already exist" in message:
                    st.info(f"ℹ️ {message}")
                    # Try to fetch existing annotations from backend
                    cached_data = api_client.get_annotations(dataset_name)
                    if cached_data.get("total_annotations", 0) > 0:
                        st.success(
                            f"✅ Found {cached_data['total_annotations']} cached annotations"
                        )

                        # Update local dataframe with cached annotations
                        path_to_annotation = {
                            ann["path"]: ann for ann in cached_data["annotations"]
                        }
                        for idx, row in st.session_state["final_data_df"].iterrows():
                            if row["path"] in path_to_annotation:
                                cached = path_to_annotation[row["path"]]
                                st.session_state["final_data_df"].at[idx, "label"] = cached.get(
                                    "label", "pending"
                                )
                                st.session_state["final_data_df"].at[idx, "description"] = (
                                    cached.get("description", "No description")
                                )
                                st.session_state["final_data_df"].at[idx, "patient"] = str(
                                    cached.get("patient_id", "anonymous")
                                )

                        # Update available labels from cached data
                        for label in st.session_state["final_data_df"]["label"].unique():
                            if label not in st.session_state["available_labels"]:
                                st.session_state["available_labels"][label] = colors[
                                    colors_i % len(colors)
                                ]
                                colors_i += 1
                else:
                    st.success(f"✅ {message}")
            else:
                st.warning(
                    f"⚠️ Dataset loaded locally but backend load failed: {result.get('error', 'Unknown error')}"
                )

        print("Data collected: ", st.session_state["imgs"])

# EXPORT & Statistics --------------------------------------------------------------------------------


@st.dialog("Statistics", width="large")
def show_statistics():
    # st.bar_chart()
    st.write("Data")

    if "final_data_df" in st.session_state is not None:

        st.dataframe(st.session_state["final_data_df"])

        st.write("Label Frequencies")
        frequencies_df = st.session_state["final_data_df"]["label"].value_counts()

        st.bar_chart(frequencies_df, horizontal=True)
    else:
        st.error("Please choose a folder before viewing statistics.")


export_and_st = st.columns(2)

with export_and_st[0]:
    if st.button("# 📦 Export Results", use_container_width=True):
        if "dataset_name" in st.session_state:
            with st.spinner("Exporting dataset..."):
                result = api_client.export_dataset(st.session_state["dataset_name"])
                if result.get("total_annotations", 0) > 0:
                    st.download_button(
                        "💾 Download JSON",
                        data=json.dumps(result["annotations"], indent=2),
                        file_name=f"{st.session_state['dataset_name']}_annotations.json",
                        mime="application/json",
                    )
                    st.success(f"✅ Exported {result['total_annotations']} annotations")
                else:
                    st.warning("No annotations to export")
        else:
            st.error("Please load a dataset first")
with export_and_st[1]:
    if st.button("📊 View Statistics", use_container_width=True):
        show_statistics()

# MAIN AREA (Where Images are Displayed) -------------------------------------------------------------

columns = st.columns(3, gap="medium")

if "page_num" not in st.session_state:
    st.session_state["page_num"] = 0
with st.container(key="imgs_page"):

    if len(st.session_state["imgs"]) > 1:
        last_page = len(st.session_state["imgs"])
        st.session_state["page_num"] = st.select_slider("Page", options=range(last_page))

    for i, img in enumerate(st.session_state["imgs"][st.session_state["page_num"]]):
        display_img(
            columns[i % 3],
            img,
            st.session_state["final_data_df"][st.session_state["final_data_df"]["path"] == img],
            str(i),
            st.session_state["available_labels"],
        )


# SIDEBAR (Chatbot Zone) -----------------------------------------------------------------------------
with st.sidebar:
    # Backend health check
    is_healthy, health_data = api_client.health_check()
    if is_healthy:
        st.success("✅ Backend Connected")
    else:
        st.error("❌ Backend Disconnected")
        st.warning("Start backend: `python -m src.api.main`")

    st.divider()

    st.write("**Labels:**")
    label_html = " ".join(
        [
            f"<span style='background-color:{color};padding:4px 8px;border-radius:4px;margin:2px;display:inline-block'>{label}</span>"
            for label, color in st.session_state["available_labels"].items()
        ]
    )
    st.markdown(label_html, unsafe_allow_html=True)

    with st.form("context"):
        st.write("Write the medical context for your dataset:")
        data_context = st.text_input("context")
        submit_button = st.form_submit_button("Submit")

    if submit_button:
        print(data_context)

    with st.container(key="chat_area"):
        "---"
        "# AI Chat"

        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["name"]):
                st.write(msg["content"])

        with st.chat_message("user"):
            with st.form("user_msg_form", clear_on_submit=True):
                user_input = st.text_input(
                    "You:",
                    placeholder="Can you label these images according to anomalies found?",
                    value="",
                )
                submit = st.form_submit_button("Send", icon="➡️")

                if submit and user_input:
                    st.session_state["chat_history"].append({"name": "user", "content": user_input})

                    # Call backend chat API
                    with st.spinner("AI is thinking..."):
                        response = api_client.chat_with_ai(
                            message=user_input,
                            dataset_name=st.session_state.get("dataset_name"),
                            chat_history=st.session_state["chat_history"],
                        )

                    if response.get("success"):
                        st.session_state["chat_history"].append(
                            {
                                "name": "ai",
                                "content": response.get(
                                    "ai_message", "Sorry, I could not process that."
                                ),
                            }
                        )
                    else:
                        st.session_state["chat_history"].append(
                            {
                                "name": "ai",
                                "content": f"Error: {response.get('error', 'Unknown error')}",
                            }
                        )
                    st.rerun()
