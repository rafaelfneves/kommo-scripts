import os, requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")
BASE_URL = f"https://{DOMAIN}/api/v4"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

ORIGEM_PIPELINE = 14327815 # Prospecção 2026
NOME_DESTINO = "MDB" # Nome do funil de destino
TAG = "MDB"

DRY_RUN = False # True = só lista | False = move de verdade

def api_get(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code!= 200:
        print(f"❌ {r.status_code} {url}\n{r.text[:500]}")
        return None
    return r.json()

def has_tag_mdb(entity):
    for t in entity.get("_embedded",{}).get("tags",[]) or []:
        if t.get("name","").strip().lower() == TAG.lower():
            return True
    return False

def get_pipelines():
    d = api_get(f"{BASE_URL}/leads/pipelines")
    pipelines = d['_embedded']['pipelines']
    print("Funis encontrados:")
    for p in pipelines:
        print(f" - {p['name']} ID {p['id']}")
    return pipelines

def get_destino_id(pipelines):
    for p in pipelines:
        if NOME_DESTINO.lower() in p['name'].lower():
            print(f"\n✅ Funil destino encontrado: {p['name']} ID {p['id']}")
            # pega primeiro status do funil destino
            status_id = p['_embedded']['statuses'][0]['id']
            print(f"Status inicial do funil MDB: {p['_embedded']['statuses'][0]['name']} ID {status_id}")
            return p['id'], status_id
    raise Exception(f"Funil com nome '{NOME_DESTINO}' não encontrado")

def get_leads_origem_com_mdb():
    leads_com_mdb = []
    total = 0
    url = f"{BASE_URL}/leads?filter[pipeline_id][]={ORIGEM_PIPELINE}&limit=250"
    page = 1
    while url:
        print(f"📋 Prospecção 2026 página {page} - varridos {total} | com MDB {len(leads_com_mdb)}")
        d = api_get(url)
        if not d: break
        batch = d['_embedded']['leads']
        if not batch: break
        total += len(batch)
        for lead in batch:
            # 1. Tag MDB direto no lead?
            if has_tag_mdb(lead):
                leads_com_mdb.append(lead)
                continue
            # 2. Tag MDB no contato vinculado?
            for c in lead.get("_embedded",{}).get("contacts",[]) or []:
                # precisa buscar contato completo pra ver tags
                c_full = api_get(f"{BASE_URL}/contacts/{c['id']}")
                if c_full and has_tag_mdb(c_full):
                    leads_com_mdb.append(lead)
                    break
        url = d['_links'].get('next',{}).get('href')
        page += 1
    print(f"\nTotal no Prospecção 2026: {total}")
    print(f"Com tag MDB (lead ou contato): {len(leads_com_mdb)}")
    return leads_com_mdb

# INICIO
print("="*70)
print(f"🚀 MOVER MDB: Prospecção 2026 -> Funil MDB")
print("="*70)

pipelines = get_pipelines()
dest_pipeline_id, dest_status_id = get_destino_id(pipelines)

leads_para_mover = get_leads_origem_com_mdb()

print(f"\nLeads para mover: {len(leads_para_mover)}")
if not leads_para_mover:
    print("Nada para mover")
    exit()

if DRY_RUN:
    print("\n--- MODO TESTE ---")
    for l in leads_para_mover[:20]:
        print(f" Moveria: Lead {l['id']} {l.get('name')}")
    print(f"\nMude DRY_RUN=False para mover {len(leads_para_mover)} de verdade")
    exit()

conf = input(f"\n⚠️ Vai MOVER {len(leads_para_mover)} leads para o funil MDB. Digite MOVER: ").strip().upper()
if conf!= "MOVER":
    exit()

movidos = 0
for i, lead in enumerate(leads_para_mover, 1):
    print(f"[{i}/{len(leads_para_mover)}] Movendo Lead {lead['id']}... ", end="")
    payload = [{
        "id": lead['id'],
        "pipeline_id": dest_pipeline_id,
        "status_id": dest_status_id
    }]
    r = requests.patch(f"{BASE_URL}/leads", headers=HEADERS, json=payload)
    if r.status_code in [200,202]:
        print("✅")
        movidos += 1
    else:
        print(f"❌ {r.text[:200]}")

print(f"\n🏁 Finalizado: {movidos}/{len(leads_para_mover)} movidos para o funil MDB")