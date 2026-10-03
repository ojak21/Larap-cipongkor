import glob, json, os
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj

print("Mulai convert UTM ke WGS84...")
tr = pyproj.Transformer.from_crs("EPSG:32748","EPSG:4326",always_xy=True)
os.makedirs("wgs", exist_ok=True)

def first_x(g):
    try:
        c=g['coordinates']
        while isinstance(c[0], (list,tuple)): c=c[0]
        return float(c[0])
    except: return 0

files = glob.glob("*.geojson")
for f in files:
    if "wgs" in f: continue
    with open(f,'r',encoding='utf-8') as fd:
        data=json.load(fd)
    out=[]
    for ft in data['features']:
        if not ft.get('geometry'): continue
        gd=ft['geometry']
        try:
            if abs(first_x(gd))>180:
                g=shape(gd)
                def t(x,y,z=None): return tr.transform(x,y)
                gd=mapping(transform(t,g))
        except Exception as e:
            print(f" skip 1 feat di {f}: {e}")
            continue
        ft['geometry']=gd
        out.append(ft)
    with open(f"wgs/{f}",'w',encoding='utf-8') as outf:
        json.dump({"type":"FeatureCollection","features":out}, outf)
    print(f"✓ {f} -> wgs/{f} ({len(out)} bidang)")

print("\nSELESAI! Cek folder wgs di sebelah kiri VS Code")