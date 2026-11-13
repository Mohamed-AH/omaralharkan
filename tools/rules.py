import json, re, collections, sys
Y='../yt/'
def norm(s):
    import unicodedata; s=unicodedata.normalize('NFKC',s or ''); s=re.sub('[\u064B-\u0652\u0640\u200e\u200f\ufffc]','',s)
    for a,b in (('أ','ا'),('إ','ا'),('آ','ا'),('ة','ه'),('ى','ي')): s=s.replace(a,b)
    s=s.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789'))
    s=re.sub(r'"?قناه الشيخ عمر.*?الرسميه"?\s*(بثا مباشرا)?','',s)
    return re.sub(r'\s+',' ',s).strip()
BOOKS=[ # (key, display, category, regex on normalized title)
 ('riyadh','رياض الصالحين','الحديث',r'رياض الصالحين'),
 ('kashf','كشف الشبهات','العقيدة',r'كشف الشبهات'),
 ('nawaqid','نواقض الإسلام','العقيدة',r'نواقض الاسلام'),
 ('muqaddima_tafsir','مقدمة التفسير','التفسير',r'مقدمه التفسير'),
 ('sifat_salah','صفة الصلاة','الفقه',r'صفه الصلاه'),
 ('shurut_salah','شروط الصلاة','الفقه',r'شروط الصلاه'),
 ('nahw_tatbiq','تطبيقات نحوية وإعراب','النحو',r'تطبيقات (في النحو|نحويه)|مدخل الي النحو|اعراب'),
 ('mawarith','آيات المواريث','الفقه',r'المواريث'),
 ('jahiliyya','مسائل الجاهلية','العقيدة',r'مسائل الجاهليه'),
 ('man_nahnu','من نحن','متفرقات',r'^من نحن'),
 ('naba','تفسير سورة النبأ','التفسير',r'سوره النبا'),
 ('shajara','شجرة الإيمان لابن سعدي','العقيدة',r'شجره الايمان'),
 ('mahajja','المحجة لابن رجب','الآداب والتزكية',r'المحجه'),
 ('salman','قصة سلمان الفارسي','السيرة والتاريخ',r'سلمان الفارسي'),
 ('uhud','الحكم والغايات في غزوة أحد','السيرة والتاريخ',r'(معركه|وقعه) احد'),
 ('sabr','قاعدة في الصبر','الآداب والتزكية',r'قاعده في الصبر'),
 ('hamawiyya','فتح رب البرية بتلخيص الحموية','العقيدة',r'الحمويه'),
 ('usul_sunnah','أصول السنة للإمام أحمد','العقيدة',r'اصول السنه|الاصول السنه'),
 ('zad','زاد المستقنع','الفقه',r'زاد المستقنع|في الزاد'),
 ('usul3','الأصول الثلاثة','العقيدة',r'الاصول ?الثلاثه'),
 ('fadl_islam','فضل الإسلام','العقيدة',r'فضل ?الاسلام'),
 ('ibnqayyim','تفسير ابن القيم','التفسير',r'تفسير ا?بن القيم'),
 ('siyar','سير أعلام النبلاء','السيرة والتاريخ',r'سير اعلام النبلاء'),
 ('khawatim_imran','تفسير خواتيم سورة آل عمران','التفسير',r'خواتيم سوره ال عمران'),
 ('khawatim_baqara','تفسير خواتيم سورة البقرة','التفسير',r'خواتيم سوره البقره'),
 ('mukhtasar_seerah','مختصر السيرة','السيرة',r'مختصر السيره'),
 ('tazakka','قد أفلح من تزكى','التزكية',r'قد ?افلح من تزكي'),
 ('munafiqun','تفسير سورة المنافقون','التفسير',r'سوره ?المنافقون'),
 ('usul_ilm','الأصول من علم الأصول','أصول الفقه',r'الاصول من علم الاصول'),
 ('bukhari','التعليق على صحيح البخاري','الحديث',r'البخاري'),
 ('barbahari','التعليق على شرح السنة للبربهاري','العقيدة',r'بربهاري|شرح السنه|السنه ?للبر'),
 ('sadi','التعليق على تفسير ابن سعدي','التفسير',r'تفسير ?ا?بن سعدي|ابن سعدي (الايه|سوره)|في تفسير ابن سعدي'),
 ('tawhid','كتاب التوحيد','العقيدة',r'كتاب ?التوحيد|كناب التوحيد|كنات توحيد|كتاب الوحيد|^التوحيد|كتب التوحيد'),
 ('raheeq','السيرة النبوية: الرحيق المختوم','السيرة',r'الرحيق'),
 ('seerah_rashid','السيرة لموسى بن راشد','السيرة',r'السيره لموسي'),
 ('lumah','لمعة الاعتقاد','العقيدة',r'اللمعه|لمعه الاعتقاد'),
 ('akhsar','أخصر المختصرات','الفقه',r'اخصر ?المختصر ?ات'),
 ('shabrawiya','الشبراوية في النحو','النحو',r'الشبراو|الشبرويه'),
 ('ajurrumiya','الآجرومية','النحو',r'الاجروميه|اجروميه'),
 ('yawm','سلسلة يوم من التاريخ','السيرة والتاريخ',r'(يوم|سلسله) من التاريخ'),
 ('ilmahat','إلماحات في تفسير القرآن','التفسير',r'الماحات'),
 ('aqeedah','دروس في العقيدة','العقيدة',r'(في|من) العقيده'),
 ('fiqh','دروس في الفقه','الفقه',r'في الفقه'),
 ('adab','الآداب','الآداب',r'في الاداب|منظومه ?الاداب'),
 ('usul6','الأصول الستة','العقيدة',r'الاصول السته'),
 ('asbab','أسباب النزول','التفسير',r'اسباب النزول'),
 ('umdah','عمدة الفقه لابن قدامة','الفقه',r'العمده'),
 ('khutbah','الخطب','خطب ومحاضرات',r'خطبه'),
 ('lecture','محاضرات','خطب ومحاضرات',r'محاضره|محاضرات|^(بدات )?كلمه'),
 ('sinani','دروس أ.د. عصام السناني','دروس ضيوف',r'السناني|ا د عصام'),
 ('qaseem','رسالة إلى أهل القصيم','العقيدة',r'اهل القصيم'),
 ('fatiha','تفسير سورة الفاتحة','التفسير',r'الفاتحه'),
 ('kursi','تفسير آية الكرسي','التفسير',r'الكرسي'),
 ('muhimma','الدروس المهمة لعامة الأمة','العقيدة',r'الدروس المهمه'),
 ('faraid','الفرائض','الفقه',r'الفرائض'),
 ('siyam','حقيقة الصيام','الفقه',r'حقيقه الصيام'),
]
NUM=re.compile(r'(?:الدرس|درس|الحلقه|اليوم|المجلس|رقم)\s*\(?\s*(\d+)|^(\d+)\s*\||(?:البخاري|التوحيد|البربهاري)\s*(\d+)|(\d+)$')
BARE=re.compile(r'^(?:بدا |بدات اعاده )?(?:الدرس|اعادهالدرس) ?(\d+)')
def guess(t):
    m=BARE.match(norm(t))
    if not m: return None,None
    n=int(m.group(1))
    if n>=230: return 'bukhari',n
    if 40<=n<=164: return 'raheeq',n
    return None,None
# Books whose early sessions are numbered in words («المجلس الحادي عشر») and form one sequence with the
# numbered ones. Not for series whose numbering restarts per surah or per biography (أسباب النزول، سير أعلام النبلاء).
WORDS={'tawhid','bukhari'}
UNITS={'الاول':1,'الحادي':1,'الثاني':2,'الثالث':3,'الرابع':4,'الخامس':5,'السادس':6,'السابع':7,'الثامن':8,'التاسع':9,'العاشر':10}
TENS={'العشرون':20,'والعشرون':20,'الثلاثون':30,'والثلاثون':30,'الاربعون':40,'والاربعون':40}
def ordinal(n):
    # «المجلس الحادي والعشرون» -> 21, «[المجلس السابع] عشر» -> 17
    m=re.search(r'المجلس\W*((?:ال|و)\S+(?:\W+(?:عشر|و?ال\S+ون))?)',n)
    if not m: return None
    w=re.sub(r'[^\w ]',' ',m.group(1)).split()
    u=UNITS.get(w[0]); t=TENS.get(w[0])
    if t: return t
    if u is None: return None
    if len(w)>1 and w[1]=='عشر': return u+10 if u<10 else None
    if len(w)>1 and w[1] in TENS: return u+TENS[w[1]]
    return u
def number(n, words=False):
    n=re.sub(r'\d{4}/\d{1,2}/\d{1,2}',' ',n)   # Hijri dates glued to the lesson number: «الدرس94١٤٤٤/٢/١٢»
    n=re.sub(r'(?:^|\s)ص\s*\d+',' ',n)          # page numbers: «ص ٣٨٩»
    m=NUM.search(n.strip()); num=next((int(g) for g in (m.groups() if m else []) if g),None)
    if num is None and re.search(r'الدرس\W*الاول\b', n): return 1
    return num if num is not None or not words else ordinal(n)
def classify(t):
    n=norm(t)
    for k,d,c,rx in BOOKS:
        if re.search(rx,n):
            return k,number(n, k in WORDS)
    return None,None
UNTITLED=re.compile(r'^((بدات|ستبدا) قناه\s*|بدون عنوان)$')
if __name__=='__main__':
    out=collections.defaultdict(list); un=[]
    for tab in ('streams','videos'):
        for x in json.load(open(Y+tab+'_flat.json')):
            k,num=classify(x['t'])
            if k: out[k].append(num)
            elif UNTITLED.match(norm(x['t'])): out['untitled'].append(None)
            else: un.append((tab,x['t']))
    meta={k:(d,c) for k,d,c,_ in BOOKS}; meta['untitled']=('بثوث بلا عنوان','غير مصنف')
    tot=sum(len(v) for v in out.values())
    for k,v in sorted(out.items(),key=lambda kv:-len(kv[1])):
        nums=[n for n in v if n]; print(f'{len(v):4d} {meta[k][1]:14s} {meta[k][0]}  nums:{len(nums)} max:{max(nums) if nums else "-"}')
    print('classified',tot,'unclassified',len(un))
    json.dump(un,open(Y+'unclassified.json','w'),ensure_ascii=False,indent=0)
