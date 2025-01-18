import streamlit as st
import os
import google.generativeai as genai
import os
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import markdown
import tempfile
from html.parser import HTMLParser
from pdfutils import process_markdown, create_pdf
from listutils import add_item, edit_item, delete_item  

MODEL_ID = "gemini-2.0-flash-exp" 
api_key = os.getenv("GEMINI_API_KEY")
model_id = MODEL_ID
genai.configure(api_key=api_key)

if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(MODEL_ID)

model = st.session_state.model
chat = model.start_chat()

ENABLE_STREAMING = True

def generate_ai_response(prompt):
    """Generates a response from an AI model

    Args:
    prompt: The prompt to send to the AI model.

    Returns:
    response from the AI model.
    """


# Function to create the prompt for the AI model
def createprompt(course_title, reference_textbook, specific_topic):
    prompt = f"""
    You are an expert instructor. Create a course syllabus for a course titled '{course_title}'. 
    The syllabus should focus only on the module: '{specific_topic}' 
    and search the web and refer to the reference textbook '{reference_textbook}'. 
    
    Use the Outcomes-Based Education (OBE) framework and create a course design matrix. 
    A typical module takes 2 to 3 meeks to cover. 
    
    Output this matrix as a table with the following columns: Desired Learning Outcomes (DLO) - 
    What should students be able to do after completing this module? (Give 3 to 4 DLOs. Use action verbs – explain, 
    analyze, evaluate, etc.) Course Content/Subject Matter - Specific topics within the module that 
    contribute to achieving the DLO. Textbooks/References - Relevant reading materials that support 
    the content. (Include titles and authors if possible) Outcomes-Based Teaching & Learning (OBTL) 
    Learning activities aligned with the DLOs (e.g., lectures, discussions, case studies, site 
    visits, etc.) Assessment of Learning Outcomes (ALO)	- How will you measure student achievement 
    of the DLOs? (e.g., quizzes, essays, presentations, projects, etc.) Resource Material - 
    Supplementary materials to enhance learning (e.g., maps, documentaries, websites, guest 
    speakers) Time Table - Suggested allocation of time for each topic/activity within the module. 
    Use only the book {reference_textbook} as reference.  The output must include the column titles.
    Use concise and clear language.
    Label the table with the module title {specific_topic} formatted as Module: {specific_topic}. 
    Output the table exactly with the specified columns in Markdown format. 
    
    Do not add any additional information.
    """
    return prompt

def download_markdown(content):
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/markdown;base64,{b64}" download="output.md">Download Markdown</a>'
    return href

# Streamlit app
def main():
    st.title("OBE Syllabus Generator")

    with st.expander("ℹ️ About"):
        st.write(
            """
            This app generates a course syllabus for a specific module using the \
            Outcomes-Based Education (OBE) framework. The syllabus is created \
            using a high performance AI model. 
            """
        )
        st.write("Programmed by Louie F. Cervantes, M.Eng.(Information Engineering).")

    # Initialize session state to store the list of moldues
    if 'item_list' not in st.session_state:
        st.session_state.item_list = []
    if 'new_item' not in st.session_state:
        st.session_state.new_item = ''

    # User input fields
    course_title = st.text_input("Course Title")
    reference_textbook = st.text_input("Reference Textbook")\
    
    # Create a tab for each action
    tab_add, tab_list, tab_edit = st.tabs(['Add Module', 'List of Modules', 'Edit/Delete Module'])

    # Add new item tab
    with tab_add:
        st.header('Add New Module')
        st.session_state.new_item = st.text_input('Enter new item')
        st.button('Add', on_click=add_item)

    # List of items tab
    with tab_list:
        st.header('List of Modules')
        for i, item in enumerate(st.session_state.item_list):
            st.write(f'{i+1}. {item}')

    # Edit or delete item tab
    with tab_edit:
        st.header('Edit or Delete Module')
        selected_item = st.selectbox('Select module', st.session_state.item_list)
        if selected_item:
            index = st.session_state.item_list.index(selected_item)
            edit_value = st.text_input('Edit Module', value=selected_item)
            if st.button('Save Module'):
                edit_item(index, edit_value)
            if st.button('Delete'):
                delete_item(index)

    def generate_module_matrix(module):
        prompt = createprompt(course_title, reference_textbook, module)
        try:
            full_response = ""
            # Send file and prompt to Gemini API
            response = chat.send_message(
                [ prompt ],                 
                stream=ENABLE_STREAMING
            )   

            if ENABLE_STREAMING:
                response_placeholder = st.empty()
                # Process the response stream
                for chunk in response:
                    full_response += chunk.text                        
                    response_placeholder.markdown(full_response)  
            else:
                # Extract and display the response
                full_response = response.text
                st.markdown(full_response)  
            
            return full_response
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None

    # Generate prompt
    if st.button("Generate"):
        full_syllabus = f"# Syllabus for {course_title}\n\n"

        with st.spinner("Thinking..."):
            for item in st.session_state.item_list:
                full_syllabus += generate_module_matrix(item)

        if full_syllabus != "":
            st.write("Download the markdown file:")
            st.markdown(download_markdown(full_syllabus), unsafe_allow_html=True)

            json_string = process_markdown(full_syllabus)

            pdf_filepath = create_pdf(json_string)

            if pdf_filepath:  # Check if PDF was generated successfully
                st.success("PDF generated successfully!")

            with open(pdf_filepath, "rb") as f:
                pdf_bytes = f.read()
                st.download_button("Download PDF", data=pdf_bytes, file_name="genrated_syllabus.pdf")

        else:
            st.warning("No response was obtained from the AI Model.")

    

if __name__ == "__main__":
    main()