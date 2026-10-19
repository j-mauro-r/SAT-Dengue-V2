// PLAN_009: separate candidate only. No modification of original climate CSV.
// Recipe reference: microproyecto-tema3 b63257c, gee-query-dengue.py.
// Rebuilt geometry is a candidate; compare control dates before incorporation.
var sourceAsset = 'projects/microproyecto-tema3/assets/mgn2025_municipalities_recovery';
var fields = ['dpto_ccdgo', 'dpto_cnmbr', 'mpio_ccdgo', 'mpio_cdpmp', 'mpio_cnmbr'];
var variables = ['rain_mm_day', 'temp_mean_c', 'dewpoint_mean_c',
  'soil_water_l1_mean', 'surface_runoff_mm_day', 'total_evaporation_mm_day_ecmwf',
  'wind_u_mean_ms', 'wind_v_mean_ms', 'solar_radiation_mj_m2_day'];
var selectors = ['date', 'year', 'month', 'day_of_year'].concat(fields).concat(variables);
var raw = ee.FeatureCollection(sourceAsset);
var municipalities = raw.filter(ee.Filter.inList('dpto_ccdgo', ['50', '73']))
  .map(function(f) {
    return ee.Feature(f.geometry().simplify(500), f.toDictionary(fields));
  });
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY');
var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR');
function daily(date) {
  date = ee.Date(date);
  var end = date.advance(1, 'day');
  var era = ee.Image(era5.filterDate(date, end).first());
  var image = ee.Image(chirps.filterDate(date, end).first())
    .select('precipitation').rename('rain_mm_day')
    .addBands(era.select('temperature_2m').subtract(273.15).rename('temp_mean_c'))
    .addBands(era.select('dewpoint_temperature_2m').subtract(273.15).rename('dewpoint_mean_c'))
    .addBands(era.select('volumetric_soil_water_layer_1').rename('soil_water_l1_mean'))
    .addBands(era.select('surface_runoff_sum').multiply(1000).rename('surface_runoff_mm_day'))
    .addBands(era.select('total_evaporation_sum').multiply(1000).rename('total_evaporation_mm_day_ecmwf'))
    .addBands(era.select('u_component_of_wind_10m').rename('wind_u_mean_ms'))
    .addBands(era.select('v_component_of_wind_10m').rename('wind_v_mean_ms'))
    .addBands(era.select('surface_solar_radiation_downwards_sum').divide(1000000)
      .rename('solar_radiation_mj_m2_day'));
  // CHIRPS first-band projection and scale match the reference recipe.
  return image.reduceRegions({collection: municipalities, reducer: ee.Reducer.mean(),
    scale: 5566, tileScale: 4, maxPixelsPerRegion: 1000000})
    .map(function(f) {
      return ee.Feature(null, f.toDictionary(fields.concat(variables))).set({
        date: date.format('YYYY-MM-dd'), year: date.get('year'), month: date.get('month'),
        day_of_year: date.getRelative('day', 'year').add(1)
      });
    });
}
var januaryDates = ee.List.sequence(0, 30).map(function(n) {
  return ee.Date('2020-01-01').advance(n, 'day');
});
var controlDates = ee.List(['2019-12-31', '2020-02-01', '2020-02-15']);
print('Recovery preflight', ee.Dictionary({
  source_asset: sourceAsset, raw_features: raw.size(), municipalities: municipalities.size(),
  distinct_codes: municipalities.aggregate_count_distinct('mpio_cdpmp'),
  department_counts: municipalities.aggregate_histogram('dpto_ccdgo'),
  january_chirps_images: chirps.filterDate('2020-01-01', '2020-02-01').size(),
  january_era5_images: era5.filterDate('2020-01-01', '2020-02-01').size()
}));
function exportDates(dates, name) {
  var table = ee.FeatureCollection(dates.map(daily)).flatten();
  Export.table.toDrive({collection: table, description: name,
    folder: 'SAT_Dengue_January_2020_Recovery', fileNamePrefix: name,
    fileFormat: 'CSV', selectors: selectors});
}
exportDates(januaryDates, 'climate_2020_01_candidate_tolima_meta');
exportDates(controlDates, 'climate_control_dates_tolima_meta');
