# backend/notifications.py
# Email notification system using Gmail SMTP

import smtplib
import os
from email.mime.text            import MIMEText
from email.mime.multipart       import MIMEMultipart
from datetime                   import datetime
from dotenv                     import load_dotenv

load_dotenv()

SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Sends an HTML email. Returns True if sent, False if failed.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("⚠️  Email not configured — skipping send")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Gas Predictor <{SMTP_EMAIL}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        print(f"✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


def build_household_email(name: str, days_left: int,
                           depletion_date: str, cylinder_size: float,
                           alert_message: str) -> str:
    """
    Builds a nice HTML email for household depletion alert.
    """
    # Pick colour based on urgency
    if days_left <= 3:
        color  = "#dc2626"
        emoji  = "🚨"
        urgency = "URGENT — Order Now"
    elif days_left <= 7:
        color  = "#d97706"
        emoji  = "⚠️"
        urgency = "Plan Your Refill Soon"
    else:
        color  = "#16a34a"
        emoji  = "✅"
        urgency = "Gas Level OK"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }}
        .container {{ max-width: 560px; margin: 0 auto; background: white;
                      border-radius: 12px; overflow: hidden;
                      box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
        .header {{ background: #1e3a5f; color: white; padding: 28px 32px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 1.4rem; }}
        .header p  {{ margin: 6px 0 0; opacity: 0.8; font-size: 0.9rem; }}
        .body {{ padding: 28px 32px; }}
        .alert-box {{ background: {color}15; border: 2px solid {color}40;
                      border-radius: 10px; padding: 16px 20px; margin-bottom: 24px; }}
        .alert-box .label {{ color: {color}; font-weight: 700; font-size: 1rem; }}
        .alert-box .message {{ color: #374151; margin-top: 6px; font-size: 0.92rem; }}
        .stat-row {{ display: flex; gap: 12px; margin-bottom: 20px; }}
        .stat {{ flex: 1; background: #f8fafc; border-radius: 10px;
                 padding: 16px; text-align: center; border: 1px solid #e2e8f0; }}
        .stat .value {{ font-size: 1.8rem; font-weight: 800; color: #1e3a5f; }}
        .stat .label {{ font-size: 0.78rem; color: #64748b; margin-top: 4px; }}
        .cta {{ background: #2563eb; color: white; text-align: center;
                padding: 14px; border-radius: 10px; font-weight: 700;
                font-size: 1rem; margin-top: 8px; }}
        .footer {{ background: #f8fafc; padding: 16px 32px; text-align: center;
                   font-size: 0.78rem; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>⛽ Gas Predictor Alert</h1>
          <p>AI-powered gas depletion notification</p>
        </div>
        <div class="body">
          <p style="color:#374151; margin-bottom:20px;">
            Hello <b>{name}</b>, here is your latest gas cylinder status:
          </p>

          <div class="alert-box">
            <div class="label">{emoji} {urgency}</div>
            <div class="message">{alert_message}</div>
          </div>

          <div class="stat-row">
            <div class="stat">
              <div class="value" style="color:{color}">{days_left}</div>
              <div class="label">Days Remaining</div>
            </div>
            <div class="stat">
              <div class="value">{cylinder_size}kg</div>
              <div class="label">Cylinder Size</div>
            </div>
            <div class="stat">
              <div class="value" style="font-size:1.1rem">
                {datetime.strptime(depletion_date, '%Y-%m-%d').strftime('%d %b')}
              </div>
              <div class="label">Expected Runout</div>
            </div>
          </div>

          <div class="cta">
            {'🛒 Contact your nearest LPG station to order now!' if days_left <= 7
             else '📅 Remember to check back as your depletion date approaches.'}
          </div>
        </div>
        <div class="footer">
          Gas Predictor — AI-powered LPG management for Sri Lanka<br/>
          This is an automated prediction based on your usage pattern.
        </div>
      </div>
    </body>
    </html>
    """


def build_station_email(station_id: str, station_type: str,
                         avg_daily: float, total_7_day: int,
                         forecast: list, alert_message: str) -> str:
    """
    Builds HTML email for station operator with 7-day forecast table.
    """
    rows = ""
    for day in forecast:
        rows += f"""
        <tr>
          <td style="padding:10px 14px; font-weight:600">{day['day_label']}</td>
          <td style="padding:10px 14px; color:#64748b">{day['date']}</td>
          <td style="padding:10px 14px; font-weight:700; color:#1e3a5f">
            {day['predicted_sales']} cylinders
          </td>
        </tr>"""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white;
                      border-radius: 12px; overflow: hidden;
                      box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
        .header {{ background: #1e3a5f; color: white; padding: 28px 32px; }}
        .header h1 {{ margin: 0; font-size: 1.3rem; }}
        .body {{ padding: 28px 32px; }}
        .alert-box {{ background: #eff6ff; border: 2px solid #bfdbfe;
                      border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;
                      color: #1e40af; font-weight: 500; }}
        .stats {{ display: flex; gap: 12px; margin-bottom: 20px; }}
        .stat {{ flex:1; background:#f8fafc; border-radius:10px; padding:16px;
                 text-align:center; border:1px solid #e2e8f0; }}
        .stat .val {{ font-size:1.7rem; font-weight:800; color:#1e3a5f; }}
        .stat .lbl {{ font-size:0.78rem; color:#64748b; margin-top:4px; }}
        table {{ width:100%; border-collapse:collapse; }}
        thead tr {{ background:#f8fafc; }}
        th {{ padding:10px 14px; text-align:left; font-size:0.82rem;
              color:#374151; border-bottom:2px solid #e2e8f0; }}
        tr {{ border-bottom:1px solid #f1f5f9; }}
        .footer {{ background:#f8fafc; padding:14px 32px; text-align:center;
                   font-size:0.78rem; color:#94a3b8; border-top:1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>📊 7-Day Demand Forecast — {station_id}</h1>
          <p style="margin:6px 0 0; opacity:0.8; font-size:0.88rem">
            {station_type} Station · Generated {datetime.now().strftime('%d %B %Y')}
          </p>
        </div>
        <div class="body">
          <div class="alert-box">{alert_message}</div>

          <div class="stats">
            <div class="stat">
              <div class="val">{int(avg_daily)}</div>
              <div class="lbl">Avg Cylinders/Day</div>
            </div>
            <div class="stat">
              <div class="val">{total_7_day}</div>
              <div class="lbl">Total 7-Day Demand</div>
            </div>
            <div class="stat">
              <div class="val">{int(total_7_day * 1.1)}</div>
              <div class="lbl">Recommended Stock</div>
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th>Day</th><th>Date</th><th>Predicted Sales</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        <div class="footer">
          Gas Predictor — AI-powered demand forecasting for Sri Lanka LPG stations
        </div>
      </div>
    </body>
    </html>
    """


# ── Test function ────────────────────────────────────
if __name__ == "__main__":
    print("Testing email system...")
    print(f"SMTP Email:    {SMTP_EMAIL}")
    print(f"SMTP Password: {'SET' if SMTP_PASSWORD else 'NOT SET'}")

    if SMTP_EMAIL and SMTP_PASSWORD:
        html = build_household_email(
            name           = "Test User",
            days_left      = 3,
            depletion_date = "2026-03-08",
            cylinder_size  = 12.5,
            alert_message  = "Your gas cylinder is expected to run out in 3 days!"
        )
        result = send_email(SMTP_EMAIL, "⛽ Gas Predictor — Test Email", html)
        print(f"Result: {'✅ Sent!' if result else '❌ Failed'}")
    else:
        print("⚠️  Set SMTP_EMAIL and SMTP_PASSWORD in .env first")