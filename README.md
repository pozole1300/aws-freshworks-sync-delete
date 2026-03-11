# AWS Lambda: Orquestador de Borrado Simultáneo (Freshworks)

## Descripción
Script _serverless_ desarrollado en Python para resolver limitaciones de sincronización de datos nativas en el ecosistema Freshworks. Esta función Lambda automatiza la búsqueda y eliminación simultánea de agentes o contactos a través de múltiples entornos (Freshdesk y Freshchat/CRM).

## Arquitectura y Tecnologías
* **Computación:** AWS Lambda (Python 3.x)
* **Integración:** Interacción directa con APIs REST de Freshdesk (v2) y Freshchat.
* **Librerías Core:** `urllib3` (para solicitudes HTTP ligeras sin dependencias externas), `json`, `base64`.
* **Seguridad:** Gestión de credenciales (API Keys y Dominios) mediante variables de entorno de AWS, con autenticación Basic (Base64) y Token.

## Flujo de Trabajo
1. La función recibe un *Request* HTTP (vía *queryStringParameters* o *body* JSON) con el correo del agente/contacto objetivo.
2. **Fase 1 (Freshchat):** Autentica, localiza el ID interno asociado al correo y ejecuta el protocolo de borrado.
3. **Fase 2 (Freshdesk):** Genera el token de autorización en Base64, busca el identificador cruzado y purga el registro.
4. Retorna un reporte de ejecución estructurado en HTML para el usuario final.
