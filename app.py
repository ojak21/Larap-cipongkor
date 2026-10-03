from flask import Flask, jsonify, send_from_directory
import json, os, glob
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj
app = Flask(__name__)
transformer = pyproj.Transformer.from_crs("EPSG:32748", "EPSG:4326", always_xy=True)

def get_first_x(geom):
    try:
        c = geom['coordinates']
        # cari angka pertama terus
        while isinstance(c[0], (list, tuple)):
            c = c[0]
        return float(c[0])
    except:
        return 0

def reproject(gd):
    try:
        x = get_first_x(gd)
        # kalau x > 180 berarti masih UTM 700rb, harus di-reproject
        if abs(x) <= 180:
            return gd, shape(gd).area
        # UTM -> WGS
        g = shape(gd); area = g.area
        def t(x,y,z=None): return transformer.transform(x,y)
        return mapping(transform(t,g)), area
    except Exception as e:
        print("REPROJ ERR", e)
        return gd, 0

def load(n):
    nc=n.lower().replace('_',' ').replace('-',' ')
    for f in glob.glob("*.geojson"):
        fc=os.path.splitext(f)[0].lower().replace('_',' ').replace('-',' ')
        if fc==nc or fc.replace(' ','')==nc.replace(' ',''):
            with open(f,'r',encoding='utf-8') as fd: return json.load(fd)
    return {"type":"FeatureCollection","features":[]}

def luas(props,fb=0):
    for k,v in props.items():
        if 'luas' in k.lower():
            try:
                if v not in (None,'','null',''): return float(v)
            except: pass
    return fb

@app.route('/api/<name>')
def api(name):
    d=load(name); out=[]
    for ft in d['features']:
        if not ft.get('geometry'): continue
        wgs, ar = reproject(ft['geometry'])
        ft['geometry']=wgs; ft['properties']['_luas_m2']=luas(ft.get('properties',{}),ar); out.append(ft)
    return jsonify({"type":"FeatureCollection","features":out})

@app.route('/api/stats/<name>')
def stats(name):
    d=load(name); tot=0
    for ft in d['features']:
        if not ft.get('geometry'): continue
        _, ar = reproject(ft['geometry'])
        tot+=luas(ft.get('properties',{}),ar)
    return jsonify({"jumlah_bidang":len(d['features']),"total_m2":round(tot,2),"total_ha":round(tot/10000,4)})

@app.route('/api/list')
def lst(): return jsonify([os.path.splitext(f)[0] for f in glob.glob("*.geojson")])

@app.route('/')
def home(): return send_from_directory('.', 'final.html')

@app.route('/<path:p>')
def sf(p): return send_from_directory('.', p)

if __name__ == '__main__': app.run(debug=True, port=5000)