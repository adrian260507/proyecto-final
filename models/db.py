import mysql.connector
from flask import current_app

# funcion para conectar con base de datos
def conectar():
    cfg = current_app.config
    return mysql.connector.connect(
        host=cfg["DB_HOST"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        port=cfg["DB_PORT"]
    )
    
#funcion para extraer todas las filas en una consulta
def q_all(sql, params=(), dictcur=False):
    con = conectar()                             # 1️⃣ Abre una conexión a la base de datos.
    cur = con.cursor(dictionary=dictcur)         # 2️⃣ Crea un cursor (permite ejecutar comandos SQL).
    cur.execute(sql, params)                     # 3️⃣ Ejecuta la consulta SQL con los parámetros dados.
    rows = cur.fetchall()                        # 4️⃣ Recupera todas las filas de resultados.
    cur.close(); con.close()                     # 5️⃣ Cierra el cursor y la conexión.
    return rows                                  # 6️⃣ Devuelve la lista de filas obtenidas.

#funcion para devolver un solo resultado
def q_one(sql, params=(), dictcur=False):
    rows = q_all(sql, params, dictcur=dictcur)   # 1️⃣ Ejecuta la consulta usando q_all()
    return rows[0] if rows else None             # 2️⃣ Devuelve la primera fila, o None si no hay resultados

#funcion para modificar datos (no devolver filas)
def q_exec(sql, params=()):
    con = conectar()            # 1️⃣ Abre una conexión a la base de datos
    cur = con.cursor()          # 2️⃣ Crea un cursor para ejecutar la consulta
    cur.execute(sql, params)    # 3️⃣ Ejecuta la instrucción SQL con los parámetros dados
    con.commit()                # 4️⃣ Confirma los cambios en la base de datos (commit)
    last = cur.lastrowid        # 5️⃣ Obtiene el ID del último registro insertado (si aplica)
    cur.close(); con.close()    # 6️⃣ Cierra el cursor y la conexión
    return last                 # 7️⃣ Devuelve el ID del último registro insertado

