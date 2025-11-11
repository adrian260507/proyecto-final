from flask import Flask,render_template
from flask_mail import Mail
from flask_login import LoginManager  
from config import Config
from utils.filters import register_filters
from controllers import publico_bp, auth_bp, eventos_bp, admin_bp
from models.rol import ensure_roles
from models.user import ensure_default_admin, User  
from dotenv import load_dotenv
#por comentar

load_dotenv()

mail = Mail()
login_manager = LoginManager()  

#por comentar

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensiones
    mail.init_app(app)
    login_manager.init_app(app)
    
    
    # Configuración Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    

    # Filtros Jinja - ESTA LÍNEA DEBE ESTAR PRESENTE
    register_filters(app)
    

    # Blueprints
    app.register_blueprint(publico_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(eventos_bp, url_prefix="/eventos")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404  # Cambiado

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500  # Cambiado
    
    # Bootstrap de datos esenciales
    with app.app_context():
        try:
            ensure_roles()
            ensure_default_admin()
            
#por comentar

                
        except Exception as e:
            app.logger.warning(f"Bootstrap warning: {e}")

    return app
#por comentar

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.get_by_id(int(user_id))

