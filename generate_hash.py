"""
Ejecutar con: python generate_hash.py
Genera el hash SHA-256 de la contraseña para poner en secrets.toml
"""
import hashlib
import getpass

password = getpass.getpass("Nueva contraseña: ")
confirm  = getpass.getpass("Confirmar contraseña: ")

if password != confirm:
    print("❌ Las contraseñas no coinciden.")
else:
    h = hashlib.sha256(password.encode()).hexdigest()
    print(f"\n✅ Hash generado:")
    print(f'\nEn .streamlit/secrets.toml pon:')
    print(f'[auth]')
    print(f'username = "irc"')
    print(f'password_hash = "{h}"')
    print(f'\nEn Streamlit Cloud Secrets pon lo mismo.')
