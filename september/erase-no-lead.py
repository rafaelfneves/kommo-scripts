import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")
BASE_URL = f"https://{DOMAIN}/api/v4"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

DRY_RUN = True  # True = só lista | False = deleta de verdade
DELETAR_CONTATO_JUNTO = False  # Se True, apaga o lead E o contato. Se False, só o lead

def api_get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        print(f"❌ GET {r.status_code} {url}\n{r.text[:500]}")
        return None
    return r.json()

def contact_has_phone_or_email(contact_id):
    data = api_get(f"{BASE_URL}/contacts/{contact_id}")
    if not data:
        return False
    fields = data.get("custom_fields_values", []) or []
    for f in fields:
        code = str(f.get("field_code","")).upper()
        if "PHONE" in code or "EMAIL" in code:
            for v in (f.get("values") or []):
                if str(v.get("value","")).strip():
                    return True
    return False

def lead_has_phone_or_email_direct(lead):
    # alguns funis tem telefone direto no lead
    fields = lead.get("custom_fields_values", []) or []
    for f in fields:
        code = str(f.get("field_code","")).upper()
        if "PHONE" in code or "EMAIL" in code:
            for v in (f.get("values") or []):
                if str(v.get("value","")).strip():
                    return True
    return False

def get_all_leads():
    leads_sem = []
    total = 0
    url = f"{BASE_URL}/leads?limit=250&with=contacts,custom_fields_values"
    page = 1
    while url:
        print(f"📋 Página {page} - varrendo leads...")
        data = api_get(url)
        if not data: break
        batch = data.get("_embedded", {}).get("leads", [])
        if not batch: break

        for lead in batch:
            total += 1
            
            # 1. Checa se o próprio lead tem telefone/email
            if lead_has_phone_or_email_direct(lead):
                continue

            # 2. Checa contatos vinculados
            contacts_embed = lead.get("_embedded", {}).get("contacts", [])
            if not contacts_embed:
                # lead sem nenhum contato vinculado = lixo
                leads_sem.append(lead)
                continue

            tem_contato_valido = False
            for c in contacts_embed:
                cid = c.get("id")
                if contact_has_phone_or_email(cid):
                    tem_contato_valido = True
                    break
            
            if not tem_contato_valido:
                leads_sem.append(lead)

        print(f"   -> Lidos: {total} | Leads sem contato até agora: {len(leads_sem)}")
        url = data.get("_links", {}).get("next", {}).get("href")
        page += 1
    return leads_sem, total

def delete_lead(lead_id):
    r = requests.delete(f"{BASE_URL}/leads/{lead_id}", headers=HEADERS)
    return r.status_code in [200,202,204], r.text

def delete_contact(contact_id):
    r = requests.delete(f"{BASE_URL}/contacts/{contact_id}", headers=HEADERS)
    return r.status_code in [200,202,204], r.text

# INICIO
print("="*70)
print("🚀 KOMMO - DELETAR LEADS SEM TELEFONE E SEM EMAIL")
print("="*70)
print(f"MODO: {'TESTE' if DRY_RUN else 'DELEÇÃO REAL'}")

leads_lixo, total = get_all_leads()

print("\n" + "="*70)
print(f"Total varridos: {total}")
print(f"Leads SEM telefone/email: {len(leads_lixo)}")
print("="*70)

if not leads_lixo:
    print("✅ Nada para deletar.")
    exit()

print("\nPrimeiros 10:")
for l in leads_lixo[:10]:
    print(f" - Lead ID {l['id']} | {l.get('name')} | pipeline {l.get('pipeline_id')} | status {l.get('status_id')}")

if DRY_RUN:
    print(f"\n--- MODO TESTE --- Seriam deletados {len(leads_lixo)} leads.")
    print("Mude DRY_RUN = False para deletar de verdade.")
    exit()

conf = input(f"\n⚠️ Vai DELETAR {len(leads_lixo)} LEADS. Digite DELETAR LEADS: ").strip().upper()
if conf != "DELETAR LEADS":
    print("Cancelado")
    exit()

sucesso = 0
for i, lead in enumerate(leads_lixo, 1):
    print(f"[{i}/{len(leads_lixo)}] Deletando lead {lead['id']}... ", end="")
    ok, _ = delete_lead(lead['id'])
    if ok:
        print("✅ Lead", end="")
        sucesso += 1
        if DELETAR_CONTATO_JUNTO:
            for c in lead.get("_embedded", {}).get("contacts", []):
                delete_contact(c.get("id"))
                print(f" + Contato {c.get('id')} ✅", end="")
        print("")
    else:
        print(f"❌")

print(f"\n🏁 Deletados {sucesso}/{len(leads_lixo)}")