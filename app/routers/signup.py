from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

# Standard NIBSS bank codes -- public, standardized across every Nigerian
# payment provider, not specific to Nomba. Hardcoded here rather than
# fetched live, since the live lookup needs the same Nomba auth call that's
# currently geo-blocked from this server anyway.
NIGERIAN_BANKS = [
    ("044", "Access Bank"),
    ("023", "Citibank Nigeria"),
    ("050", "Ecobank Nigeria"),
    ("070", "Fidelity Bank"),
    ("011", "First Bank of Nigeria"),
    ("214", "First City Monument Bank"),
    ("058", "Guaranty Trust Bank"),
    ("030", "Heritage Bank"),
    ("301", "Jaiz Bank"),
    ("082", "Keystone Bank"),
    ("076", "Polaris Bank"),
    ("101", "Providus Bank"),
    ("221", "Stanbic IBTC Bank"),
    ("232", "Sterling Bank"),
    ("032", "Union Bank of Nigeria"),
    ("033", "United Bank for Africa"),
    ("215", "Unity Bank"),
    ("035", "Wema Bank"),
    ("057", "Zenith Bank"),
]


@router.get("/signup", response_class=HTMLResponse)
def signup_page():
    bank_options = "\n".join(
        f'<option value="{code}">{name}</option>' for code, name in NIGERIAN_BANKS
    )

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SubFlow -- Business Sign Up</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #0f1115; color: #e6e8eb;
         display: flex; justify-content: center; padding: 40px 16px; }}
  .card {{ background: #171a21; border: 1px solid #2a2e37; border-radius: 12px; padding: 32px;
          max-width: 440px; width: 100%; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  p.sub {{ color: #9aa1ac; margin: 0 0 24px; font-size: 14px; }}
  label {{ display: block; font-size: 13px; color: #b8bec9; margin: 16px 0 6px; }}
  input, select {{ width: 100%; box-sizing: border-box; padding: 10px 12px; background: #0f1115;
                  border: 1px solid #2a2e37; border-radius: 8px; color: #e6e8eb; font-size: 14px; }}
  input:focus, select:focus {{ outline: none; border-color: #4f7cff; }}
  button {{ margin-top: 24px; width: 100%; padding: 12px; background: #4f7cff; color: white; border: none;
           border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; }}
  button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
  #result {{ margin-top: 20px; padding: 14px; border-radius: 8px; font-size: 13px; display: none;
            word-break: break-word; }}
  #result.ok {{ background: #103c22; border: 1px solid #1e7a44; color: #7ee2a8; display: block; }}
  #result.err {{ background: #3c1010; border: 1px solid #7a1e1e; color: #ff9d9d; display: block; }}
  .fieldset-title {{ font-size: 13px; color: #6f7684; text-transform: uppercase; letter-spacing: 0.04em;
                     margin-top: 28px; border-top: 1px solid #2a2e37; padding-top: 20px; }}
</style>
</head>
<body>
  <div class="card">
    <h1>Register your business</h1>
    <p class="sub">Get set up on SubFlow -- no office visit, no waiting on a bank account.</p>

    <form id="signup-form">
      <label for="name">Business name</label>
      <input id="name" required placeholder="e.g. GymFlex Ltd">

      <label for="email">Business email</label>
      <input id="email" type="email" required placeholder="billing@yourbusiness.com">

      <div class="fieldset-title">Where should we pay you?</div>

      <label for="bank_code">Bank</label>
      <select id="bank_code" required>
        <option value="" disabled selected>Select your bank</option>
        {bank_options}
      </select>

      <label for="bank_account_number">Account number</label>
      <input id="bank_account_number" required maxlength="10" pattern="[0-9]{{10}}"
             placeholder="10-digit account number">

      <label for="bank_account_name">Account holder name</label>
      <input id="bank_account_name" required placeholder="Name exactly as it appears on the account">

      <button type="submit" id="submit-btn">Create my account</button>
    </form>

    <div id="result"></div>
  </div>

<script>
  const form = document.getElementById("signup-form");
  const resultBox = document.getElementById("result");
  const submitBtn = document.getElementById("submit-btn");

  function showResult(message, ok) {{
    resultBox.textContent = message;
    resultBox.className = ok ? "ok" : "err";
  }}

  form.addEventListener("submit", async (e) => {{
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating...";

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const bank_code = document.getElementById("bank_code").value;
    const bank_account_number = document.getElementById("bank_account_number").value.trim();
    const bank_account_name = document.getElementById("bank_account_name").value.trim();

    try {{
      const tenantResp = await fetch("/api/tenants/", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ name, email }}),
      }});
      if (!tenantResp.ok) {{
        const err = await tenantResp.json();
        throw new Error(err.detail || "Could not create tenant");
      }}
      const tenant = await tenantResp.json();

      const updateResp = await fetch(`/api/tenants/${{tenant.id}}`, {{
        method: "PUT",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ bank_code, bank_account_number, bank_account_name }}),
      }});
      if (!updateResp.ok) {{
        const err = await updateResp.json();
        throw new Error(err.detail || "Tenant created, but saving bank details failed");
      }}

      showResult(
        `You're all set. Your API key is ${{tenant.api_key}} -- save this, it won't be shown again.`,
        true
      );
      form.reset();
    }} catch (err) {{
      showResult(err.message, false);
    }} finally {{
      submitBtn.disabled = false;
      submitBtn.textContent = "Create my account";
    }}
  }});
</script>
</body>
</html>
"""
