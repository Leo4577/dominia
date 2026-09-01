#!/usr/bin/env python3
"""
Dashboard DOMINIA (juzia_dashboard.html + docs/index.html) — site organizado por abas,
tema claro/roxo. Consulta por Setor+Tese+Ano ao vivo. Lê juzia_base.json, emergentes.json,
base_massa.json, registros_validados.json, registros_massa.json.
"""
import json, os
from collections import defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)))
def L(f,d): return json.load(open(f,encoding="utf-8")) if os.path.exists(f) else d
base=L("juzia_base.json",{"total":0,"setores":[]}); emg=L("emergentes.json",{"teses":[]})
massa=L("base_massa.json",{"total":0,"setores":[],"reus":[]})
RV=L("registros_validados.json",[]); RM=L("registros_massa.json",[])
DJE=L("dje_stats.json",{"total":0,"cidades":0,"n_juizes":0,"foros":{},"dano_moral_por_area":[],"exito_por_area":[],"comarcas":[],"reus":[],"juizes":[]})
RDJE=L("registros_dje.json",[])
# Juizado: usa o Datajud/CNJ (o DJEN não pega Projudi). Resultado por códigos oficiais; sem íntegra/dano moral.
try:
    from suspensoes import SUSPENSOES
except Exception:
    SUSPENSOES=[]
BUSCA=L("busca_index.json",{"itens":[]})   # índice p/ Busca IA (1º grau + Turmas)
CENSO=L("censo_juizado.json",{})       # (A) censo tese × comarca + exemplos de processo
REUS_B=L("reus_stats.json",{})         # (B) ranking por réu + dano moral + exemplos
VARA=L("vara_stats.json",{})           # por VARA (1º grau) + por RELATOR/TURMA (2º grau, acórdão×monocrática)
JUI=L("juizes_stats.json",{})          # por JUIZ: % procedência + comarca + dano moral mediano
DJDJ=L("datajud_juizado.json",{})
if DJDJ.get("por_setor"):
    DJE.setdefault("por_foro",{})["JUIZADO"]={
      "total":DJDJ.get("julgados",0),"fonte":"Datajud/CNJ","sem_integra":True,
      "exito_por_area":[{"setor":s["setor"],"n":s["n"],"pct":s.get("pct_proc")}
                        for s in sorted(DJDJ["por_setor"],key=lambda x:-x["n"])],
      "dano_moral_por_area":[],
      "comarcas":[{"comarca":c["comarca"],"n":c["n"],"pct":c.get("pct"),"dm":None,"pct_dm":None} for c in DJDJ.get("comarcas",[])],
      "comparador":{}}

LABEL={"FINANCEIRO":"Instituições financeiras","AEREO":"Companhias aéreas","SAUDE":"Planos de saúde",
       "COELBA":"Coelba (energia)","EMBASA":"Embasa (água)","TELECOM":"Telefonia / internet",
       "ECOMMERCE":"Produto / e-commerce","CONSUMO":"Consumo geral","FRAUDE":"Fraude / golpe digital","APOSTAS":"Apostas / bet",
       "CONSUMO_DIGITAL":"Plataformas digitais"}
ICON={"FINANCEIRO":"🏦","AEREO":"✈️","SAUDE":"🏥","COELBA":"⚡","EMBASA":"💧","TELECOM":"📱",
      "ECOMMERCE":"🛒","CONSUMO":"🛍️","FRAUDE":"🔒","APOSTAS":"🎰"}

grid=defaultdict(lambda:defaultdict(lambda:[0,0,0]))
for r in RM:
    a=r.get("a") or "s/ano"; c=grid[r["s"]][a]; c[0]+=1
    if r.get("g")=="F": c[1]+=1
    elif r.get("g")=="U": c[2]+=1
massa_grid={s:{a:v for a,v in ans.items()} for s,ans in grid.items()}
setor_codes=sorted(massa_grid.keys(), key=lambda s:-sum(v[0] for v in massa_grid[s].values()))
for r in RV:
    if r["setor"] not in setor_codes: setor_codes.append(r["setor"])
setores=[{"code":c,"label":LABEL.get(c,c),"icon":ICON.get(c,"•"),
          "massa_n":sum(v[0] for v in massa_grid.get(c,{}).values())} for c in setor_codes]

anos_set={r.get("a") for r in RM}|{r.get("ano") for r in RV}
anos=sorted([a for a in anos_set if a and str(a).isdigit() and int(a)>=2022], reverse=True)

EMERG=("NOVA","SURGINDO","CRESCENDO")
teses=[{"tese":t["tese"],"status":t["status"],"mult":t["multiplicador"],"antes":t["n_antigo"],"agora":t["n_recente"],
        "mult6":t.get("mult_6m"),"antes6":t.get("n_anterior_6m"),"agora6":t.get("n_recente_6m"),
        "setor":t["setor"],"guia":t.get("guia"),"processos":t.get("processos",[])}
       for t in emg.get("teses",[]) if t.get("guia") or t["status"] in EMERG]
try:
    from receita import receita_de
    for t in teses: t["receita"]=receita_de(t["tese"], t.get("guia") or {}, t.get("setor"))
except Exception as _e:
    pass
ordem={"NOVA":0,"SURGINDO":1,"CRESCENDO":2,"ESTAVEL":3,"DECLINANDO":4}
teses.sort(key=lambda x:(ordem.get(x["status"],9),-(x["mult"] or 0)))
n_emergentes=sum(1 for t in teses if t["status"] in EMERG)
reus=[{"reu":r["reu"],"n":r["n"],"pct":r["pct_fav_sinal"]} for r in massa.get("reus",[]) if r.get("pct_fav_sinal") is not None][:16]

DADOS={"massa_total":massa.get("total",0),"validados":base["total"],"n_setores":len(setores),
       "setores":setores,"anos":anos,"massa_grid":massa_grid,"rv":RV,"reus":reus,
       "teses":teses,"n_emergentes":n_emergentes,"labels":LABEL,"gerado_em":emg.get("gerado_em",""),
       "dje":DJE,"rdje":RDJE,"censo":CENSO,"reus_b":REUS_B,"busca":[],"vara":VARA,"juizes":JUI,
       "suspensoes":[s for s in SUSPENSOES if s.get("status")=="SUSPENSA"]}

HTML=r"""<meta charset="utf-8">
<title>DOMINIA — Inteligência para o Direito</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{--purple:#7c1fd0;--purple2:#a855f7;--purple-deep:#5b0a9e;--tint:#f4ecfd;--ink:#1a1526;--ink-soft:#615a72;
    --ink-faint:#a49cb4;--bg:#fbfaff;--surface:#ffffff;--line:#efeaf7;--track:#f3eefb;--win:#00a868;--win-tint:#e5f6ef;
    --amber:#c47d00;--amber-tint:#fbf1dd;--shadow:0 1px 2px rgba(90,10,158,.03),0 6px 20px rgba(90,10,158,.05);}
  :root{color-scheme:light}   /* DOMINIA: identidade clara e clean, sempre — detalhes em roxo claro e escuro */
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;}
  /* nav */
  .nav{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--surface) 88%,transparent);backdrop-filter:saturate(1.2) blur(10px);border-bottom:1px solid var(--line)}
  .nav-in{max-width:1240px;margin:0 auto;padding:12px 32px;display:flex;align-items:center;gap:18px}
  .logo{display:flex;align-items:center;gap:10px;flex:none}
  .logo .wm{font-size:20px;font-weight:600;letter-spacing:.20em;line-height:1;display:flex;flex-direction:column;gap:3px;color:var(--ink)}
  .logo .wm .j{color:var(--purple)}
  .logo .wm .tag{font-size:8px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--purple2)}
  .tabs{display:flex;gap:4px;margin-left:auto;flex-wrap:wrap}
  .tab{font:inherit;font-size:13px;font-weight:600;color:var(--ink-soft);background:none;border:none;padding:8px 13px;border-radius:10px;cursor:pointer}
  .tab:hover{background:var(--tint);color:var(--purple)}
  .tab.on{background:var(--purple);color:#fff}
  .wrap{max-width:1240px;margin:0 auto;padding:26px 32px 90px}
  .view{display:none}.view.on{display:block}
  h2{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint);font-weight:700;margin:0 0 14px}
  .pagehead{font-size:20px;font-weight:800;letter-spacing:-.01em;margin:0 0 4px}
  .pagesub{color:var(--ink-soft);font-size:13.5px;margin:0 0 20px}
  /* kpis */
  .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}
  @media(max-width:640px){.kpis{grid-template-columns:repeat(2,1fr)}}
  .kpi{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:15px 17px;box-shadow:var(--shadow)}
  .kpi .v{font-size:25px;font-weight:800;letter-spacing:-.02em;line-height:1;color:var(--purple)}
  .kpi .v.ink{color:var(--ink)}.kpi .l{font-size:11px;color:var(--ink-faint);margin-top:6px}
  /* consulta */
  .consulta{background:linear-gradient(135deg,var(--purple-deep),var(--purple));border-radius:20px;padding:20px 22px 22px;box-shadow:var(--shadow);color:#fff}
  .consulta h3{margin:0 0 3px;font-size:16px;font-weight:700}.consulta .cs{font-size:12px;opacity:.9;margin:0 0 14px}
  .filtros{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
  @media(max-width:640px){.filtros{grid-template-columns:1fr}}
  .fld label{display:block;font-size:10px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;opacity:.85;margin-bottom:5px}
  .fld select{width:100%;font:inherit;font-size:14px;font-weight:600;color:var(--ink);background:#fff;border:none;border-radius:12px;padding:11px 13px;cursor:pointer;appearance:none;
    background-image:linear-gradient(45deg,transparent 50%,var(--purple) 50%),linear-gradient(135deg,var(--purple) 50%,transparent 50%);background-position:calc(100% - 18px) 55%,calc(100% - 13px) 55%;background-size:5px 5px;background-repeat:no-repeat}
  .resultado{background:var(--surface);border:1px solid var(--line);border-top:none;border-radius:0 0 18px 18px;margin-top:-12px;padding:24px 22px 20px;box-shadow:var(--shadow)}
  .big{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  .big .num{font-size:50px;font-weight:800;letter-spacing:-.03em;line-height:1;color:var(--win)}
  .big .num.low{color:var(--amber)}.big .num.mid{color:var(--purple)}
  .big .meta{font-size:13px;color:var(--ink-soft)}.big .meta b{color:var(--ink)}
  .ic{font-family:ui-monospace,monospace;font-size:12px;color:var(--ink-faint)}
  .pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
  .pill{font-size:12px;background:var(--tint);color:var(--ink-soft);border-radius:10px;padding:7px 12px}.pill b{color:var(--purple)}
  .mini{font-size:11px;color:var(--ink-faint);letter-spacing:.05em;text-transform:uppercase;font-weight:700;margin:18px 0 8px}
  .reuchips{display:flex;flex-wrap:wrap;gap:7px}
  .reuchip{font-size:11.5px;background:var(--tint);color:var(--ink-soft);border-radius:8px;padding:4px 9px}.reuchip b{color:var(--purple)}
  details.procs{margin-top:16px;border-top:1px solid var(--line);padding-top:12px}
  details.procs summary{cursor:pointer;font-size:12px;color:var(--purple);font-weight:600;list-style:none}
  details.procs summary::-webkit-details-marker{display:none}
  .proclist{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
  .proc{font-family:ui-monospace,monospace;font-size:10.5px;color:var(--ink-soft);background:var(--track);border-radius:5px;padding:3px 7px}
  .aviso{font-size:11.5px;color:var(--ink-faint);margin-top:16px;line-height:1.6}
  .semval{font-size:13px;color:var(--ink-soft);background:var(--tint);border-radius:12px;padding:14px 16px;margin-top:6px}
  /* grupos emergentes */
  /* suspensões (alerta) */
  .susp-band{background:linear-gradient(135deg,var(--amber-tint),var(--tint));border:1px solid var(--amber);border-radius:16px;padding:16px 18px;margin-bottom:22px}
  .susp-band .sh{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:800;color:var(--amber);margin-bottom:12px}
  .susp-card{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:8px;cursor:pointer}
  .susp-card:hover{border-color:var(--amber)}
  .susp-card .st{flex:1;min-width:0}.susp-card .st b{font-size:13.5px;font-weight:700}.susp-card .st small{display:block;color:var(--ink-faint);font-size:11.5px;margin-top:1px}
  .susp-card .sb{font-size:9.5px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;background:var(--amber);color:#fff;padding:3px 8px;border-radius:7px;flex:none}
  .nichos{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px}
  .nicho{font:inherit;font-size:12.5px;font-weight:600;color:var(--ink-soft);background:var(--surface);border:1px solid var(--line);border-radius:99px;padding:6px 13px;cursor:pointer}
  .nicho:hover{border-color:var(--purple2);color:var(--purple)}
  .nicho.on{background:var(--purple);color:#fff;border-color:var(--purple)}
  .grp{margin-bottom:22px}
  .grp-h{display:flex;align-items:center;gap:8px;margin-bottom:10px}
  .grp-h .tag{font-size:10px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;padding:4px 9px;border-radius:8px}
  .tag.NOVA{background:var(--purple);color:#fff}.tag.SURGINDO{background:var(--win-tint);color:var(--win)}.tag.CRESCENDO{background:var(--amber-tint);color:var(--amber)}
  .grp-h span{font-size:12px;color:var(--ink-faint)}
  .emg{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  @media(max-width:640px){.emg{grid-template-columns:1fr}}
  .emgcard{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:13px 15px;box-shadow:var(--shadow);display:flex;align-items:center;gap:11px;cursor:pointer}
  .emgcard:hover{border-color:var(--purple2)}
  .emgcard .t{font-size:13px;font-weight:600;flex:1;min-width:0}.emgcard .t small{display:block;color:var(--ink-faint);font-weight:400;font-size:11px}
  .emgcard .x{font-family:ui-monospace,monospace;font-size:15px;font-weight:800;color:var(--purple)}
  /* réu */
  .reugrid{display:grid;grid-template-columns:1fr 1fr;gap:6px 22px}
  @media(max-width:560px){.reugrid{grid-template-columns:1fr}}
  .reurow{display:grid;grid-template-columns:130px 1fr 44px;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line)}
  .reurow .rn{font-size:12.5px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .reurow .tk{height:7px;background:var(--track);border-radius:99px;overflow:hidden}.reurow .tk>div{height:100%;background:var(--purple);border-radius:99px}
  .reurow .rv{font-size:12.5px;font-weight:700;color:var(--purple);text-align:right}
  /* setores grid */
  .setgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  @media(max-width:640px){.setgrid{grid-template-columns:1fr}}
  .setcard{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:var(--shadow);cursor:pointer;display:flex;align-items:center;gap:14px}
  .setcard:hover{border-color:var(--purple2)}
  .setcard .ic2{width:42px;height:42px;border-radius:12px;background:var(--tint);display:flex;align-items:center;justify-content:center;font-size:20px;flex:none}
  .setcard .nm{font-size:14.5px;font-weight:650;flex:1}.setcard .nm small{display:block;font-weight:400;color:var(--ink-faint);font-size:11.5px}
  .setcard .go{color:var(--purple);font-size:18px}
  .disc{margin-top:36px;font-size:11.5px;color:var(--ink-faint);border-top:1px solid var(--line);padding-top:16px;line-height:1.7}.disc b{color:var(--ink-soft)}
  /* botão relatório */
  .btn{font:inherit;font-size:13px;font-weight:650;border:none;border-radius:11px;padding:10px 16px;cursor:pointer;display:inline-flex;align-items:center;gap:7px}
  .btn.pri{background:var(--purple);color:#fff}.btn.pri:hover{background:var(--purple-deep)}
  .btn.ghost{background:var(--tint);color:var(--purple)}.btn.ghost:hover{background:var(--track)}
  .actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:18px}
  /* modal */
  .modal{position:fixed;inset:0;z-index:50;display:none;align-items:flex-start;justify-content:center;padding:40px 16px;overflow:auto;background:rgba(28,19,48,.45);backdrop-filter:blur(3px)}
  .modal.on{display:flex}
  .sheet{background:var(--surface);border:1px solid var(--line);border-radius:20px;max-width:640px;width:100%;box-shadow:0 20px 60px rgba(28,19,48,.3);padding:26px 28px 28px}
  .sheet .close{float:right;font-size:22px;line-height:1;color:var(--ink-faint);background:none;border:none;cursor:pointer;margin:-6px -6px 0 0}
  .sheet h3{margin:0 4px 2px 0;font-size:20px;font-weight:800;letter-spacing:-.01em;padding-right:28px}
  .sheet .sub{font-size:12.5px;color:var(--ink-faint);margin-bottom:16px}
  .sec{margin-top:18px}.sec h4{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--purple);font-weight:700;margin:0 0 8px}
  .sec p{margin:0;font-size:13.5px;color:var(--ink-soft);line-height:1.62}
  .sec ul{margin:0;padding-left:18px}.sec li{font-size:13px;color:var(--ink-soft);margin-bottom:5px;line-height:1.5}
  .fchips{display:flex;flex-wrap:wrap;gap:6px}.fchip{font-size:11.5px;background:var(--tint);color:var(--purple);border-radius:8px;padding:4px 10px;font-weight:600}
  .valref{font-size:13px;color:var(--ink);background:var(--win-tint);border-radius:10px;padding:11px 14px;line-height:1.5}
  .receita{background:linear-gradient(180deg,#faf5ff,#fff);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
  .exito-badge{font-size:12.5px;background:var(--win-tint);color:#0a7a52;border-radius:8px;padding:7px 11px;display:inline-block;margin-bottom:10px}
  .exito-badge b{color:#0a7a52}
  ol.passos{margin:6px 0 0;padding-left:20px;display:flex;flex-direction:column;gap:9px}
  ol.passos li{font-size:13px;line-height:1.5;color:var(--ink);padding-left:4px}
  ol.passos li::marker{color:var(--purple);font-weight:700}
  .pd{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
  @media(max-width:560px){.pd{grid-template-columns:1fr}}
  .pd-ok,.pd-no{font-size:12.5px;line-height:1.45;border-radius:10px;padding:10px 12px}
  .pd-ok{background:var(--win-tint)}.pd-no{background:#fdeeee}
  .pd-ok span,.pd-no span{display:block;font-weight:700;font-size:11px;letter-spacing:.04em;margin-bottom:4px}
  .pd-ok span{color:#0a7a52}.pd-no span{color:#c0392b}
  .procbox{max-height:150px;overflow:auto;background:var(--track);border-radius:10px;padding:10px}
  .procgrid{display:flex;flex-wrap:wrap;gap:5px}.pnum{font-family:ui-monospace,monospace;font-size:10.5px;color:var(--ink-soft);background:var(--surface);border:1px solid var(--line);border-radius:5px;padding:3px 7px}
  /* formulário petição */
  .form{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:20px 22px;box-shadow:var(--shadow)}
  .frow{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:640px){.frow{grid-template-columns:1fr}}
  .field{margin-bottom:13px}
  .field label{display:block;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;font-weight:700;color:var(--ink-faint);margin-bottom:5px}
  .field input,.field textarea,.field select{width:100%;font:inherit;font-size:14px;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
  .field textarea{min-height:110px;resize:vertical;line-height:1.5}
  .field input:focus,.field textarea:focus,.field select:focus{outline:none;border-color:var(--purple2)}
  .peca{background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:26px 28px;margin-top:18px;font-size:13.5px;line-height:1.7;color:var(--ink)}
  .peca h5{font-size:13px;font-weight:800;text-align:center;letter-spacing:.02em;margin:18px 0 10px}.peca h5:first-child{margin-top:0}
  .peca p{margin:0 0 11px;text-align:justify}.peca .cab{text-align:center;font-weight:700}.peca .end{text-align:right}
  .peca .ass{text-align:center;margin-top:26px}.peca em{color:var(--purple)}
  /* decisões */
  .dfilters{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:14px}
  @media(max-width:640px){.dfilters{grid-template-columns:1fr 1fr}}
  .dsearch{display:flex;align-items:center;gap:10px;background:var(--surface);border:1.5px solid var(--line);border-radius:13px;padding:0 14px;margin-bottom:12px;box-shadow:var(--shadow);transition:border-color .15s}
  .dsearch:focus-within{border-color:var(--purple)}
  .dsearch svg{width:19px;height:19px;color:var(--purple);flex:none}
  .dsearch input{flex:1;border:0;outline:0;background:transparent;font:inherit;font-size:15px;color:var(--ink);padding:13px 0}
  .dsearch input::placeholder{color:var(--ink-faint)}
  .dfilters select{width:100%;font:inherit;font-size:13px;font-weight:600;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:10px 12px;cursor:pointer}
  .dcount{font-size:12px;color:var(--ink-faint);margin:0 0 12px}
  .bbox{display:flex;gap:9px;margin-bottom:12px}@media(max-width:600px){.bbox{flex-direction:column}}
  .bbox input{flex:1;font:inherit;font-size:15px;color:var(--ink);background:var(--surface);border:1.5px solid var(--line);border-radius:13px;padding:13px 16px}
  .bbox input:focus{outline:none;border-color:var(--purple2)}
  .bchips{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px}
  .bchip{font-size:12px;color:var(--purple);background:var(--tint);border:none;border-radius:99px;padding:6px 12px;cursor:pointer;font:inherit}.bchip:hover{background:var(--track)}
  .bcard{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:15px 17px;box-shadow:var(--shadow);margin-bottom:10px}
  .bcard .bt{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}
  .bcard .grau{font-size:10px;font-weight:800;letter-spacing:.05em;padding:3px 8px;border-radius:7px;background:var(--tint);color:var(--purple)}
  .bcard .res{font-size:11px;font-weight:700;padding:2px 8px;border-radius:7px}
  .bcard .res.favoravel{background:var(--win-tint);color:var(--win)}.bcard .res.desfavoravel{background:var(--amber-tint);color:var(--amber)}
  .bcard .bem{font-size:13px;color:var(--ink-soft);line-height:1.55}
  .bcard .bfoot{display:flex;justify-content:space-between;gap:8px;margin-top:9px;font-size:11.5px}
  .bcard .bproc{font-family:ui-monospace,monospace;color:var(--ink-soft)}.bcard .breu{color:var(--purple);font-weight:600}
  .fsel{font:inherit;font-size:13.5px;font-weight:600;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:10px 13px;cursor:pointer;margin-bottom:12px;min-width:240px;max-width:100%}
  .crow.c5{grid-template-columns:1fr 54px 64px 74px 70px}
  .crow.c6{grid-template-columns:1.4fr 90px 52px 64px 82px 52px}
  @media(max-width:640px){.crow.c6{grid-template-columns:1.2fr 64px 44px 56px}.crow.c6 span:nth-child(5),.crow.c6 span:nth-child(6){display:none}}
  .frow{display:flex;gap:10px;flex-wrap:wrap}.frow .fsel{flex:1;min-width:180px}
  .crow .cf{color:var(--ink-faint);font-weight:600}
  .fonte-nota{font-size:11.5px;color:var(--ink-faint);background:var(--tint);border-radius:10px;padding:9px 13px;margin:0 0 14px;line-height:1.5}
  .dmrow .dtk>div.acc{background:linear-gradient(90deg,var(--win),#3fcf8e)}
  .dcard{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:var(--shadow);margin-bottom:9px}
  .dcard .dtop{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
  .dcard .res{font-size:11px;font-weight:800;padding:3px 9px;border-radius:8px}
  .res.PROCEDENTE,.res.PARCIAL{background:var(--win-tint);color:var(--win)}.res.IMPROCEDENTE{background:var(--amber-tint);color:var(--amber)}.res.INDEF{background:var(--track);color:var(--ink-faint)}
  .dcard .val{font-size:16px;font-weight:800;color:var(--win)}
  .dcard .dmeta{display:flex;flex-wrap:wrap;gap:5px 14px;margin-top:9px;font-size:12px;color:var(--ink-soft)}
  .dcard .dmeta b{color:var(--ink);font-weight:600}.dcard .dmeta .k{color:var(--ink-faint)}
  .dcard a.int{font-size:11.5px;color:var(--purple);font-weight:600;text-decoration:none}
  .dcard .dem{margin-top:9px;font-size:12.5px;line-height:1.5;color:var(--ink-soft);background:var(--tint);border-left:3px solid var(--purple);border-radius:0 8px 8px 0;padding:8px 11px}
  .dmore{display:block;margin:12px auto 0;font:inherit;font-size:13px;font-weight:600;color:var(--purple);background:var(--tint);border:none;border-radius:11px;padding:11px 20px;cursor:pointer}
  /* dano moral por área */
  .dmrow{display:grid;grid-template-columns:130px 1fr 96px;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line)}
  .dmrow .dn{font-size:13px;font-weight:600}.dmrow .dtk{height:9px;background:var(--track);border-radius:99px;overflow:hidden}.dmrow .dtk>div{height:100%;background:linear-gradient(90deg,var(--purple2),var(--purple));border-radius:99px}
  .dmrow .dvv{font-size:13.5px;font-weight:800;color:var(--win);text-align:right}
  /* comarcas tabela */
  .ctable{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--surface);box-shadow:var(--shadow)}
  .crow{display:grid;grid-template-columns:1fr 60px 70px 90px;gap:8px;padding:10px 14px;font-size:12.5px;border-bottom:1px solid var(--line);align-items:center}
  .crow:last-child{border-bottom:none}.crow.h{background:var(--tint);font-weight:700;color:var(--ink-faint);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase}
  .crow .cc{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.crow .cp{color:var(--win);font-weight:700}.crow .cd{font-weight:700}
  /* juízes */
  .jgrid{display:grid;grid-template-columns:1fr 1fr;gap:7px}@media(max-width:640px){.jgrid{grid-template-columns:1fr}}
  .jchip{display:flex;justify-content:space-between;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:9px 13px;font-size:12.5px}
  .jchip .jn{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.jchip .jq{color:var(--purple);font-weight:700;flex:none}
  /* planos */
  .planos{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}@media(max-width:760px){.planos{grid-template-columns:1fr}}
  .plano{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:22px 20px;box-shadow:var(--shadow);display:flex;flex-direction:column}
  .plano.pop{border:2px solid var(--purple);position:relative}
  .plano .badge{position:absolute;top:-10px;left:20px;background:var(--purple);color:#fff;font-size:10px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;padding:3px 10px;border-radius:8px}
  .plano .pnome{font-size:15px;font-weight:800}.plano .preco{font-size:34px;font-weight:800;letter-spacing:-.02em;margin:8px 0 2px}.plano .preco small{font-size:14px;color:var(--ink-faint);font-weight:600}
  .plano .pfeat{list-style:none;padding:0;margin:14px 0 18px;flex:1}.plano .pfeat li{font-size:12.5px;color:var(--ink-soft);padding:6px 0 6px 22px;position:relative;line-height:1.4}
  .plano .pfeat li:before{content:"✓";position:absolute;left:0;color:var(--win);font-weight:800}
  .plano .pcta{font:inherit;font-size:13.5px;font-weight:700;border:none;border-radius:11px;padding:12px;cursor:pointer;background:var(--tint);color:var(--purple)}
  .plano.pop .pcta{background:var(--purple);color:#fff}
  /* cursos */
  .cursos{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:640px){.cursos{grid-template-columns:1fr}}
  .curso{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:var(--shadow);display:flex;flex-direction:column;cursor:pointer}
  .curso:hover{border-color:var(--purple2)}
  .curso .ctop{display:flex;align-items:center;gap:12px;margin-bottom:10px}
  .curso .cico{width:44px;height:44px;border-radius:12px;background:var(--tint);display:flex;align-items:center;justify-content:center;font-size:22px;flex:none}
  .curso .ct{font-size:15px;font-weight:750;line-height:1.2}.curso .ct small{display:block;color:var(--ink-faint);font-weight:500;font-size:11.5px;margin-top:2px}
  .curso .cdesc{font-size:13px;color:var(--ink-soft);line-height:1.55;flex:1}
  .curso .cfoot{display:flex;align-items:center;justify-content:space-between;margin-top:14px;gap:8px}
  .curso .cmod{font-size:11.5px;color:var(--ink-faint);font-weight:600}
  .curso .cjm{font-size:10.5px;font-weight:700;color:var(--purple);background:var(--tint);border-radius:7px;padding:4px 8px}
  /* relatório (impressão) */
  #report{display:none}
  @media print{
    body{background:#fff}
    .nav,.wrap,.modal{display:none !important}
    #report{display:block !important;padding:0;color:#111;font-size:12px}
    #report .rhead{border-bottom:2px solid #8a05be;padding-bottom:10px;margin-bottom:16px}
    #report h1{font-size:20px;margin:0 0 2px;color:#5b0a9e}
    #report h2{font-size:13px;color:#8a05be;text-transform:uppercase;letter-spacing:.05em;margin:16px 0 6px}
    #report .muted{color:#666;font-size:11px}
    #report ul{margin:4px 0;padding-left:18px}#report li{margin-bottom:3px}
    #report .big{font-size:34px;font-weight:800;color:#00a868}
    #report table{border-collapse:collapse;width:100%;font-size:11px}#report td{border:1px solid #ddd;padding:4px 6px}
    #report .pnums{font-family:monospace;font-size:9.5px;color:#444;line-height:1.7}
    #report .rchart{margin:6px 0 10px;max-width:620px}
    #report ol{margin:4px 0;padding-left:20px}#report ol li{margin-bottom:5px;line-height:1.45}
    @page{margin:1.6cm}
  }
</style>
<div class="nav"><div class="nav-in">
  <div class="logo">
    <div class="wm">DOMIN<span class="j">IA</span><small class="tag">Inteligência para o Direito</small></div>
  </div>
  <div class="tabs">
    <button class="tab on" data-v="consulta">Consulta</button>
    <button class="tab" data-v="decisoes">Decisões</button>
    <button class="tab" data-v="comarcas">Comarcas</button>
    <button class="tab" data-v="varas">Varas</button>
    <button class="tab" data-v="tendencias">Tendências</button>
    <button class="tab" data-v="peticao">Petição</button>
    <button class="tab" data-v="reus">Réus</button>
    <button class="tab" data-v="cursos">Cursos</button>
    <button class="tab" data-v="planos">Planos</button>
  </div>
</div></div>

<div class="wrap">
  <!-- CONSULTA -->
  <div class="view on" id="v-consulta">
    <div class="kpis">
      <div class="kpi"><div class="v" id="k-total"></div><div class="l">decisões no Juizado (censo real)</div></div>
      <div class="kpi"><div class="v ink" id="k-val"></div><div class="l">sentenças de 1º grau (íntegra)</div></div>
      <div class="kpi"><div class="v ink" id="k-set"></div><div class="l">acórdãos das Turmas</div></div>
      <div class="kpi"><div class="v" id="k-emg"></div><div class="l">teses emergentes</div></div>
    </div>
    <div class="consulta">
      <h3>Consultar jurimetria</h3><p class="cs">Escolha setor, tese e ano — o êxito recalcula na hora.</p>
      <div class="filtros">
        <div class="fld"><label>Setor</label><select id="f-setor"></select></div>
        <div class="fld"><label>Tese</label><select id="f-tese"></select></div>
        <div class="fld"><label>Ano</label><select id="f-ano"></select></div>
      </div>
    </div>
    <div class="resultado" id="resultado"></div>
  </div>
  <!-- TENDENCIAS -->
  <div class="view" id="v-tendencias">
    <p class="pagehead">Teses emergentes</p>
    <p class="pagesub">O que está surgindo nos Juizados — comparando o volume de ~3 anos atrás com o último ano. Toque numa tese para o guia prático.</p>
    <div id="suspensoes-band"></div>
    <div class="nichos" id="jan-toggle" style="margin-bottom:10px"></div>
    <div class="nichos" id="emg-nichos"></div>
    <div id="emg-groups"></div>
  </div>
  <!-- PETICAO -->
  <div class="view" id="v-peticao">
    <p class="pagehead">Gerar petição inicial</p>
    <p class="pagesub">Preencha os dados, resuma os fatos e escolha a tese — a minuta é montada com os fundamentos e precedentes reais do TJBA. Revise antes de protocolar.</p>
    <div class="form">
      <div class="frow">
        <div class="field"><label>Autor (nome e qualificação)</label><input id="p-autor" placeholder="Ex: FULANO DE TAL, brasileiro, CPF..."></div>
        <div class="field"><label>Réu (empresa)</label><input id="p-reu" placeholder="Ex: BANCO X S.A." list="p-reulist"><datalist id="p-reulist"></datalist></div>
      </div>
      <div class="frow">
        <div class="field"><label>Tese / assunto</label><select id="p-tese"></select></div>
        <div class="field"><label>Valor da causa (opcional)</label><input id="p-valor" placeholder="Ex: R$ 15.000,00"></div>
      </div>
      <div class="field"><label>Resumo dos fatos</label><textarea id="p-fatos" placeholder="Descreva o que aconteceu: datas, valores, como o consumidor foi lesado, tentativas de solução..."></textarea></div>
      <div class="actions"><button class="btn pri" onclick="gerarPeticao()">✍️ Gerar minuta</button></div>
    </div>
    <div id="peticao-out"></div>
  </div>
  <!-- REUS -->
  <div class="view" id="v-reus">
    <p class="pagehead">Ranking de êxito por réu</p>
    <p class="pagesub">Percentual de êxito do consumidor contra cada empresa, sobre a base ampla. Quanto maior o n, mais confiável.</p>
    <div class="reugrid" id="reu"></div>
  </div>
  <!-- SETORES -->
  <div class="view" id="v-setores">
    <p class="pagehead">Setores mapeados</p>
    <p class="pagesub">Clique num setor para consultar sua jurimetria.</p>
    <div class="setgrid" id="setgrid"></div>
  </div>
  <!-- BUSCA IA -->
  <div class="view" id="v-busca">
    <p class="pagehead">Busca por caso <span style="font-size:12px;font-weight:600;color:var(--purple);background:var(--tint);border-radius:7px;padding:3px 8px;vertical-align:middle">IA ancorada</span></p>
    <p class="pagesub">Descreva o caso em linguagem natural. Entende o significado (não só a palavra) e traz <b>precedentes que existem de verdade</b> — 1º grau e Turmas Recursais — com a ementa e o nº do processo. Nunca inventa.</p>
    <div class="bbox">
      <input id="b-q" placeholder="Ex: meu voo atrasou e perdi a conexão, com gastos de hotel" autocomplete="off">
      <button class="btn pri" id="b-go">Buscar precedentes</button>
    </div>
    <div class="bchips" id="b-sugestoes"></div>
    <p class="dcount" id="b-count"></p>
    <div id="b-list"></div>
  </div>
  <!-- DECISOES (cada decisão, tudo o que importa) -->
  <div class="view" id="v-decisoes">
    <p class="pagehead">Decisões — tudo o que importa</p>
    <p class="pagesub">Sentenças reais de 1º grau (TJBA), estruturadas: valor, resultado, comarca/vara, réu e a íntegra. Pesquise por palavra, réu, tese ou nº do processo.</p>
    <div class="dsearch">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21" stroke-linecap="round"/></svg>
      <input id="d-busca" type="search" placeholder="Buscar nas decisões: ex. cirurgia reparadora, Bradesco, negativação, 0801234…">
    </div>
    <div class="dfilters">
      <select id="d-foro"></select><select id="d-setor"></select><select id="d-comarca"></select><select id="d-reu"></select><select id="d-res"></select>
    </div>
    <p class="dcount" id="d-count"></p>
    <div id="d-list"></div>
  </div>
  <!-- COMARCAS -->
  <div class="view" id="v-comarcas">
    <p class="pagehead">Mapa do 1º grau</p>
    <p class="pagesub">Onde ajuizar importa. <b>Três foros separados</b> — Juizado Especial Cível (consumo), Juizado da Fazenda Pública (contra o Estado — Planserv, servidores) e Justiça Comum. Escolha o do seu caso.</p>
    <div class="nichos" id="foro-toggle"></div>
    <p class="fonte-nota" id="foro-nota"></p>
    <div class="kpis" id="dje-kpis"></div>
    <p class="mini" style="margin-top:8px" id="lbl-dm"></p>
    <div id="dm-area"></div>
    <div id="comp-box">
      <p class="mini" style="margin-top:24px">Comparar tese entre comarcas <span style="text-transform:none;font-weight:400;color:var(--ink-faint)">— onde é mais viável ajuizar</span></p>
      <select id="comp-setor" class="fsel"></select>
      <div class="ctable" id="comp-tbl"></div>
    </div>
    <p class="mini" style="margin-top:24px">Ranking geral de comarcas</p>
    <div class="ctable" id="comarca-tbl"></div>
    <p class="mini" style="margin-top:24px">Juízes mapeados</p>
    <div class="jgrid" id="juizes"></div>
  </div>
  <!-- VARAS & RELATORES -->
  <div class="view" id="v-varas">
    <p class="pagehead">Varas &amp; Relatores — onde e diante de quem</p>
    <p class="pagesub">A média muda de <b>vara para vara</b>, não só de comarca. Salvador tem ~20 varas de consumo. Veja a <b>duração até a decisão</b>, a <b>procedência</b> e o <b>dano moral</b> por vara — e, nas Turmas, o perfil de cada <b>relator</b> (inclusive quanto ele decide sozinho, por decisão monocrática).</p>

    <p class="mini" style="margin-top:20px">1º grau — por vara</p>
    <div class="frow" style="margin:8px 0 4px">
      <select id="vara-com" class="fsel"></select>
      <select id="vara-ord" class="fsel">
        <option value="dur">Ordenar: mais rápida primeiro</option>
        <option value="proc">Ordenar: maior procedência</option>
        <option value="n">Ordenar: mais casos</option>
        <option value="dm">Ordenar: maior dano moral</option>
      </select>
    </div>
    <div class="ctable" id="vara-tbl"></div>
    <p class="fonte-nota">Duração estimada pelo ano do nº CNJ até a data de julgamento. Clique numa vara para ver processos.</p>

    <p class="mini" style="margin-top:26px">2º grau — Turmas Recursais, por relator</p>
    <p class="pagesub" style="margin-top:4px">% favorável ao consumidor, tempo até o julgamento e quanto o relator resolve por <b>decisão monocrática</b> (sozinho) × <b>acórdão</b> (colegiado).</p>
    <div class="ctable" id="rel-tbl"></div>

    <p class="mini" style="margin-top:26px">1º grau — por juiz</p>
    <p class="pagesub" style="margin-top:4px">Percentual de procedência × improcedência de cada juiz, a comarca a que pertence e o dano moral mediano que arbitra. Extraído do texto das sentenças (o censo do Datajud não expõe o juiz).</p>
    <div class="frow" style="margin:8px 0 4px">
      <select id="juiz-ord" class="fsel">
        <option value="n">Ordenar: mais casos</option>
        <option value="proc">Ordenar: maior procedência</option>
        <option value="dm">Ordenar: maior dano moral</option>
      </select>
    </div>
    <div class="ctable" id="juiz-tbl"></div>
  </div>
  <!-- CURSOS -->
  <div class="view" id="v-cursos">
    <p class="pagehead">Cursos DOMINIA</p>
    <p class="pagesub">Formação prática em Juizados, com a jurimetria embutida: cada trilha usa os dados reais do TJBA — % de êxito, fundamentos que vencem e modelos de peça atualizados.</p>
    <div class="cursos" id="cursos"></div>
    <p class="disc" style="margin-top:26px">Conteúdo autoral, atualizado pelos dados da plataforma. Incluído no plano Escritório; avulso nos demais. Não reproduz material de terceiros.</p>
  </div>
  <!-- PLANOS -->
  <div class="view" id="v-planos">
    <p class="pagehead">Planos</p>
    <p class="pagesub">Sem fidelidade no mensal · pagamento seguro · acesso imediato · 7 dias grátis.</p>
    <div class="planos" id="planos"></div>
  </div>
  <p class="disc">Base real das Turmas Recursais do TJBA. <b>Processos analisados</b> = base ampla com classificação automática (sinal). <b>Validados por IA</b> = extração estruturada com intervalo de confiança e precedentes auditáveis. Amostra em crescimento; precedente é persuasivo, não vinculante. <b>Não é previsão nem garantia de êxito.</b></p>
</div>
<div class="modal" id="modal"><div class="sheet" id="sheet"></div></div>
<div id="report"></div>
<script>
const D=__DADOS__;
let _consulta=null;
const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const nf=n=>(n||0).toLocaleString('pt-BR');
const hojeBR=()=>new Date().toLocaleDateString('pt-BR');
const setorLabel=code=>{const s=D.setores.find(s=>s.code===code);return s?s.label:((D.labels&&D.labels[code])||code);};
const cap=s=>s.replace(/_/g,' ').toLowerCase().replace(/^\w/,c=>c.toUpperCase());
const z=1.96;
function wilson(k,n){if(!n)return[0,0,0];const p=k/n,d=1+z*z/n,c=(p+z*z/(2*n))/d,m=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return[Math.round(100*p),Math.max(0,Math.round(100*(c-m))),Math.min(100,Math.round(100*(c+m)))];}
function median(a){if(!a.length)return 0;const s=[...a].sort((x,y)=>x-y),m=s.length>>1;return s.length%2?s[m]:Math.round((s[m-1]+s[m])/2);}

(()=>{const s=(D.censo&&D.censo.segmentos)||{};let ct=0;for(const k in s)ct+=s[k].total||0;
  const comum=(D.dje.por_foro&&D.dje.por_foro.COMUM)?D.dje.por_foro.COMUM.total:0;
  $("#k-total").textContent=nf(ct); $("#k-val").textContent=nf(comum); $("#k-set").textContent=nf(D.massa_total); $("#k-emg").textContent=D.n_emergentes;})();

// nav
$$(".tab").forEach(t=>t.addEventListener("click",()=>{
  $$(".tab").forEach(x=>x.classList.toggle("on",x===t));
  $$(".view").forEach(v=>v.classList.toggle("on",v.id==="v-"+t.dataset.v));
  window.scrollTo({top:0,behavior:"smooth"});
}));
function goConsulta(setor){
  $$(".tab").forEach(x=>x.classList.toggle("on",x.dataset.v==="consulta"));
  $$(".view").forEach(v=>v.classList.toggle("on",v.id==="v-consulta"));
  if(setor&&[...$("#f-setor").options].some(o=>o.value===setor)){$("#f-setor").value=setor;popularTeses();render();}
  window.scrollTo({top:0,behavior:"smooth"});
}

// filtros
$("#f-setor").innerHTML='<option value="TODOS">Todos os setores</option>'+D.setores.map(s=>`<option value="${s.code}">${s.icon} ${s.label}</option>`).join("");
$("#f-ano").innerHTML='<option value="TODOS">Todos os anos</option>'+D.anos.map(a=>`<option value="${a}">${a}</option>`).join("");
function popularTeses(){const st=$("#f-setor").value;
  const teses=[...new Set(D.rv.filter(r=>st==="TODOS"||r.setor===st).map(r=>r.tese))].sort();
  $("#f-tese").innerHTML='<option value="TODOS">Todas as teses</option>'+teses.map(t=>`<option value="${t}">${cap(t)}</option>`).join("");}
function massaCount(st,ano){let n=0,f=0,u=0;
  for(const [s,ans] of Object.entries(D.massa_grid)){if(st!=="TODOS"&&s!==st)continue;
    for(const [a,v] of Object.entries(ans)){if(ano!=="TODOS"&&a!==ano)continue;n+=v[0];f+=v[1];u+=v[2];}}
  return {n,sinal:(f+u)?Math.round(100*f/(f+u)):null};}
function render(){
  const st=$("#f-setor").value,te=$("#f-tese").value,an=$("#f-ano").value;
  const mc=massaCount(st,an);
  const rv=D.rv.filter(r=>(st==="TODOS"||r.setor===st)&&(te==="TODOS"||r.tese===te)&&(an==="TODOS"||r.ano===an));
  const n=rv.length,fav=rv.filter(r=>r.fav).length,[pct,lo,hi]=wilson(fav,n);
  const dm=rv.filter(r=>r.dm).length,vals=rv.filter(r=>r.dm&&r.valor).map(r=>r.valor);
  const cls=pct>=70?"":pct<=40?"low":"mid";
  const rmap={};rv.forEach(r=>{const k=r.reu||"n/d";(rmap[k]=rmap[k]||{n:0,f:0}).n++;if(r.fav)rmap[k].f++;});
  const reus=Object.entries(rmap).filter(([k,v])=>k!=="n/d"&&v.n>=2).sort((a,b)=>b[1].n-a[1].n).slice(0,8);
  const foros={};rv.forEach(r=>{const k=r.foro||"JUIZADO";(foros[k]=foros[k]||{n:0,f:0}).n++;if(r.fav)foros[k].f++;});
  let h=`<div class="big"><div class="num ${cls}">${n?pct+"%":"—"}</div><div class="meta">${n?`de êxito ao consumidor<br><span class="ic">n=${n} · IC95% [${lo}–${hi}]</span>`:"sem casos validados neste recorte"}</div></div>`;
  if(n){
    h+=`<div class="pills"><span class="pill"><b>${nf(mc.n)}</b> na base ampla${mc.sinal!=null?` · sinal ${mc.sinal}%`:""}</span>`;
    if(dm)h+=`<span class="pill">dano moral <b>${Math.round(100*dm/n)}%</b> · med R$ ${nf(median(vals))}</span>`;
    if(Object.keys(foros).length>1)h+=Object.entries(foros).map(([k,v])=>`<span class="pill">${k==="JUIZADO"?"Juizado":"J. Comum"} <b>${Math.round(100*v.f/v.n)}%</b> (${v.n})</span>`).join("");
    h+=`</div>`;
    if(reus.length)h+=`<div class="mini">Êxito por réu neste recorte</div><div class="reuchips">`+reus.map(([k,v])=>`<span class="reuchip">${k} <b>${Math.round(100*v.f/v.n)}%</b> <span style="color:var(--ink-faint)">(${v.n})</span></span>`).join("")+`</div>`;
    h+=`<details class="procs"><summary>Ver ${rv.length} processos (auditável)</summary><div class="proclist">`+rv.map(r=>`<span class="proc">${r.proc}</span>`).join("")+`</div></details>`;
    h+=`<p class="aviso">Percentual validado por IA com intervalo de confiança de Wilson. A base ampla é o sinal automático do mesmo recorte.</p>`;
  }else{h+=`<div class="semval">Ainda não há decisões <b>validadas por IA</b> neste recorte — mas a base ampla tem <b>${nf(mc.n)}</b> processos${mc.sinal!=null?` (sinal ${mc.sinal}%)`:""}. Validação sendo expandida.</div>`;}
  h+=`<div class="actions"><button class="btn pri" onclick="relatorioConsulta()">📄 Gerar relatório</button></div>`;
  _consulta={st,te,an,n,pct,lo,hi,mcn:mc.n,sinal:mc.sinal,dm,medVal:median(vals),reus,rv};
  $("#resultado").innerHTML=h;
}
$("#f-setor").addEventListener("change",()=>{popularTeses();render();});
$("#f-tese").addEventListener("change",render);$("#f-ano").addEventListener("change",render);

// tendências agrupadas por status + filtro por nicho
const EMERGJS=["NOVA","SURGINDO","CRESCENDO"];
const G={NOVA:{t:"Novas",s:"praticamente não existiam há 3 anos"},SURGINDO:{t:"Surgindo",s:"multiplicaram no último ano"},CRESCENDO:{t:"Crescendo",s:"em alta constante"}};
let _tendNicho="TODOS";
function renderNichos(){
  const ns=[...new Set(D.teses.filter(e=>EMERGJS.includes(e.status)).map(e=>e.setor))];
  $("#emg-nichos").innerHTML=[["TODOS","Todos os nichos"],...ns.map(n=>[n,setorLabel(n)])].map(([v,l])=>`<button class="nicho ${_tendNicho===v?'on':''}" data-n="${v}">${l}</button>`).join("");
}
let _jan="12";
function renderJan(){$("#jan-toggle").innerHTML=[["12","Último ano"],["6","Últimos 6 meses"]].map(([v,l])=>`<button class="nicho ${_jan===v?'on':''}" data-j="${v}">${l}</button>`).join("");}
function janVals(e){return _jan==="6"?{antes:e.antes6,agora:e.agora6,mult:e.mult6}:{antes:e.antes,agora:e.agora,mult:e.mult};}
function renderTend(){
  const src=D.teses.filter(e=>EMERGJS.includes(e.status)&&(_tendNicho==="TODOS"||e.setor===_tendNicho));
  const html=["NOVA","SURGINDO","CRESCENDO"].map(st=>{
    const items=src.map(e=>[e,D.teses.indexOf(e)]).filter(([e])=>e.status===st);if(!items.length)return"";
    return `<div class="grp"><div class="grp-h"><span class="tag ${st}">${st}</span><span>${G[st].t} — ${G[st].s}</span></div>
      <div class="emg">`+items.map(([e,i])=>{const w=janVals(e);return `<div class="emgcard" data-idx="${i}"><span class="t">${e.tese}<small>era ${w.antes} → agora ${w.agora} · toque para o passo a passo</small></span><span class="x">${w.mult!=null?w.mult+'×':'—'}</span></div>`;}).join("")+`</div></div>`;
  }).join("");
  $("#emg-groups").innerHTML=html||`<p class="pagesub">Nenhuma tese emergente neste nicho no momento.</p>`;
}
renderJan(); renderNichos(); renderTend();
$("#jan-toggle").addEventListener("click",ev=>{const b=ev.target.closest(".nicho");if(!b)return;_jan=b.dataset.j;renderJan();renderTend();});
$("#emg-nichos").addEventListener("click",ev=>{const b=ev.target.closest(".nicho");if(!b)return;_tendNicho=b.dataset.n;renderNichos();renderTend();});
$("#emg-groups").addEventListener("click",ev=>{const c=ev.target.closest(".emgcard");if(!c)return;openTese(+c.dataset.idx);});

// ---- suspensões (teses repetitivas suspensas: por quê + como afastar) ----
const SUS=D.suspensoes||[];
function openSusp(i){
  const s=SUS[i];
  const afastar=(s.como_afastar||[]).map(a=>`<li>${a}</li>`).join("");
  $("#sheet").innerHTML=`<button class="close" onclick="closeModal()">×</button>
    <h3>${s.tese}</h3><div class="sub"><span class="sb" style="font-size:9px;padding:2px 7px;border-radius:6px">SUSPENSA</span> &nbsp;${s.instrumento}${s.desde?` · desde ${s.desde}`:""} · ${setorLabel(s.setor)}</div>
    <div class="sec"><h4>Por que está suspensa</h4><p>${s.porque}</p></div>
    <div class="sec"><h4>Como afastar / prosseguir</h4><ul>${afastar}</ul></div>
    <p class="disc">${s.fonte||""} <b>A suspensão é temporária — confirme o status atual antes de peticionar.</b></p>`;
  $("#modal").classList.add("on");
}
if(SUS.length){
  $("#suspensoes-band").innerHTML=`<div class="susp-band"><div class="sh">⚠️ Teses repetitivas SUSPENSAS — atenção antes de ajuizar</div>`+
    SUS.map((s,i)=>`<div class="susp-card" onclick="openSusp(${i})"><span class="sb">${(s.instrumento||"").split("/")[0]}</span><span class="st"><b>${s.tese}</b><small>${s.instrumento}${s.desde?` · desde ${s.desde}`:""} — toque para o porquê e como afastar</small></span><span style="color:var(--amber);font-size:18px">›</span></div>`).join("")+`</div>`;
}

// ---- modal de guia da tese ----
function openTese(i){
  const e=D.teses[i],g=e.guia||{};
  const docs=(g.documentos||[]).map(d=>`<li>${d}</li>`).join("");
  const fund=(g.fundamentos||[]).map(f=>`<span class="fchip">${f}</span>`).join("");
  const pnums=(e.processos||[]).map(p=>`<span class="pnum">${p.n}</span>`).join("");
  $("#sheet").innerHTML=`<button class="close" onclick="closeModal()">×</button>
    <h3>${e.tese}</h3>
    <div class="sub"><span class="tag ${e.status}" style="font-size:9px;padding:2px 7px">${e.status}</span> &nbsp;${e.mult}× no último ano · ${setorLabel(e.setor)}</div>
    ${g.explicacao?`<div class="sec"><h4>O que é</h4><p>${g.explicacao}</p></div>`:""}
    ${docs?`<div class="sec"><h4>Documentos necessários</h4><ul>${docs}</ul></div>`:""}
    ${g.como_ajuizar?`<div class="sec"><h4>Como ajuizar</h4><p>${g.como_ajuizar}</p></div>`:""}
    ${fund?`<div class="sec"><h4>Fundamentos jurídicos</h4><div class="fchips">${fund}</div></div>`:""}
    ${e.receita?`<div class="sec receita"><h4>🏆 Passo a passo para o êxito</h4>
      <div class="exito-badge">Chance de êxito: <b>${e.receita.faixa_exito}</b></div>
      <ol class="passos">${(e.receita.passos||[]).map(s=>`<li>${s}</li>`).join("")}</ol>
      <div class="pd"><div class="pd-ok"><span>✅ Prova decisiva</span>${e.receita.prova_decisiva}</div>
      <div class="pd-no"><span>⚠️ O que faz PERDER</span>${e.receita.o_que_faz_perder}</div></div></div>`:""}
    ${g.valor_referencia?`<div class="sec"><h4>Valor de referência (dano moral)</h4><div class="valref">${g.valor_referencia}</div></div>`:""}
    <div class="sec"><h4>Processos analisados — ${e.agora} no último ano${(e.processos||[]).length?`, amostra de ${e.processos.length}`:""}</h4>
      ${pnums?`<div class="procbox"><div class="procgrid">${pnums}</div></div>`:`<p class="sec" style="color:var(--ink-faint);font-size:12px">${e.agora} decisões no período — números em atualização.</p>`}</div>
    <div class="actions">
      <button class="btn pri" onclick="relatorioTese(${i})">📄 Gerar relatório</button>
      <button class="btn ghost" onclick="closeModal();irPeticao(${i})">✍️ Gerar petição inicial</button>
      <button class="btn ghost" onclick="closeModal();goConsulta('${e.setor}')">Ver jurimetria</button>
    </div>`;
  $("#modal").classList.add("on");
}
function closeModal(){$("#modal").classList.remove("on");}
$("#modal").addEventListener("click",ev=>{if(ev.target.id==="modal")closeModal();});
document.addEventListener("keydown",ev=>{if(ev.key==="Escape")closeModal();});

// ---- relatórios (imprimir / salvar PDF) ----
function printReport(html){$("#report").innerHTML=html;window.print();}
// gráficos SVG p/ relatório (imprimíveis, sem libs)
function svgGauge(pct){pct=Math.round(pct||0);const w=520,bw=w-72;
  return `<svg viewBox="0 0 ${w} 42" width="100%" style="max-width:${w}px">
   <rect x="0" y="13" width="${bw}" height="17" rx="8.5" fill="#ece7f5"/>
   <rect x="0" y="13" width="${(bw*pct/100).toFixed(1)}" height="17" rx="8.5" fill="#0f9d6b"/>
   <text x="${bw+10}" y="27" font-size="15" font-weight="800" fill="#0f9d6b">${pct}%</text></svg>`;}
function svgBarsH(items){const w=620,rh=30,pad=150,bw=w-pad-118,top=6,h=top+items.length*rh+6;
  let b="";items.forEach((it,i)=>{const y=top+i*rh,pct=Math.max(0,Math.min(100,it.pct||0));
    b+=`<text x="0" y="${y+20}" font-size="12" fill="#2a2340">${(it.label||"").slice(0,22)}</text>`
      +`<rect x="${pad}" y="${y+7}" width="${bw}" height="16" rx="8" fill="#ece7f5"/>`
      +`<rect x="${pad}" y="${y+7}" width="${(bw*pct/100).toFixed(1)}" height="16" rx="8" fill="#7c1fd0"/>`
      +`<text x="${pad+bw+8}" y="${y+20}" font-size="12" font-weight="700" fill="#5b16a8">${it.right!=null?it.right:pct+"%"}</text>`;});
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-width:${w}px">${b}</svg>`;}
function relatorioTese(i){
  const e=D.teses[i],g=e.guia||{};
  const docs=(g.documentos||[]).map(d=>`<li>${d}</li>`).join("");
  const fund=(g.fundamentos||[]).join(" · ");
  const pnums=(e.processos||[]).map(p=>`${p.n}${p.d?" ("+p.d+")":""}`).join("  ·  ");
  printReport(`<div class="rhead"><h1>DOMINIA · Relatório de Tese Emergente</h1>
    <div class="muted">${e.tese} — ${setorLabel(e.setor)} · gerado em ${hojeBR()}</div></div>
    <p><b>Status:</b> ${e.status} — crescimento de ${e.mult}× (de ${e.antes} para ${e.agora} decisões/ano nas Turmas Recursais do TJBA).</p>
    <h2>Crescimento da tese</h2>
    <div class="rchart">${svgBarsH([{label:"Antes",pct:100*e.antes/Math.max(e.antes,e.agora,1),right:String(e.antes)},{label:"Último ano",pct:100*e.agora/Math.max(e.antes,e.agora,1),right:String(e.agora)}])}</div>
    ${e.receita?`<h2>Passo a passo para o êxito</h2><p><b>Chance de êxito:</b> ${e.receita.faixa_exito}</p><ol>${(e.receita.passos||[]).map(s=>`<li>${s}</li>`).join("")}</ol>
    <p><b>✅ Prova decisiva:</b> ${e.receita.prova_decisiva}</p><p><b>⚠️ O que faz perder:</b> ${e.receita.o_que_faz_perder}</p>`:""}
    ${g.explicacao?`<h2>O que é</h2><p>${g.explicacao}</p>`:""}
    ${docs?`<h2>Documentos necessários</h2><ul>${docs}</ul>`:""}
    ${g.como_ajuizar?`<h2>Como ajuizar</h2><p>${g.como_ajuizar}</p>`:""}
    ${fund?`<h2>Fundamentos jurídicos</h2><p>${fund}</p>`:""}
    ${g.valor_referencia?`<h2>Valor de referência</h2><p>${g.valor_referencia}</p>`:""}
    <h2>Processos analisados (${e.agora} no último ano)</h2>
    ${pnums?`<p class="pnums">${pnums}</p>`:`<p class="muted">Números em atualização.</p>`}
    <h2 style="border:none">Aviso</h2>
    <p class="muted">Dados das Turmas Recursais do TJBA. Precedente de 1º grau/Turma é persuasivo, não vinculante. Não é garantia de êxito nem substitui a análise do caso concreto.</p>`);
}
function relatorioConsulta(){
  const q=_consulta; if(!q)return;
  const setorNm=q.st==="TODOS"?"Todos os setores":setorLabel(q.st);
  const teseNm=q.te==="TODOS"?"Todas as teses":cap(q.te);
  const anoNm=q.an==="TODOS"?"Todos os anos":q.an;
  const reusRows=q.reus.map(([k,v])=>`<tr><td>${k}</td><td>${Math.round(100*v.f/v.n)}%</td><td>${v.n}</td></tr>`).join("");
  const pnums=q.rv.map(r=>r.proc).join("  ·  ");
  printReport(`<div class="rhead"><h1>DOMINIA · Relatório de Jurimetria</h1>
    <div class="muted">${setorNm} · ${teseNm} · ${anoNm} · gerado em ${hojeBR()}</div></div>
    ${q.n?`<p class="big">${q.pct}% de êxito ao consumidor</p><div class="rchart">${svgGauge(q.pct)}</div><p class="muted">n=${q.n} decisões validadas · IC95% [${q.lo}–${q.hi}] · base ampla ${nf(q.mcn)} processos${q.sinal!=null?` (sinal ${q.sinal}%)`:""}</p>`
      :`<p>Sem decisões validadas neste recorte. Base ampla: ${nf(q.mcn)} processos${q.sinal!=null?` (sinal ${q.sinal}%)`:""}.</p>`}
    ${q.n&&q.dm?`<h2>Dano moral</h2><p>Deferido em ${Math.round(100*q.dm/q.n)}% dos casos · mediana R$ ${nf(q.medVal)}.</p><div class="rchart">${svgBarsH([{label:"Defere dano moral",pct:Math.round(100*q.dm/q.n),right:Math.round(100*q.dm/q.n)+"%"}])}</div>`:""}
    ${q.reus&&q.reus.length?`<h2>Êxito por réu</h2><div class="rchart">${svgBarsH(q.reus.map(([k,v])=>({label:k,pct:Math.round(100*v.f/v.n),right:Math.round(100*v.f/v.n)+"% (n="+v.n+")"})))}</div>`:""}
    ${reusRows?`<table><tr><td><b>Réu</b></td><td><b>Êxito</b></td><td><b>n</b></td></tr>${reusRows}</table>`:""}
    ${pnums?`<h2>Processos validados (auditável)</h2><p class="pnums">${pnums}</p>`:""}
    <h2 style="border:none">Metodologia</h2>
    <p class="muted">Percentual validado por IA sobre decisões das Turmas Recursais do TJBA, com intervalo de confiança de Wilson (95%). Precedente é persuasivo, não vinculante. Não é garantia de êxito.</p>`);
}

// ---- petição inicial ----
let _peca="";
const teseOpts=D.teses.map((e,i)=>[e,i]).filter(([e])=>e.guia);
$("#p-tese").innerHTML = teseOpts.length? teseOpts.map(([e,i])=>`<option value="${i}">${e.tese}</option>`).join("") : '<option value="-1">—</option>';
$("#p-reulist").innerHTML=D.reus.map(r=>`<option value="${r.reu}">`).join("");
function irPeticao(i){
  $$(".tab").forEach(x=>x.classList.toggle("on",x.dataset.v==="peticao"));
  $$(".view").forEach(v=>v.classList.toggle("on",v.id==="v-peticao"));
  if(i!=null&&[...$("#p-tese").options].some(o=>o.value==String(i)))$("#p-tese").value=i;
  window.scrollTo({top:0,behavior:"smooth"});
}
function corpoPeticao(e,g,autor,reu,fatos,valor){
  const fund=(g.fundamentos||[]).join("; ");
  const procs=(e.processos||[]).slice(0,8).map(p=>p.n);
  const precTxt=procs.length?`Citam-se, exemplificativamente, os seguintes julgados das Turmas Recursais do TJBA: ${procs.join("; ")}.`
    :`No período recente foram identificadas ${e.agora} decisões sobre a matéria nas Turmas Recursais do TJBA.`;
  const valLinha=valor?`Dá-se à causa o valor de ${valor}.`:`Dá-se à causa o valor a ser apurado conforme os pedidos.`;
  return {
   ender:`EXCELENTÍSSIMO(A) SENHOR(A) DR(A). JUIZ(A) DE DIREITO DO JUIZADO ESPECIAL CÍVEL DA COMARCA DE [___] — BA`,
   intro:`${autor}, vem, respeitosamente, à presença de Vossa Excelência, com fundamento na Lei nº 9.099/95 e no Código de Defesa do Consumidor, propor a presente AÇÃO DECLARATÓRIA C/C INDENIZAÇÃO POR DANOS MORAIS E MATERIAIS, com pedido de tutela de urgência, em face de ${reu}, pelos fatos e fundamentos a seguir expostos.`,
   fatos,
   direito:`A relação é de consumo, aplicando-se o CDC e a responsabilidade objetiva do fornecedor (art. 14). ${g.explicacao||""} ${fund?("Incidem, ainda: "+fund+"."):""} Requer-se a inversão do ônus da prova (art. 6º, VIII, CDC), por verossímeis as alegações e hipossuficiente o consumidor.`,
   prec:`A matéria é reiteradamente enfrentada pelas Turmas Recursais do TJBA (tendência ${e.status}, crescimento de ${e.mult}× no último ano). ${precTxt} Trata-se de precedente persuasivo que reforça a procedência.`,
   tutela:`Presentes a probabilidade do direito e o perigo de dano, requer-se a concessão de TUTELA DE URGÊNCIA para ${g.como_ajuizar?("adoção das medidas cabíveis ("+g.como_ajuizar.split(".")[0]+")"):"cessação imediata da conduta lesiva"}.`,
   pedidos:[
    `a concessão da tutela de urgência acima;`,
    `a inversão do ônus da prova (art. 6º, VIII, CDC);`,
    `no mérito, a procedência para declarar/condenar conforme o direito exposto (${g.como_ajuizar?g.como_ajuizar.split(".")[0].toLowerCase():"reparação integral"});`,
    `a restituição dos valores indevidos, em dobro quando cabível (art. 42, § único, CDC);`,
    `a condenação em danos morais${g.valor_referencia?(" ("+g.valor_referencia+")"):""};`,
    `os benefícios da gratuidade da justiça e a dispensa de custas no JEC.`
   ],
   valLinha
  };
}
function gerarPeticao(){
  const idx=+$("#p-tese").value; if(!(idx>=0)){alert("Selecione uma tese.");return;}
  const e=D.teses[idx],g=e.guia||{};
  const autor=($("#p-autor").value||"[AUTOR — nome, nacionalidade, estado civil, profissão, CPF, endereço]").trim();
  const reu=($("#p-reu").value||"[RÉU — razão social, CNPJ, endereço]").trim();
  const fatos=($("#p-fatos").value||"[Resumo dos fatos]").trim();
  const valor=($("#p-valor").value||"").trim();
  const c=corpoPeticao(e,g,autor,reu,fatos,valor);
  const ped=c.pedidos.map(p=>`<p>${p}</p>`).join("");
  const html=`<h5 class="cab">${c.ender}</h5>
    <p style="margin-top:26px">${c.intro}</p>
    <h5>I – DOS FATOS</h5><p>${c.fatos}</p>
    <h5>II – DO DIREITO</h5><p>${c.direito}</p>
    <h5>III – DOS PRECEDENTES (TURMAS RECURSAIS DO TJBA)</h5><p>${c.prec}</p>
    <h5>IV – DA TUTELA DE URGÊNCIA</h5><p>${c.tutela}</p>
    <h5>V – DOS PEDIDOS</h5><p>Ante o exposto, requer:</p>${ped}
    <p style="margin-top:8px">Protesta por todos os meios de prova. ${c.valLinha}</p>
    <p style="margin-top:14px">Nestes termos, pede deferimento.</p>
    <p class="end">[Local], [data].</p>
    <p class="ass">_______________________________<br>[Advogado(a) — OAB/BA]</p>`;
  $("#peticao-out").innerHTML=`<div class="peca">${html}</div>
    <div class="actions"><button class="btn pri" onclick="imprimirPeticao()">🖨️ Imprimir / Salvar PDF</button>
    <button class="btn ghost" onclick="copiarPeticao()">📋 Copiar texto</button></div>
    <p class="disc" style="margin-top:16px">Minuta gerada por modelo a partir dos precedentes reais do TJBA. <b>Revise e adapte ao caso concreto antes de protocolar.</b> Precedente de Turma Recursal é persuasivo, não vinculante.</p>`;
  _peca=`<div class="rhead"><h1>DOMINIA · Minuta de Petição Inicial</h1><div class="muted">${e.tese} · gerado em ${hojeBR()}</div></div>`+html;
  $("#peticao-out").scrollIntoView({behavior:"smooth"});
}
function imprimirPeticao(){printReport(_peca);}
function copiarPeticao(){const t=$(".peca").innerText;navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>{},()=>{});}

// réus (B) — ranking dos acórdãos: êxito + dano moral + comarca + processos p/ validar
const RB=(D.reus_b&&D.reus_b.reus)||[];
function openReu(i){
  const r=RB[i];
  const coms=(r.por_comarca||[]).map(c=>`<div class="reurow"><span class="rn">${c.comarca}</span><div class="tk"><div style="width:${c.pct}%"></div></div><span class="rv">${c.pct}% <span style="color:var(--ink-faint);font-weight:500;font-size:11px">(${c.n})</span></span></div>`).join("");
  $("#sheet").innerHTML=`<button class="close" onclick="closeModal()">×</button>
    <h3>${r.reu}</h3><div class="sub">êxito do consumidor ${r.pct_fav_sinal}% · n=${nf(r.n)} · dano moral ${r.dano_moral_mediana?"mediana R$ "+nf(r.dano_moral_mediana):"—"}</div>
    ${coms?`<div class="sec"><h4>Êxito por comarca</h4>${coms}</div>`:""}
    <div class="sec"><h4>Processos favoráveis — validar</h4><div class="procbox"><div class="procgrid">${procChips(r.ex_favoravel)}</div></div></div>
    ${r.ex_desfavoravel&&r.ex_desfavoravel.length?`<div class="sec"><h4>Processos desfavoráveis — validar</h4><div class="procbox"><div class="procgrid">${procChips(r.ex_desfavoravel)}</div></div></div>`:""}
    <p class="disc">% de êxito = sinal dos acórdãos das Turmas (não validado por IA) — valide pelos números. Dano moral = condenação citada no texto.</p>`;
  $("#modal").classList.add("on");
}
$("#reu").innerHTML=(RB.length?RB.map((r,i)=>`<div class="reurow" style="cursor:pointer" onclick="openReu(${i})"><span class="rn">${r.reu}</span><div class="tk"><div style="width:${r.pct_fav_sinal}%"></div></div><span class="rv">${r.pct_fav_sinal}%${r.dano_moral_mediana?` <span style="color:var(--ink-faint);font-weight:500;font-size:10.5px">R$${nf(r.dano_moral_mediana)}</span>`:""}</span></div>`)
  :D.reus.map(r=>`<div class="reurow"><span class="rn">${r.reu}</span><div class="tk"><div style="width:${r.pct}%"></div></div><span class="rv">${r.pct}%</span></div>`)).join("");
// setores
$("#setgrid").innerHTML=D.setores.map(s=>`<div class="setcard" data-setor="${s.code}"><div class="ic2">${s.icon}</div><div class="nm">${s.label}<small>${nf(s.massa_n)} processos</small></div><div class="go">›</div></div>`).join("");
$("#setgrid").addEventListener("click",e=>{const c=e.target.closest(".setcard");if(c)goConsulta(c.dataset.setor);});

// ---- DECISÕES (cada decisão, tudo o que importa) ----
const RD=D.rdje||[];
let dShown=40;
const RESLBL={PROCEDENTE:"Procedente",PARCIAL:"Parcial",IMPROCEDENTE:"Improcedente",INDEF:"—"};
if(RD.length){
  const dSet=[...new Set(RD.map(r=>r.s))].sort();
  const dCom=[...new Set(RD.map(r=>r.c).filter(Boolean))].sort();
  const dReu=[...new Set(RD.map(r=>r.r).filter(Boolean))].sort();
  $("#d-setor").innerHTML='<option value="TODOS">Todos os setores</option>'+dSet.map(s=>`<option value="${s}">${setorLabel(s)}</option>`).join("");
  $("#d-comarca").innerHTML='<option value="TODOS">Todas as comarcas</option>'+dCom.map(c=>`<option value="${c}">${c}</option>`).join("");
  $("#d-reu").innerHTML='<option value="TODOS">Todos os réus</option>'+dReu.map(c=>`<option value="${c}">${c}</option>`).join("");
  $("#d-res").innerHTML='<option value="TODOS">Todos os resultados</option><option value="win">Procedente / parcial</option><option value="IMPROCEDENTE">Improcedente</option>';
  $("#d-foro").innerHTML='<option value="TODOS">Juizado + Comum</option><option value="JUIZADO">Só Juizado</option><option value="COMUM">Só Justiça Comum</option>';
  ["#d-foro","#d-setor","#d-comarca","#d-reu","#d-res"].forEach(s=>$(s).addEventListener("change",()=>renderDec(true)));
  let _dbt; $("#d-busca").addEventListener("input",()=>{clearTimeout(_dbt);_dbt=setTimeout(()=>renderDec(true),180);});
  renderDec(true);
}
function bnormDec(s){return (s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");}
function filtraDec(){
  const f=$("#d-foro").value,s=$("#d-setor").value,c=$("#d-comarca").value,r=$("#d-reu").value,res=$("#d-res").value;
  const q=bnormDec($("#d-busca").value.trim()); const termos=q?q.split(/\s+/):[];
  return RD.filter(x=>{
    if(!((f==="TODOS"||x.fg===f)&&(s==="TODOS"||x.s===s)&&(c==="TODOS"||x.c===c)&&(r==="TODOS"||x.r===r)&&
      (res==="TODOS"||(res==="win"?(x.res==="PROCEDENTE"||x.res==="PARCIAL"):x.res===res)))) return false;
    if(!termos.length) return true;
    const hay=bnormDec([x.em,x.r,x.c,x.j,x.tese,x.proc,setorLabel(x.s)].join(" "));
    return termos.every(t=>hay.includes(t));
  });
}
function abrevJuiz(n){if(!n)return n;const p=n.trim().split(/\s+/);if(p.length<=2)return n;return p[0]+" "+p.slice(1,-1).map(w=>w[0]+".").join("")+" "+p[p.length-1];}
function verMaisDec(){dShown+=40;renderDec(false);}
function renderDec(reset){
  if(reset)dShown=40;
  const f=filtraDec();
  $("#d-count").textContent=`${nf(f.length)} decisões · ${nf(f.filter(x=>x.res==="PROCEDENTE"||x.res==="PARCIAL").length)} com êxito`;
  $("#d-list").innerHTML=f.slice(0,dShown).map(x=>`<div class="dcard">
    <div class="dtop"><span class="res ${x.res}">${RESLBL[x.res]||x.res}</span>${x.v?`<span class="val">R$ ${nf(x.v)}</span>`:""}</div>
    <div class="dmeta"><span><span class="k">Foro:</span> <b>${x.fg==="JUIZADO"?"Juizado":"J. Comum"}</b></span>${x.r?`<span><span class="k">Réu:</span> <b>${x.r}</b></span>`:""}${x.c?`<span><span class="k">Comarca:</span> <b>${x.c}</b></span>`:""}${x.j?`<span><span class="k">Juiz:</span> <b>${abrevJuiz(x.j)}</b></span>`:""}<span><span class="k">Tese:</span> <b>${x.tese||setorLabel(x.s)}</b></span>${x.d?`<span class="k">${x.d}</span>`:""}</div>
    ${x.em?`<div class="dem">${x.em}…</div>`:""}
    <div style="margin-top:9px;display:flex;justify-content:space-between;gap:8px;align-items:center"><span class="proc">${x.proc}</span>${x.link?`<a class="int" href="${x.link}" target="_blank" rel="noopener">Ver íntegra ↗</a>`:""}</div></div>`).join("")
    +(f.length>dShown?`<button class="dmore" onclick="verMaisDec()">Ver mais ${nf(f.length-dShown)}</button>`:"");
}

// ---- COMARCAS: Juizado × Justiça Comum + comparador ----
const dje=D.dje||{};
const PF=dje.por_foro||{JUIZADO:{},COMUM:{}};
const FLBL={CIVEL:"Juizado Cível",FAZENDA:"Fazenda Pública",COMUM:"Justiça Comum"};
let _foro="CIVEL";
function censoSeg(){return ((D.censo&&D.censo.segmentos)||{})[_foro]||{};}
const crow5=c=>`<div class="crow c5"><span class="cc">${c.comarca}</span><span>${nf(c.n)}</span><span class="cp">${c.pct!=null?c.pct+"%":"—"}</span><span class="cd">${c.dm?"R$ "+nf(c.dm):"—"}</span><span class="cf">${c.pct_dm!=null?c.pct_dm+"%":"—"}</span></div>`;
const chead=`<div class="crow c5 h"><span>Comarca</span><span>Casos</span><span>Êxito</span><span>D.moral</span><span>Defere</span></div>`;
function renderForoToggle(){$("#foro-toggle").innerHTML=["CIVEL","FAZENDA","COMUM"].map(f=>`<button class="nicho ${_foro===f?'on':''}" data-f="${f}">${FLBL[f]}</button>`).join("");}
function procChips(ps){return (ps||[]).map(p=>`<span class="pnum">${p}</span>`).join("")||'<span style="color:var(--ink-faint);font-size:12px">—</span>';}
function openProcs(titulo,sub,fav,unf){
  $("#sheet").innerHTML=`<button class="close" onclick="closeModal()">×</button>
    <h3>${titulo}</h3><div class="sub">${sub}</div>
    <div class="sec"><h4>Processos favoráveis — validar na fonte</h4><div class="procbox"><div class="procgrid">${procChips(fav)}</div></div></div>
    ${unf&&unf.length?`<div class="sec"><h4>Processos improcedentes — validar</h4><div class="procbox"><div class="procgrid">${procChips(unf)}</div></div></div>`:""}
    <p class="disc">Amostra real do censo. Consulte cada número na busca do TJBA para conferir a decisão. <b>É o dado, auditável.</b></p>`;
  $("#modal").classList.add("on");
}
function openProcsTese(i){const t=censoSeg().por_tese[i];openProcs(t.nome,`${t.pct_fav}% favorável · n=${nf(t.n)} · ${FLBL[_foro]}`,t.ex_favoravel,t.ex_improcedente);}
function openProcsComarca(i){const c=censoSeg().comarcas[i];openProcs(c.nome,`${c.pct_fav}% favorável · n=${nf(c.n)} · ${FLBL[_foro]}`,c.ex_favoravel,c.ex_improcedente);}
function renderComarcas(){
  const pf=PF[_foro]||{};
  const juiz=_foro!=="COMUM";
  if(juiz){
    const cs=censoSeg();
    const nota=_foro==="FAZENDA"
      ? `<b>Juizado da Fazenda Pública</b> — ações contra o Estado/Município (Planserv, servidores, saúde pública etc.). <b>Censo completo</b> via Datajud/CNJ (${nf(cs.total||0)} decisões). Clique numa tese/comarca para ver os processos e validar.`
      : `<b>Juizado Especial Cível</b> — consumo e cível privado (exclui órgãos da Fazenda Pública). <b>Censo completo</b> via Datajud/CNJ (${nf(cs.total||0)} decisões, ${(cs.comarcas||[]).length} comarcas). Clique numa tese/comarca para ver os processos. Valor de dano moral só na Justiça Comum.`;
    $("#foro-nota").innerHTML=nota;
    $("#dje-kpis").innerHTML=[[nf(cs.total||0),"decisões · censo"],[nf((cs.por_tese||[]).length),"teses"],[nf((cs.comarcas||[]).length),"comarcas"],[(cs.pct_fav_geral||0)+"%","favorável geral"]].map(([v,l])=>`<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
    $("#lbl-dm").innerHTML=`Procedência por tese <span style="text-transform:none;font-weight:400;color:var(--ink-faint)">— censo · clique p/ ver os processos</span>`;
    $("#dm-area").innerHTML=(cs.por_tese||[]).slice(0,15).map((t,i)=>`<div class="dmrow" style="cursor:pointer" onclick="openProcsTese(${i})"><span class="dn">${t.nome}</span><div class="dtk"><div class="acc" style="width:${t.pct_fav}%"></div></div><span class="dvv">${t.pct_fav}% <span style="color:var(--ink-faint);font-weight:500;font-size:11px">n=${nf(t.n)}</span></span></div>`).join("")||'<p class="pagesub">Sem base.</p>';
    $("#comp-box").style.display="none";
    $("#comarca-tbl").innerHTML=`<div class="crow c5 h"><span>Comarca</span><span>Casos</span><span>Favor.</span><span>proc</span><span>improc</span></div>`+(cs.comarcas||[]).slice(0,30).map((c,i)=>`<div class="crow c5" style="cursor:pointer" onclick="openProcsComarca(${i})"><span class="cc">${c.nome}</span><span>${nf(c.n)}</span><span class="cp">${c.pct_fav}%</span><span>${nf(c.procedente+c.parcial)}</span><span class="cf">${nf(c.improcedente)}</span></div>`).join("");
    return;
  }
  $("#foro-nota").innerHTML=`<b>Justiça Comum</b> (Varas de Consumo) — fonte <b>DJEN</b>, com inteiro teor. Dano moral = mediana quando deferido.`;
  $("#dje-kpis").innerHTML=[[nf(pf.total||0),"sentenças · Justiça Comum"],[nf(dje.cidades||0),"cidades"],[nf(dje.n_juizes||0),"juízes"],[nf((pf.comarcas||[]).length),"comarcas c/ base"]].map(([v,l])=>`<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  $("#lbl-dm").innerHTML=`Dano moral por área <span style="text-transform:none;font-weight:400;color:var(--ink-faint)">— mediana quando deferido · % dos casos que recebem</span>`;
  const dm=pf.dano_moral_por_area||[];const dmMax=Math.max(1,...dm.map(x=>x.mediana||0));
  $("#dm-area").innerHTML=dm.map(x=>`<div class="dmrow"><span class="dn">${setorLabel(x.setor)}</span><div class="dtk"><div style="width:${Math.round(100*(x.mediana||0)/dmMax)}%"></div></div><span class="dvv">R$ ${nf(x.mediana)} <span style="color:var(--ink-faint);font-weight:500;font-size:11px">· ${x.pct_dm}%</span></span></div>`).join("")||'<p class="pagesub">Amostra insuficiente.</p>';
  $("#comp-box").style.display="";
  const comp=pf.comparador||{};
  const sets=Object.keys(comp).sort((a,b)=>setorLabel(a).localeCompare(setorLabel(b)));
  $("#comp-setor").innerHTML=sets.length?sets.map(s=>`<option value="${s}">${setorLabel(s)}</option>`).join(""):'<option value="">— sem base —</option>';
  renderComp();
  $("#comarca-tbl").innerHTML=chead+(pf.comarcas||[]).slice(0,25).map(crow5).join("")||'<div class="crow">Sem comarcas com base suficiente.</div>';
}
function renderComp(){
  const pf=PF[_foro]||{},comp=pf.comparador||{},s=$("#comp-setor").value;
  const lst=(comp[s]||[]).slice(0,20);
  $("#comp-tbl").innerHTML=lst.length?chead+lst.map(crow5).join(""):'<div class="crow">Sem comarcas com base suficiente neste recorte.</div>';
}
$("#juizes").innerHTML=(dje.juizes||[]).slice(0,30).map(j=>`<div class="jchip"><span class="jn">${abrevJuiz(j.juiz)}</span><span class="jq">${j.n} sent.</span></div>`).join("")||'<p class="pagesub">Sem dado.</p>';
$("#foro-toggle").addEventListener("click",ev=>{const b=ev.target.closest(".nicho");if(!b)return;_foro=b.dataset.f;renderForoToggle();renderComarcas();});
$("#comp-setor").addEventListener("change",renderComp);
renderForoToggle(); renderComarcas();

// ---- VARAS & RELATORES ----
const VG=(D.vara&&D.vara.varas_1grau)||[], TG=(D.vara&&D.vara.turmas_2grau)||[];
const dmt=v=>v?("R$ "+nf(v)):"—", mst=v=>(v!=null?v+" m":"—");
function fillVaraCom(){
  const coms=[...new Set(VG.map(v=>v.comarca).filter(Boolean))].sort((a,b)=>a.localeCompare(b));
  const sel=$("#vara-com"); if(!sel) return;
  sel.innerHTML=`<option value="">Todas as comarcas (${coms.length})</option>`+coms.map(c=>`<option value="${c}">${c}${c==="Salvador"?" ("+VG.filter(v=>v.comarca==="Salvador").length+" varas)":""}</option>`).join("");
  sel.value="Salvador";
}
function renderVaras(){
  if(!VG.length){$("#vara-tbl").innerHTML='<div class="crow">Sem base de varas.</div>';}
  else{
    const com=$("#vara-com").value, ord=$("#vara-ord").value;
    let lst=VG.filter(v=>!com||v.comarca===com);
    const key={dur:v=>v.meses_mediana==null?9e9:v.meses_mediana, proc:v=>-(v.pct_proc||0), n:v=>-(v.n_merito||0), dm:v=>-(v.dano_moral_mediana||0)}[ord];
    lst=lst.slice().sort((a,b)=>key(a)-key(b)).slice(0,60);
    const h=`<div class="crow c6 h"><span>Vara</span><span>Comarca</span><span>proc.</span><span>duração</span><span>dano moral</span><span>casos</span></div>`;
    $("#vara-tbl").innerHTML=h+lst.map(v=>`<div class="crow c6" style="cursor:pointer" onclick="openVara('${v.comarca}||${v.vara.replace(/'/g,'')}')"><span class="cc" title="${v.vara}">${v.vara}</span><span>${v.comarca||"—"}</span><span class="cp">${v.pct_proc}%</span><span class="cd">${mst(v.meses_mediana)}</span><span>${dmt(v.dano_moral_mediana)}</span><span>${nf(v.n_merito)}</span></div>`).join("");
  }
  if(!TG.length){$("#rel-tbl").innerHTML='<div class="crow">Sem base de relatores.</div>';return;}
  const rh=`<div class="crow c6 h"><span>Relator</span><span>Turma</span><span>favor.</span><span>monocr.</span><span>duração</span><span>n</span></div>`;
  $("#rel-tbl").innerHTML=rh+TG.slice(0,40).map(r=>`<div class="crow c6"><span class="cc" title="${r.relator}">${r.relator}</span><span>${(r.turma||"").replace(/ Recursal.*/i," TR")}</span><span class="cp">${r.pct_fav}%</span><span title="${r.monocratica} de ${r.n} decisões sozinho">${r.pct_monocratica}%</span><span class="cd">${mst(r.meses_mediana)}</span><span>${nf(r.n)}</span></div>`).join("");
}
function openVara(k){const[com,vara]=k.split("||");const v=VG.find(x=>x.comarca===com&&x.vara.replace(/'/g,'')===vara);if(!v)return;
  openProcs(v.vara,`${v.comarca||""} · proc ${v.pct_proc}% · ${mst(v.meses_mediana)} até a sentença · dano moral ${dmt(v.dano_moral_mediana)} · n=${nf(v.n_merito)}${v.juizes&&v.juizes.length?" · juízes: "+v.juizes.map(abrevJuiz).join(", "):""}`,v.ex,[]);}
const _vc=$("#vara-com"),_vo=$("#vara-ord");
if(_vc){fillVaraCom();_vc.addEventListener("change",renderVaras);}
if(_vo)_vo.addEventListener("change",renderVaras);
renderVaras();

// ---- juízes (1º grau) ----
const JZ=((D.juizes&&D.juizes.juizes)||[]).filter(j=>j.comarca);
function renderJuizes(){
  const el=$("#juiz-tbl"); if(!el)return;
  if(!JZ.length){el.innerHTML='<div class="crow">Sem base de juízes.</div>';return;}
  const ord=$("#juiz-ord").value;
  const key={n:j=>-(j.n||0),proc:j=>-(j.pct_proc||0),dm:j=>-(j.dano_moral_mediana||0)}[ord];
  const lst=JZ.slice().sort((a,b)=>key(a)-key(b)).slice(0,40);
  const h=`<div class="crow c6 h"><span>Juiz</span><span>Comarca</span><span>proc.</span><span>improc.</span><span>dano moral</span><span>n</span></div>`;
  el.innerHTML=h+lst.map(j=>`<div class="crow c6"><span class="cc" title="${abrevJuiz(j.juiz)}">${abrevJuiz(j.juiz)}</span><span>${j.comarca}</span><span class="cp">${j.pct_proc}%</span><span class="cf">${j.pct_improc}%</span><span>${j.dano_moral_mediana?"R$ "+nf(j.dano_moral_mediana):"—"}</span><span>${nf(j.n)}</span></div>`).join("");
}
const _jo=$("#juiz-ord"); if(_jo)_jo.addEventListener("change",renderJuizes);
renderJuizes();

// ---- PLANOS ----
const PLANOS=[
 {nome:"Essencial",preco:"47",pop:false,feats:["Base de 62 mil decisões (Turmas + 1º grau)","Buscas ilimitadas por setor, tese e ano","Jurimetria com % e intervalo de confiança de Wilson","Ranking de réus e comarcas","Relatórios em PDF: 20/mês"]},
 {nome:"Profissional",preco:"97",pop:true,feats:["Tudo do Essencial","Decisões estruturadas: valor, juiz, comarca, íntegra","Guias práticos das teses emergentes","Gerador de petição inicial com precedentes","Relatórios em PDF ilimitados","Comparativo entre comarcas"]},
 {nome:"Escritório",preco:"197",pop:false,feats:["Tudo do Profissional","Multiusuário (equipe)","Dano moral por réu/comarca (ferramenta de acordo)","Juízes mapeados e histórico","Custas e dados para citação","Suporte prioritário"]},
];
$("#planos").innerHTML=PLANOS.map(p=>`<div class="plano ${p.pop?"pop":""}">${p.pop?'<span class="badge">Mais popular</span>':""}<div class="pnome">${p.nome}</div><div class="preco">R$ ${p.preco}<small>/mês</small></div><ul class="pfeat">${p.feats.map(f=>`<li>${f}</li>`).join("")}</ul><button class="pcta">Assinar ${p.nome}</button></div>`).join("");

// ---- CURSOS (área educacional data-driven) ----
const CURSOS=[
 {ico:"🎓",t:"Fundamentos no Juizado",s:"trilha base",mod:8,setor:null,d:"Rito da Lei 9.099/95, competência, CDC na prática, inversão do ônus, provas e recursos. A porta de entrada pra atuar em volume."},
 {ico:"✈️",t:"Direito Aéreo",s:"bagagem · atraso · cancelamento",mod:6,setor:"AEREO",d:"As teses que vencem e as que perdem: extravio (êxito alto), atraso >4h × <4h, overbooking. Com os precedentes e faixas de dano moral reais."},
 {ico:"🔒",t:"Fraudes e Golpes Bancários",s:"PIX · engenharia social",mod:7,setor:"FRAUDE",d:"Golpe do PIX, falso funcionário, biometria. Como provar a falha do banco e a Súmula 479 STJ. A área que mais cresce nos Juizados."},
 {ico:"🏦",t:"Bancário e Consignado",s:"negativação · descontos",mod:7,setor:"FINANCEIRO",d:"Negativação indevida, consignado não contratado, descontos associativos, repetição em dobro. O maior volume da Justiça de consumo."},
 {ico:"🏥",t:"Planos de Saúde",s:"rol · negativas · reajuste",mod:6,setor:"SAUDE",d:"Rol exemplificativo (Lei 14.454), negativa de cobertura, cirurgia reparadora, reajuste abusivo. Onde o dano moral é o mais alto (mediana R$10k)."},
 {ico:"⚖️",t:"Prática: Peça e Acordo com Dados",s:"aplicado",mod:5,setor:null,pet:true,d:"Montar a inicial a partir dos precedentes, calcular a faixa de dano moral por réu/comarca e negociar acordo com número na mão — usando a própria plataforma."},
];
$("#cursos").innerHTML=CURSOS.map((c,i)=>`<div class="curso" data-i="${i}">
  <div class="ctop"><div class="cico">${c.ico}</div><div class="ct">${c.t}<small>${c.s}</small></div></div>
  <div class="cdesc">${c.d}</div>
  <div class="cfoot"><span class="cmod">${c.mod} módulos</span><span class="cjm">jurimetria embutida</span></div></div>`).join("");
$("#cursos").addEventListener("click",ev=>{const c=ev.target.closest(".curso");if(!c)return;const k=CURSOS[+c.dataset.i];if(k.pet)irPeticao();else if(k.setor)goConsulta(k.setor);});

// ---- BUSCA IA (ancorada em precedentes reais, anti-alucinação) ----
const BI=D.busca||[];
const BSIN={voo:["aereo","aeronave","aerea"],atraso:["atrasado","demora","cancelamento"],bagagem:["mala","extravio"],negativacao:["inscricao","spc","serasa","inadimplente"],consignado:["emprestimo","rmc","margem"],plano:["saude","operadora","ans","cobertura"],golpe:["fraude","estelionato","pix"],energia:["coelba","fatura","medidor"],agua:["embasa","esgoto"],dano:["moral","indenizacao"],reajuste:["abusivo","faixa","etaria"],cirurgia:["reparadora","bariatrica","reparador"]};
const BSTOP=new Set("de da do das dos a o e em para por com que se um uma no na meu minha tive foi nao com".split(" "));
function bnorm(s){return (s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");}
function btermos(q){
  const base=(bnorm(q).match(/[a-z]{3,}/g)||[]).filter(t=>!BSTOP.has(t));
  const set=new Set(base);
  base.forEach(t=>{for(const k in BSIN){if(k.includes(t)||t.includes(k)){set.add(k);BSIN[k].forEach(s=>set.add(s));}}});
  return [...set];
}
function buscarIA(q){
  const ts=btermos(q); if(!ts.length)return [];
  const sc=BI.map(it=>{const hay=(it.k||"")+" "+bnorm(it.e||"");let s=0,dist=0;ts.forEach(t=>{const c=hay.split(t).length-1;if(c){s+=c;dist++;}});return{it,score:s+dist*4};}).filter(x=>x.score>2);
  sc.sort((a,b)=>b.score-a.score);
  return sc.slice(0,8).map(x=>x.it);
}
function renderBusca(q){
  const res=buscarIA(q);
  $("#b-count").textContent=res.length?`${res.length} precedentes reais (de ${nf(BI.length)} indexados · 1º grau + Turmas) — valide pelo nº`:(q?"Nenhum precedente na base para esse caso — reformule com outros termos.":"");
  $("#b-list").innerHTML=res.map(it=>`<div class="bcard">
    <div class="bt"><span class="grau">${it.g==="TR"?"Turma Recursal":"1º grau"}</span>${it.res&&it.res!=="—"?`<span class="res ${it.res}">${it.res}</span>`:""}</div>
    <div class="bem">${it.e||"—"}…</div>
    <div class="bfoot"><span class="bproc">${it.p}</span><span>${it.r?`<span class="breu">${it.r}</span> · `:""}${it.o}</span></div></div>`).join("");
}
const BSUG=["atraso de voo com perda de conexão","negativação indevida por dívida paga","plano de saúde negou cirurgia","golpe do pix com falha do banco","reajuste abusivo de plano de saúde"];
function sugBusca(s){$("#b-q").value=s;renderBusca(s);}
$("#b-sugestoes").innerHTML=BSUG.map(s=>`<button class="bchip" onclick="sugBusca('${s}')">${s}</button>`).join("");
$("#b-go").addEventListener("click",()=>renderBusca($("#b-q").value));
$("#b-q").addEventListener("keydown",e=>{if(e.key==="Enter")renderBusca($("#b-q").value);});

popularTeses();render();
</script>
"""
_cap=int(os.environ.get("RDJE_CAP","15000"))     # teto GLOBAL de decisões embutidas
_percom=int(os.environ.get("RDJE_PERCOM","160"))  # teto POR COMARCA
def _comkey(r):
    c=(r.get("c") or "").split(">")[0].strip().upper()
    return {"CAPITAL":"Salvador"}.get(c,c) or "?"
def _balancear(regs, teto_global, teto_com):
    from collections import defaultdict as _dd, OrderedDict
    porc=OrderedDict()
    for r in regs: porc.setdefault(_comkey(r),[]).append(r)  # ordem preserva recência
    # round-robin: 1 de cada comarca por rodada -> toda comarca aparece antes de estourar o teto
    sel=[]; rodada=0
    while (not teto_global or len(sel)<teto_global) and rodada<teto_com:
        avancou=False
        for lst in porc.values():
            if rodada<len(lst):
                sel.append(lst[rodada]); avancou=True
                if teto_global and len(sel)>=teto_global: break
        if not avancou: break
        rodada+=1
    return sel
DADOS["rdje"]=_balancear(RDJE, _cap, _percom) if _cap else RDJE
_bcap=int(os.environ.get("BUSCA_CAP","0"))
if _bcap: DADOS["busca"]=DADOS["busca"][:_bcap]
out=HTML.replace("__DADOS__", json.dumps(DADOS, ensure_ascii=False))
_dest=os.environ.get("OUT_HTML")
if _dest:
    open(_dest,"w",encoding="utf-8").write(out); print("teste ->",_dest); raise SystemExit
open("juzia_dashboard.html","w",encoding="utf-8").write(out)
os.makedirs("docs",exist_ok=True); open("docs/app.html","w",encoding="utf-8").write(out)
print(f"DOMINIA (abas): {DADOS['massa_total']} base · {DADOS['validados']} validados · {len(setores)} setores · {len(anos)} anos")
