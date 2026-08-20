#!/usr/bin/env python3
"""
Check la Lage — Newsletter Sender
Edit the SHOW dict below and run:  python send_newsletter.py
"""

import json
import requests

# ── Configuration ──────────────────────────────────────────────────────────────
# Get your API key at: Brevo → Settings (top right) → API Keys → Generate a new key
API_KEY      = 'YOUR_BREVO_API_KEY'
LIST_ID      = 3          # Brevo → Contacts → Lists → hover over your list to see the ID
SENDER_NAME  = 'Check la Lage'
SENDER_EMAIL = 'lorenzvonroemer@gmail.com'   # must be verified in Brevo → Senders & IPs

# ── Show details — edit this for each newsletter ───────────────────────────────
SHOW = {
    'subject':      'Check la Lage — Show this Saturday!',
    'preview_text': 'Improv. No script. Anything can happen.',
    'date':         'Saturday, 23 August 2026',
    'time':         '20:00',
    'venue':        'Ballhaus Ost, Pappelallee 15, 10437 Berlin',
    'tickets_url':  'https://schokokrossi.github.io/check_la_lage/#shows',
    'description': (
        'We\'re back on stage and ready to surprise ourselves just as much as you. '
        'Bring your friends, your questions, and zero expectations — '
        'we\'ll take it from there.'
    ),
    'extra': '',  # Optional second paragraph (leave empty to omit)
}


# ── HTML template ──────────────────────────────────────────────────────────────
def build_html(show: dict) -> str:
    extra_block = f'''
          <tr>
            <td style="padding: 0 40px 24px; color: #aaaaaa; font-family: Arial, Helvetica, sans-serif;
                       font-size: 16px; line-height: 1.7;">
              {show["extra"]}
            </td>
          </tr>''' if show.get('extra') else ''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background:#0a0a0a;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a; padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="max-width:600px; width:100%; background:#111111; border:1px solid #222222;">

          <!-- Header -->
          <tr>
            <td style="padding:48px 40px 32px; border-bottom:1px solid #222222;">
              <div style="font-family:'Bebas Neue',Arial Black,Impact,sans-serif;
                          font-size:52px; color:#ffffff; letter-spacing:2px; line-height:1;">
                Check la Lage
              </div>
              <div style="font-family:Arial,Helvetica,sans-serif; font-size:11px;
                          color:#555555; letter-spacing:4px; text-transform:uppercase;
                          margin-top:6px;">
                Improv Theatre Berlin
              </div>
            </td>
          </tr>

          <!-- Label -->
          <tr>
            <td style="padding:32px 40px 0;">
              <div style="font-family:Arial,Helvetica,sans-serif; font-size:11px;
                          color:#666666; letter-spacing:3px; text-transform:uppercase;">
                Upcoming Show
              </div>
            </td>
          </tr>

          <!-- Date -->
          <tr>
            <td style="padding:8px 40px 4px;">
              <div style="font-family:'Bebas Neue',Arial Black,Impact,sans-serif;
                          font-size:38px; color:#ffffff; letter-spacing:1px; line-height:1.1;">
                {show["date"]}
              </div>
            </td>
          </tr>

          <!-- Time & Venue -->
          <tr>
            <td style="padding:0 40px 0;">
              <div style="font-family:Arial,Helvetica,sans-serif; font-size:15px;
                          color:#777777; line-height:1.5;">
                {show["time"]} &nbsp;·&nbsp; {show["venue"]}
              </div>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:28px 40px;">
              <div style="height:1px; background:#222222;"></div>
            </td>
          </tr>

          <!-- Description -->
          <tr>
            <td style="padding:0 40px 24px; color:#cccccc;
                       font-family:Arial,Helvetica,sans-serif; font-size:16px; line-height:1.75;">
              {show["description"]}
            </td>
          </tr>

          {extra_block}

          <!-- CTA button -->
          <tr>
            <td style="padding:8px 40px 52px;">
              <a href="{show["tickets_url"]}"
                 style="display:inline-block; background:#ffffff; color:#000000;
                        font-family:Arial,Helvetica,sans-serif; font-size:12px;
                        font-weight:bold; letter-spacing:2px; text-transform:uppercase;
                        text-decoration:none; padding:14px 32px;">
                Get Tickets &rarr;
              </a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px; border-top:1px solid #1a1a1a;">
              <div style="font-family:Arial,Helvetica,sans-serif; font-size:12px;
                          color:#3a3a3a; line-height:1.7;">
                You're receiving this because you subscribed at
                <a href="https://schokokrossi.github.io/check_la_lage/"
                   style="color:#555555; text-decoration:none;">check-la-lage.de</a>.<br>
                <a href="{{{{unsubscribe}}}}" style="color:#555555;">Unsubscribe</a>
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''


# ── Brevo API ──────────────────────────────────────────────────────────────────
def send_newsletter(show: dict) -> None:
    headers = {
        'api-key':      API_KEY,
        'Content-Type': 'application/json',
        'Accept':       'application/json',
    }

    payload = {
        'name':         f"[CLL] {show['subject']}",
        'subject':      show['subject'],
        'previewText':  show.get('preview_text', ''),
        'sender':       {'name': SENDER_NAME, 'email': SENDER_EMAIL},
        'type':         'classic',
        'htmlContent':  build_html(show),
        'recipients':   {'listIds': [LIST_ID]},
    }

    # 1. Create campaign
    r = requests.post(
        'https://api.brevo.com/v3/emailCampaigns',
        headers=headers,
        data=json.dumps(payload),
    )
    r.raise_for_status()
    campaign_id = r.json()['id']
    print(f'Campaign created (ID {campaign_id})')

    # 2. Send immediately
    r2 = requests.post(
        f'https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow',
        headers=headers,
    )
    r2.raise_for_status()
    print(f'Newsletter sent! Campaign ID: {campaign_id}')
    print(f'Track it at: https://app.brevo.com/campaign/email/{campaign_id}/report')


if __name__ == '__main__':
    send_newsletter(SHOW)
