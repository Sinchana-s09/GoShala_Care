import zipfile, pandas as pd, os, shutil

BASE = 'd:/goshala'

print('=== EXTRACTING ALL DATASETS ===\n')

# 1. Extract archive (7) -> data/vitals (already extracted, just confirm)
print('[1] Archive 7 - Cattle disease detection + milk yield CSVs')
with zipfile.ZipFile(f'{BASE}/archive (7).zip') as zf:
    for n in zf.namelist():
        out = f'{BASE}/data/vitals/{n}'
        if not os.path.exists(out):
            zf.extract(n, f'{BASE}/data/vitals/')
            print(f'  Extracted: {n}')
        else:
            print(f'  Already exists: {n}')

# 2. Extract archive (8) -> data/vitals/mastitis_training
print('\n[2] Archive 8 - Mastitis training/testing CSVs')
os.makedirs(f'{BASE}/data/vitals/mastitis', exist_ok=True)
with zipfile.ZipFile(f'{BASE}/archive (8).zip') as zf:
    for n in zf.namelist():
        out = f'{BASE}/data/vitals/mastitis/{n}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
            print(f'  Extracted: {n}')
        else:
            print(f'  Already exists: {n}')

# 3. Extract archive (9) -> data/symptom_disease
print('\n[3] Archive 9 - Disease-symptom-severity datasets')
os.makedirs(f'{BASE}/data/symptom_disease', exist_ok=True)
with zipfile.ZipFile(f'{BASE}/archive (9).zip') as zf:
    for n in zf.namelist():
        out = f'{BASE}/data/symptom_disease/{n}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
            print(f'  Extracted: {n}')
        else:
            print(f'  Already exists: {n}')

# 4. Extract archive (11) -> data/images/lumpy_skin
print('\n[4] Archive 11 - Lumpy Skin Disease Images')
os.makedirs(f'{BASE}/data/images', exist_ok=True)
with zipfile.ZipFile(f'{BASE}/archive (11).zip') as zf:
    names = zf.namelist()
    lumpy = [n for n in names if 'Lumpy Skin' in n and not n.endswith('/')]
    normal = [n for n in names if 'Normal' in n and not n.endswith('/')]
    
    out_lumpy = f'{BASE}/data/images/lumpy_skin'
    out_normal = f'{BASE}/data/images/healthy'
    os.makedirs(out_lumpy, exist_ok=True)
    os.makedirs(out_normal, exist_ok=True)
    
    for n in lumpy[:300]:  # Take max 300 for training
        fname = os.path.basename(n)
        out = f'{out_lumpy}/{fname}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
    print(f'  Extracted {min(len(lumpy),300)} lumpy skin images -> data/images/lumpy_skin/')
    
    for n in normal[:200]:
        fname = os.path.basename(n)
        out = f'{out_normal}/{fname}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
    print(f'  Extracted {min(len(normal),200)} normal skin images -> data/images/healthy/')

# 5. Extract archive (12) -> data/images (FMD, healthy, lumpy)
print('\n[5] Archive 12 - Cow Disease Images (FMD, Lumpy, Healthy)')
with zipfile.ZipFile(f'{BASE}/archive (12).zip') as zf:
    names = zf.namelist()
    
    fmd = [n for n in names if 'foot-and-mouth' in n and not n.endswith('/')]
    lumpy = [n for n in names if '/lumpy' in n.lower() and not n.endswith('/')]
    healthy = [n for n in names if '/healthy' in n.lower() and not n.endswith('/')]
    
    out_fmd = f'{BASE}/data/images/foot_mouth'
    out_lumpy2 = f'{BASE}/data/images/lumpy_skin'
    out_healthy = f'{BASE}/data/images/healthy'
    os.makedirs(out_fmd, exist_ok=True)
    
    for n in fmd[:250]:
        fname = os.path.basename(n)
        out = f'{out_fmd}/{fname}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
    print(f'  Extracted {min(len(fmd),250)} FMD images -> data/images/foot_mouth/')
    
    added_lumpy = 0
    for n in lumpy[:200]:
        fname = os.path.basename(n)
        out = f'{out_lumpy2}/{fname}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
            added_lumpy += 1
    print(f'  Added {added_lumpy} more lumpy images')
    
    added_healthy = 0
    for n in healthy[:200]:
        fname = os.path.basename(n)
        out = f'{out_healthy}/{fname}'
        if not os.path.exists(out):
            with zf.open(n) as src, open(out, 'wb') as dst:
                dst.write(src.read())
            added_healthy += 1
    print(f'  Added {added_healthy} more healthy images')

print('\n=== EXTRACTION COMPLETE ===')
print('Image counts:')
for folder in ['healthy', 'lumpy_skin', 'foot_mouth']:
    p = f'{BASE}/data/images/{folder}'
    if os.path.exists(p):
        count = len([f for f in os.listdir(p) if f.lower().endswith(('.jpg','.jpeg','.png'))])
        print(f'  {folder}: {count} images')
