# run.py

from app import create_app
import threading

# Creamos una instancia de la aplicación usando nuestra función factory.
app = create_app()

if __name__ == '__main__':
    # --- INICIO DE TAREAS EN SEGUNDO PLANO ---
    # Importamos la función de la tarea aquí para evitar importaciones circulares.
    from app.services.background_tasks import check_inactive_conversations_job

    # Creamos un hilo que ejecutará nuestra tarea.
    # Lo configuramos como 'daemon' para que se cierre automáticamente
    # cuando la aplicación principal de Flask se detenga.
    background_thread = threading.Thread(
        target=check_inactive_conversations_job,
        args=(app,),
        daemon=True
    )
    background_thread.start()
    
    # Este bloque solo se ejecuta cuando corremos 'python run.py' directamente.
    # Es para el desarrollo local.
    # Usamos use_reloader=False para prevenir que el hilo se inicie dos veces.
    app.run(debug=True, use_reloader=False)