# TU CÓDIGO ACTUAL (mantener)
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# AGREGAR ESTA LÍNEA
from flask_mail import Mail

# TU FUNCIÓN create_app ACTUAL - MODIFICAR:
def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    
    # TUS CONFIGURACIONES ACTUALES (mantener)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # AGREGAR CONFIGURACIONES DE EMAIL
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    # TUS INICIALIZACIONES ACTUALES (mantener)
    CORS(app, origins=os.getenv('CORS_ORIGINS', '').split(','))
    jwt = JWTManager(app)
    
    # AGREGAR ESTA LÍNEA
    mail = Mail(app)
    
    # Hacer mail accesible globalmente
    app.mail = mail
    
    # TUS BLUEPRINTS ACTUALES (mantener)
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    return app