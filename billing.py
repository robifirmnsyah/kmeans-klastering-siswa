from google.cloud import billing_v1
from google.oauth2 import service_account

# Path ke file service account JSON
service_account_path = "hr-harmony-deployment-469f15afb6f6.json"
credentials = service_account.Credentials.from_service_account_file(service_account_path)

# Buat client untuk Cloud Billing API
client = billing_v1.CloudBillingClient(credentials=credentials)

def get_billing_info():
    # Ganti dengan ID billing account Anda
    billing_account_id = "billingAccounts/010D92-342A91-50A7DB"  # Ganti dengan ID billing yang sesuai

    # Ambil informasi tentang akun billing
    billing_info = client.get_billing_account(name=billing_account_id)

    # Tampilkan informasi akun billing
    print(f"Billing Account ID: {billing_info.name}")
    print(f"Display Name: {billing_info.display_name}")
    print(f"Open: {billing_info.open}")
    print(f"Master Billing Account: {billing_info.master_billing_account}")

# Memanggil fungsi
get_billing_info()
