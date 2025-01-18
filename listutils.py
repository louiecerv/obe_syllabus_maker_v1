import streamlit as st

# Function to add new item
def add_item():
    if st.session_state.new_item == "":
        st.error('Please enter a new item')
        return
    else:
        new_item = st.session_state.new_item
        st.session_state.item_list.append(new_item)
        st.session_state.new_item = ''
        st.write(f'Added item: {new_item}')

# Function to edit item
def edit_item(index, new_value):
    st.session_state.item_list[index] = new_value

# Function to delete item
def delete_item(index):
    del st.session_state.item_list[index]