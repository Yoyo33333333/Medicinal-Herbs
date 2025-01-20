from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
import requests
from transformers import pipeline
import os
import google.generativeai as genai


app = Flask(__name__)
app.config['SECRET_KEY'] = '5f4dcc3b5aa765d61d8327deb882cf99a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6'  # Hardcode your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///herbs.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Gemini API
genai.configure(api_key="AIzaSyDe89ZqOhLI7SomtqrIgxS36rtINZ3J-70")  # Replace with your Gemini API key

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    favorites = db.Column(db.String(500), default="")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load herbs data
try:
    herbs_df = pd.read_csv('herbs_data.csv')
    print("Herbs DataFrame:", herbs_df.head())  # Debug
except FileNotFoundError:
    herbs_df = pd.DataFrame(columns=['Herb Name', 'Medicinal properties', 'Region/Origin', 'Description', 'Benefits'])
except Exception as e:
    print(f"Error loading herbs data: {str(e)}")  # Debug

# Moon Phase API Function
def get_moon_phase(date):
    """
    Fetches the moon phase data for a given date using the RapidAPI Moon Phase API.
    """
    url = "https://moon-phases-api-apiverve.p.rapidapi.com/v1/"
    headers = {
        "x-rapidapi-key": "35f29e5765msh28ce5fca3cacf35p1e3083jsn38ee480935db",  # Hardcode your key here
        "x-rapidapi-host": "moon-phases-api-apiverve.p.rapidapi.com",
        "Accept": "application/json"
    }
    querystring = {"date": date}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

# Moon Phase Route
@app.route('/moon_phase', methods=['GET'])
def moon_phase():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'Date is required (format: MM-DD-YYYY)'}), 400

    # Convert the date to MM-DD-YYYY format if necessary
    try:
        # Parse the input date (assuming it's in DD-MM-YYYY format)
        day, month, year = date.split('-')
        formatted_date = f"{month}-{day}-{year}"  # Convert to MM-DD-YYYY
    except Exception as e:
        return jsonify({'error': 'Invalid date format. Use MM-DD-YYYY.'}), 400

    try:
        moon_data = get_moon_phase(formatted_date)
        if 'error' in moon_data:
            return jsonify({'error': moon_data['error']}), 401  # Unauthorized
        return jsonify(moon_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    

def get_moon_phase_by_city(city):
    """
    Fetches the moon phase data for a given city using the RapidAPI Moon Phase API.
    """
    url = "https://moon-phase1.p.rapidapi.com/"
    headers = {
        "x-rapidapi-key": "35f29e5765msh28ce5fca3cacf35p1e3083jsn38ee480935db",  # Replace with your RapidAPI key
        "x-rapidapi-host": "moon-phase1.p.rapidapi.com"
    }
    querystring = {"city": city}

    # Debug: Log the request URL and parameters
    print(f"Request URL: {url}")
    print(f"Query Parameters: {querystring}")
    print(f"Headers: {headers}")

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {str(e)}")  # Debug
        return {'error': str(e)}
    

@app.route('/moon_phase_by_city', methods=['GET'])
def moon_phase_by_city():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    try:
        moon_data = get_moon_phase_by_city(city)
        if 'error' in moon_data:
            return jsonify({'error': moon_data['error']}), 401  # Unauthorized
        return jsonify(moon_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Weather API Function
def get_weather(city):
    api_key = "93257f7dacff47e3eafc03ca19b9a0344"  # Hardcode your key here
    if not api_key:
        return {'error': 'API key is missing'}

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

# Weather Route
@app.route('/weather', methods=['GET'])
def weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City name is required'}), 400

    weather_data = get_weather(city)
    return jsonify(weather_data)

# FDA Safety Alerts API Function
def get_safety_alerts(herb_name):
    url = "https://api.fda.gov/drug/event.json"
    params = {
        "search": f"patient.drug.medicinalproduct:{herb_name}",
        "limit": 5
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

# Safety Alerts Route
@app.route('/safety_alerts', methods=['GET'])
def safety_alerts():
    herb_name = request.args.get('herb')
    if not herb_name:
        return jsonify({'error': 'Herb name is required'}), 400

    alerts = get_safety_alerts(herb_name)
    return jsonify(alerts)

# Recipe Recommendations
try:
    recipes_df = pd.read_csv('recipes_data.csv')  # Load recipes data
except FileNotFoundError:
    recipes_df = pd.DataFrame(columns=['Recipe Name', 'Ingredients', 'Instructions'])

# Recipe Recommendations Route
@app.route('/recommend_recipes', methods=['GET'])
def recommend_recipes():
    herb_name = request.args.get('herb')
    if not herb_name:
        return jsonify({'error': 'Herb name is required'}), 400

    recommended_recipes = recipes_df[recipes_df['Ingredients'].str.contains(herb_name, case=False, na=False)]
    return jsonify(recommended_recipes.to_dict(orient='records'))

# Routes
@app.route('/')
def index():
    return render_template('medicinal_herbs.html')

@app.route('/api/herbs', methods=['GET', 'POST'])
def herbs():
    global herbs_df  # Declare herbs_df as global at the beginning of the function

    if request.method == 'GET':
        # Handle GET request (fetch herbs)
        search_query = request.args.get('search', '').lower()
        if herbs_df.empty:
            return jsonify({'error': 'No herbs data available'}), 404

        if search_query:
            filtered = herbs_df[
                herbs_df['Herb Name'].str.contains(search_query, case=False, na=False) |
                herbs_df['Medicinal properties'].str.contains(search_query, case=False, na=False) |
                herbs_df['Region/Origin'].str.contains(search_query, case=False, na=False)
            ]
            if filtered.empty:
                return jsonify({'message': 'No herbs found matching your search'}), 200
            return jsonify(filtered.to_dict(orient='records'))
        else:
            return jsonify(herbs_df.to_dict(orient='records'))

    elif request.method == 'POST':
        # Handle POST request (add a new herb)
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['Herb Name', 'Medicinal properties', 'Region/Origin', 'Description', 'Benefits']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        new_herb = pd.DataFrame([data])
        herbs_df = pd.concat([herbs_df, new_herb], ignore_index=True)
        herbs_df.to_csv('herbs_data.csv', index=False)  # Save updated data to CSV
        return jsonify({'message': 'Herb added successfully'}), 201

@app.route('/api/herbs/<string:name>', methods=['DELETE'])
def delete_herb(name):
    global herbs_df  # Declare herbs_df as global at the beginning of the function

    herb_index = herbs_df.index[herbs_df['Herb Name'].str.lower() == name.lower()].tolist()
    if not herb_index:
        return jsonify({'error': 'Herb not found'}), 404

    herbs_df = herbs_df.drop(herb_index)
    herbs_df.to_csv('herbs_data.csv', index=False)  # Save updated data to CSV
    return jsonify({'message': 'Herb deleted successfully'}), 200

@app.route('/api/herbs/<string:name>', methods=['PUT'])
def update_herb(name):
    global herbs_df  # Declare herbs_df as global at the beginning of the function

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    herb_index = herbs_df.index[herbs_df['Herb Name'].str.lower() == name.lower()].tolist()
    if not herb_index:
        return jsonify({'error': 'Herb not found'}), 404

    for key, value in data.items():
        if key in herbs_df.columns:
            herbs_df.at[herb_index[0], key] = value

    herbs_df.to_csv('herbs_data.csv', index=False)  # Save updated data to CSV
    return jsonify({'message': 'Herb updated successfully'}), 200

@app.route('/identify_plant', methods=['POST'])
def identify_plant():
    # Debug: Log the request headers
    print("Request headers:", request.headers)
    print("Request Content-Type:", request.headers.get('Content-Type'))  # Debug

    # Check if the Content-Type is multipart/form-data
    if not request.headers.get('Content-Type', '').startswith('multipart/form-data'):
        print("Error: Invalid Content-Type. Expected multipart/form-data.")  # Debug
        return jsonify({'error': 'Invalid Content-Type. Expected multipart/form-data.'}), 400

    # Check if an image file is provided
    if 'image' not in request.files:
        print("Error: No 'image' key in request.files")  # Debug
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        print("Error: No selected file")  # Debug
        return jsonify({'error': 'No selected file'}), 400

    # Debug: Log the file details
    print(f"File received: {image_file.filename}, {image_file.content_type}")  # Debug

    # Save the uploaded image temporarily
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    image_path = os.path.join(uploads_dir, image_file.filename)
    image_file.save(image_path)

    # Debug: Verify the file was saved
    print(f"Image saved at: {image_path}")  # Debug
    print(f"File exists: {os.path.exists(image_path)}")  # Debug

    # Upload the image to Gemini
    try:
        uploaded_file = genai.upload_file(image_path, mime_type="image/jpeg")
        print(f"Uploaded file '{uploaded_file.display_name}' as: {uploaded_file.uri}")  # Debug
    except Exception as e:
        print(f"Failed to upload image to Gemini: {str(e)}")  # Debug
        return jsonify({'error': f"Failed to upload image to Gemini: {str(e)}"}), 500

    # Create the Gemini model
    generation_config = {
        "temperature": 2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
    )

    # Start a chat session with the uploaded image
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    uploaded_file,
                    "Do you know what plant this is? How do I best take care of it?",
                ],
            },
        ]
    )

    # Send the question to Gemini
    try:
        response = chat_session.send_message("Do you know what plant this is? How do I best take care of it?")
        print(f"Gemini API Response: {response.text}")  # Debug
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")  # Debug
        return jsonify({'error': f"Failed to get response from Gemini: {str(e)}"}), 500
    finally:
        # Clean up the uploaded file
        try:
            os.remove(image_path)
            print(f"Deleted temporary file: {image_path}")  # Debug
        except Exception as e:
            print(f"Error deleting file: {str(e)}")  # Debug
            
# User Authentication Routes
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    try:
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401

        login_user(user)
        return jsonify({'message': 'Logged in successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/profile')
@login_required
def profile():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'favorites': current_user.favorites.split(',') if current_user.favorites else []
    })

@app.route('/add_favorite/<string:herb_name>', methods=['POST'])
@login_required
def add_favorite(herb_name):
    if herb_name not in current_user.favorites:
        current_user.favorites += f"{herb_name},"
        db.session.commit()
    return jsonify({'message': 'Herb added to favorites'}), 200

# Run the app
if __name__ == '__main__':
    # Create the uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)