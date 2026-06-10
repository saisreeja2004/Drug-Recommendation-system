import streamlit as st
import mysql.connector
from mysql.connector import Error
import hashlib
import google.generativeai as genai
import streamlit as st

from pathlib import Path
import os
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io


# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
# model = genai.GenerativeModel("gemini-1.5-flash")


# Load environment variables from .env
load_dotenv()

# Configure the SDK using the key from your environment
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# -------------------- Database Functions -------------------- #

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  
            database="chatbot"
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, email, password):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT UPPER(email) FROM users WHERE UPPER(email) = %s", (email.upper(),))
        if cursor.fetchone():
            st.error("This email ID already exists!")
        else:
            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", 
                           (name, email, hashed_password))
            connection.commit()
            st.success("Registration successful! Please log in.")
        connection.close()

staff_email = "staff@gmail.com"
staff_password = "staff123"

def authenticate_user(email, password):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE UPPER(email) = %s", (email.upper(),))
        user = cursor.fetchone()
        connection.close()
        if user and user[3] == hash_password(password):
            return user
        return None

    else:
        st.error("Failed to connect to the database.")
        return None
    

import PyPDF2
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# -------------------- Main Function -------------------- #

def main():
    st.set_page_config(page_title="project", layout="wide")

    st.title("My project")

    menu = ["Home", "Login", "Register", "Staff"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        if st.session_state.get("user"):
            st.success(f"Welcome, {st.session_state['user'][1]}!")

            if st.sidebar.button("Logout"):
                st.session_state["user"] = None
                st.experimental_set_query_params()

            def generate_pdf(recommendations, filename="recommendations.pdf"):
                
                pdf_dir = './uploads'
                if not os.path.exists(pdf_dir):
                    os.makedirs(pdf_dir)

                # Define the full path for the PDF file
                pdf_filename = os.path.join(pdf_dir, filename)

                # Create a BytesIO buffer to hold the PDF in memory
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)

                # Set up the PDF content
                c.drawString(100, 750, "Disease Prediction and Recommendations")
                c.drawString(100, 730, "-------------------------------------------------")
                c.drawString(100, 710, f"Recommendations:")

                # Add the recommendations text to the PDF with wrapping
                text_object = c.beginText(100, 690)
                text_object.setFont("Helvetica", 10)
                text_object.setTextOrigin(100, 690)  # Set the starting position

                # Add the recommendations line by line
                for line in recommendations.split("\n"):
                    text_object.textLine(line)

                c.drawText(text_object)

                # Finalize the PDF
                c.showPage()
                c.save()

                # Save the PDF to a file (binary write mode)
                with open(pdf_filename, "wb") as f:
                    f.write(buffer.getvalue())

                # Return the path of the generated PDF file
                return pdf_filename

            def get_recommendations(symptoms):
    
                prompt = f"""Given the following symptoms, predict the disease and provide 
                recommendations:\nSymptoms: {symptoms}\nProvide the disease name, medication, dosage, precautions, 
                and diet recommendations."""

                response = model.generate_content(prompt)

                recommendations = response.text.strip()

                return recommendations


            # Streamlit app
            st.subheader("Enter Symptoms and Get Recommendations")

            # Text area for symptoms input
            symptoms_input = st.text_area("Describe Symptoms", height=200)

            submit_button = st.button("submit")

            if submit_button:
                if symptoms_input:
                    # Process the input and get recommendations from Gemini model
                    recommendations = get_recommendations(symptoms_input)
                    st.write(recommendations)
                    
                    # Generate PDF based on recommendations
                    pdf_filename = generate_pdf(recommendations)
                    pdf_filename
                    
                    st.write("PDF has downloaded.")

        else:
            st.info("Please log in or register to continue.")

    elif choice == "Login":
        
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate_user(email, password)
            if user:
                st.success(f"Logged in as {user[1]}")
                st.session_state["user"] = user
                value = ""
                st.experimental_get_query_params()["key"] = value
            else:
                st.error("Invalid email or password")

    elif choice == "Register":
        st.subheader("Register")
        with st.form("registration_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Register"):
                if password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    register_user(name, email, password)


    elif choice == "Staff":
        st.subheader("Extract Text from Files (PDF)")

        file = st.file_uploader("Upload a file", type=["pdf"], key="file_upload")

        if file is not None:
            if file.name.endswith("pdf"):
                        
                text = extract_text_from_pdf(file)

                st.session_state["extracted_text"] = text

                st.text_area("Extracted Text", text, height=300)

            else:
                st.error("Only PDF files are supported for extraction.")             
    else:
        st.write("error")

upload_dir = './uploads'

Path(upload_dir).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main()

