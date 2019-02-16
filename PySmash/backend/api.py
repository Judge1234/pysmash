import platform
import psutil
import threading
from datetime import datetime
from config import Config
from auto import Smasher
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_basicauth import BasicAuth




#   API and Database Configurations
app = Flask(__name__)
app.config.from_object(Config)
basic_auth = BasicAuth(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
options = Options()
options.headless = False

THREADLOCK      = threading.Lock()
GLOBAL_COUNT    = 0
URL_0           = 'https://www.google.com/'




#   Session Model
class SmashLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)   
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    target = db.Column(db.String(250))
    count = db.Column(db.Integer)

    def __init__(self, target, count):
        self.target = target
        self.count=count
        
    def __str__(self):
        return f'Session {self.timestamp}'





#   Threading Functions
def run(*, smash_amount):
    assert type(smash_amount) == int
    driver = webdriver.Chrome(ChromeDriverManager().install(),
                              chrome_options=options)
    smash_0 = Smasher(driver, URL_0)
    for i in range(smash_amount):
        smash_0.start()
        global GLOBAL_COUNT
        with THREADLOCK:
            GLOBAL_COUNT += 1
    

def threaded_smash(*, smash_amount, num_threads):
    threads = []
    for i in range(num_threads):
            thread = threading.Thread(target=run, kwargs={'smash_amount': smash_amount})
            threads.append(thread)      
    [t.start() for t in threads]

            
def reset_global():
    global GLOBAL_COUNT
    GLOBAL_COUNT = 0






#   API Routes
@app.route('/data')
@app.route('/')
def index():
    return jsonify({"GLOBAL_COUNT": GLOBAL_COUNT,
                    "CPU": psutil.cpu_times_percent(),
                    "FAN RPM": psutil.sensors_fans()})


@app.route('/execute', methods=['GET', 'POST'])
@basic_auth.required
def execute():
    amount = request.json['amount']
    threads = request.json['threads']
    try:
        threaded_smash(smash_amount=int(amount), num_threads=threads)
        session = SmashLog(URL, amount * threads)
        db.session.add(session)
        db.session.commit()
    except Exception:
        return jsonify({"Error": "Invalid Entry"})
    
    return jsonify({"Status": "In Progress",
                    "Targets": [URL_0],
                    "Total Hits": amount * threads,
                    "Threads": threads,
                    "Running On": platform.platform(),
                    "Network Data": psutil.net_if_addrs()}), 201


@app.route('/history')
@basic_auth.required
def get_sessions():
    sessions = db.session.query(SmashLog).all()
    cumulative = 0
    output = []
    for session in sessions:
        session_data = {}
        session_data['timestamp'] = session.timestamp
        session_data['target'] = session.target
        session_data['count'] = session.count
        cumulative += session.count
        output.append(session_data)

    return jsonify({"Total": cumulative,
                    "Session Count": len(sessions),
                    "Sessions": output})
        

@app.route('/reset')
def reset():
    reset_global()
    return jsonify({"Status": "Global Count Reset"})


@app.errorhandler(404)
def error404(error):
    return jsonify({"Status":"Error: 404"}), 404


@app.errorhandler(401)
def error401(error):
    return jsonify({"Status":"Error: 401"}), 401
    








