import os
import uuid
import time
import json
import streamlit as st
from PIL import Image
import pillow_heif

from dc_storage_utils import does_image_folder_exist, upload_images_from_dir, upload_json_descriptions_file, download_images

MAIN_DIR = os.path.dirname(os.path.realpath(__file__))
JSON_DIR = os.path.join(MAIN_DIR, 'descr_base')
IMAGE_BASE_PATH = os.path.join(MAIN_DIR, 'image_base')

st.title("Description Creator")

def upload_to_remote(img_dir):
    upload_images_from_dir(img_dir)


def make_entry(img_name, descr):
    entry = {
        "prompt": descr,
        "expected": [img_name]
    }
    return entry


def add_to_json_file(img_name, descr):
    print(f"\nimage: {img_name}")
    print(f"descr: {descr}")
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
    json_file = os.path.join(JSON_DIR, st.session_state.image_key + '_inputs.json')
    if os.path.exists(json_file):
        # If file exists, load existing data
        with open(json_file, 'r') as file:
            data = json.load(file)
    else:
        # If file does not exist, start with an empty list
        data = []

    entry = make_entry(img_name, descr)
    append = True
    for i, e in enumerate(data):
        if img_name in e['expected']:
            data[i] = entry
            append = False

    if append:
        data.append(entry)

    # Write the updated data back to the file
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=2)


def user_folder_exists_remote(key):
    folder_name = key[-5:]
    if does_image_folder_exist(folder_name):
        print('found db folder')
        local_folder = os.path.join(IMAGE_BASE_PATH, folder_name)
        if os.path.exists(local_folder):
            print('found matching local folder')
            #TODO: check same as remote 
            return True
        else:
            print('making local folder')
            os.makedirs(local_folder)
            #TODO: download images
            return True


def resize_image_to_height(image, fixed_height):
    width, height = image.size
    #print(f"width {width}, height {height}")
    aspect_ratio = width / height
    new_width = int(fixed_height * aspect_ratio)
    resized_image = image.resize((new_width, fixed_height), Image.LANCZOS)
    return resized_image


def clear_text():
    st.session_state["text_input"] = ""


def upload_descr_file():
    descr_file = os.path.join(JSON_DIR, st.session_state.image_key + '_inputs.json')
    upload_json_descriptions_file(descr_file)


def sync_local_with_remote():
    #a5c0c
    local_folder = os.path.join(IMAGE_BASE_PATH, st.session_state.image_key)
    print('syncing')
    download_images(st.session_state.image_key, local_folder)


def previous():
    st.session_state.prev = True


def handle_form_submission():
    st.session_state.submitted_descr = st.session_state.user_descr_input
    st.session_state.user_descr_input = ""

    st.session_state.descriptions[st.session_state.curr_img_name] = st.session_state.submitted_descr

    add_to_json_file(st.session_state.image_names[st.session_state.image_index], st.session_state.submitted_descr)


def sync_descr_dict():
    descr_file = os.path.join(JSON_DIR, st.session_state.image_key + '_inputs.json')
    if os.path.exists(descr_file):
        # If file exists, load existing data
        with open(descr_file, 'r') as file:
            data = json.load(file)

        if data:
            for e in data:
                img = e['expected'][0]
                descr = e['prompt']
                st.session_state.descriptions[img] = descr


def create_descriptions_page():
    """
    # st.markdown(""
    #     <script>
    #     (function() {
    #         function updateWindowHeight() {
    #             var height = window.innerHeight;
    #             var docHeightInput = document.getElementById("windowHeight");
    #             if (docHeightInput) {
    #                 docHeightInput.value = height;
    #                 docHeightInput.dispatchEvent(new Event('change'));
    #             }
    #         }
    #         window.addEventListener('resize', updateWindowHeight);
    #         window.onload = updateWindowHeight;
    #     })();
    #     </script>
    # "", unsafe_allow_html=True)

    # Hidden input to capture the window height
    if "window_height" not in st.session_state:
        st.session_state.window_height = 0

    window_height = st.text_input("Window Height", value=st.session_state.window_height, key="windowHeight")

    # Update session state on change of the window_height input
    if window_height:
        st.session_state.window_height = int(window_height)
        print(st.session_state.window_height)

    if st.session_state.window_height:
        fixed_height = st.session_state.window_height // 2 
        #print(window_height)
    """

    if 'create_descr_dict' not in st.session_state:
        st.session_state.create_descr_dict = True

    if 'image_index' not in st.session_state:
        st.session_state.image_index = 0
    elif st.session_state.prev:
        if st.session_state.image_index == 0:
            st.session_state.image_index = len(st.session_state.image_names) - 1
        else:
            st.session_state.image_index = st.session_state.image_index - 1
        st.session_state.prev = False
    else:
        if st.session_state.image_index >= len(st.session_state.image_names) - 1:
            st.session_state.image_index = 0
        else:
            st.session_state.image_index = st.session_state.image_index + 1

    st.write(st.session_state.image_key)
    img_dir = os.path.join(IMAGE_BASE_PATH, st.session_state.image_key)
    if not st.session_state.image_names:
        st.session_state.image_names = [f for f in os.listdir(img_dir) if f.endswith('.png')]
        if not st.session_state.image_names:
            raise Exception("no PNGs files in folder")
    
    i = st.session_state.image_index
    st.session_state.curr_img_name = st.session_state.image_names[i]
    img_path = os.path.join(img_dir, st.session_state.curr_img_name)

    if str(st.session_state.curr_img_name) in st.session_state.descriptions:
        st.write(st.session_state.descriptions[st.session_state.curr_img_name])

    displayed_image = Image.open(img_path)

    image_height = 500
    resized_image = resize_image_to_height(displayed_image, image_height)
    caption = f"({i+1}/{len(st.session_state.image_names)}) - {st.session_state.curr_img_name}"
    st.image(resized_image, caption=caption, use_column_width=False)

    #print(img_name)
    with st.form(key='descr_submission'):
        
        descr_input_col, descr_submit_btn_col = st.columns([5, 1])
        with descr_input_col:
            #TODO: populate with descr if exists
            user_descr_input = st.text_input(label="why is this required", label_visibility='collapsed',
                                             key="user_descr_input", placeholder="Enter a description for this image")

        with descr_submit_btn_col:
            submit_descr_button = st.form_submit_button(label='Submit', on_click=handle_form_submission)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col3:
        prev_button = st.button('<PREV', on_click=previous)
    with col4:
        next_btn = st.button('NEXT>')
    with col6:
        upload_descr_btn = st.button('UPLOAD', on_click=upload_descr_file)

    if next_btn:
        print('next')

    
    #     #handle clearing text input
    #     #st.session_state.toggle = not st.session_state.toggle
    #     #clear_text()


def submit_images_page():
    st.write(st.session_state.image_key)
    uploaded_files = []
    uploaded_files = st.file_uploader("Choose images...", type=['png', 'heic'], accept_multiple_files=True)

    if uploaded_files:
        st.session_state.image_key = str(uuid.uuid4().hex)[-5:]
        img_dir = os.path.join(IMAGE_BASE_PATH, st.session_state.image_key)
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)

        for img_file in uploaded_files:
            image = None
            file_name, file_type = img_file.name.split('.')
            file_type = file_type.lower()
            if file_type == 'heic':
                # Read the HEIC file
                heif_file = pillow_heif.read_heif(img_file)
                image = Image.frombytes(
                    heif_file.mode, 
                    heif_file.size, 
                    heif_file.data, 
                    "raw", 
                    heif_file.mode, 
                    heif_file.stride
                )
            elif file_type == 'png':
                image = Image.open(img_file)

            #optionally, save image
            save_path = os.path.join(img_dir, file_name + '.png')
            image.save(save_path, "PNG")
            st.write(f"Image saved as {save_path}")

        upload_to_remote(img_dir)
        st.session_state.submit_images_page = False
        st.session_state.create_page = True
        return True
    else:
        return False


def main():
    #start page - choose to enter key to get image base from db, or submit own pics
    if st.session_state.start_page:
        with st.form('key_submission'):
            key_text_input_col, key_submit_btn_col = st.columns([5, 1])
            with key_text_input_col:
                user_key_input = st.text_input(label="why is this required", label_visibility='collapsed', key="user_key_input", placeholder="Enter an Image Key")

            with key_submit_btn_col:
                submit_key_button = st.form_submit_button(label='Submit')

        st.write('OR')

        submit_own_images_button = st.button(label='Submit My Own Images', key='smoi')

        if submit_key_button:
            if user_folder_exists_remote(user_key_input):
                print('remote folder found')
                st.session_state.start_page = False
                st.session_state.create_page = True
                st.session_state.image_key = user_key_input
                sync_local_with_remote()
            else:
                st.error("Inputted key {} not recognized")
        
        if submit_own_images_button:
            st.session_state.start_page = False
            st.session_state.submit_images_page = True

    if st.session_state.create_page:
        create_descriptions_page()
                

    if st.session_state.submit_images_page:

        if submit_images_page():
            if st.button("Continue"):
                print('continuing')

    
#main loop
if 'start_page' not in st.session_state:
    st.session_state.start_page = True

if 'create_page' not in st.session_state:
    st.session_state.create_page = False
    
if 'submit_images_page' not in st.session_state:
    st.session_state.submit_images_page = False

if 'image_key' not in st.session_state:
    st.session_state.image_key = ""

if 'image_names' not in st.session_state:
    st.session_state.image_names = []

if 'submitted_descr' not in st.session_state:
    st.session_state.submitted_descr = ""

if 'descriptions' not in st.session_state:
    st.session_state.descriptions = dict()

if 'toggle' not in st.session_state:
    st.session_state.toggle = True

if 'text_input' not in st.session_state:
    st.session_state.text_input = ''

if 'prev' not in st.session_state:
    st.session_state.prev = False

if 'curr_image_name' not in st.session_state:
    st.session_state.curr_img_name = ""


main()