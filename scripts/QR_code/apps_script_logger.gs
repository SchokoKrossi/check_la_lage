// Paste this into script.google.com (Extensions > Apps Script) for a Google Sheet.
// Deploy as a Web App (Execute as: Me, Who has access: Anyone), then paste the
// resulting URL into qr/index.html in place of REPLACE_WITH_APPS_SCRIPT_WEB_APP_URL.

function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Scans');
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('Scans');
    sheet.appendRow(['Timestamp', 'User Agent']);
  }
  sheet.appendRow([new Date(), e.parameter.ua || '']);
  return ContentService.createTextOutput('ok');
}
