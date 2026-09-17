import os, requests
from dotenv import load_dotenv
load_dotenv()
DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")
BASE_URL = f"https://{DOMAIN}/api/v4"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

PIPELINE_ID = 14327815
STATUS_ID = 110658339
TAG = "MDB"
CAMPO_PARTIDO = "Partido"
VALOR_PARTIDO = "MDB"
DRY_RUN = False # AGORA VAI CRIAR

def api_get(url):
    r = requests.get(url, headers=HEADERS)
    return r.json() if r.status_code==200 else None

def has_tag_mdb(entity):
    for t in entity.get("_embedded",{}).get("tags",[]) or []:
        if t.get("name","").strip().lower() == TAG.lower():
            return True
    return False

def get_campo():
    d = api_get(f"{BASE_URL}/leads/custom_fields?limit=250")
    for f in d['_embedded']['custom_fields']:
        if f['name'].strip().lower()==CAMPO_PARTIDO.lower():
            enum_id=None
            if f['type'] in ['select','radio','multiselect']:
                for e in f.get('enums',[]):
                    if e['value'].strip().lower()==VALOR_PARTIDO.lower():
                        enum_id=e['id']
            return f['id'], enum_id
    raise Exception("Campo Partido não achado")

field_id, enum_id = get_campo()
partido_value = [{"enum_id": enum_id}] if enum_id else [{"value": VALOR_PARTIDO}]

# Busca rápida já filtrada que você validou
print("Buscando contatos e leads com MDB (filtrado no código)...")
contatos_mdb=[]
url=f"{BASE_URL}/contacts?limit=250"
while url:
    d=api_get(url)
    if not d: break
    for c in d['_embedded']['contacts']:
        if has_tag_mdb(c): contatos_mdb.append(c)
    url=d['_links'].get('next',{}).get('href')

leads_mdb=[]
url=f"{BASE_URL}/leads?limit=250"
while url:
    d=api_get(url)
    if not d: break
    for l in d['_embedded']['leads']:
        if has_tag_mdb(l): leads_mdb.append(l)
    url=d['_links'].get('next',{}).get('href')

print(f"REAL: {len(contatos_mdb)} contatos e {len(leads_mdb)} leads com MDB")

# Verifica duplicidade
ja_no_funil_ids=set()
url=f"{BASE_URL}/leads?filter[pipeline_id][]={PIPELINE_ID}&limit=250"
while url:
    d=api_get(url)
    if not d: break
    for l in d['_embedded']['leads']:
        # guarda id de contato já no funil
        for c in l.get("_embedded",{}).get("contacts",[]) or []:
            ja_no_funil_ids.add(c['id'])
    url=d['_links'].get('next',{}).get('href')

print(f"Contatos que já têm lead no Prospecção 2026: {len(ja_no_funil_ids)}")

criados=0
for c in contatos_mdb:
    if c['id'] in ja_no_funil_ids:
        continue # já existe, não cria
    payload={
        "name": c.get('name') or "Sem nome",
        "pipeline_id": PIPELINE_ID,
        "status_id": STATUS_ID,
        "tags_to_add": [{"name": TAG}],
        "custom_fields_values": [{"field_id": field_id, "values": partido_value}],
        "_embedded": {"contacts": [{"id": c['id']}]}
    }
    if DRY_RUN:
        print(f"[TESTE] Criaria {c.get('name')}")
    else:
        r=requests.post(f"{BASE_URL}/leads", headers=HEADERS, json=[payload])
        if r.status_code in [200,201]:
            criados+=1
            print(f"[{criados}] Criado: {c.get('name')} ✅")

print(f"\n🏁 FINALIZADO: {criados} novos leads criados no Prospecção 2026 com Partido MDB")
print(f"Os {len(ja_no_funil_ids)} que já existiam foram ignorados pra não duplicar")