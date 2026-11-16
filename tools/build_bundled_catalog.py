"""Create an exact-match Chinese display catalog for bundled Glaze prompts.
Protect protocol syntax. Leave source prompts and serialized user data intact.
"""
import ast,json,pathlib,re,time
ROOT=pathlib.Path('glaze')
OUT=pathlib.Path('localization')
OUT.mkdir(exist_ok=True)
cache_path=OUT/'bundled_zh.json'
cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
manual_path=OUT/'bundled_manual_zh.json'
manual=json.loads(manual_path.read_text()) if manual_path.exists() else {}
from argostranslate import package,translate
package.update_package_index()
available=package.get_available_packages()
for a,b in [('en','zh'),('ru','en')]:
    if not any(p.from_code==a and p.to_code==b for p in package.get_installed_packages()):
        p=next(p for p in available if p.from_code==a and p.to_code==b)
        package.install_from_path(p.download())
trans={lang:translate.get_translation_from_codes(lang,'zh') for lang in ('en','ru')}
LITERAL=re.compile(r"""(?P<raw>r)?(?P<lit>'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")""")
def decode(m):
    lit=m.group('lit')
    if m.group('raw'):return lit[3:-3] if lit.startswith(("'''",'"""')) else lit[1:-1]
    try:return ast.literal_eval(lit)
    except (SyntaxError,ValueError):return None
corpus=set()
for p in ROOT.joinpath('assets/presets').glob('*.json'):
    obj=json.loads(p.read_text())
    for item in obj.get('prompts',[]):
        for field in ('name','content'):
            if isinstance(item.get(field),str):corpus.add(item[field])
for path in ['lib/core/db/studio_preset_seed.dart','lib/core/services/preset_defaults.dart',
             'lib/core/services/memory_prompt_presets.dart','lib/core/services/summary_prompt_presets.dart',
             'lib/core/services/translation_prompt_presets.dart']:
    s=(ROOT/path).read_text()
    parts=list(LITERAL.finditer(s));i=0
    while i<len(parts):
        m=parts[i];value=decode(m);end=m.end();i+=1
        if value is None:continue
        while i<len(parts) and not s[end:parts[i].start()].strip():
            more=decode(parts[i])
            if more is None:break
            value+=more;end=parts[i].end();i+=1
        if re.search(r'[A-Za-zА-Яа-я]',value) and (len(value)>80 or ' ' in value):
            corpus.add(value)
protected=re.compile(r"\{\{[\s\S]*?\}\}|</?[^>\n]+>|https?://\S+|\x60[^\x60\n]+\x60|(?:[A-Za-z_][A-Za-z0-9_.]*\([^)\n]*\))")
headings=re.compile(r'^(\s*(?:[-*]\s*)?)([A-Za-z_][A-Za-z0-9_ /&.-]{0,75}:)(\s*)')
structural={'Memory','Keys','Focus','Constraints','Avoid','Status','Actions','Characters',
            'AUTHORITATIVE_LEDGER_RANGE','Present now','beat_type','tempo','scene_pressure',
            'what_must_advance','stop_point','avoid_repeating','target_length','target_paragraphs',
            'prose_mode_compliance'}
def prose(s):
    if not re.search(r'[A-Za-zА-Яа-я]',s) or re.fullmatch(r'[\W\d_]+',s):return s
    if len(s.strip())<3:return s
    if re.fullmatch(r'[A-Za-z0-9_./+ -]{1,40}',s) and not re.search(r'\s',s.strip()):return s
    lang='ru' if len(re.findall(r'[А-Яа-я]',s))>len(re.findall(r'[A-Za-z]',s))/2 else 'en'
    lead=s[:len(s)-len(s.lstrip())];tail=s[len(s.rstrip()):]
    value=trans[lang].translate(s.strip())
    return lead+value+tail
def line_translate(line):
    match=headings.match(line);prefix=''
    if match and match.group(2)[:-1].strip() in structural:
        prefix=match.group();line=line[len(prefix):]
    pieces=[];at=0
    for m in protected.finditer(line):
        pieces.extend((prose(line[at:m.start()]),m.group()))
        at=m.end()
    pieces.append(prose(line[at:]))
    return prefix+''.join(pieces)
def translate_safe(s):
    if s in manual:return manual[s]
    if s in cache:return cache[s]
    result=[];fenced=False
    for line in s.splitlines(keepends=True):
        nl='\n' if line.endswith('\n') else ''
        text=line[:-1] if nl else line
        if text.lstrip().startswith(chr(96)*3):
            fenced=not fenced;result.append(line);continue
        stripped=text.strip()
        code=(fenced or bool(re.match(r'(?:const |let |var |function |document\.|window\.|@media|[.#][\w-]+\s*\{)',stripped)))
        if stripped.startswith(('{','[')):
            try:json.loads(stripped);code=True
            except ValueError:pass
        result.append(line if code else line_translate(text)+nl)
    value=''.join(result);cache[s]=value
    return value
start=time.time()
for i,s in enumerate(sorted(corpus)):
    translate_safe(s)
    if i%25==0:
        cache_path.write_text(json.dumps(cache|manual,ensure_ascii=False,indent=2)+'\n')
        print('translated',i,'/',len(corpus),'elapsed',round(time.time()-start),flush=True)
cache.update(manual)
cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
(OUT/'catalog_report.json').write_text(json.dumps({
    'source_strings':len(corpus),'translated_strings':len(cache),
    'method':'offline Argos EN->ZH and RU->EN->ZH; exact-match display only',
    'preserved':'original source prompts, user data, complete macros, tags, code fences, JSON examples and parser-sensitive headings',
    'limitations':'Machine draft; core UI is manually translated. Technical macro arguments and embedded code remain original.'
},ensure_ascii=False,indent=2)+'\n')
print('DONE',len(cache),flush=True)
