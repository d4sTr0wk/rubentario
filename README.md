# Sistema Distribuido de Gestión de Inventario en Tiempo Real

![Imagen decorativa, puedes reemplazarla](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Amazon_Espa%C3%B1a_por_dentro_%28San_Fernando_de_Henares%29.JPG/800px-Amazon_Espa%C3%B1a_por_dentro_%28San_Fernando_de_Henares%29.JPG)
## Descripción del Proyecto

Este proyecto implementa un Sistema Distribuido de Gestión de Inventario en Tiempo Real, diseñado para garantizar la consistencia y sincronización de información entre múltiples almacenes. Proporciona funcionalidades avanzadas como:

    Actualización y consulta en tiempo real.
    Sincronización automática entre nodos distribuidos.
    Alertas automáticas de reposición de stock.
    Historial de movimientos detallado.

Objetivo

🔹 Consultar y actualizar inventarios en tiempo real.
🔹 Sincronizar automáticamente los datos entre nodos.
🔹 Generar alertas de reposición.
🔹 Consultar inventarios globales desde múltiples almacenes.
🔹 Registrar un historial detallado de movimientos.
Arquitectura del Sistema

El sistema está basado en una arquitectura distribuida con los siguientes componentes clave:

    Modelo: Peer-to-Peer.
    Middleware: RabbitMQ.
    Persistencia: Bases de datos distribuidas Redis.
    Algoritmos Distribuidos:
        Exclusión Mutua Distribuida: Prevención de conflictos en accesos concurrentes.
        Snapshots Distribuidos: Sincronización del estado global.
        Sincronización de Relojes: Ordenación y coordinación de eventos.

🚀 Funcionalidades Principales

✅ Gestión de Stock: Actualización y consulta en tiempo real.
✅ Sincronización Global: Cambios reflejados en todos los nodos.
✅ Alertas de Reposición: Notificaciones para stock bajo.
✅ Historial de Movimientos: Registro detallado de entradas, salidas y transferencias.
🛠️ Tecnologías Utilizadas

    Lenguajes: Python.
    Middleware: RabbitMQ.
    Bases de Datos: Redis.

📦 Instalación

# 1. Clona el repositorio
    > git clone https://github.com/tu-usuario/tu-repositorio.git

# 2. Ejecuta el sistema
    > python main.py

📄 Documentación Técnica

📂 Toda la documentación, incluyendo diagramas y explicaciones detalladas, está disponible en la carpeta docs.

📝 Licencia

Este proyecto está bajo la licencia MIT.
