"""
DOOM AI — Login page with 3 modes
Company (Founder) · Employee · Normal (disabled)
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<title>DOOM AI — Login</title>
<style>
body{background:#050505;color:#f5f5f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.box{background:#111;border:1px solid #1c1c1c;border-radius:10px;padding:28px;width:340px}
h1{color:#49ff96;font-size:18px;margin:0 0 12px}
.tabs{display:flex;gap:6px;margin-bottom:14px}
.tab{flex:1;padding:8px;border:1px solid #1c1c1c;background:#101010;color:#f5f5f5;border-radius:6px;cursor:pointer;font-size:12px}
.tab.active{background:#49ff96;color:#050505;border-color:#49ff96}
input,select{width:100%;background:#101010;border:1px solid #1c1c1c;border-radius:6px;padding:10px;color:#f5f5f5;margin-bottom:8px;box-sizing:border-box}
button.primary{width:100%;background:#49ff96;color:#050505;border:none;border-radius:6px;padding:10px;font-weight:600;cursor:pointer}
.msg{font-size:12px;margin-top:8px;color:#49ff96}
.err{color:#ff6b6b;font-size:12px;margin-top:8px}
.hidden{display:none}
</style>
</head>
<body>
<div class="box">
  <h1>DOOM AI</h1>
  <div class="tabs">
    <div class="tab active" onclick="setMode('company')">Company</div>
    <div class="tab" onclick="setMode('employee')">Employee</div>
    <div class="tab" onclick="setMode('normal')">Normal</div>
  </div>

  <div id="company">
    <input id="cEmail" placeholder="Founder email" />
    <input id="cPass" type="password" placeholder="Password" />
    <button class="primary" onclick="companyLogin()">Enter as Founder</button>
    <button class="primary" style="background:#1c1c1c;color:#f5f5f5;margin-top:6px" onclick="googleLogin('company')">Continue with Google</button>
    <p class="msg" style="margin-top:8px">
      <a href="#" onclick="showSignup()" style="color:#49ff96">Create company</a> ·
      <a href="#" onclick="showReset()" style="color:#49ff96">Forgot password</a>
    </p>
  </div>

  <div id="employee" class="hidden">
    <input id="eEmail" placeholder="Invited email" />
    <button class="primary" onclick="employeeCheck()">Check access</button>
    <div id="eMsg" class="msg"></div>
    <div id="eSet" class="hidden">
      <input id="ePass" type="password" placeholder="Set password" />
      <button class="primary" onclick="sendOTP('employee')">Send OTP</button>
      <input id="eOtp" placeholder="6-digit OTP" maxlength="6" style="margin-top:6px" />
      <button class="primary" onclick="employeeSet()">Verify & enter</button>
    </div>
  </div>

  <div id="reset" class="hidden">
    <input id="rEmail" placeholder="Email" />
    <button class="primary" onclick="sendOTP('reset')">Send reset OTP</button>
    <input id="rOtp" placeholder="6-digit OTP" maxlength="6" style="margin-top:6px" />
    <input id="rPass" type="password" placeholder="New password" />
    <button class="primary" onclick="doReset()">Reset password</button>
  </div>

  <div id="normal" class="hidden">
    <p class="err">Normal signup is disabled. Use Company (Founder) or Employee login.</p>
  </div>

  <div id="signup" class="hidden">
    <input id="sEmail" placeholder="Founder email" />
    <input id="sPass" type="password" placeholder="Password" />
    <input id="sCompany" placeholder="Company name" />
    <button class="primary" onclick="companySignup()">Create company</button>
  </div>

  <div id="err" class="err"></div>
</div>
<script>
function setMode(m) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  ['company','employee','normal','signup'].forEach(id => document.getElementById(id).classList.add('hidden'));
  document.getElementById(m).classList.remove('hidden');
  document.getElementById('err').textContent = '';
}
function showSignup() {
  ['company','employee','normal'].forEach(id => document.getElementById(id).classList.add('hidden'));
  document.getElementById('signup').classList.remove('hidden');
}
async function companyLogin() {
  const email = document.getElementById('cEmail').value;
  const password = document.getElementById('cPass').value;
  const res = await fetch('/api/accounts/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, password, mode:'company'})});
  if (res.ok) {
    const d = await res.json();
    localStorage.setItem('doom_user', JSON.stringify(d));
    location.href = '/';
  } else document.getElementById('err').textContent = 'Invalid founder credentials';
}
async function companySignup() {
  const email = document.getElementById('sEmail').value;
  const password = document.getElementById('sPass').value;
  const company = document.getElementById('sCompany').value;
  const res = await fetch('/api/accounts/company/signup', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, password, company})});
  if (res.ok) { alert('Company created. Now login.'); setMode('company'); }
  else document.getElementById('err').textContent = 'Signup failed';
}
async function employeeCheck() {
  const email = document.getElementById('eEmail').value;
  const res = await fetch('/api/accounts/employee/check', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email})});
  const d = await res.json();
  document.getElementById('eMsg').textContent = d.message;
  if (d.status === 'allowed') document.getElementById('eSet').classList.remove('hidden');
}
async function sendOTP(purpose) {
  const email = purpose === 'reset' ? document.getElementById('rEmail').value : document.getElementById('eEmail').value;
  const res = await fetch('/api/accounts/otp/send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, purpose})});
  const d = await res.json();
  alert('OTP sent (demo): ' + d.demo_code);
}
async function googleLogin(mode) {
  const email = prompt('Google email (demo):');
  if (!email) return;
  const res = await fetch('/api/accounts/google', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, mode})});
  if (res.ok) {
    const d = await res.json();
    localStorage.setItem('doom_user', JSON.stringify(d));
    location.href = '/';
  } else document.getElementById('err').textContent = 'Google login failed';
}
function showReset() {
  ['company','employee','normal','signup'].forEach(id => document.getElementById(id).classList.add('hidden'));
  document.getElementById('reset').classList.remove('hidden');
}
async function doReset() {
  const email = document.getElementById('rEmail').value;
  const code = document.getElementById('rOtp').value;
  const new_password = document.getElementById('rPass').value;
  const res = await fetch('/api/accounts/reset', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, code, new_password})});
  if (res.ok) { alert('Password reset. Login now.'); setMode('company'); }
  else document.getElementById('err').textContent = 'Reset failed';
}
  const email = document.getElementById('eEmail').value;
  const password = document.getElementById('ePass').value;
  const res = await fetch('/api/accounts/employee/set-password', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, password})});
  if (res.ok) {
    const login = await fetch('/api/accounts/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, password, mode:'employee'})});
    if (login.ok) {
      const d = await login.json();
      localStorage.setItem('doom_user', JSON.stringify(d));
      location.href = '/';
    }
  } else document.getElementById('err').textContent = 'Could not set password';
}
</script>
</body>
</html>
"""

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return LOGIN_HTML
