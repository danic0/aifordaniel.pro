import json, re, base64, io, asyncio, os, html as H, urllib.parse as UP
HERE=os.path.dirname(os.path.abspath(__file__));os.chdir(HERE)
from bs4 import BeautifulSoup
import qrcode, qrcode.image.svg
from playwright.async_api import async_playwright

SRC=os.path.join(HERE,'..','index.html');OUT=os.path.join(HERE,'..','sicily-booklet.pdf')
s=BeautifulSoup(open(SRC,encoding='utf-8'),'html.parser')
def txt(el):
    if el is None: return ''
    el=BeautifulSoup(str(el),'html.parser')
    for a in el.select('a.map'): a.decompose()
    for br in el.select('br'): br.replace_with(' ')
    return re.sub(r'\s+',' ',el.get_text()).strip()
E=H.escape
COL=['#5d6e7c','#2f7fb5','#17806f','#6f8a1f','#a8741a','#86528f']
DATE=['25','26','27','28','29','30']

def gmaps(q): return 'https://www.google.com/maps/search/?api=1&query='+UP.quote_plus(q)
# names -> google maps url, taken from the restaurant and bar cards on the page
CARD={}
for c in s.select('a.gc'):
    url=c['href']; h3=c.select_one('h3')
    if c.get('id'): CARD['#'+c['id']]=url
    nm=re.split(r'[,،]|[\u0590-\u05FF]',h3.get_text().strip())[0].strip()
    if len(nm)>=4: CARD[nm]=url
for c in s.select('article.nc'):
    m=c.select_one('a.map')
    if not m: continue
    url=m['href']; h3=c.select_one('h3')
    for sp in h3.select('.rk'): sp.decompose()
    nm=re.split(r'[,،]|[\u0590-\u05FF]',h3.get_text().strip())[0].strip()
    CARD['#'+c['id']]=url
    if len(nm)>=4: CARD[nm]=url
NAMES={}
def short_names(li):
    out=[]
    for b in li.select('b'):
        for part in re.split(r'\s+או\s+',b.get_text().strip()):
            part=re.sub(r'\s+',' ',part).strip(' ,.')
            if re.search(r'[A-Za-z]',part): part=re.split(r'[\u0590-\u05FF]',part)[0].strip(' ,.')
            if len(part)>=4: out.append(part)
    return out
def day_names(a,city):
    d=dict((k,v) for k,v in CARD.items() if not k.startswith('#'))
    for li in a.select('.meals li, .tips.night li'):
        mp=li.select_one('a.map'); ref=mp['href'] if mp and mp.get('href','').startswith('#') else None
        for k,part in enumerate(short_names(li)):
            hit=[v for kk,v in CARD.items() if not kk.startswith('#') and part.lower() in kk.lower()]
            d[part]=CARD.get(ref) if (k==0 and ref in CARD) else (hit[0] if len(set(hit))==1 else gmaps(part+' '+city))
    for b in a.select('.rain b'):
        t=re.sub(r'\s+',' ',b.get_text()).strip()
        if len(t)>=4 and not t.startswith('אם'): d.setdefault(t,gmaps(t+' '+city))
    return d
LINKER=[None]
def L(raw):
    raw=str(raw); d=LINKER[0]
    if not d: return E(raw)
    pat=re.compile('|'.join(re.escape(k) for k in sorted(d,key=len,reverse=True)))
    out='';pos=0
    for m in pat.finditer(raw):
        if m.start()<pos: continue
        out+=E(raw[pos:m.start()])+f'<a class="pl" href="{E(d[m.group(0)])}">{E(m.group(0))}</a>';pos=m.end()
    return out+E(raw[pos:])

def sentences(t,n):
    p=[x.strip() for x in re.split(r'(?<=\.)\s+',t) if x.strip()]
    return ' '.join(p[:n])

def qr(url):
    img=qrcode.make(url,image_factory=qrcode.image.svg.SvgPathImage,box_size=10,border=1)
    b=io.BytesIO();img.save(b);return 'data:image/svg+xml;base64,'+base64.b64encode(b.getvalue()).decode()

def font(path,fam,w,rng):
    d=base64.b64encode(open('node_modules/@fontsource/'+path,'rb').read()).decode()
    return f"@font-face{{font-family:{fam};font-weight:{w};src:url(data:font/woff2;base64,{d}) format('woff2');unicode-range:{rng}}}"
HE='U+0590-05FF,U+200C-2010,U+20AA,U+25CC,U+FB1D-FB4F'
LA='U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'
FONTS=''.join([font('heebo/files/heebo-hebrew-400-normal.woff2','Heebo',400,HE),font('heebo/files/heebo-hebrew-700-normal.woff2','Heebo',700,HE),
 font('heebo/files/heebo-latin-400-normal.woff2','Heebo',400,LA),font('heebo/files/heebo-latin-700-normal.woff2','Heebo',700,LA),
 font('rubik/files/rubik-hebrew-700-normal.woff2','Rubik',700,HE),font('rubik/files/rubik-hebrew-900-normal.woff2','Rubik',900,HE),
 font('rubik/files/rubik-latin-700-normal.woff2','Rubik',700,LA),font('rubik/files/rubik-latin-900-normal.woff2','Rubik',900,LA)])

def ul(items,cls=''):
    return f'<ul class="{cls}">'+''.join(f'<li>{L(x)}</li>' for x in items if x)+'</ul>'

pages=[]
# ---------- cover ----------
ov=''
for i in range(6):
    a=s.select_one(f'#d{i}')
    ov+=f'<div class="ovr" style="--c:{COL[i]}"><b>{DATE[i]}.1</b><span>{E(txt(a.select_one(".dmeta .w")).split(",")[0])}</span><em>{E(txt(a.select_one(".dh h2")))}</em></div>'
pages.append(f'''<section class="pg cover"><div class="cin">
<small>חוברת טיול · שמורה לשימוש בלי אינטרנט</small>
<h1>סירקוזה<br>וסיציליה</h1>
<p class="cl">25-30 בינואר 2027 · דניאל ויוליה</p>
<div class="ov">{ov}</div>
<div class="fl"><div><b>הלוך LY383</b><span>25.1 · 18:15 תל אביב ← 21:00 רומא, טרמינל 3 · מושב 38K</span></div>
<div><b>טיסת פנים הלוך</b><span>25.1 · בלילה, רומא ← קטניה (שעה לפי הכרטיס)</span></div>
<div><b>טיסת פנים חזור, Aeroitalia</b><span>30.1 · 15:40 קטניה ← 17:05 רומא</span></div>
<div><b>חזור LY384</b><span>30.1 · 21:55 רומא ← 02:15 תל אביב · מושב 42K</span></div></div>
<p class="note2">כל עמוד הוא יום. שמות של מסעדות, ברים ואתרים לחיצים ופותחים אותם בגוגל מפות. קוד ה-QR בראש כל יום פותח את מסלול היום.</p>
</div></section>''')

# ---------- days ----------
for i in range(6):
    a=s.select_one(f'#d{i}')
    title=txt(a.select_one('.dh h2')); wd=txt(a.select_one('.dmeta .w'))
    LINKER[0]=day_names(a,{2:'Noto',3:'Modica'}.get(i,'Siracusa'))
    tl=''.join(f'<li><span class="t">{E(txt(li.select_one(".t")))}</span><span>{L(txt(li.select_one("div")))}</span></li>' for li in a.select('.tl li'))
    meals=''.join(f'<li><span class="t">{E(txt(li.select_one(".mt")))}</span><span>{L(txt(li.select_one("div")))}</span></li>' for li in a.select('.meals li'))
    tips=[txt(x) for x in a.select('.tips:not(.night) li')]
    night=[txt(x) for x in a.select('.tips.night li')]
    bw=[txt(x) for x in a.select('.bwb li')]
    rain=[txt(x) for x in a.select('.rain li')]
    notes=''
    for n in a.select('.note'):
        b=n.select_one('b');bt=txt(b);full=txt(n)
        body=full[len(bt):].strip() if full.startswith(bt) else full
        notes+=f'<div class="nt"><b>{E(bt)}</b>{L(body)}</div>'
    g=a.select_one('.quick a.go'); go=g['href']; glab=txt(g).replace('ניווט: ','')
    hc=s.select_one(f'#h-d{i}'); ht=txt(hc.select_one('h3')); hist=sentences(' '.join(txt(p) for p in hc.select('p')),4)
    fc=s.select_one(f'.fc[data-date="2027-01-{25+i}"]'); wx=txt(fc) if fc else 'בתוך הטרמינל והמלון.'
    blocks_r=''
    if tips: blocks_r+=f'<div class="bx"><h3>טיפים</h3>{ul(tips)}</div>'
    blocks_r+=f'<div class="bx bw"><h3>להיזהר</h3>{ul(bw)}</div>'
    blocks_r+=f'<div class="bx rn"><h3>אם יורד גשם</h3>{ul(rain)}</div>'
    blocks_l=f'<div class="bx"><h3>לוח הזמנים</h3><ul class="tl">{tl}</ul></div>'
    if meals: blocks_l+=f'<div class="bx"><h3>איפה לאכול</h3><ul class="tl ml">{meals}</ul></div>'
    if night: blocks_l+=f'<div class="bx"><h3>ערב ולילה</h3>{ul(night)}</div>'
    blocks_l+=notes
    pages.append(f'''<section class="pg day" style="--c:{COL[i]}">
<header><div class="dn">{DATE[i]}</div><div class="hm"><span>יום {i+1} מתוך 6 · {E(wd)}</span><h2>{E(title)}</h2><p class="wx">מזג אוויר: {E(wx)}</p></div>
<a class="qr" href="{E(go)}"><img src="{qr(go)}" alt=""><span>{E(glab)}</span></a></header>
<div class="cols"><div class="col">{blocks_l}</div><div class="col">{blocks_r}<div class="bx hs"><h3>{E(ht)}</h3><p>{E(hist)}</p></div></div></div>
<footer><span>סירקוזה, ינואר 2027</span><span>{DATE[i]}.1</span></footer>
</section>''')

# ---------- restaurants, pizza, booking, prep ----------
TYPE={'street':'רחוב','pizza':'פיצה','tratt':'טרטוריה','cafe':'בוקר'}
def rrows(areas):
    cs=[c for c in s.select('a.gc') if c['data-a'] in areas]
    cs.sort(key=lambda c:(-float(c['data-v']),-float(c['data-r'])))
    out=''
    for c in cs:
        nm=txt(c.select_one('h3')); g=c.select_one('.gg')
        rt=txt(g.select_one('b')); cnt=txt(g.select_one('small')).replace(' ביקורות','')
        dish=txt(c.select_one('.gd b')); v=txt(c.select_one('.gv b')).replace('/10','')
        cl=txt(c.select_one('.gcl')); pr='€'*int(c['data-p'])
        out+=f'<tr><td><a class="pl" href="{E(c["href"])}">{E(nm)}</a></td><td>{TYPE[c["data-t"]]}</td><td>{pr}</td><td><b>{E(rt)}</b> <small>({E(cnt)})</small></td><td><b>{E(v)}</b>/10</td><td>{E(dish)}</td><td><small>{E(cl)}</small></td></tr>'
    return out
TH='<thead><tr><th>מקום</th><th>סוג</th><th>מחיר</th><th>גוגל</th><th>תמורה</th><th>מנה</th><th>מתי סגור</th></tr></thead>'
def rpage(title,sub,parts):
    body=''.join(f'<div class="bx"><h3>{E(t)}</h3><table class="rt">{TH}<tbody>{rrows(a)}</tbody></table></div>' for t,a in parts)
    return f'<section class="pg ess" style="--c:#0b5fa5"><header class="eh"><h2>{E(title)}</h2><p class="sm">{E(sub)}</p></header><div class="cols one"><div class="col">{body}</div></div><footer><span>שם המקום לחיץ ופותח את גוגל מפות</span><span>aifordaniel.pro/italy-2027</span></footer></section>'
SUB='ממוין לפי תמורה למחיר. תמורה: ציון שלנו מ-1 עד 10. מנה: מחיר משוער לאדם, בלי שתייה.'
pages.append(rpage('מסעדות באורטיג׳יה',SUB,[('אורטיג׳יה',['o'])]))
pages.append(rpage('מסעדות בסירקוזה, נוטו וקטניה',SUB,[('סירקוזה, ליד הגשר והתחנה',['s']),('נוטו',['n']),('קטניה, אם עוברים בה',['c'])]))
pages.append(rpage('מסעדות בראגוזה, מודיקה ומרזממי',SUB,[('ראגוזה איבלה ומודיקה, 28.1',['g']),('מרזממי, 27.1',['m'])]))
pages.append(rpage('מסעדות בטאורמינה (אופציה)',SUB,[('טאורמינה',['t'])]))
pz=''
for a in s.select('#pizza article.pz'):
    nm=txt(a.select_one('h3')); bd=txt(a.select_one('.pzb')); area=txt(a.select_one('.gsub'))
    nums=[txt(x.select_one('b')) for x in a.select('.pzn div')]
    mp=a.select_one('a.gm2:not(.tel)')['href']; tel=txt(a.select_one('a.tel')).replace('חיוג ','')
    pz+=f'<li><a class="pl" href="{E(mp)}">{E(nm)}</a> · {E(bd)}<br><small>{E(area)} · גוגל {E(nums[0])} · פיצה {E(nums[1])} · הזמנה {E(nums[2])} · <span dir="ltr">{E(tel)}</span></small></li>'
rs=''
for li in s.select('#reserve li.rs'):
    nm=txt(li.select_one('.rsm b')); meta=txt(li.select_one('.rsm span')); w=txt(li.select_one('.rsw b'))
    tel=li.select_one('a.tel'); t=(tel['href'].replace('tel:','') if tel else 'באינטרנט')
    mp=li.select_one('a.gm2:not(.tel)')['href']
    rs+=f'<li><a class="pl" href="{E(mp)}">{E(nm)}</a> · {E(w)}<br><small>{E(meta)} · <span dir="ltr">{E(t)}</span></small></li>'
say=txt(s.select_one('#reserve .say p')); sayh=txt(s.select_one('#reserve .say small'))
noq=''.join(f'<li><b>{E(txt(x.select_one("b")))}</b> {E(txt(x)[len(txt(x.select_one("b"))):])}</li>' for x in s.select('#reserve ul.local li'))
pzt=ul([txt(x) for x in s.select('#pizza .pzt li')])
pages.append('<section class="pg ess" style="--c:#c0392b"><header class="eh"><h2>פיצה, ומסעדות שמזמינים בהן מקום</h2></header>'
 f'<div class="cols"><div class="col"><div class="bx"><h3>פיצה איטלקית אמיתית</h3><ul class="pzl">{pz}</ul></div>'
 f'<div class="bx"><h3>איך אוכלים פיצה כמו סיציליאנים</h3>{pzt}</div></div>'
 f'<div class="col"><div class="bx"><h3>להזמין מקום מראש</h3><ul class="pzl">{rs}</ul></div>'
 f'<div class="bx"><h3>מה אומרים בטלפון</h3><p dir="ltr" style="text-align:left;font-weight:700;margin:0">{E(say)}</p><p class="sm">{E(sayh)}</p></div>'
 f'<div class="bx"><h3>לא מזמינים, מגיעים מוקדם</h3><ul>{noq}</ul></div></div></div>'
 '<footer><span>שם המקום לחיץ ופותח את גוגל מפות</span><span>aifordaniel.pro/italy-2027</span></footer></section>')
sl=''
for a in s.select('#sleep article.sl'):
    when=' '.join(txt(x) for x in a.select('.sln b, .sln span')); h3=txt(a.select_one('h3')); p=txt(a.select_one('.slb p'))
    mp=a.select_one('a.gm2')['href']
    sl+=f'<li><b>{E(when)}: <a class="pl" href="{E(mp)}">{E(h3)}</a></b><br>{E(p)}</li>'
chk=', '.join(txt(x) for x in s.select('#sleep .slc li b'))
apps=''.join(f'<li><b>{E(txt(a.select_one("h3")))}</b> · {E(txt(a.select_one(".arole")))} <small>({E(txt(a.select_one(".alvl")))})</small></li>' for a in s.select('#ready article.app'))
es=''.join(f'<li><b>{E(txt(x.select_one("b")))}</b> {E(txt(x.select_one("span")))} · {E(txt(x.select_one("strong")))}</li>' for x in s.select('#ready .eo'))
todo=''
for g in s.select('#ready .chk'):
    todo+=f'<h4>{E(txt(g.select_one("h4")))}</h4><ul class="cb">'+''.join(f'<li>{E(txt(x))}</li>' for x in g.select('label span'))+'</ul>'
pages.append('<section class="pg ess" style="--c:#17806f"><header class="eh"><h2>לפני הטיסה: לינה, אפליקציות ומשימות</h2></header>'
 f'<div class="cols"><div class="col"><div class="bx"><h3>איפה ישנים</h3><ul class="pzl">{sl}</ul><p class="sm">לבדוק לפני שמזמינים: {E(chk)}.</p></div>'
 f'<div class="bx"><h3>אפליקציות להוריד</h3><ul>{apps}</ul></div>'
 f'<div class="bx"><h3>eSIM לגלישה</h3><ul>{es}</ul></div></div>'
 f'<div class="col"><div class="bx"><h3>משימות לפי זמן</h3>{todo}</div></div></div>'
 '<footer><span>לסמן בעט</span><span>aifordaniel.pro/italy-2027</span></footer></section>')

# ---------- taormina option + car rental ----------
def items(sel):
    out=''
    for li in s.select(sel):
        b=li.select_one('b'); bt=txt(b) if b else ''; full=txt(li)
        body=full[len(bt):].strip() if bt and full.startswith(bt) else full
        out+=f'<li><b>{E(bt)}</b> {E(body)}</li>' if bt else f'<li>{E(full)}</li>'
    return '<ul class="pzl">'+out+'</ul>'
tvb=''.join(f'<li><b>{E(txt(li.select_one("b")))}.1</b> {E(txt(li)[len(txt(li.select_one("b"))):])}</li>' for li in s.select('#taormina .tv-b li'))
cards=s.select('#taormina .tcard')
pages.append('<section class="pg ess" style="--c:#c0392b"><header class="eh"><h2>אופציה: טאורמינה</h2><p class="sm">'+E(txt(s.select_one('#taormina .lead')))+'</p></header>'
 '<div class="cols"><div class="col">'
 f'<div class="bx"><h3>המסלול עם טאורמינה</h3><ul class="pzl">{tvb}</ul><p class="sm">{E(txt(s.select_one("#taormina .tv-b p")))}</p></div>'
 f'<div class="bx"><h3>{E(txt(cards[0].select_one("h3")))}</h3>{items("#taormina .tcard:nth-of-type(1) li")}</div>'
 f'<div class="bx"><h3>{E(txt(cards[1].select_one("h3")))}</h3>{items("#taormina .tcard:nth-of-type(2) li")}</div>'
 '</div><div class="col">'
 f'<div class="bx"><h3>{E(txt(cards[2].select_one("h3")))}</h3>{items("#taormina .tcard:nth-of-type(3) li")}</div>'
 f'<div class="bx"><h3>בעד ונגד</h3><p><b>בעד:</b> {E(" ".join(txt(x) for x in s.select("#taormina .pro:not(.con) li")))}</p><p><b>נגד:</b> {E(" ".join(txt(x) for x in s.select("#taormina .pro.con li")))}</p></div>'
 f'<div class="bx"><h3>מה אומרים ב-Reddit</h3>{items("#taormina .tw2 li")}</div>'
 '</div></div><footer><span>המסעדות של טאורמינה בעמוד המסעדות</span><span>aifordaniel.pro/italy-2027</span></footer></section>')
dest=''.join(f'<li><b>{E(txt(d.select_one(".cdh b")))}: {E(txt(d.select_one(".cdh span")))}.</b> {E(txt(d.select_one("p")))}</li>' for d in s.select('#car .cd'))
cost=''.join(f'<li><b>{E(txt(d.select_one("span")))}: {E(txt(d.select_one("b")))}</b> <small>{E(txt(d.select_one("small")))}</small></li>' for d in s.select('#car .costs div'))
scam=''.join(f'<li><b>{E(txt(d.select_one("b")))}.</b> {E(txt(d.select_one("p")))}</li>' for d in s.select('#car .scam > div'))
chk=''.join(f'<li>{E(txt(x))}</li>' for x in s.select('#car .chk2 li'))
docs=items('#car .tcard:nth-of-type(4) li'); car=items('#car .tcard:nth-of-type(1) li'); where=items('#car .tcard:nth-of-type(2) li')
pages.append('<section class="pg ess" style="--c:#1c2e3b"><header class="eh"><h2>השכרת רכב (1/2)</h2><p class="sm">'+E(txt(s.select_one('#car .verdict p')))+'</p></header>'
 '<div class="cols"><div class="col">'
 f'<div class="bx"><h3>לפי יעד</h3><ul class="pzl">{dest}</ul></div>'
 '</div><div class="col">'
 f'<div class="bx"><h3>עלויות בינואר</h3><ul class="pzl">{cost}</ul></div>'
 f'<div class="bx"><h3>מסמכים</h3>{docs}</div>'
 '</div></div><footer><span>מקורות: Reddit r/sicily, Tyremap, Parclick, Qeeq, Reid\'s</span><span>aifordaniel.pro/italy-2027</span></footer></section>')
pages.append('<section class="pg ess" style="--c:#1c2e3b"><header class="eh"><h2>השכרת רכב (2/2): תרמיות, רכב ודלפק</h2></header>'
 '<div class="cols"><div class="col">'
 f'<div class="bx bw"><h3>תרמיות נפוצות ואיך נמנעים</h3><ul class="pzl">{scam}</ul></div>'
 '</div><div class="col">'
 f'<div class="bx"><h3>איזה רכב ומאיפה</h3>{car}{where}</div>'
 f'<div class="bx"><h3>צ׳קליסט בדלפק</h3><ul class="cb">{chk}</ul></div>'
 '</div></div><footer><span>מקורות: Reddit r/sicily, Trustpilot, The Local</span><span>aifordaniel.pro/italy-2027</span></footer></section>')

# ---------- essentials ----------
ph=[]
for li in s.select('#it .pgrp li')[:12]:
    ph.append(f'<li><b dir="ltr">{E(txt(li.select_one("b")))}</b><span>{E(txt(li.select_one("small")))}</span></li>')
pages.append(f'''<section class="pg ess">
<header class="eh"><h2>חשוב לשמור</h2></header>
<div class="cols"><div class="col">
<div class="bx"><h3>חירום באיטליה</h3><ul class="nums"><li><b>112</b>חירום כללי</li><li><b>118</b>אמבולנס</li><li><b>113</b>משטרה</li><li><b>115</b>כבאות</li></ul></div>
<div class="bx"><h3>שגרירות ישראל ברומא</h3><p>Via Michele Mercati 14, רומא</p><ul class="nums"><li><b dir="ltr">+39 06 36198 586</b>קונסולרית</li><li><b dir="ltr">+39 06 36198 505</b>חירום וסופ״ש</li><li><b dir="ltr">+972 2 5303155</b>חדר מצב, משרד החוץ</li></ul><p class="sm">דרכון שאבד: קודם משטרה, אחר כך השגרירות.</p></div>
<div class="bx"><h3>הפרטים שלנו</h3><div class="fill"><span>מלון 25-29.1</span><i></i></div><div class="fill"><span>הסעה מהשדה 25.1</span><i></i></div><div class="fill"><span>רכב 27-28.1</span><i></i></div><div class="fill"><span>ביטוח</span><i></i></div><div class="fill"><span>קלנועית</span><i></i></div></div>
</div><div class="col">
<div class="bx"><h3>איטלקית בקצרה</h3><ul class="ph">{''.join(ph)}</ul></div>
<div class="bx"><h3>כללי אצבע</h3><ul><li>במסוף כרטיס בוחרים תמיד לחייב באירו.</li><li>דג לפי משקל: שואלים מחיר ל-100 גרם.</li><li>"coperto" של 1 עד 3 אירו לאדם הוא חוקי.</li><li>מונית: רק לבנה רשמית, מחיר מסכימים מראש.</li></ul></div>
</div></div>
<footer><span>סירקוזה, ינואר 2027</span><span>aifordaniel.pro/italy-2027</span></footer>
</section>''')

CSS=FONTS+r'''
@page{size:A4;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:Heebo,sans-serif;color:#0e1c26;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.pg{width:210mm;height:297mm;overflow:hidden;position:relative;page-break-after:always;break-after:page;padding:12mm 12mm 14mm;font-size:var(--fs,9.6pt);line-height:1.5;background:#fbfcfd}
.pg:last-child{page-break-after:auto}
h1,h2,h3{font-family:Rubik,Heebo,sans-serif;margin:0}
ul{margin:0;padding-inline-start:1.1em}li{margin:.18em 0}
.cover{background:#0b5fa5;color:#fff;display:flex;align-items:stretch}
.cin{display:flex;flex-direction:column;gap:7mm;justify-content:flex-end;width:100%}
.cover small{font:700 10pt Rubik;letter-spacing:.06em;color:#bcdcff}
.cover h1{font:900 54pt/0.95 Rubik;letter-spacing:-.02em}
.cl{font-size:15pt;margin:0}
.ov{display:grid;gap:2.2mm}
.ovr{display:grid;grid-template-columns:20mm 22mm 1fr;align-items:center;gap:3mm;background:rgba(255,255,255,.1);border-inline-start:5px solid var(--c);border-radius:3mm;padding:3mm 4mm;font-size:11pt}
.ovr b{font:900 15pt Rubik}.ovr span{color:#cfe3f7}.ovr em{font-style:normal;font-weight:700}
.fl{display:grid;grid-template-columns:1fr 1fr;gap:3mm}
.fl div{background:#fff;color:#0e1c26;border-radius:3mm;padding:3.5mm 4mm;display:grid;gap:1mm}.fl b{font:800 11pt Rubik}.fl span{font-size:9.5pt}
.note2{font-size:9.5pt;color:#cfe3f7;margin:0}
.day header{display:grid;grid-template-columns:auto 1fr auto;gap:5mm;align-items:center;padding-bottom:4mm;border-bottom:3px solid var(--c);margin-bottom:4mm}
.day::before{content:"";position:absolute;inset:0 0 auto 0;height:4mm;background:var(--c)}
.dn{font:900 46pt/0.85 Rubik;color:var(--c);letter-spacing:-.04em}
.hm span{font:700 9pt Rubik;color:#3f5260}
.hm h2{font:900 19pt/1.15 Rubik;margin:1mm 0}
.wx{margin:0;font-size:8.8pt;color:#3f5260}
.qr{display:grid;justify-items:center;gap:1mm;text-decoration:none;color:#3f5260;width:28mm;text-align:center}
.qr img{width:24mm;height:24mm}.qr span{font-size:7pt;line-height:1.25}
.cols{display:grid;grid-template-columns:1.12fr 1fr;gap:5mm}
.col{display:grid;gap:3mm;align-content:start}
.bx{background:#fff;border:1px solid #d1dbe0;border-radius:3mm;padding:3mm 3.5mm}
.bx h3{font:800 10.5pt Rubik;color:var(--c,#0b5fa5);margin-bottom:1.5mm}
.tl{list-style:none;padding:0}
.tl li{display:grid;grid-template-columns:15mm 1fr;gap:2.5mm;padding:1.3mm 0;border-top:1px solid #e6ecef;margin:0}
.tl li:first-child{border-top:0}
.tl .t{font:800 9pt Rubik;color:var(--c)}
.bw{border-color:#e0b49c;background:#fdf6f1}.bw h3{color:#b4501e}
.rn{background:#eef5fb;border-color:#c7dcef}.rn h3{color:#0b5fa5}
.nt{font-size:.92em;background:#eef2f4;border-radius:3mm;padding:2.5mm 3.5mm}.nt b{display:block;font:800 9.5pt Rubik}
.hs p{margin:0;font-size:.95em}
.pg footer{position:absolute;bottom:6mm;inset-inline:12mm;display:flex;justify-content:space-between;font:700 7.5pt Rubik;color:#8a9aa5}
.ess .eh{border-bottom:3px solid #0b5fa5;padding-bottom:3mm;margin-bottom:4mm}.ess h2{font:900 22pt Rubik}
.nums{list-style:none;padding:0}.nums li{display:flex;gap:3mm;align-items:baseline;padding:1.2mm 0;border-top:1px solid #e6ecef}.nums b{font:900 13pt Rubik;min-width:16mm;unicode-bidi:isolate}
.ph{list-style:none;padding:0}.ph li{display:grid;padding:1.2mm 0;border-top:1px solid #e6ecef}.ph b{font-family:Rubik;text-align:right}.ph span{font-size:.9em;color:#3f5260}
.fill{display:grid;grid-template-columns:24mm 1fr;align-items:end;gap:2mm;margin-top:3.5mm}.fill i{border-bottom:1px solid #8a9aa5;height:5mm}
.sm{font-size:.88em;color:#3f5260;margin:1mm 0 0}
.one{grid-template-columns:1fr}
.rt{width:100%;border-collapse:collapse;font-size:.86em}
.rt th{font:700 7.6pt Rubik;color:#3f5260;text-align:start;padding:1mm 1.2mm;border-bottom:1.5px solid #c9d4da}
.rt td{padding:1.05mm 1.2mm;border-bottom:1px solid #e6ecef;vertical-align:top}
.rt td:first-child{font-weight:700}
.rt small{color:#3f5260}
.pzl{list-style:none;padding:0}.pzl li{padding:1.3mm 0;border-top:1px solid #e6ecef}.pzl li:first-child{border-top:0}
.cb{list-style:none;padding:0}.cb li{padding:.9mm 0;padding-inline-start:6mm;position:relative}.cb li::before{content:"";position:absolute;inset-inline-start:0;top:1.6mm;width:3.2mm;height:3.2mm;border:1.3px solid #3f5260;border-radius:.8mm}
h4{font:800 9.5pt Rubik;margin:2.5mm 0 .5mm;color:var(--c)}
.ess .eh p{margin:1mm 0 0}
a.pl{color:inherit;text-decoration:underline;text-decoration-color:var(--c,#0b5fa5);text-decoration-thickness:1.5px;text-underline-offset:1.2mm;font-weight:700}
'''
doc=f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>סירקוזה וסיציליה, חוברת טיול ינואר 2027</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'
open('booklet.html','w',encoding='utf-8').write(doc)
LINKS=doc.count('class="pl"')

FIT=r'''()=>{const out=[];document.querySelectorAll('.pg').forEach(p=>{let fs=9.6;p.style.setProperty('--fs',fs+'pt');
 const over=()=>{const f=p.querySelector('footer');const lim=f?f.getBoundingClientRect().top-6:p.getBoundingClientRect().bottom;let m=0;p.querySelectorAll('.col,.cin').forEach(c=>{m=Math.max(m,c.getBoundingClientRect().bottom)});return m>lim};
 while(over()&&fs>7.4){fs-=0.2;p.style.setProperty('--fs',fs.toFixed(1)+'pt')} out.push(fs.toFixed(1)+(over()?'!OVER':''))});return out}'''
async def main():
    async with async_playwright() as p:
        exe=os.environ.get('CHROME_PATH')
        b=await p.chromium.launch(**({'executable_path':exe} if exe else {}),args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':794,'height':1123})
        await pg.goto('file://'+HERE+'/booklet.html');await pg.evaluate('document.fonts.ready')
        print('fit',await pg.evaluate(FIT))
        await pg.pdf(path=OUT,format='A4',print_background=True,prefer_css_page_size=True)
        print('links in pdf:',LINKS)
        if os.environ.get('SHOTS'):
            for k in range(len(await pg.query_selector_all('.pg'))):
                el=(await pg.query_selector_all('.pg'))[k]
                await el.screenshot(path=f'/tmp/p{k}.png')
        await b.close()
asyncio.run(main())
