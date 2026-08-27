import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")

BASE_URL = f"https://{DOMAIN}/api/v4"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def get_all_contacts():
    """Busca todos os contatos do Kommo."""
    contacts = []
    page = 1

    while True:
        url = f"{BASE_URL}/contacts"
        params = {
            "page": page,
            "limit": 250
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar contatos: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        results = data.get("_embedded", {}).get("contacts", [])

        if not results:
            break

        contacts.extend(results)

        print(f"Página {page}: {len(results)} contatos encontrados")

        if len(results) < 250:
            break

        page += 1

    return contacts


def get_tags(contact):
    """Retorna as tags de um contato."""
    tags = contact.get("_embedded", {}).get("tags", [])
    return [tag.get("name", "").strip().lower() for tag in tags]


def get_pipelines():
    """Busca os funis e etapas do Kommo."""
    url = f"{BASE_URL}/leads/pipelines"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar funis: {response.status_code}")
        print(response.text)
        return []

    return response.json().get("_embedded", {}).get("pipelines", [])


print("=" * 60)
print(" 🔎 DIAGNÓSTICO KOMMO - TAG PSB")
print("=" * 60)

# ---------------------------------------------------------
# 1. BUSCAR CONTATOS
# ---------------------------------------------------------

print("\n📋 Buscando contatos...")

contacts = get_all_contacts()

print(f"\nTotal de contatos encontrados: {len(contacts)}")


# ---------------------------------------------------------
# 2. FILTRAR TAG PSB
# ---------------------------------------------------------

psb_contacts = []

for contact in contacts:
    tags = get_tags(contact)

    if "psb" in tags:
        psb_contacts.append(contact)


print("\n" + "=" * 60)
print(f"🏷️ CONTATOS COM TAG PSB: {len(psb_contacts)}")
print("=" * 60)


for contact in psb_contacts:
    contact_id = contact.get("id")
    contact_name = contact.get("name")

    print(f"ID: {contact_id} | Nome: {contact_name}")


# ---------------------------------------------------------
# 3. BUSCAR FUNIS
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("🎯 FUNIS DO KOMMO")
print("=" * 60)

pipelines = get_pipelines()

for pipeline in pipelines:

    pipeline_id = pipeline.get("id")
    pipeline_name = pipeline.get("name")

    print(f"\nFunil: {pipeline_name}")
    print(f"ID: {pipeline_id}")

    statuses = pipeline.get("_embedded", {}).get("statuses", [])

    for status in statuses:
        status_id = status.get("id")
        status_name = status.get("name")

        print(f"   └── Etapa: {status_name} | ID: {status_id}")


print("\n" + "=" * 60)
print("✅ DIAGNÓSTICO FINALIZADO")
print("⚠️ Nenhum contato ou lead foi alterado.")
print("=" * 60)