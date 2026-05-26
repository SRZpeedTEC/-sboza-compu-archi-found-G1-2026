# UI

La interfaz se separa por responsabilidades para que el archivo de entrada no concentre toda la lógica visual:

- `app.py`: arranque de PySide6 y creación de la ventana.
- `main_window.py`: ventana principal, tabs superiores e historial.
- `pages/`: pantallas completas de procesador y comparación.
- `widgets/`: componentes visuales reutilizables.
- `controllers/`: métodos de actualización visual y acciones de simulación usados por `ProcessorPage`.
- `styles/`: hoja de estilos global de la aplicación.

`interfaz.py` queda como punto de compatibilidad para ejecutar la app o importar las clases principales.
