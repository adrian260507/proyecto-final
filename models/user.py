from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db import q_one, q_exec
import random
from datetime import datetime, timedelta

class User(UserMixin):
    def __init__(self, id_usuario, nombre, apellido, correo, contrasena, celular, documento_id, created_at, activo, rol_id, email_verified=False, verification_token=None, token_created_at=None):
        self.id = id_usuario
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.contrasena = contrasena
        self.celular = celular
        self.documento_id = documento_id
        self.created_at = created_at
        self.activo = activo
        self.rol_id = rol_id
        self.email_verified = email_verified
        self.verification_token = verification_token
        self.token_created_at = token_created_at

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.activo == 1

    # MÉTODOS ESTÁTICOS PARA VERIFICACIÓN DE CORREO
    @staticmethod
    def generate_verification_token():
        """Genera un token de verificación de 6 dígitos"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    @staticmethod
    def set_verification_token(user_id, token):
        """Establece el token de verificación para un usuario"""
        q_exec(
            "UPDATE usuarios SET verification_token=%s, token_created_at=NOW() WHERE ID_usuario=%s",
            (token, user_id)
        )

    @staticmethod
    def verify_email_with_token(user_id, token):
        """Verifica el correo usando el token"""
        # Verificar token y que no haya expirado (válido por 24 horas)
        user_data = q_one(
            "SELECT verification_token, token_created_at FROM usuarios WHERE ID_usuario=%s",
            (user_id,), dictcur=True
        )
        
        if not user_data or not user_data['verification_token']:
            return False, "Token no encontrado"
        
        # Verificar expiración (24 horas)
        token_created = user_data['token_created_at']
        if isinstance(token_created, str):
            token_created = datetime.strptime(token_created, '%Y-%m-%d %H:%M:%S')
        
        if datetime.now() - token_created > timedelta(hours=24):
            return False, "El token ha expirado"
        
        if user_data['verification_token'] != token:
            return False, "Token incorrecto"
        
        # Marcar correo como verificado y limpiar token
        q_exec(
            "UPDATE usuarios SET email_verified=1, verification_token=NULL, token_created_at=NULL WHERE ID_usuario=%s",
            (user_id,)
        )
        
        return True, "Correo verificado exitosamente"

    @staticmethod
    def is_email_verified(user_id):
        """Verifica si el correo está verificado"""
        result = q_one(
            "SELECT email_verified FROM usuarios WHERE ID_usuario=%s",
            (user_id,), dictcur=True
        )
        return result and result.get('email_verified', 0) == 1

    # MÉTODOS ESTÁTICOS EXISTENTES (actualizados con nuevos campos)
    @staticmethod
    def get_by_email(email: str):
        row = q_one("""
            SELECT u.*, ur.id_rol 
            FROM usuarios u 
            LEFT JOIN usuarios_roles ur ON u.ID_usuario = ur.id_usuario 
            WHERE u.correo=%s
        """, (email,), dictcur=True)
        if row:
            return User(
                id_usuario=row['ID_usuario'],
                nombre=row['nombre'],
                apellido=row['apellido'],
                correo=row['correo'],
                contrasena=row['contrasena'],
                celular=row['celular'],
                documento_id=row['documento_id'],
                created_at=row['created_at'],
                activo=row['activo'],
                rol_id=row['id_rol'],
                email_verified=row.get('email_verified', 0) == 1,
                verification_token=row.get('verification_token'),
                token_created_at=row.get('token_created_at')
            )
        return None
    #funcion para crear obtener un usuario en base al id 
    @staticmethod
    def get_by_id(uid: int):
        row = q_one("""
            SELECT u.*, ur.id_rol 
            FROM usuarios u 
            LEFT JOIN usuarios_roles ur ON u.ID_usuario = ur.id_usuario 
            WHERE u.ID_usuario=%s
        """, (uid,), dictcur=True)
        if row:
            return User(
                id_usuario=row['ID_usuario'],
                nombre=row['nombre'],
                apellido=row['apellido'],
                correo=row['correo'],
                contrasena=row['contrasena'],
                celular=row['celular'],
                documento_id=row['documento_id'],
                created_at=row['created_at'],
                activo=row['activo'],
                rol_id=row['id_rol'],
                email_verified=row.get('email_verified', 0) == 1,
                verification_token=row.get('verification_token'),
                token_created_at=row.get('token_created_at')
            )
        return None
    #funcion para crear usuario 
    @staticmethod
    def create_user(nombre, apellido, correo, contrasena, celular=None, documento_id=None):
        # FORZAR PBKDF2 con parámetros consistentes
        hashed = generate_password_hash(
            contrasena, 
            method='pbkdf2:sha256',
            salt_length=16
        )
        uid = q_exec("""
            INSERT INTO usuarios (nombre, apellido, correo, contrasena, celular, documento_id)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (nombre, apellido, correo, hashed, (celular or None), (documento_id or None)))
        
        q_exec("""
            INSERT IGNORE INTO usuarios_roles (id_usuario, id_rol)
            VALUES (%s, 1)
        """, (uid,))
        return uid
    #funcion para actualizar a los usuarios 
    @staticmethod
    def actualizar_usuario(uid: int, data: dict):
        campos_permitidos = ['nombre', 'apellido', 'celular', 'documento_id']
        updates = []
        params = []
        
        for campo in campos_permitidos:
            if campo in data and data[campo] is not None:
                updates.append(f"{campo}=%s")
                params.append(data[campo].strip())
        
        if not updates:
            return False
        
        params.append(uid)
        sql = f"UPDATE usuarios SET {', '.join(updates)} WHERE ID_usuario=%s"
        
        try:
            q_exec(sql, tuple(params))
            return True
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error actualizando usuario: {e}")
            return False

def ensure_default_admin():
    admin = q_one("""
        SELECT u.ID_usuario
        FROM usuarios u
        JOIN usuarios_roles ur ON ur.id_usuario=u.ID_usuario
        WHERE ur.id_rol=2
        LIMIT 1
    """)
    if admin:
        return
    uid = User.create_user("Admin", "Sistema", "admin@sgtc.local", "Admin123*")

    q_exec("UPDATE usuarios_roles SET id_rol=2 WHERE id_usuario=%s", (uid,))
