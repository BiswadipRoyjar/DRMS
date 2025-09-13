# -----------------------------
# DISARM: Master Global Disaster Scanner
# -----------------------------

import ee
import geemap

# Authenticate and initialize Earth Engine
ee.Authenticate()
ee.Initialize()

# -----------------------------
# Step 1: Define Global ROI
# -----------------------------
roi = ee.Geometry.Rectangle([-180, -90, 180, 90])

# -----------------------------
# Step 2: NDVI Pre/Post for vegetation-based indices
# -----------------------------
# Pre-disaster NDVI (2 months ago)
ndvi_pre = ee.ImageCollection('COPERNICUS/S2') \
            .filterDate('2025-06-01', '2025-06-30') \
            .filterBounds(roi) \
            .map(lambda img: img.normalizedDifference(['B8','B4']).rename('NDVI')) \
            .median()

# Post-disaster NDVI (last month)
ndvi_post = ee.ImageCollection('COPERNICUS/S2') \
             .filterDate('2025-08-01', '2025-08-31') \
             .filterBounds(roi) \
             .map(lambda img: img.normalizedDifference(['B8','B4']).rename('NDVI')) \
             .median()

ndvi_drop = ndvi_pre.subtract(ndvi_post).unitScale(0,1)

# -----------------------------
# Step 3: Flood Index (example)
# -----------------------------
flooded = ee.ImageCollection('COPERNICUS/S1_GRD')\
           .filterDate('2025-08-01','2025-08-31')\
           .filterBounds(roi)\
           .mean()  # placeholder
flood_norm = flooded.unitScale(0,1)

# -----------------------------
# Step 4: Burned Area / Wildfire Index (example using NDVI drop)
# -----------------------------
burned_area = ndvi_drop  # for demo
burned_norm = burned_area.unitScale(0,1)

# -----------------------------
# Step 5: Drought Index (example using NDVI + precipitation)
# -----------------------------
# CHIRPS monthly precipitation
precip = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')\
          .filterDate('2025-08-01', '2025-08-31')\
          .sum()
precip_norm = precip.unitScale(0,300)

ndvi_norm = ndvi_post.unitScale(0,1)
drought_index = (ee.Image(1).subtract(ndvi_norm).add(ee.Image(1).subtract(precip_norm))).divide(2)
drought_norm = drought_index

# -----------------------------
# Step 6: Landslide Index
# -----------------------------
dem = ee.Image('USGS/SRTMGL1_003')
slope = ee.Terrain.slope(dem)
slope_norm = slope.unitScale(0,60)

# Monthly rainfall for landslide
rain = precip
rain_norm = rain.unitScale(0,300)

landslide_index = slope_norm.add(rain_norm).add(ndvi_drop).divide(3)

# -----------------------------
# Step 7: Heatwave Index
# -----------------------------
lst = ee.ImageCollection('MODIS/006/MOD11A2')\
        .filterDate('2025-08-01','2025-08-31')\
        .select('LST_Day_1km')\
        .mean()\
        .multiply(0.02)

heatwave_index = lst.unitScale(250,330)

# -----------------------------
# Step 8: Cyclone / Storm Index
# -----------------------------
era5 = ee.ImageCollection('ECMWF/ERA5/DAILY')\
          .filterDate('2025-08-01','2025-08-31')

era5_mean = era5.mean()
u = era5_mean.select('u_component_of_wind_10m')
v = era5_mean.select('v_component_of_wind_10m')
wind = u.pow(2).add(v.pow(2)).sqrt()
wind_norm = wind.unitScale(0,50)

rain = era5.select('total_precipitation').sum()
rain_norm = rain.unitScale(0,0.5)

cyclone_index = wind_norm.add(rain_norm).divide(2)

# -----------------------------
# Step 9: Combine all 6 indices
# -----------------------------
disaster_index = flood_norm.add(burned_norm)\
                           .add(drought_norm)\
                           .add(landslide_index)\
                           .add(heatwave_index)\
                           .add(cyclone_index)\
                           .divide(6)

# High-risk areas (>0.7)
alert_threshold = 0.7
high_risk = disaster_index.gt(alert_threshold)

# -----------------------------
# Step 10: Map Visualization
# -----------------------------
Map = geemap.Map(center=[0,0], zoom=2)
Map.addLayer(disaster_index, {'min':0,'max':1,'palette':['green','yellow','orange','red']}, 'DISARM Global Index')
Map.addLayer(high_risk.updateMask(high_risk), {'palette':['red']}, 'High Risk Areas')
Map.addLayer(roi, {}, 'ROI')
Map.addLayerControl()
Map

# -----------------------------
# Step 11: Export Disaster Index
# -----------------------------
export_task = ee.batch.Export.image.toDrive(
    image=disaster_index,
    description='DISARM_Global_DisasterIndex',
    folder='DISARM_Exports',
    fileNamePrefix='disaster_index_global',
    scale=1000,
    region=roi.getInfo()['coordinates']
)
export_task.start()
print("✅ Export task started: DISARM_Global_DisasterIndex")
