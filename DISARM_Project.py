
# DISARM: Disaster Risk Assessment and Monitoring
# Author: Biswadip Roy
# Email: biswadip.roy.tech@gmail.com

import ee
import geemap

# Initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# Define ROI as the whole world
roi = ee.Geometry.Polygon(
    [[[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]]
)

# ---------------------------------------------
# 1. Flood Detection
# ---------------------------------------------
s1 = ee.ImageCollection("COPERNICUS/S1_GRD") \    .filterBounds(roi) \    .filterDate('2025-08-01', '2025-08-31') \    .filter(ee.Filter.eq('instrumentMode', 'IW'))

vh = s1.select('VH').mean()
flooded = vh.gt(-18).selfMask()  # threshold for flooded areas

# ---------------------------------------------
# 2. Burned Area (Wildfire)
# ---------------------------------------------
modis_burn = ee.ImageCollection("MODIS/006/MCD64A1") \    .filterDate('2025-08-01', '2025-08-31') \    .select('BurnDate') \    .mean()

burned_area = modis_burn.gt(0).selfMask()

# ---------------------------------------------
# 3. Drought Monitoring
# ---------------------------------------------
chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") \    .filterDate('2025-06-01', '2025-08-31') \    .select('precipitation')

precip = chirps.mean()
precip_norm = precip.unitScale(0, 300)

ndvi = ee.ImageCollection("MODIS/061/MOD13A2") \    .filterDate('2025-06-01', '2025-08-31') \    .select('NDVI') \    .mean()

ndvi_norm = ndvi.unitScale(0, 9000)
drought_index = (ndvi_norm.multiply(0.5).add(precip_norm.multiply(0.5))).multiply(-1)

# ---------------------------------------------
# 4. Landslide Risk
# ---------------------------------------------
srtm = ee.Image("USGS/SRTMGL1_003")
slope = ee.Terrain.slope(srtm)

ndvi_pre = ee.ImageCollection("MODIS/061/MOD13A2").filterDate('2025-06-01', '2025-06-30').select('NDVI').mean()
ndvi_post = ee.ImageCollection("MODIS/061/MOD13A2").filterDate('2025-08-01', '2025-08-31').select('NDVI').mean()
ndvi_drop = ndvi_pre.subtract(ndvi_post).unitScale(0, 1)

rain = chirps.sum().unitScale(0, 500)
landslide_index = slope.unitScale(0, 60).add(ndvi_drop).add(rain).divide(3)

# ---------------------------------------------
# 5. Heatwave Risk
# ---------------------------------------------
era5 = ee.ImageCollection("ECMWF/ERA5/DAILY") \    .filterDate('2025-08-01', '2025-08-31')

temp = era5.select('mean_2m_air_temperature').mean().subtract(273.15)
temp_norm = temp.unitScale(20, 50)

heatwave_index = temp_norm

# ---------------------------------------------
# 6. Cyclone Risk
# ---------------------------------------------
u_wind = era5.select('u_component_of_wind_10m').mean()
v_wind = era5.select('v_component_of_wind_10m').mean()
wind_speed = u_wind.pow(2).add(v_wind.pow(2)).sqrt()

wind_norm = wind_speed.unitScale(0, 50)
cyclone_index = wind_norm

# ---------------------------------------------
# Combine All Indices
# ---------------------------------------------
flood_norm = flooded.unitScale(0, 1)
burned_norm = burned_area.unitScale(0, 1)
drought_norm = drought_index.unitScale(-1, 1)

disaster_index = (flood_norm.add(burned_norm).add(drought_norm)
                  .add(landslide_index).add(heatwave_index).add(cyclone_index)) \                  .divide(6)

# ---------------------------------------------
# Visualization
# ---------------------------------------------
Map = geemap.Map(center=[20, 0], zoom=2)
disaster_vis = {'min': 0, 'max': 1, 'palette': ['green','yellow','orange','red']}

Map.addLayer(disaster_index, disaster_vis, 'Global DISARM Disaster Index')
Map.addLayer(roi, {}, 'ROI')

# Display Map
Map
