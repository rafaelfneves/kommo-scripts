import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")
BASE_URL = f"https://{DOMAIN}/api/v4"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

TAG_ALVO = "PSB"
CAMPO_NOME = "Partido"
VALOR = "PSB"

# Se quiser SÓ no Prospecção 2026, muda para True
SOMENTE_PROSPECCAO_2026 = False
PIPELINE_PROSPECCAO_2026 = 14327815

def api_get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code!= 200:
        print(f"❌ {r.status_code} {url}\n{r.text[:1000]}")
        return None
    return r.json()

def get_tag_id():
    data = api_get(f"{BASE_URL}/leads/tags?limit=250")
    for t in data['_embedded']['tags']:
        if t['name'].strip().lower() == TAG_ALVO.lower():
            print(f"Tag: {t['name']} ID {t['id']}")
            return t['id']
    raise Exception("Tag PSB não encontrada")

def get_campo():
    data = api_get(f"{BASE_URL}/leads/custom_fields?limit=250")
    for f in data['_embedded']['custom_fields']:
        if f['name'].strip().lower() == CAMPO_NOME.lower():
            print(f"Campo: {f['name']} ID {f['id']} Tipo {f['type']}")
            enum_id = None
            if f['type'] in ['select','radio','multiselect']:
                for e in f.get('enums', []):
                    if e['value'].strip().lower() == VALOR.lower():
                        enum_id = e['id']
                        print(f" Valor da lista: {e['value']} enum_id {enum_id}")
                        break
                if not enum_id:
                    raise Exception(f"Crie o valor '{VALOR}' em Kommo > Configurações > Campos > Lead > {CAMPO_NOME}")
            return f['id'], f['type'], enum_id
    raise Exception(f"Campo {CAMPO_NOME} não encontrado")

def get_leads(tag_id):
    leads = []
    url = f"{BASE_URL}/leads?filter[tags][0][id]={tag_id}&limit=250"
    p = 1
    while url:
        print(f"📋 Buscando PSB - página {p}...")
        data = api_get(url)
        if not data: break
        batch = data['_embedded']['leads']
        if not batch: break

        # Filtra aqui no código se precisar
        if SOMENTE_PROSPECCAO_2026:
            batch = [l for l in batch if l.get('pipeline_id') == PIPELINE_PROSPECCAO_2026]

        leads.extend(batch)
        url = data['_links'].get('next', {}).get('href')
        p += 1
    return leads

# INICIO
print("="*70)
print(f"🚀 KOMMO - TAG {TAG_ALVO} -> CAMPO {CAMPO_NOME} = {VALOR}")
print("="*70)

tag_id = get_tag_id()
field_id, field_type, enum_id = get_campo()
leads = get_leads(tag_id)

print(f"\nTotal para atualizar: {len(leads)}")
if SOMENTE_PROSPECCAO_2026:
    print("(Filtrado apenas Prospecção 2026)")

if not leads:
    exit()

if field_type in ['select','radio','multiselect']:
    values = [{"enum_id": enum_id}]
else:
    values = [{"value": VALOR}]

conf = input(f"\nDigite ATUALIZAR para gravar {len(leads)} leads: ").strip().upper()
if conf!= "ATUALIZAR":
    exit()

ok = 0
for i, lead in enumerate(leads, 1):
    print(f"[{i}/{len(leads)}] Lead {lead['id']}... ", end="")
    payload = [{
        "id": lead['id'],
        "custom_fields_values": [{"field_id": field_id, "values": values}]
    }]
    r = requests.patch(f"{BASE_URL}/leads", headers=HEADERS, json=payload)
    if r.status_code in [200,202,204]:
        print("✅")
        ok += 1
    else:
        print(f"❌ {r.text[:200]}")

print(f"\n🏁 Finalizado {ok}/{len(leads)}")