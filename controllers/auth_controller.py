from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from . import auth_bp
from models.user import User
from models.db import q_exec

# Crea un serializador seguro con temporizador usando la SECRET_KEY de la aplicación
def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

@auth_bp.route("/registro", methods=["GET","POST"])
def registro():
    if request.method == "POST":
        # Obtener y limpiar datos del formulario
        nombre = request.form.get("nombre","").strip()
        apellido = request.form.get("apellido","").strip()
        correo = request.form.get("correo","").strip().lower()
        contrasena = request.form.get("contrasena","").strip()
        celular = request.form.get("celular","").strip()
        documento_id = request.form.get("documento_id","").strip()

        # Validar campos obligatorios
        if not (nombre and apellido and correo and contrasena):
            flash("Completa los campos obligatorios.", "warning")
            return render_template("auth/registro.html")

        # Verificar si el correo ya está registrado
        if User.get_by_email(correo):
            flash("Este correo electrónico ya está registrado.", "danger")
            return render_template("auth/registro.html")

        # Crear usuario
        try:
            uid = User.create_user(nombre, apellido, correo, contrasena, celular or None, documento_id or None)
            
            # ❌ VERIFICACIÓN DE CORREO DESACTIVADA - Iniciar sesión directamente
            user = User.get_by_id(uid)
            if user:
                login_user(user)
                flash("✅ Cuenta creada exitosamente. ¡Bienvenido/a!", "success")
                return redirect(url_for("publico.inicio_publico"))
            else:
                flash("Cuenta creada pero no se pudo iniciar sesión automáticamente. Por favor, inicia sesión.", "warning")
                return redirect(url_for("auth.login"))
                
        except Exception as e:
            current_app.logger.error(f"Error creando usuario: {e}")
            flash("Error al crear la cuenta. Por favor, intenta nuevamente.", "danger")
            return render_template("auth/registro.html")
    
    return render_template("auth/registro.html")

# ❌ ELIMINADA LA RUTA DE VERIFICACIÓN DE CORREO
# @auth_bp.route("/verify-email", methods=["GET", "POST"])
# def verify_email():

# ❌ ELIMINADA LA RUTA DE REENVÍO DE VERIFICACIÓN
# @auth_bp.route("/resend-verification", methods=["POST"])

# Ruta para inicio de sesión de usuarios - SIN VERIFICACIÓN DE CORREO
@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        flash("Ya tienes una sesión activa.", "info")
        return redirect(url_for("publico.inicio_publico"))
    
    if request.method == "POST":
        correo = request.form.get("correo","").strip().lower()
        contrasena = request.form.get("contrasena","").strip()
        user = User.get_by_email(correo)
        
        if user and check_password_hash(user.contrasena, contrasena):
            if not user.is_active:
                flash("El usuario está deshabilitado", "danger")
            else:
                # ❌ SIN VERIFICACIÓN DE CORREO - Iniciar sesión directamente
                login_user(user)
                flash("Bienvenido/a", "success")
                return redirect(url_for("publico.inicio_publico"))
        else:
            flash("Credenciales inválidas.", "danger")
    
    return render_template("auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("publico.inicio_publico"))

#ruta para configurar la cuenta del usuario
@auth_bp.route("/configuracion", methods=["GET", "POST"])
@login_required
def configuracion_usuario():
    if request.method == "POST":
        data = {
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'celular': request.form.get('celular'),
            'documento_id': request.form.get('documento_id')
        }
        
        if User.actualizar_usuario(current_user.id, data):
            flash("Tus datos se han actualizado correctamente.", "success")
            # Recargar usuario actualizado
            updated_user = User.get_by_id(current_user.id)
            login_user(updated_user)  # Actualizar la sesión
            return redirect(url_for('auth.configuracion_usuario'))
        else:
            flash("Error al actualizar los datos. Intenta nuevamente.", "danger")
    
    return render_template("auth/configuracion_usuario.html", usuario=current_user)

#ruta para cambiar la contraseña
@auth_bp.route("/configuracion/cambiar-password", methods=["POST"])
@login_required
def cambiar_password():
    from models.db import q_exec
    from werkzeug.security import generate_password_hash
    
    password_actual = request.form.get('password_actual')
    nueva_password = request.form.get('nueva_password')
    confirmar_password = request.form.get('confirmar_password')
    
    if not password_actual or not nueva_password:
        flash("Todos los campos son obligatorios.", "danger")
        return redirect(url_for('auth.configuracion_usuario'))
    
    if nueva_password != confirmar_password:
        flash("Las nuevas contraseñas no coinciden.", "danger")
        return redirect(url_for('auth.configuracion_usuario'))
    
    if len(nueva_password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "danger")
        return redirect(url_for('auth.configuracion_usuario'))
    
    # Verificar contraseña actual
    if not check_password_hash(current_user.contrasena, password_actual):
        flash("La contraseña actual es incorrecta.", "danger")
        return redirect(url_for('auth.configuracion_usuario'))
    
    # Actualizar contraseña
    hashed_password = generate_password_hash(nueva_password)
    q_exec("UPDATE usuarios SET contrasena=%s WHERE ID_usuario=%s", 
           (hashed_password, current_user.id))
    
    flash("Contraseña actualizada correctamente.", "success")
    return redirect(url_for('auth.configuracion_usuario'))

#ruta cuando se olvida la contraseña
@auth_bp.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        user = User.get_by_email(email)
        
        if user:
            try:
                token = _serializer().dumps(email, salt="recuperar-salt")
                link = url_for("auth.reset_password", token=token, _external=True)
                
                # USAR TEMPLATE EN LUGAR DE HTML MANUAL
                from utils.email_renderer import send_templated_email
                
                context = {
                    'usuario_nombre': user.nombre,
                    'url_reset': link
                }
                
                success = send_templated_email(
                    subject="Recuperación de contraseña - Sistema de Gestión",
                    recipients=[email],
                    template_path="emails/auth/recuperar.html",
                    **context
                )
                
                if success:
                    current_app.logger.info(f"✅ Correo de recuperación enviado exitosamente a: {email}")
                    flash("Se ha enviado un enlace de recuperación a tu correo electrónico.", "success")
                else:
                    current_app.logger.error(f"❌ Fallo al enviar correo de recuperación a: {email}")
                    flash("Error al enviar el correo. Por favor, intenta más tarde.", "danger")
                    
            except Exception as e:
                current_app.logger.exception(f"💥 Error en proceso de recuperación para {email}: {e}")
                flash("Ocurrió un error inesperado. Por favor, contacta al administrador.", "danger")
        else:
            current_app.logger.warning(f"Intento de recuperación para email no registrado: {email}")
            flash("Si existe una cuenta con ese correo, se ha enviado un enlace para restablecer la contraseña.", "info")
        
        return redirect(url_for("auth.forgot"))
    
    return render_template("auth/forgot.html")

#ruta para validar token de reinicio de contraseña
@auth_bp.route("/reset/<token>", methods=["GET","POST"])
def reset_password(token):
    try:
        email = _serializer().loads(token, salt="recuperar-salt", max_age=3600)
    except SignatureExpired:
        flash("El enlace expiró. Solicita uno nuevo.", "warning")
        return redirect(url_for("auth.forgot"))
    except BadSignature:
        flash("Token inválido.", "warning")
        return redirect(url_for("auth.forgot"))

    user = User.get_by_email(email) 
    if not user:
        flash("Cuenta no encontrada.", "danger")
        return redirect(url_for("auth.registro"))

    if request.method == "POST":
        p1 = request.form.get("password","").strip()
        p2 = request.form.get("password2","").strip()
        if not p1 or p1 != p2:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("auth/reset.html", token=token)
        hashed = generate_password_hash(p1)
        q_exec("UPDATE usuarios SET contrasena=%s WHERE correo=%s", (hashed, email))
        flash("Contraseña actualizada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset.html", token=token)

@auth_bp.route("/admin-reset-passwords")
def admin_reset_passwords():
    """Endpoint temporal para resetear todas las contraseñas"""
    from models.db import q_all, q_exec
    from werkzeug.security import generate_password_hash
    
    # Solo permitir a admins
    if not current_user.is_authenticated or current_user.rol_id != 2:
        return "No autorizado", 403
    
    # Contraseña temporal
    temp_password = "Temp123!"
    hashed_password = generate_password_hash(temp_password)
    
    # Resetear todos los usuarios excepto el admin principal
    q_exec("""
        UPDATE usuarios 
        SET contrasena = %s 
        WHERE correo != 'adriansernagonzalez260507@gmail.com'
    """, (hashed_password,))
    
    return f"""
    <h1>Contraseñas Reseteadas</h1>
    <p>Se han actualizado todas las contraseñas.</p>
    <p><strong>Contraseña temporal: {temp_password}</strong></p>
    <p>Los usuarios deben cambiar su contraseña después del primer login.</p>
    """



