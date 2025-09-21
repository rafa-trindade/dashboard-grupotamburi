import os
import io
import json
from datetime import datetime
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

FOLDER_ID = "1onpfyP538eqARrC5gkHvJpclIjOFLsNx"

def _load_credentials_json():

    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        try:
            return json.loads(creds_json)
        except Exception:

            pass


    try:

        secret = st.secrets.get("GOOGLE_CREDENTIALS")
        if secret:
            if isinstance(secret, dict):
                return secret
            return json.loads(secret)
    except Exception:
        pass


    local_path = os.path.join(os.path.dirname(__file__), "credenciais.json")
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise RuntimeError(
        "Credenciais do Google não encontradas. Defina a variável de ambiente GOOGLE_CREDENTIALS "
        "ou adicione a chave GOOGLE_CREDENTIALS em st.secrets."
    )

@st.cache_resource
def carregar_servico():
    """Carrega o serviço do Drive a partir das credenciais seguras."""
    creds_dict = _load_credentials_json()
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def listar_arquivos_docs():
    """Lista os arquivos Google Docs da pasta do Drive (ordem decrescente)."""
    service = carregar_servico()
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.document'",
        orderBy="modifiedTime desc",
        fields="files(id, name, modifiedTime)"
    ).execute()
    return results.get("files", [])


def exportar_pdf(file_id, nome_arquivo):
    """Exporta um Google Docs como PDF e retorna BytesIO + nome do arquivo final (.pdf)."""
    service = carregar_servico()
    request = service.files().export_media(fileId=file_id, mimeType="application/pdf")
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)
    nome_pdf = nome_arquivo if nome_arquivo.lower().endswith(".pdf") else nome_arquivo + ".pdf"
    return fh, nome_pdf
