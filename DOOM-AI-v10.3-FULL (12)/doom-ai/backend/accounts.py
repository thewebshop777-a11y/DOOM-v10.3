"""
DOOM AI — Account system
Company (Founder) · Employee · Normal (disabled)
Forget password · Google · 6-digit OTP
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
import random

router = APIRouter()
pwd = CryptContext(schemes=["argon2"], deprecated="auto")

ACCOUNTS = {
    "founder@webshop.local": {
        "email": "founder@webshop.local",
        "password_hash": pwd.hash("founder123"),
        "type": "founder",
        "workspace": "web-shop",
        "can_bill": True,
    }
}

OTP_STORE = {}  # email → {code, expires, purpose}

def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"

class CompanySignup(BaseModel):
    email: str
    password: str
    company: str

class EmployeeCheck(BaseModel):
    email: str

class EmployeeSetPassword(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
    mode: str = "company"

class OTPRequest(BaseModel):
    email: str
    purpose: str = "login"  # login | reset | verify

class OTPVerify(BaseModel):
    email: str
    code: str
    purpose: str = "login"

class ResetPassword(BaseModel):
    email: str
    code: str
    new_password: str

class GoogleLogin(BaseModel):
    email: str
    name: Optional[str] = None
    mode: str = "company"

@router.post("/otp/send")
async def send_otp(req: OTPRequest):
    code = generate_otp()
    OTP_STORE[req.email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=10),
        "purpose": req.purpose,
    }
    from main import settings
    if settings.resend_api_key and not settings.resend_api_key.startswith("re_your"):
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
                json={
                    "from": settings.resend_from,
                    "to": [req.email],
                    "subject": "DOOM AI — Your OTP",
                    "html": f"<p>Your 6-digit code is <strong>{code}</strong>. Valid for 10 minutes.</p>",
                },
            )
        return {"status": "sent", "email": req.email, "expires_in": 600}
    # Fallback demo
    return {"status": "sent", "email": req.email, "demo_code": code, "expires_in": 600}

@router.post("/otp/verify")
async def verify_otp(req: OTPVerify):
    rec = OTP_STORE.get(req.email)
    if not rec or rec["purpose"] != req.purpose:
        raise HTTPException(400, "No OTP found")
    if datetime.utcnow() > rec["expires"]:
        raise HTTPException(400, "OTP expired")
    if rec["code"] != req.code:
        raise HTTPException(400, "Invalid OTP")
    del OTP_STORE[req.email]
    return {"status": "verified", "email": req.email}

@router.post("/company/signup")
async def company_signup(req: CompanySignup):
    if req.email in ACCOUNTS:
        raise HTTPException(400, "Account exists")
    ACCOUNTS[req.email] = {
        "email": req.email,
        "password_hash": pwd.hash(req.password),
        "type": "founder",
        "workspace": req.company.lower().replace(" ", "-"),
        "can_bill": True,
        "created": datetime.utcnow().isoformat(),
    }
    return {"status": "created", "type": "founder", "email": req.email}

@router.post("/employee/check")
async def employee_check(req: EmployeeCheck):
    from permissions import PERMISSIONS
    if req.email not in PERMISSIONS:
        return {"status": "not_invited", "message": "This email has not been invited."}
    return {"status": "allowed", "message": "Allowed. Set your password to continue.", "email": req.email}

@router.post("/employee/set-password")
async def employee_set_password(req: EmployeeSetPassword):
    from permissions import PERMISSIONS
    if req.email not in PERMISSIONS:
        raise HTTPException(403, "Not invited")
    ACCOUNTS[req.email] = {
        "email": req.email,
        "password_hash": pwd.hash(req.password),
        "type": "employee",
        "workspace": "web-shop",
        "can_bill": False,
        "role": PERMISSIONS[req.email].get("role", "member"),
        "created": datetime.utcnow().isoformat(),
    }
    return {"status": "password_set", "type": "employee", "email": req.email}

@router.post("/login")
async def login(req: LoginRequest):
    acc = ACCOUNTS.get(req.email)
    if not acc or not pwd.verify(req.password, acc["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    if req.mode == "employee" and acc["type"] != "employee":
        raise HTTPException(403, "Not an employee account")
    if req.mode == "company" and acc["type"] != "founder":
        raise HTTPException(403, "Not a company/founder account")
    return {
        "status": "ok",
        "email": req.email,
        "type": acc["type"],
        "can_bill": acc.get("can_bill", False),
        "role": acc.get("role", "founder"),
        "workspace": acc.get("workspace"),
    }

@router.get("/google/login")
async def google_login_redirect():
    """Redirect user to Google consent screen."""
    from main import settings
    if not settings.google_client_id:
        raise HTTPException(500, "GOOGLE_CLIENT_ID not set")
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str):
    """Handle Google redirect and create/login user."""
    from main import settings
    import httpx
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(400, "Google token exchange failed")
        tokens = token_res.json()
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        info = user_res.json()
    email = info.get("email")
    if not email:
        raise HTTPException(400, "No email from Google")
    # Create or login
    if email not in ACCOUNTS:
        ACCOUNTS[email] = {
            "email": email,
            "password_hash": "",
            "type": "founder",
            "workspace": "web-shop",
            "can_bill": True,
            "google": True,
            "created": datetime.utcnow().isoformat(),
        }
    acc = ACCOUNTS[email]
    from fastapi.responses import RedirectResponse
    # In production set a secure cookie/token; for now redirect with query
    return RedirectResponse(f"/?google_login={email}&type={acc['type']}")

@router.post("/reset")
async def reset_password(req: ResetPassword):
    rec = OTP_STORE.get(req.email)
    if not rec or rec["purpose"] != "reset" or rec["code"] != req.code:
        raise HTTPException(400, "Invalid or expired reset code")
    if datetime.utcnow() > rec["expires"]:
        raise HTTPException(400, "OTP expired")
    acc = ACCOUNTS.get(req.email)
    if not acc:
        raise HTTPException(404, "Account not found")
    acc["password_hash"] = pwd.hash(req.new_password)
    del OTP_STORE[req.email]
    return {"status": "password_reset", "email": req.email}

@router.get("/me")
async def me(email: str):
    acc = ACCOUNTS.get(email)
    if not acc:
        raise HTTPException(404)
    return {
        "email": acc["email"],
        "type": acc["type"],
        "can_bill": acc.get("can_bill", False),
        "role": acc.get("role", "founder"),
    }
