import pandas as pd
import os
import docx
import google.generativeai as genai
from flask import Flask, request, jsonify

# Set your Google Gemini API key
os.environ["API_KEY"] = 'AIzaSyCiBsFlqKVWUVbU6bjwIlRWArG3SwjGlHk'

# Configure the Gemini API
genai.configure(api_key=os.environ["API_KEY"])

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

# Paths to the data files
data_file_path = 'payment_history.xlsx'  # Replace with your actual file path
doc_file_path = 'Income Tax List Section-80.docx'  # Replace with your actual file path

# Load and preprocess data
def preprocess_data(file_path):
    payment_history = pd.read_excel(file_path)
    payment_history.fillna(0, inplace=True)
    payment_history['transaction_month'] = pd.to_datetime(payment_history['Date']).dt.month
    payment_history['is_high_value'] = payment_history['Amount'] > 10000
    return payment_history

# Read the Income Tax document
def read_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Generate recommendation based on tax document
def generate_recommendation(payment_history, tax_info):
    total_expenditure = payment_history[payment_history['Amount'] < 0]['Amount'].sum()
    medical_expenses = payment_history[payment_history['Sub Category'] == 'medical']['Amount'].sum()
    education_expenses = payment_history[payment_history['Sub Category'] == 'education']['Amount'].sum()
    total_savings = payment_history[payment_history['Amount'] > 0]['Amount'].sum()

    # Create a prompt for the Gemini model to generate the recommendation
    prompt = f"""
    The customer has the following expenditure and savings details:
    - Total Expenditure: {total_expenditure}
    - Medical Expenses: {medical_expenses}
    - Education Expenses: {education_expenses}
    - Total Savings: {total_savings}

    The following is the information about tax exemptions:
    {tax_info}

    Based on the expenditure and savings, provide investment recommendations to maximize tax savings under the relevant sections of the Income Tax Act. The response should include:
    Section Name
    Type of investment
    Where you can invest
    Amount you can invest
    """

    response = model.generate_content(prompt)
    return response.text

# Flask app
app = Flask(__name__)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    pan_number = data['PAN_Number']
    
    # Read payment history from the provided Excel file
    payment_history = preprocess_data(data_file_path)
    
    if payment_history.empty:
        return jsonify({'error': 'No data found for the customer'}), 404

    # Read the Income Tax document
    tax_info = read_docx(doc_file_path)
    
    # Generate recommendation
    recommendation = generate_recommendation(payment_history, tax_info)
    
    return jsonify({'PAN_Number': pan_number, 'recommendation': recommendation})

if __name__ == '__main__':
    app.run(debug=True)