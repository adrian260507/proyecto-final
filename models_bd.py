import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from flask import session, flash, redirect, url_for
from functools import wraps
import os

# Configuración de conexión

config = {
    "host": os.getenv("MYSQLHOST", "localhost"),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "sistemagestionbd"),
    "port": int(os.getenv("MYSQLPORT", 3306))
}

def conectar():
    return mysql.connector.connect(**config)

# =========================
# CREACIÓN DE TABLAS ACTUALIZADA - COINCIDENTE CON SQL
# =========================
def crear_tablas():
    con = conectar()
    cur = con.cursor()

    # Tabla usuarios (ACTUALIZADA con nuevos campos)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        ID_usuario INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100),
        correo VARCHAR(150) NOT NULL UNIQUE,
        contrasena VARCHAR(500) NOT NULL,
        celular VARCHAR(20),
        documento_id VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activo TINYINT(1) DEFAULT 1,
        email_verified TINYINT(1) DEFAULT 0,
        verification_token VARCHAR(10),
        token_created_at DATETIME,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)

    # Tabla roles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id_rol INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(50) NOT NULL,
        activo TINYINT(1) DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)

    # Tabla usuarios_roles (muchos a muchos)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios_roles (
        id_usuario_rol INT AUTO_INCREMENT PRIMARY KEY,
        id_usuario INT,
        id_rol INT,
        activo TINYINT(1) DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(ID_usuario) ON DELETE CASCADE,
        FOREIGN KEY (id_rol) REFERENCES roles(id_rol) ON DELETE CASCADE,
        UNIQUE KEY uq_usuario_rol_unico (id_usuario)
    )
    """)

    # Tabla eventos (ACTUALIZADA con nuevos campos)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos (
        id_evento INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        tipo_evento VARCHAR(50) NOT NULL,
        fecha_inicio DATETIME NOT NULL,
        fecha_fin DATETIME NOT NULL,
        lugar VARCHAR(150),
        ciudad VARCHAR(100),
        descripcion TEXT,
        cupo_maximo INT NOT NULL,
        id_organizador INT NOT NULL,
        activo TINYINT(1) DEFAULT 1,
        modalidad ENUM('virtual','presencial') NOT NULL DEFAULT 'presencial',
        enlace_virtual VARCHAR(500),
        hora_inicio_diaria TIME,
        hora_fin_diaria TIME,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_organizador) REFERENCES usuarios(ID_usuario)
    )
    """)

    # Tabla inscripciones (ACTUALIZADA con nuevos campos)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inscripciones (
        id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
        id_usuario INT NOT NULL,
        id_evento INT NOT NULL,
        asistio TINYINT(1) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        activo TINYINT(1) DEFAULT 1,
        certificado_notificado TINYINT(1) DEFAULT 0,
        porcentaje_asistencia DECIMAL(5,2) DEFAULT 0.00,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(ID_usuario) ON DELETE CASCADE,
        FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
        UNIQUE KEY uq_unica (id_usuario, id_evento)
    )
    """)

    # Tabla asistencias
    cur.execute("""
    CREATE TABLE IF NOT EXISTS asistencias (
        id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
        id_evento INT NOT NULL,
        id_usuario INT NOT NULL,
        fecha DATE NOT NULL,
        asistio TINYINT(1) DEFAULT 0,
        activo TINYINT(1) DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(ID_usuario) ON DELETE CASCADE,
        UNIQUE KEY uq_evt_user_day (id_evento, id_usuario, fecha)
    )
    """)

    # Tabla certificados (ACTUALIZADA con nuevo campo)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS certificados (
        id_certificado INT AUTO_INCREMENT PRIMARY KEY,
        id_inscripcion INT NOT NULL,
        fecha_emision DATETIME DEFAULT CURRENT_TIMESTAMP,
        numero_serie VARCHAR(64),
        archivo LONGBLOB,
        activo TINYINT(1) DEFAULT 1,
        enviado_por_correo TINYINT(1) DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion) ON DELETE CASCADE
    )
    """)

    # Tabla qr_asistencias (NUEVA)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qr_asistencias (
        id_qr INT AUTO_INCREMENT PRIMARY KEY,
        id_evento INT,
        token VARCHAR(64),
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_expiracion DATETIME,
        activo TINYINT(1) DEFAULT 1,
        usado_por INT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
        UNIQUE KEY token (token)
    )
    """)

    # Tabla eventos_procesados (NUEVA - para el scheduler)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS eventos_procesados (
        id_evento_procesado INT AUTO_INCREMENT PRIMARY KEY,
        id_evento INT NOT NULL,
        fecha_procesado DATETIME DEFAULT CURRENT_TIMESTAMP,
        tipo_procesamiento VARCHAR(50) DEFAULT 'certificados',
        FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE,
        UNIQUE KEY uq_evento_procesado (id_evento, tipo_procesamiento)
    )
    """)

    con.commit()
    con.close()

# =========================
# FUNCIONES DE CONSULTA (se mantienen igual)
# =========================
def q_all(sql, params=(), dictcur=False):
    con = conectar()
    cur = con.cursor(dictionary=dictcur)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    con.close()
    return rows

def q_one(sql, params=(), dictcur=False):
    rows = q_all(sql, params, dictcur=dictcur)
    return rows[0] if rows else None

def q_exec(sql, params=()):
    con = conectar()
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    last_id = cur.lastrowid
    cur.close()
    con.close()
    return last_id

# =========================
# DECORADORES (se mantienen igual)
# =========================
def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if "uid" not in session:
            flash("Debes iniciar sesión.", "warning")
            return redirect(url_for("auth.login"))
        return f(*a, **k)
    return w

def role_required(*ids):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if "uid" not in session:
                flash("Debes iniciar sesión.", "warning")
                return redirect(url_for("auth.login"))
            if session.get("rol_id") not in ids:
                flash("No tienes permisos.", "danger")
                return redirect(url_for("publico.inicio_publico"))
            return f(*a, **k)
        return w

    return deco

