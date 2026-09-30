import os
import shutil
import zipfile
import glob

def extract_and_organize():
    print(">>> 1. Removing old synthetic datasets...")
    for folder in ['data/vitals', 'data/train', 'data/val']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    os.makedirs('data/vitals', exist_ok=True)
    os.makedirs('data/train/healthy', exist_ok=True)
    os.makedirs('data/train/lumpy_skin', exist_ok=True)
    os.makedirs('data/train/foot_and_mouth', exist_ok=True)
    os.makedirs('data/val/healthy', exist_ok=True)
    os.makedirs('data/val/lumpy_skin', exist_ok=True)
    os.makedirs('data/val/foot_and_mouth', exist_ok=True)

    print(">>> 2. Extracting real CSV datasets from archive (7).zip...")
    if os.path.exists('archive (7).zip'):
        with zipfile.ZipFile('archive (7).zip', 'r') as zf:
            zf.extractall('data/vitals')
        print("   Extracted global_cattle_disease_detection_dataset.csv and milk yield CSV!")

    # Also copy clinical mastitis dataset
    for f in glob.glob('*mastitis*.csv'):
        dest = os.path.join('data/vitals', os.path.basename(f))
        shutil.copy(f, dest)
        print(f"   Copied {f} to data/vitals/")

    # Also extract archive (8).zip and archive (9).zip if relevant
    for arc in ['archive (8).zip', 'archive (9).zip']:
        if os.path.exists(arc):
            with zipfile.ZipFile(arc, 'r') as zf:
                zf.extractall(os.path.join('data/vitals', arc.replace('.zip', '')))
            print(f"   Extracted {arc}")

    print(">>> 3. Extracting real image datasets from archive (11).zip and archive (12).zip...")

    # archive (11).zip
    if os.path.exists('archive (11).zip'):
        with zipfile.ZipFile('archive (11).zip', 'r') as zf:
            for member in zf.namelist():
                if member.lower().endswith(('.png', '.jpg', '.jpeg')):
                    fn = os.path.basename(member)
                    if not fn:
                        continue
                    if 'Lumpy Skin' in member:
                        target = os.path.join('data/train/lumpy_skin', fn)
                    elif 'Normal Skin' in member:
                        target = os.path.join('data/train/healthy', fn)
                    else:
                        continue
                    with zf.open(member) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
        print("   Extracted archive (11).zip into data/train/lumpy_skin and data/train/healthy")

    # archive (12).zip
    if os.path.exists('archive (12).zip'):
        with zipfile.ZipFile('archive (12).zip', 'r') as zf:
            for member in zf.namelist():
                if member.lower().endswith(('.png', '.jpg', '.jpeg')):
                    fn = os.path.basename(member)
                    if not fn:
                        continue
                    if 'foot-and-mouth' in member:
                        target = os.path.join('data/train/foot_and_mouth', fn)
                    elif 'healthy' in member:
                        target = os.path.join('data/train/healthy', 'cows_' + fn)
                    elif 'lumpy' in member:
                        target = os.path.join('data/train/lumpy_skin', 'cows_' + fn)
                    else:
                        continue
                    with zf.open(member) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
        print("   Extracted archive (12).zip into data/train/")

    print("\n>>> DATASET INGESTION SUMMARY:")
    print("Real Cattle Image Datasets:")
    for cls in os.listdir('data/train'):
        p = os.path.join('data/train', cls)
        if os.path.isdir(p):
            print(f"  • {cls}: {len(os.listdir(p))} images")

    print("\nReal Vitals CSV Datasets in data/vitals:")
    for root, dirs, files in os.walk('data/vitals'):
        for f in files:
            fp = os.path.join(root, f)
            print(f"  • {os.path.relpath(fp, 'data/vitals')} ({os.path.getsize(fp) / 1024:.1f} KB)")

if __name__ == '__main__':
    extract_and_organize()
