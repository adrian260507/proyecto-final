from .db import q_exec

#funcion para establecer roles
def ensure_roles():
    # id_rol: 1 Usuario, 2 Administrador, 3 Organizador
    for rid, name in [(1, "Usuario"), (2, "Administrador"), (3, "Organizador")]:
        q_exec(
            "INSERT INTO roles (id_rol, nombre) VALUES (%s,%s) "
            "ON DUPLICATE KEY UPDATE nombre=VALUES(nombre)",
            (rid, name)
        )
