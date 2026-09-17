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
# DESTINO
# ============================================================

DESTINATION_PIPELINE_ID = 14327815
DESTINATION_STATUS_ID = 110658339

DESTINATION_NAME = "Prospecção 2026 → Contato inicial"


# ============================================================
# REQUISIÇÃO
# ============================================================

def api_get(url, params=None):

    response = requests.get(
        url,
        headers=HEADERS,
        params=params
    )

    if response.status_code != 200:
        print(f"❌ GET {response.status_code}")
        print(response.text)
        return None

    return response.json()


# ============================================================
# BUSCAR TODOS OS CONTATOS
# ============================================================

def get_all_contacts():

    contacts = []
    page = 1

    while True:

        print(f"📋 Buscando contatos - página {page}...")

        data = api_get(
            f"{BASE_URL}/contacts",
            {
                "page": page,
                "limit": 250
            }
        )

        if not data:
            break

        results = data.get("_embedded", {}).get("contacts", [])

        if not results:
            break

        contacts.extend(results)

        if len(results) < 250:
            break

        page += 1

    return contacts


# ============================================================
# VERIFICAR TAG PSB
# ============================================================

def has_psb_tag(contact):

    tags = contact.get("_embedded", {}).get("tags", [])

    for tag in tags:

        tag_name = tag.get("name", "").strip().lower()

        if tag_name == "psb":
            return True

    return False


# ============================================================
# BUSCAR LEADS ASSOCIADOS
# ============================================================

def get_contact_leads(contact_id):

    data = api_get(
        f"{BASE_URL}/contacts/{contact_id}/links"
    )

    if not data:
        return []

    links = data.get("_embedded", {}).get("links", [])

    lead_ids = []

    for link in links:

        if link.get("to_entity_type") == "leads":

            lead_id = link.get("to_entity_id")

            if lead_id:
                lead_ids.append(lead_id)

    return lead_ids


# ============================================================
# BUSCAR DADOS DO LEAD
# ============================================================

def get_lead(lead_id):

    return api_get(
        f"{BASE_URL}/leads/{lead_id}"
    )


# ============================================================
# MOVER LEAD
# ============================================================

def move_lead(lead_id):

    url = f"{BASE_URL}/leads"

    payload = [
        {
            "id": int(lead_id),
            "pipeline_id": DESTINATION_PIPELINE_ID,
            "status_id": DESTINATION_STATUS_ID
        }
    ]

    response = requests.patch(
        url,
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 202]:

        return True, response.text

    return False, response.text


# ============================================================
# INÍCIO
# ============================================================

print("=" * 70)
print("🚀 KOMMO - MOVIMENTAÇÃO DOS LEADS PSB")
print("=" * 70)

print()
print(f"Destino: {DESTINATION_NAME}")
print(f"Pipeline ID: {DESTINATION_PIPELINE_ID}")
print(f"Status ID: {DESTINATION_STATUS_ID}")

print()
print("🔎 Buscando contatos...")


# ============================================================
# BUSCAR CONTATOS
# ============================================================

contacts = get_all_contacts()

print()
print(f"Total de contatos encontrados: {len(contacts)}")


# ============================================================
# FILTRAR PSB
# ============================================================

psb_contacts = []

for contact in contacts:

    if has_psb_tag(contact):

        psb_contacts.append(contact)


print()
print(f"🏷️ Contatos com PSB: {len(psb_contacts)}")


# ============================================================
# ENCONTRAR LEADS
# ============================================================

lead_ids = set()

print()
print("🔎 Procurando leads associados...")


for index, contact in enumerate(psb_contacts, start=1):

    contact_id = contact.get("id")
    contact_name = contact.get("name")

    print(
        f"[{index}/{len(psb_contacts)}] "
        f"{contact_name}"
    )

    leads = get_contact_leads(contact_id)

    for lead_id in leads:

        lead_ids.add(int(lead_id))


# ============================================================
# RESULTADO
# ============================================================

print()
print("=" * 70)
print("📊 RESULTADO DA BUSCA")
print("=" * 70)

print(f"Contatos com PSB: {len(psb_contacts)}")
print(f"Leads encontrados: {len(lead_ids)}")

print()
print(f"Destino:")
print(f"Funil: Prospecção 2026")
print(f"Etapa: Contato inicial")

# ============================================================
# CONFIRMAÇÃO
# ============================================================

print()
print("=" * 70)
print("⚠️ ATENÇÃO")
print("=" * 70)

print()
print(f"Serão movidos {len(lead_ids)} leads para:")
print()
print("Prospecção 2026")
print("└── Contato inicial")
print()

confirmacao = input(
    "Digite MOVER para confirmar: "
).strip().upper()

if confirmacao != "MOVER":

    print()
    print("❌ Operação cancelada.")
    print("Nenhum lead foi alterado.")
    exit()


# ============================================================
# MOVIMENTAÇÃO
# ============================================================

print()
print("=" * 70)
print("🚀 INICIANDO MOVIMENTAÇÃO")
print("=" * 70)

sucesso = 0
erros = 0

for index, lead_id in enumerate(sorted(lead_ids), start=1):

    print(
        f"[{index}/{len(lead_ids)}] "
        f"Lead {lead_id}...",
        end=" "
    )

    ok, response = move_lead(lead_id)

    if ok:

        sucesso += 1

        print("✅ MOVED")

    else:

        erros += 1

        print("❌ ERRO")
        print(f"    {response}")


# ============================================================
# RESUMO FINAL
# ============================================================

print()
print("=" * 70)
print("🏁 PROCESSO FINALIZADO")
print("=" * 70)

print()
print(f"🏷️ Contatos PSB: {len(psb_contacts)}")
print(f"🎯 Leads encontrados: {len(lead_ids)}")
print(f"✅ Leads movidos: {sucesso}")
print(f"❌ Erros: {erros}")

print()
print("Destino:")
print("Prospecção 2026 → Contato inicial")

print("=" * 70)