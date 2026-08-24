#!/var/ossec/framework/python/bin/python3
import html, json, sys
from datetime import datetime
import requests

LOG = "/var/ossec/logs/integrations.log"

# nivel do Wazuh -> urgencia do GLPI (1 a 5)
def urgencia(n):
    if n >= 14: return 5
    if n >= 12: return 4
    if n >= 10: return 3
    return 2

# grupo da regra -> ID da categoria no GLPI
CATEGORIAS = {
    "authentication_failed": 2,
    "authentication_failures": 2,
    "invalid_login": 2,
    "virustotal": 3,
    "malware": 3,
    "syscheck": 4,
}

def log(msg):
    with open(LOG, "a") as f:
        f.write("%s wazuh-glpi: %s\n" % (datetime.now().isoformat(timespec="seconds"), msg))

def corpo(a):
    r = a.get("rule", {}); ag = a.get("agent", {}); d = a.get("data", {}) or {}
    linhas = [
        ("Regra", "%s - %s" % (r.get("id"), r.get("description"))),
        ("Nivel", r.get("level")),
        ("MITRE", ", ".join(r.get("mitre", {}).get("id", []) or []) or "-"),
        ("Agente", "%s (%s)" % (ag.get("name"), ag.get("ip", "-"))),
        ("Data", a.get("timestamp")),
        ("Origem", d.get("srcip", "-")),
        ("Usuario", d.get("srcuser") or d.get("dstuser") or "-"),
    ]
    c = "<p><b>Chamado aberto automaticamente pelo Wazuh.</b></p><ul>"
    for k, v in linhas:
        c += "<li><b>%s:</b> %s</li>" % (k, html.escape(str(v)))
    c += "</ul>"
    if a.get("full_log"):
        c += "<p><b>Log:</b></p><pre>%s</pre>" % html.escape(str(a["full_log"])[:1500])
    return c

def main():
    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        conteudo = f.read().strip()
    # o Wazuh às vezes grava o alerta em mais de uma linha; pega o ultimo JSON valido
    alerta = None
    for linha in reversed(conteudo.splitlines()):
        linha = linha.strip()
        if linha.startswith("{"):
            try:
                alerta = json.loads(linha)
                break
            except Exception:
                continue
    if alerta is None:
        alerta = json.loads(conteudo)
    app_token, user_token = sys.argv[2].split(":", 1)
    url = sys.argv[3].rstrip("/")
    h = {"Content-Type": "application/json", "App-Token": app_token}

    r = requests.get(url + "/initSession",
                     headers=dict(h, Authorization="user_token " + user_token), timeout=15)
    r.raise_for_status()
    sess = r.json()["session_token"]

    rule = alerta.get("rule", {})
    nivel = int(rule.get("level", 0))
    cat = next((CATEGORIAS[g] for g in rule.get("groups", []) if g in CATEGORIAS), 0)

    payload = {
        "name": ("[WAZUH][N%d] %s - %s" % (nivel, alerta.get("agent", {}).get("name", "?"),
                                           rule.get("description", "Alerta")))[:250],
        "content": corpo(alerta),
        "type": 1, "status": 1,
        "urgency": urgencia(nivel), "impact": 3, "priority": urgencia(nivel),
    }
    if cat:
        payload["itilcategories_id"] = cat

    resp = requests.post(url + "/Ticket", headers=dict(h, **{"Session-Token": sess}),
                         json={"input": payload}, timeout=15)
    if resp.status_code in (200, 201):
        log("OK chamado #%s | regra %s nivel %s" % (resp.json().get("id"), rule.get("id"), nivel))
    else:
        log("ERRO HTTP %s: %s" % (resp.status_code, resp.text[:300]))

    requests.get(url + "/killSession", headers=dict(h, **{"Session-Token": sess}), timeout=15)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("EXCECAO: %s" % e)
