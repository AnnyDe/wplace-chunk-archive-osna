import os
import requests
from datetime import datetime, timedelta
from PIL import Image
import time

# Ihre Chunk-Koordinaten (von 1067,672 bis 1072,674)
chunks = []
for x in range(1067, 1073):  # 1067 bis 1072
    for y in range(672, 675):  # 672 bis 674
        chunks.append((x, y))

def download_chunk(x, y, timestamp):
    """Lädt einen einzelnen Chunk herunter"""
    url = f"https://backend.wplace.live/files/s0/tiles/{x}/{y}.png"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Erstelle Ordner-Struktur
        folder = f"chunks/{timestamp}"
        os.makedirs(folder, exist_ok=True)
        
        # Speichere Bild
        filename = f"{folder}/chunk_{x}_{y}.png"
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        print(f"✓ Downloaded chunk {x},{y}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download chunk {x},{y}: {e}")
        return False

def create_combined_image(timestamp):
    """Erstellt ein kombiniertes Bild aus allen Chunks"""
    try:
        # Lade alle Chunk-Bilder
        chunk_images = {}
        chunk_size = None
        
        for x, y in chunks:
            filename = f"chunks/{timestamp}/chunk_{x}_{y}.png"
            if os.path.exists(filename):
                img = Image.open(filename)
                chunk_images[(x, y)] = img
                if chunk_size is None:
                    chunk_size = img.size
        
        if not chunk_images:
            print("Keine Chunks zum Kombinieren gefunden")
            return
            
        # Berechne Dimensionen des kombinierten Bildes
        min_x = min(coord[0] for coord in chunks)
        max_x = max(coord[0] for coord in chunks)
        min_y = min(coord[1] for coord in chunks)
        max_y = max(coord[1] for coord in chunks)
        
        width = (max_x - min_x + 1) * chunk_size[0]
        height = (max_y - min_y + 1) * chunk_size[1]
        
        # Erstelle kombiniertes Bild
        combined = Image.new('RGB', (width, height))
        
        for (x, y), img in chunk_images.items():
            paste_x = (x - min_x) * chunk_size[0]
            paste_y = (y - min_y) * chunk_size[1]
            combined.paste(img, (paste_x, paste_y))
        
        # Speichere kombiniertes Bild
        os.makedirs("combined", exist_ok=True)
        combined.save(f"combined/{timestamp}_combined.png")
        print(f"✓ Created combined image: {timestamp}_combined.png")
        
    except Exception as e:
        print(f"✗ Failed to create combined image: {e}")

def cleanup_old_archives(keep_days=30):
    """Löscht Archive älter als keep_days Tage"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
        cutoff_str = cutoff_date.strftime("%Y%m%d")
        
        # Lösche alte chunk Ordner
        if os.path.exists("chunks"):
            for folder in os.listdir("chunks"):
                if folder < cutoff_str:
                    import shutil
                    shutil.rmtree(f"chunks/{folder}")
                    print(f"Deleted old archive: {folder}")
        
        # Lösche alte kombinierte Bilder
        if os.path.exists("combined"):
            for file in os.listdir("combined"):
                if file.endswith(".png") and file[:8] < cutoff_str:
                    os.remove(f"combined/{file}")
                    print(f"Deleted old combined: {file}")
                    
    except Exception as e:
        print(f"Cleanup error: {e}")

def main():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    print(f"Starting archive for timestamp: {timestamp}")
    
    # Cleanup alte Archive (behalte letzten 30 Tage)
    cleanup_old_archives(30)
    
    success_count = 0
    
    # Lade alle Chunks herunter
    for x, y in chunks:
        if download_chunk(x, y, timestamp):
            success_count += 1
        time.sleep(0.5)  # Kurze Pause zwischen Downloads
    
    print(f"\nDownloaded {success_count}/{len(chunks)} chunks successfully")
    
    # Erstelle kombiniertes Bild
    if success_count > 0:
        create_combined_image(timestamp)
    
    # Erstelle/Update README mit Status
    with open("README.md", "w") as f:
        f.write(f"""# Wplace Chunk Archive

Automatische Archivierung der Wplace-Chunks von (1067,672) bis (1072,674).

## Status
- **Letztes Update:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
- **Chunks heruntergeladen:** {success_count}/{len(chunks)}
- **Archivierungsintervall:** 2x täglich (8:00 und 20:00 UTC)

## Ordnerstruktur
- `chunks/YYYYMMDD_HHMM/` - Einzelne Chunk-Bilder nach Zeitstempel
- `combined/` - Kombinierte Bilder aller Chunks

## Chunk-Koordinaten
Archivierte Bereiche: {', '.join([f'({x},{y})' for x, y in chunks[:5]])}{'...' if len(chunks) > 5 else ''}

Total: {len(chunks)} Chunks
""")
    
    print("Archive completed!")

if __name__ == "__main__":
    main()
