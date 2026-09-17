import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")
BASE_URL = f"https://{DOMAIN}/api/v4"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

DRY_RUN = False  # Deixa True pra testar. Depois muda pra False pra deletar de verdade

def api_get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        print(f"❌ GET {r.status_code} {url}\n{r.text[:1000]}")
        return None
    return r.json()

def has_phone_or_email(contact):
    fields = contact.get("custom_fields_values", []) or []
    for f in fields:
        # PHONE e EMAIL podem vir com field_code ou field_id diferente, então checa tudo
        code = str(f.get("field_code","")).upper()
        f_id = f.get("field_id")
        values = f.get("values") or []
        if not values:
            continue
        
        # Lista de IDs padrão do Kommo, mas o code é mais seguro
        if "PHONE" in code or "EMAIL" in code:
            # se tem algum valor não vazio
            for v in values:
                if str(v.get("value","")).strip():
                    return True
    return False

def get_contacts_sem_contato():
    sem_contato = []
    total = 0
    page = 1
    url = f"{BASE_URL}/contacts?limit=250&with=custom_fields_values"

    while url:
        print(f"📋 Página {page} - verificando...")
        data = api_get(url)
        if not data: break
        
        batch = data.get("_embedded", {}).get("contacts", [])
        if not batch: break

        for c in batch:
            total += 1
            if not has_phone_or_email(c):
                sem_contato.append(c)

        print(f"   -> Total lidos: {total} | Sem telefone/email até agora: {len(sem_contato)}")

        url = data.get("_links", {}).get("next", {}).get("href")
        page += 1

    return sem_contato, total

def delete_contact(contact_id):
    r = requests.delete(f"{BASE_URL}/contacts/{contact_id}", headers=HEADERS)
    return r.status_code in [200, 202, 204], r.text

# INICIO
print("="*70)
print("🚀 KOMMO - LIMPEZA DE CONTATOS SEM TELEFONE E SEM EMAIL")
print("="*70)
print(f"MODO: {'TESTE (não vai deletar)' if DRY_RUN else 'DELEÇÃO REAL'}")

contatos_lixo, total_lido = get_contacts_sem_contato()

print("\n" + "="*70)
print(f"Total de contatos varridos: {total_lido}")
print(f"Contatos SEM telefone e SEM email: {len(contatos_lixo)}")
print("="*70)

if not contatos_lixo:
    print("✅ Nenhum contato lixo encontrado. Nada para fazer.")
    exit()

print("\nExemplos (primeiros 10):")
for c in contatos_lixo[:10]:
    print(f" - ID {c['id']} | Nome: {c.get('name','(sem nome)')} | Criado em: {c.get('created_at')}")

if DRY_RUN:
    print("\n--- MODO TESTE ---")
    print(f"Seriam deletados {len(contatos_lixo)} contatos.")
    print("Se estiver correto, abra o arquivo e mude DRY_RUN = False e rode de novo.")
    exit()

conf = input(f"\n⚠️ ATENÇÃO: Você vai DELETAR {len(contatos_lixo)} contatos PERMANENTEMENTE.\nDigite DELETAR para confirmar: ").strip().upper()
if conf != "DELETAR":
    print("❌ Cancelado.")
    exit()

print("\n🚀 Iniciando deleção...")
sucesso = 0
for i, c in enumerate(contatos_lixo, 1):
    print(f"[{i}/{len(contatos_lixo)}] Deletando {c['id']} {c.get('name')}... ", end="")
    ok, resp = delete_contact(c['id'])
    if ok:
        print("✅")
        sucesso += 1
    else:
        print(f"❌ {resp[:300]}")

print(f"\n🏁 Finalizado - Deletados {sucesso}/{len(contatos_lixo)}")