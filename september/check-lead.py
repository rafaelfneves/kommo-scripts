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


# ============================================================
# REQUISIÇÃO
# ============================================================

def get(url, params=None):

    response = requests.get(
        url,
        headers=HEADERS,
        params=params
    )

    if response.status_code != 200:
        print(f"\n❌ Erro HTTP {response.status_code}")
        print(response.text)
        return None

    return response.json()


# ============================================================
# BUSCAR CONTATOS
# ============================================================

def get_all_contacts():

    contacts = []
    page = 1

    while True:

        print(f"Buscando contatos - página {page}...")

        data = get(
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
# VERIFICAR TAG
# ============================================================

def has_psb_tag(contact):

    tags = contact.get("_embedded", {}).get("tags", [])

    for tag in tags:

        tag_name = tag.get("name", "").strip().lower()

        if tag_name == "psb":
            return True

    return False


# ============================================================
# BUSCAR LEADS DE UM CONTATO
# ============================================================

def get_contact_leads(contact_id):

    data = get(
        f"{BASE_URL}/contacts/{contact_id}/links"
    )

    if not data:
        return []

    links = data.get("_embedded", {}).get("links", [])

    leads = []

    for link in links:

        if link.get("to_entity_type") == "leads":

            leads.append(link.get("to_entity_id"))

    return leads


# ============================================================
# BUSCAR INFORMAÇÕES DO LEAD
# ============================================================

def get_lead(lead_id):

    return get(
        f"{BASE_URL}/leads/{lead_id}"
    )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("=" * 70)
print(" 🔎 DIAGNÓSTICO - CONTATOS COM TAG PSB")
print("=" * 70)

print("\n🎯 DESTINO CONFIGURADO:")

print(f"Pipeline ID: {DESTINATION_PIPELINE_ID}")
print(f"Status ID:   {DESTINATION_STATUS_ID}")

print("\n⚠️ MODO DIAGNÓSTICO")
print("Nenhum lead será alterado.\n")


# ============================================================
# 1. BUSCAR CONTATOS
# ============================================================

contacts = get_all_contacts()

print(f"\n📋 Total de contatos encontrados: {len(contacts)}")


# ============================================================
# 2. FILTRAR PSB
# ============================================================

psb_contacts = [
    contact
    for contact in contacts
    if has_psb_tag(contact)
]


print("\n" + "=" * 70)
print(f"🏷️ CONTATOS COM TAG PSB: {len(psb_contacts)}")
print("=" * 70)


# ============================================================
# 3. BUSCAR LEADS
# ============================================================

total_leads = 0
leads_found = []


for index, contact in enumerate(psb_contacts, start=1):

    contact_id = contact.get("id")
    contact_name = contact.get("name")

    print(
        f"\n[{index}/{len(psb_contacts)}] "
        f"{contact_name} | Contato ID: {contact_id}"
    )

    lead_ids = get_contact_leads(contact_id)

    if not lead_ids:

        print("   └── ⚠️ Nenhum lead associado")

        continue


    for lead_id in lead_ids:

        lead = get_lead(lead_id)

        if not lead:
            continue

        total_leads += 1

        pipeline_id = lead.get("pipeline_id")
        status_id = lead.get("status_id")
        lead_name = lead.get("name")

        print(
            f"   └── Lead: {lead_name}"
        )

        print(
            f"       Lead ID: {lead_id}"
        )

        print(
            f"       Pipeline atual: {pipeline_id}"
        )

        print(
            f"       Etapa atual: {status_id}"
        )

        print(
            f"       → DESTINO: "
            f"{DESTINATION_PIPELINE_ID} / "
            f"{DESTINATION_STATUS_ID}"
        )


        leads_found.append({
            "contact_id": contact_id,
            "contact_name": contact_name,
            "lead_id": lead_id,
            "lead_name": lead_name,
            "current_pipeline": pipeline_id,
            "current_status": status_id
        })


# ============================================================
# RESUMO
# ============================================================

print("\n")
print("=" * 70)
print(" 📊 RESUMO")
print("=" * 70)

print(f"Contatos com PSB:       {len(psb_contacts)}")
print(f"Leads encontrados:      {total_leads}")

print("\nDestino:")
print(f"Pipeline: Prospecção 2026 ({DESTINATION_PIPELINE_ID})")
print(f"Etapa: Contato inicial ({DESTINATION_STATUS_ID})")

print("\n⚠️ NENHUM LEAD FOI ALTERADO.")
print("=" * 70)