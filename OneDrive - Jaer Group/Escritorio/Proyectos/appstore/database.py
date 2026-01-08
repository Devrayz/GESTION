import sqlite3
import pandas as pd
import streamlit as st

DB_NAME = 'obras.db'

def init_db():
    """Inicializa la estructura de tablas si no existen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (email TEXT PRIMARY KEY, nombre TEXT, rol TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tareas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  casa TEXT, 
                  tarea TEXT, 
                  estado TEXT, 
                  asignado_a TEXT, 
                  dependencia_id INTEGER)''')
    
    # Usuario Admin por defecto
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin@jaer.com', 'Admin Jaer', 'Admin')")
    conn.commit()
    conn.close()

def run_query(query, params=(), return_data=False):
    """Ejecuta queries de forma segura."""
    conn = sqlite3.connect(DB_NAME)
    try:
        if return_data:
            df = pd.read_sql(query, conn, params=params)
            return df
        else:
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
    except Exception as e:
        st.error(f"Error de Base de Datos: {e}")
    finally:
        conn.close()


def delete_task(task_id):
    """Elimina una tarea por ID."""
    run_query("DELETE FROM tareas WHERE id=?", (task_id,))

def update_task_general(task_id, nuevo_nombre, nueva_casa, nueva_dependencia):
    """Actualiza los datos generales de una tarea (nombre, casa, dependencia)."""
    # Calculamos el estado inicial de nuevo por si cambió la dependencia
    estado = "Pendiente"
    if nueva_dependencia:
        estado = "Bloqueado"
        
    run_query('''UPDATE tareas 
                 SET tarea=?, casa=?, dependency_id=?, estado=? 
                 WHERE id=?''', 
              (nuevo_nombre, nueva_casa, nueva_dependencia, estado, task_id))