import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")

BASE_URL = f"https://{DOMAIN}/api/v4"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ============================================================
# DESTINO - Prospecção 2026
# ============================================================
DESTINATION_PIPELINE_ID = 14327815
DESTINATION_STATUS_ID = 110658339
DESTINATION_NAME = "Prospecção 2026 → Contato inicial"

TAG_ALVO = "summit 2024" # <--- troquei aqui. Deixa em minúsculo que o script já compara

def api_get(url, params=None):
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"❌ GET {response.status_code} - {url}")
        print(response.text[:500])
        return None
    return response.json()

def get_all_contacts():
    contacts = []
    page = 1
    while True:
        print(f"📋 Buscando contatos - página {page}...")
        data = api_get(f"{BASE_URL}/contacts", {"page": page, "limit": 250})
        if not data: break
        results = data.get("_embedded", {}).get("contacts", [])
        if not results: break
        contacts.extend(results)
        if len(results) < 250: break
        page += 1
    return contacts

def has_target_tag(contact):
    tags = contact.get("_embedded", {}).get("tags", [])
    for tag in tags:
        tag_name = tag.get("name", "").strip().lower()
        if tag_name == TAG_ALVO.lower():
            return True
    return False

def get_contact_leads(contact_id):
    data = api_get(f"{BASE_URL}/contacts/{contact_id}/links")
    if not data: return []
    lead_ids = []
    for link in data.get("_embedded", {}).get("links", []):
        if link.get("to_entity_type") == "leads":
            if link.get("to_entity_id"):
                lead_ids.append(int(link.get("to_entity_id")))
    return lead_ids

def move_lead(lead_id):
    url = f"{BASE_URL}/leads"
    payload = [{"id": int(lead_id), "pipeline_id": DESTINATION_PIPELINE_ID, "status_id": DESTINATION_STATUS_ID}]
    response = requests.patch(url, headers=HEADERS, json=payload)
    if response.status_code in [200, 202]:
        return True, response.text
    return False, response.text

# INÍCIO
print("="*70)
print(f"🚀 KOMMO - MOVENDO TAG {TAG_ALVO.upper()}")
print(f"Destino: {DESTINATION_NAME}")
print("="*70)

contacts = get_all_contacts()
print(f"\nTotal de contatos: {len(contacts)}")

target_contacts = [c for c in contacts if has_target_tag(c)]
print(f"🏷 Contatos com {TAG_ALVO}: {len(target_contacts)}")

lead_ids = set()
print("\n🔎 Procurando leads associados...")
for index, contact in enumerate(target_contacts, start=1):
    print(f"[{index}/{len(target_contacts)}] {contact.get('name')}")
    for lid in get_contact_leads(contact.get("id")):
        lead_ids.add(lid)

print("\n" + "="*70)
print(f"Leads encontrados para mover: {len(lead_ids)}")
print(f"Destino: {DESTINATION_NAME}")
confirmacao = input("\nDigite MOVER para confirmar: ").strip().upper()

if confirmacao != "MOVER":
    print("❌ Cancelado.")
    exit()

sucesso = erros = 0
for index, lead_id in enumerate(sorted(lead_ids), start=1):
    print(f"[{index}/{len(lead_ids)}] Lead {lead_id}... ", end="")
    ok, resp = move_lead(lead_id)
    if ok:
        sucesso += 1
        print("✅")
    else:
        erros += 1
        print(f"❌ {resp[:200]}")

print(f"\n🏁 Finalizado - Movidos: {sucesso} | Erros: {erros}")