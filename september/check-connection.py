import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("KOMMO_DOMAIN")
TOKEN = os.getenv("KOMMO_ACCESS_TOKEN")

if not DOMAIN or not TOKEN:
    print("ERRO: KOMMO_DOMAIN ou KOMMO_ACCESS_TOKEN não foi configurado no .env")
    exit()

url = f"https://{DOMAIN}/api/v4/account"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("Conectando ao Kommo...")

response = requests.get(url, headers=headers)

print(f"Status HTTP: {response.status_code}")

if response.status_code == 200:
    data = response.json()

    print("\n✅ CONEXÃO COM KOMMO OK!")
    print(f"Conta: {data.get('name')}")
    print(f"ID da conta: {data.get('id')}")

elif response.status_code == 401:
    print("\n❌ Token inválido ou expirado.")

elif response.status_code == 403:
    print("\n❌ Token sem permissão para acessar a API.")

else:
    print("\n❌ Erro ao conectar:")
    print(response.text)