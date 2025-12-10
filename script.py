import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from io import BytesIO
import base64
import re

# Ophalen spotify API keys
CLIENT_ID = "CLIENT_ID_PLACEHOLDER"
CLIENT_SECRET = "CLIENT_SECRET_PLACEHOLDER"
PLAYLIST_URL = "PLAYLIST_URL_PLACEHOLDER"

# Kleuren voor de kaartjes
back_col = [
    "1.0, 0.8, 0.8", "1.0, 0.9, 0.8", "1.0, 1.0, 0.8",
    "0.8, 1.0, 0.8", "0.8, 1.0, 1.0", "0.8, 0.9, 1.0",
    "0.9, 0.8, 1.0", "1.0, 0.8, 0.9"
]

# Spotify starten
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

def clean_title(title):
    """Opschonen titels van nummers"""
    title = re.sub(r"[-\(\[]?\s*\d{4}\s*[Rr]emaster(ed)?\s*[-\)\]]?$", "", title)
    title = re.sub(r"[-\(\[]?\s*\d{4}\s*[Rr]emix\s*[-\)\]]?$", "", title)
    title = re.sub(r"[-\(\[]?(Deluxe Edition|Remastered|Remix|Radio Edit|Short Radio Edit|Single Version)\s*[-\)\]]?$", "", title, flags=re.IGNORECASE)
    return title.strip()

def fetch_playlist_data(playlist_url):
    """Playlist verwerken"""
    playlist_id = playlist_url.split('/')[-1].split('?')[0]
    playlist = sp.playlist(playlist_id)
    data = []
    for index, item in enumerate(playlist['tracks']['items']):
        if item['track']:
            track = item['track']
            title = clean_title(track.get('name', 'Onbekend'))
            artists = ', '.join([a['name'] for a in track['artists']])
            year = track['album']['release_date'].split('-')[0] if track['album']['release_date'] else 'Onbekend'
            url = track['external_urls']['spotify']
            backcol = back_col[index % len(back_col)]
            data.append({
                'Title': title,
                'Artist': artists,
                'Year': year,
                'URL': url,
                'backcol': backcol
            })
    return data

def generate_pdf(data):
    """Genereren PDF-bestand"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    box_size = 6.5 * cm
    boxes_per_row = 2
    boxes_per_page = 6  # 2 kolommen × 3 rijen per pagina

    for page_num in range(0, len(data), boxes_per_page):
        page_data = data[page_num:page_num + boxes_per_page]

        for i, row in enumerate(page_data):
            x = 50 + (i % boxes_per_row) * 200  # 2 kolommen
            y = 750 - (i // boxes_per_row) * 150  # 3 rijen per pagina

            # Achtergrondkleur
            c.setFillColorRGB(*eval(row['backcol']))
            c.rect(x, y, box_size, box_size, fill=1, stroke=0)

            # Tekst (titel, artiest, jaar)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x + 10, y + 100, row['Title'])
            c.setFont("Helvetica", 10)
            c.drawString(x + 10, y + 80, row['Artist'])
            c.setFont("Helvetica-Bold", 24)
            c.drawString(x + 10, y + 30, row['Year'])

            # QR-code (vereenvoudigd voorbeeld)
            qr = qrcode.QRCode(box_size=5, border=1)
            qr.add_data(row['URL'])
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img_path = f"qr_{page_num}_{i}.png"
            qr_img.save(qr_img_path)
            c.drawImage(qr_img_path, x + 10, y + 120, width=50, height=50)

        c.showPage()  # Nieuwe pagina voor elke set kaartjes

    c.save()
    return buffer.getvalue()

# Uitvoeren script
data = fetch_playlist_data(PLAYLIST_URL)
pdf_bytes = generate_pdf(data)
base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
print(f"DONE:{base64_pdf}")
