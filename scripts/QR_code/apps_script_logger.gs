// Paste this into script.google.com (Extensions > Apps Script) for the QR Scans sheet.
// Deploy as a Web App (Execute as: Me, Who has access: Anyone), then paste the
// resulting URL into qr/index.html in place of REPLACE_WITH_APPS_SCRIPT_WEB_APP_URL.
//
// After pasting, reload the spreadsheet: a "QR Analytics" menu appears with an
// "Update Plots" item that (re)builds the Plots sheet and its charts from Scans.

function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Scans');
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('Scans');
    sheet.appendRow(['Timestamp', 'User Agent', 'QR Source']);
  }
  sheet.appendRow([new Date(), e.parameter.ua || '', e.parameter.qr || '']);
  return ContentService.createTextOutput('ok');
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('QR Analytics')
    .addItem('Update Plots', 'updatePlots')
    .addToUi();
}

function parseDeviceType(ua) {
  if (!ua) return 'Unknown';
  if (/iPad|Tablet/i.test(ua)) return 'Tablet';
  if (/Mobi|Android|iPhone/i.test(ua)) return 'Mobile';
  return 'Desktop';
}

function updatePlots() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var scansSheet = ss.getSheetByName('Scans');
  if (!scansSheet) return;

  var tz = ss.getSpreadsheetTimeZone();
  var data = scansSheet.getDataRange().getValues();
  data.shift(); // drop header row

  var byDate = {};
  var byHour = {};
  var byDevice = {};
  var bySource = {};

  data.forEach(function (row) {
    var timestamp = row[0];
    var ua = row[1];
    var source = row[2];
    if (!(timestamp instanceof Date)) return;

    var dateKey = Utilities.formatDate(timestamp, tz, 'yyyy-MM-dd');
    byDate[dateKey] = (byDate[dateKey] || 0) + 1;

    var hourKey = Utilities.formatDate(timestamp, tz, 'HH:00');
    byHour[hourKey] = (byHour[hourKey] || 0) + 1;

    var device = parseDeviceType(ua);
    byDevice[device] = (byDevice[device] || 0) + 1;

    var sourceKey = source || 'Unspecified';
    bySource[sourceKey] = (bySource[sourceKey] || 0) + 1;
  });

  var plots = ss.getSheetByName('Plots');
  if (plots) {
    plots.getCharts().forEach(function (chart) { plots.removeChart(chart); });
    plots.clear();
  } else {
    plots = ss.insertSheet('Plots');
  }

  // --- Table 1: scans per day ---
  var dateRows = Object.keys(byDate).sort().map(function (d) { return [d, byDate[d]]; });
  plots.getRange(1, 1, 1, 2).setValues([['Date', 'Scans']]);
  if (dateRows.length) plots.getRange(2, 1, dateRows.length, 2).setValues(dateRows);

  // --- Table 2: scans by hour of day ---
  var hourLabels = [];
  for (var h = 0; h < 24; h++) {
    hourLabels.push(('0' + h).slice(-2) + ':00');
  }
  var hourRows = hourLabels.map(function (h) { return [h, byHour[h] || 0]; });
  var hourStartCol = 4;
  plots.getRange(1, hourStartCol, 1, 2).setValues([['Hour', 'Scans']]);
  plots.getRange(2, hourStartCol, hourRows.length, 2).setValues(hourRows);

  // --- Table 3: device breakdown ---
  var deviceRows = Object.keys(byDevice).map(function (d) { return [d, byDevice[d]]; });
  var deviceStartCol = 7;
  plots.getRange(1, deviceStartCol, 1, 2).setValues([['Device', 'Scans']]);
  if (deviceRows.length) plots.getRange(2, deviceStartCol, deviceRows.length, 2).setValues(deviceRows);

  // --- Table 4: scans by QR source (which flyer/code was scanned) ---
  var sourceRows = Object.keys(bySource).map(function (s) { return [s, bySource[s]]; });
  var sourceStartCol = 10;
  plots.getRange(1, sourceStartCol, 1, 2).setValues([['QR Source', 'Scans']]);
  if (sourceRows.length) plots.getRange(2, sourceStartCol, sourceRows.length, 2).setValues(sourceRows);

  // --- Charts ---
  if (dateRows.length) {
    var dateChart = plots.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(plots.getRange(1, 1, dateRows.length + 1, 2))
      .setPosition(1, 13, 0, 0)
      .setOption('title', 'Scans per day')
      .setOption('width', 600)
      .setOption('height', 350)
      .build();
    plots.insertChart(dateChart);
  }

  var hourChart = plots.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(plots.getRange(1, hourStartCol, hourRows.length + 1, 2))
    .setPosition(20, 13, 0, 0)
    .setOption('title', 'Scans by hour of day')
    .setOption('width', 600)
    .setOption('height', 350)
    .build();
  plots.insertChart(hourChart);

  if (deviceRows.length) {
    var deviceChart = plots.newChart()
      .setChartType(Charts.ChartType.PIE)
      .addRange(plots.getRange(1, deviceStartCol, deviceRows.length + 1, 2))
      .setPosition(39, 13, 0, 0)
      .setOption('title', 'Scans by device type')
      .setOption('width', 600)
      .setOption('height', 350)
      .build();
    plots.insertChart(deviceChart);
  }

  if (sourceRows.length) {
    var sourceChart = plots.newChart()
      .setChartType(Charts.ChartType.BAR)
      .addRange(plots.getRange(1, sourceStartCol, sourceRows.length + 1, 2))
      .setPosition(58, 13, 0, 0)
      .setOption('title', 'Scans by QR source')
      .setOption('width', 600)
      .setOption('height', 350)
      .build();
    plots.insertChart(sourceChart);
  }
}
