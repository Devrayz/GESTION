import streamlit as st
import database as db
import auth
import logic

# 1. Configuración Global
st.set_page_config(page_title="Gestor de Obras", layout="wide", page_icon="🏗️")

# 2. Inicializar DB y Sesión
db.init_db()
auth.init_session()

# 3. Control de Flujo Principal
if st.session_state['logged_in']:
    # --- USUARIO LOGUEADO ---
    usuario = st.session_state['user_info']
    
    # Sidebar común
    st.sidebar.write(f"👤 **{usuario['nombre']}**")
    st.sidebar.caption(f"Rol: {usuario['rol']}")
    if st.sidebar.button("Cerrar Sesión"):
        auth.logout()
    st.sidebar.divider()
    
    # Router de Vistas
    if usuario['rol'] == 'Admin':
        logic.view_admin_dashboard()
    else:
        logic.view_operario_dashboard(usuario['email'])

else:
    # --- PANTALLA DE LOGIN ---
    auth.show_login()