import streamlit as st
import time
import database as db # Importamos nuestro módulo de DB

def init_session():
    """Inicializa variables de sesión si no existen."""
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user_info' not in st.session_state:
        st.session_state['user_info'] = None

def show_login():
    """Muestra la pantalla de login y maneja la lógica de entrada."""
    st.title("🔐 Acceso al Sistema")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942813.png", width=150)
    
    with col2:
        with st.form("login_form"):
            st.write("Ingresa tu correo para comenzar")
            email_input = st.text_input("Correo Electrónico").lower().strip()
            nombre_input = st.text_input("Tu Nombre (Solo si eres nuevo)")
            submitted = st.form_submit_button("Entrar 🚀")
            
            if submitted and email_input:
                # Usamos nuestra función modularizada
                user_data = db.run_query("SELECT * FROM usuarios WHERE email=?", (email_input,), return_data=True)
                
                if not user_data.empty:
                    # Usuario existe
                    st.session_state['user_info'] = user_data.iloc[0]
                    st.session_state['logged_in'] = True
                    st.success(f"Bienvenido, {user_data.iloc[0]['nombre']}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    # Usuario nuevo
                    if nombre_input:
                        rol = "Admin" if "admin" in email_input else "Operario"
                        db.run_query("INSERT INTO usuarios VALUES (?, ?, ?)", (email_input, nombre_input, rol))
                        
                        st.session_state['user_info'] = {'email': email_input, 'nombre': nombre_input, 'rol': rol}
                        st.session_state['logged_in'] = True
                        st.success("Cuenta creada!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("⚠️ Escribe tu nombre para registrarte.")

def logout():
    """Cierra la sesión."""
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.rerun()