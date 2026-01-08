import streamlit as st
import database as db

def view_admin_dashboard():
    st.title("📊 Panel de Control (Admin)")
    
    # KPIs
    df_tareas = db.run_query("SELECT * FROM tareas", return_data=True)
    if not df_tareas.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df_tareas))
        c2.metric("Pendientes", len(df_tareas[df_tareas['estado']=='Pendiente']))
        c3.metric("Bloqueadas", len(df_tareas[df_tareas['estado']=='Bloqueado']))
        
        # Filtro
        casas = ["Todas"] + list(df_tareas['casa'].unique())
        filtro = st.selectbox("Filtrar por Casa", casas)
        vista = df_tareas if filtro == "Todas" else df_tareas[df_tareas['casa'] == filtro]
        st.dataframe(vista, use_container_width=True, hide_index=True)
    else:
        st.info("No hay tareas aún.")

    # Crear Tarea
    with st.expander("➕ Asignar Nueva Tarea"):
        users_df = db.run_query("SELECT email FROM usuarios", return_data=True)
        with st.form("new_task"):
            t_nombre = st.text_input("Tarea")
            t_casa = st.selectbox("Casa", ["Casa Lote 4", "Apto 502", "Casa Campestre"])
            # Manejo de error si no hay usuarios aún
            opciones_users = users_df['email'] if not users_df.empty else []
            t_asignado = st.selectbox("Responsable", opciones_users)
            
            # Dependencia
            t_dependencia = st.selectbox("¿Depende de otra tarea? (ID)", [None] + (list(df_tareas['id'].unique()) if not df_tareas.empty else []))
            
            if st.form_submit_button("Crear"):
                estado_inicial = "Bloqueado" if t_dependencia else "Pendiente"
                db.run_query("INSERT INTO tareas (casa, tarea, estado, asignado_a, dependencia_id) VALUES (?, ?, ?, ?, ?)", 
                          (t_casa, t_nombre, estado_inicial, t_asignado, t_dependencia))
                st.success("Tarea Asignada")
                st.rerun()

def view_operario_dashboard(usuario_email):
    st.title(f"Panel de Operario 👷")
    
    # 1. Organizamos en Pestañas
    tab1, tab2 = st.tabs(["📋 Mis Tareas", "➕ Crear Tarea Propia"])
    
    # --- PESTAÑA 1: LISTAR, EDITAR Y BORRAR ---
    with tab1:
        mis_tareas = db.run_query("SELECT * FROM tareas WHERE asignado_a=?", (usuario_email,), return_data=True)
        
        if mis_tareas.empty:
            st.info("No tienes tareas activas.")
        else:
            for index, row in mis_tareas.iterrows():
                # Contenedor visual de la tarea
                with st.container(border=True):
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"**{row['tarea']}**")
                        st.caption(f"🏠 {row['casa']} | Estado: {row['estado']}")
                    
                    with col_actions:
                        # Botón para activar modo edición
                        modo_edicion = st.toggle("Editar", key=f"edit_mode_{row['id']}")
                    
                    # --- MODO LECTURA/AVANCE (Lo de siempre) ---
                    if not modo_edicion:
                        # Lógica de Bloqueo
                        bloqueado = False
                        if row['dependencia_id']:
                            padre = db.run_query("SELECT estado, tarea FROM tareas WHERE id=?", (row['dependencia_id'],), return_data=True)
                            if not padre.empty and padre.iloc[0]['estado'] != "Terminado":
                                bloqueado = True
                                st.error(f"⛔ Esperando a: {padre.iloc[0]['tarea']}")
                        
                        if not bloqueado:
                            # Selector de Estado rápido
                            estados = ["Pendiente", "En Progreso", "Terminado"]
                            idx_actual = estados.index(row['estado']) if row['estado'] in estados else 0
                            nuevo_estado = st.radio("Avance:", estados, index=idx_actual, key=f"status_{row['id']}", horizontal=True)
                            
                            if nuevo_estado != row['estado']:
                                db.run_query("UPDATE tareas SET estado=? WHERE id=?", (nuevo_estado, row['id']))
                                # Desbloqueo automático de hijos
                                if nuevo_estado == "Terminado":
                                    hijos = db.run_query("SELECT id FROM tareas WHERE dependencia_id=?", (row['id'],), return_data=True)
                                    for _, hijo in hijos.iterrows():
                                        db.run_query("UPDATE tareas SET estado='Pendiente' WHERE id=?", (hijo['id'],))
                                st.rerun()

                    # --- MODO EDICIÓN COMPLETA (CRUD) ---
                    else:
                        st.warning("✏️ Editando detalles de la tarea")
                        with st.form(key=f"form_edit_{row['id']}"):
                            edit_nombre = st.text_input("Nombre", value=row['tarea'])
                            edit_casa = st.selectbox("Casa", ["Casa Lote 4", "Apto 502", "Casa Campestre"], index=0) # Idealmente traer de DB
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.form_submit_button("💾 Guardar Cambios"):
                                    # Actualizamos nombre y casa (mantenemos dependencia actual por simplicidad o agregas el campo)
                                    db.run_query("UPDATE tareas SET tarea=?, casa=? WHERE id=?", (edit_nombre, edit_casa, row['id']))
                                    st.success("Modificado")
                                    st.rerun()
                            with c2:
                                if st.form_submit_button("🗑️ Eliminar Tarea", type="primary"):
                                    db.delete_task(row['id'])
                                    st.success("Eliminada")
                                    st.rerun()

    # --- PESTAÑA 2: CREAR TAREA (CREATE) ---
    with tab2:
        st.subheader("Registrar nueva actividad")
        with st.form("form_crear_propia"):
            new_nombre = st.text_input("¿Qué vas a hacer?")
            new_casa = st.selectbox("Ubicación / Casa", ["Casa Lote 4", "Apto 502", "Casa Campestre"])
            
            # El operario puede auto-asignarse dependencias si quiere
            # Traemos todas las tareas para que pueda elegir si depende de algo
            all_tasks = db.run_query("SELECT id, tarea FROM tareas", return_data=True)
            opciones_dep = [None] + list(all_tasks['id']) if not all_tasks.empty else [None]
            new_dep = st.selectbox("¿Depende de otra tarea? (Opcional)", opciones_dep, format_func=lambda x: f"ID {x}" if x else "No")

            submitted = st.form_submit_button("Crear Tarea")
            
            if submitted and new_nombre:
                estado_inicial = "Bloqueado" if new_dep else "Pendiente"
                # Se asigna a sí mismo (usuario_email)
                db.run_query("INSERT INTO tareas (casa, tarea, estado, asignado_a, dependencia_id) VALUES (?, ?, ?, ?, ?)", 
                          (new_casa, new_nombre, estado_inicial, usuario_email, new_dep))
                st.success("¡Tarea creada y asignada a ti!")
                st.rerun()
    st.title(f"Mis Tareas 👷")
    mis_tareas = db.run_query("SELECT * FROM tareas WHERE asignado_a=?", (usuario_email,), return_data=True)
    
    if mis_tareas.empty:
        st.info("No tienes tareas pendientes.")
        return
    
    for index, row in mis_tareas.iterrows():
        icono = "🔒" if row['estado'] == 'Bloqueado' else "⏳" if row['estado'] == 'Pendiente' else "✅"
        
        with st.expander(f"{icono} {row['tarea']} ({row['casa']})"):
            st.write(f"Estado: **{row['estado']}**")
            
            # LÓGICA DE BLOQUEO
            bloqueado = False
            if row['dependencia_id']:
                padre = db.run_query("SELECT estado, tarea FROM tareas WHERE id=?", (row['dependencia_id'],), return_data=True)
                # Verificación extra por si borraron la tarea padre
                if not padre.empty and padre.iloc[0]['estado'] != "Terminado":
                    bloqueado = True
                    st.error(f"⛔ Esperando a: {padre.iloc[0]['tarea']}")
            
            if not bloqueado:
                nuevo = st.radio("Actualizar:", ["Pendiente", "En Progreso", "Terminado"], key=row['id'])
                if st.button("Guardar", key=f"btn_{row['id']}"):
                    db.run_query("UPDATE tareas SET estado=? WHERE id=?", (nuevo, row['id']))
                    
                    # DESBLOQUEO AUTOMÁTICO (Trigger)
                    if nuevo == "Terminado":
                        hijos = db.run_query("SELECT id FROM tareas WHERE dependencia_id=?", (row['id'],), return_data=True)
                        for _, hijo in hijos.iterrows():
                            db.run_query("UPDATE tareas SET estado='Pendiente' WHERE id=?", (hijo['id'],))
                    
                    st.success("Actualizado")
                    st.rerun()