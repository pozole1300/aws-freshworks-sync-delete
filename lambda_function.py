import json
import os
import urllib3
import base64

http = urllib3.PoolManager()

def get_fd_headers(api_key):
    auth_str = f"{api_key}:X"
    b64_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
    return {'Authorization': f'Basic {b64_auth}', 'Content-Type': 'application/json'}

def lambda_handler(event, context):
    print("--- PROTOCOLO DE BORRADO TOTAL (DESK + CHAT) ---")
    
    # 1. Cargar Credenciales
    crm_domain = os.environ.get('CRM_DOMAIN', '').strip('/')
    crm_key = os.environ.get('CRM_API_KEY', '')
    fd_domain = os.environ.get('FD_DOMAIN', '').strip('/')
    fd_key = os.environ.get('FD_API_KEY', '')

    # --- 2. OBTENER EMAIL (MEJORADO PARA ACEPTAR URL Y BODY) ---
    email = ""
    
    # A. Buscar en la URL (Ej: tu_lambda_url/?borrar_ya=juan@correo.com)
    query = event.get('queryStringParameters') or {}
    if 'borrar_ya' in query:
        email = query.get('borrar_ya', '').strip().lower()
    elif 'email' in query:
        email = query.get('email', '').strip().lower()

    # B. Si no está en la URL, buscar en el Body (JSON)
    if not email:
        try:
            body_str = event.get('body')
            if body_str:
                body = json.loads(body_str)
                email = body.get('email', '').strip().lower()
        except:
            pass

    if not email:
        return {'statusCode': 400, 'body': 'Falta email. Agrega ?borrar_ya=correo@dominio.com a la URL.'}

    print(f"Objetivo: {email}")
    reporte = []

    # --- FASE 1: BORRAR DE FRESHCHAT (La parte difícil) ---
    print(">>> Iniciando Fase 1: Freshchat...")
    headers_crm = {'Authorization': f'Token token={crm_key}', 'Content-Type': 'application/json'}
    chat_id = None
    
    try:
        url = f"{crm_domain}/api/search?q={email}&include=contact"
        r = http.request('GET', url, headers=headers_crm)
        if r.status == 200:
            data = json.loads(r.data.decode('utf-8'))
            lista = data if isinstance(data, list) else data.get('contacts', [])
            for c in lista:
                if c.get('email', '').lower() == email:
                    chat_id = c['id']
                    break
        
        if not chat_id:
            url = f"{crm_domain}/api/filtered_search/contact?query=\"{email}\""
            r = http.request('GET', url, headers=headers_crm)
            if r.status == 200:
                data = json.loads(r.data.decode('utf-8'))
                if data.get('contacts'): chat_id = data['contacts'][0]['id']

        if chat_id:
            r_del = http.request('DELETE', f"{crm_domain}/api/contacts/{chat_id}", headers=headers_crm)
            if r_del.status in [200, 204]:
                reporte.append("✅ Borrado de Chat/CRM")
            else:
                reporte.append(f"❌ Error borrando Chat ({r_del.status})")
        else:
            reporte.append("⚠️ No encontrado en Chat (¿Ya estaba borrado?)")
            
    except Exception as e:
        reporte.append(f"❌ Error crítico Chat: {str(e)}")

    # --- FASE 2: BORRAR DE FRESHDESK (La parte nueva) ---
    print(">>> Iniciando Fase 2: Freshdesk...")
    try:
        headers_fd = get_fd_headers(fd_key)
        url_fd_search = f"{fd_domain}/api/v2/contacts?email={email}"
        r_fd = http.request('GET', url_fd_search, headers=headers_fd)
        
        fd_id = None
        if r_fd.status == 200:
            contacts = json.loads(r_fd.data.decode('utf-8'))
            if contacts:
                fd_id = contacts[0]['id']
        
        if fd_id:
            print(f"Encontrado en Desk con ID: {fd_id}. Borrando...")
            url_fd_del = f"{fd_domain}/api/v2/contacts/{fd_id}"
            r_fd_del = http.request('DELETE', url_fd_del, headers=headers_fd)
            
            if r_fd_del.status in [200, 204, 301]: 
                reporte.append("✅ Borrado de Freshdesk")
            else:
                reporte.append(f"❌ Error borrando Desk ({r_fd_del.status})")
        else:
            reporte.append("⚠️ No encontrado en Freshdesk")

    except Exception as e:
        reporte.append(f"❌ Error crítico Desk: {str(e)}")

    # --- REPORTE FINAL ---
    msg_final = " | ".join(reporte)
    print(f"FIN: {msg_final}")
    
    # Devolver respuesta legible en el navegador
    return {
        'statusCode': 200, 
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': f"<h3>Resultado de borrado para {email}:</h3><p>{msg_final}</p>"
    }