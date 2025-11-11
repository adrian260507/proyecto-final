from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db import q_one, q_exec

class User(UserMixin):
    def __init__(self, id_usuario, nombre, apellido, correo, contrasena, celular, documento_id, created_at, activo, rol_id):
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

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.activo == 1

    # MÉTODOS ESTÁTICOS EXISTENTES (simplificados sin verificación de correo)
    @staticmethod
    def get_by_email(email: str):
        try:
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
                    rol_id=row['id_rol']
                )
            return None
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error en get_by_email: {e}")
            return None

    @staticmethod
    def get_by_id(uid: int):
        try:
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
                    rol_id=row['id_rol']
                )
            return None
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error en get_by_id: {e}")
            return None

    @staticmethod
    def create_user(nombre, apellido, correo, contrasena, celular=None, documento_id=None):
        """Crea un usuario sin verificación de correo"""
        try:
            hashed = generate_password_hash(contrasena)
            uid = q_exec("""
                INSERT INTO usuarios (nombre, apellido, correo, contrasena, celular, documento_id, email_verified)
                VALUES (%s,%s,%s,%s,%s,%s,1)
            """, (nombre, apellido, correo, hashed, (celular or None), (documento_id or None)))
            
            q_exec("""
                INSERT IGNORE INTO usuarios_roles (id_usuario, id_rol)
                VALUES (%s, 1)
            """, (uid,))
            
            from flask import current_app
            current_app.logger.info(f"✅ Usuario creado exitosamente: {correo} (ID: {uid})")
            return uid
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"❌ Error creando usuario {correo}: {e}")
            raise

    @staticmethod
    def actualizar_usuario(uid: int, data: dict):
        campos_permitidos = ['nombre', 'apellido', 'celular', 'documento_id']
        updates = []
        params = []
        
        for campo in campos_permitidos:
            if campo in data and data[campo] is not None:
                updates.append(f"{campo}=%s")
                # Si el valor está vacío, guardar como NULL
                value = data[campo].strip()
                params.append(value if value else None)
        
        if not updates:
            return False
        
        params.append(uid)
        sql = f"UPDATE usuarios SET {', '.join(updates)} WHERE ID_usuario=%s"
        
        try:
            q_exec(sql, tuple(params))
            return True
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error actualizando usuario {uid}: {e}")
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
    try:
        uid = User.create_user("Admin", "Sistema", "admin@sgtc.local", "Admin123*")
        q_exec("UPDATE usuarios_roles SET id_rol=2 WHERE id_usuario=%s", (uid,))
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error creando admin por defecto: {e}")

