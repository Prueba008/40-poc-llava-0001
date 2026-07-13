# Especificación de Prompt para Análisis de Arquitectura

## Propósito
Analizar imágenes de arquitectura de software para deducir y diseñar la arquitectura técnica necesaria para soportar productos digitales con bases de datos masivas.

## Prompt Principal

### Instrucción General
Extraer de la imagen adjunta como ingeniero de software Analizar la imagen adjunta para deducir y diseñar la arquitectura técnica necesaria para soportar el producto digital que se promociona (un curso/plataforma con bases de datos masivas).

### Instrucciones de Formato
- Proporciona una explicación técnica para cada punto
- Genera código PlantUML válido encerrado en bloques de código independientes para cada diagrama
- No utilices texto genérico; basa tus deducciones en los números y activos específicos de la imagen (ej. "38,000+ AI Tools", "40,000+ Prompts")

## Análisis Requerido

### 1. Componentes y Servicios
Desglosa la arquitectura necesaria:
- API Gateways
- Microservicios de Búsqueda
- CMS para videos
- Motores de Recomendación

### 2. Stack Tecnológico
Deduce tecnologías específicas:
- Bases de datos Vectoriales para prompts
- NoSQL para el catálogo
- CDNs para el contenido de video

### 3. Patrones de Diseño
Justifica el uso de:
- Microservicios
- CQRS (para separar lectura de catálogos y escritura de usuarios)
- Event-Driven

### 4. Seguridad y Despliegue
Define estrategias de:
- OAuth2/JWT para el acceso vía QR
- Infraestructura en Kubernetes sobre AWS/GCP

### 5. Escalabilidad
Explica cómo manejarías picos de tráfico masivos tras el escaneo del código QR.

## Diagramas PlantUML Solicitados

### A. Diagrama de Componentes
Detallando la lógica interna.

### B. Diagrama de Secuencia
Flujo desde el escaneo del QR hasta la entrega del prompt/recurso.

### C. Diagrama de Despliegue
Nodos, contenedores y balanceadores de carga.

### D. Diagrama de Flujo de Datos
Movimiento de la información desde las DBs hacia el usuario final.
