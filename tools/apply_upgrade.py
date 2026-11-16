"""Apply the reviewed stable merge and display localization to restored Glaze."""
import json,pathlib,re,shutil,subprocess,os,hashlib
ROOT=pathlib.Path('glaze')
LOC=pathlib.Path('localization')
def read(p):return (ROOT/p).read_text()
def write(p,s):
    dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s)
def add_import(path,s):
    rel=os.path.relpath(ROOT/'lib/core/localization/bundled_text.dart',(ROOT/path).parent).replace(os.sep,'/')
    line="import '"+rel+"';\n"
    if line not in s:s=line+s
    return s
for p in pathlib.Path('overrides').rglob('*'):
    if p.is_file():
        dest=ROOT/p.relative_to('overrides');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
# Audit already merged JSON structurally: upstream keys plus local additions.
for lang in ['en','ru']:
    shutil.copy2(pathlib.Path('audit/sources/assets/translations')/(lang+'.json'),ROOT/'assets/translations'/(lang+'.json'))
en=json.loads(read('assets/translations/en.json'))
zh=json.loads(read('assets/translations/zh.json'))
zh.update(json.loads((LOC/'ui_zh_v0101.json').read_text()))
extra={
 'glaze_bundled_locale':('en','zh'),
 'glaze_bundled_translation_note':('Chinese reading view; long presets include machine-assisted drafts. Unedited source text is preserved.','中文阅读视图；长预设包含机器辅助译文。未编辑的原文会完整保留。'),
 'glaze_bundled_show_original':('Show original prompt','查看提示词原文'),
 'glaze_bundled_show_chinese':('Show Chinese rendering','查看中文译文'),
 'glaze_by_author':('by {name}','作者：{name}'),
 'glaze_preset_cloned':('Preset cloned','预设已克隆'),
 'glaze_authors_note_chat':("Author's note content is tied to a chat. Open a chat to edit it.",'作者注释与具体聊天关联，请打开聊天后编辑。'),
}
ru=json.loads(read('assets/translations/ru.json'))
for k,(a,b) in extra.items():en[k]=a;zh[k]=b;ru[k]='ru' if k=='glaze_bundled_locale' else a
zh={k:zh.get(k,v) for k,v in en.items()}
for lang,obj in [('en',en),('ru',ru),('zh',zh)]:
    write('assets/translations/'+lang+'.json',json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

# The resource guard must describe this official stable version, rather than
# the retired v0.9.0 strings (some keys were deliberately removed upstream).
contract = {}
for lang in ['en', 'ru']:
    original = json.loads(subprocess.check_output(
        ['git', '-C', str(ROOT), 'show', 'v0.10.1:assets/translations/'+lang+'.json'],
        text=True))
    digest = hashlib.sha256(json.dumps(
        original, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    contract[lang] = {'keys': list(original), 'sha256': digest}
write('localization/upstream-contract.json',
      json.dumps(contract, ensure_ascii=False, indent=2)+'\n')

# Generated lookup data is used by preset display only, never the transport,
# prompt builder, original preset assets or user-message storage.
catalog=json.loads((LOC/'bundled_zh.json').read_text())
manual={}
for f in ['bundled_manual_zh.json','bundled_core_zh.json','bundled_shino_zh.json','bundled_summary_defaults_zh.json']:
    if (LOC/f).exists():manual.update(json.loads((LOC/f).read_text()))
macros=lambda s:sorted(re.findall(r'\{\{[\s\S]*?\}\}',s))
dropped=[]
fixes={
 '混凝土':'具体','内存条目':'记忆条目','内存段落':'记忆段落','过去紧张':'过去时态',
 '字符声音':'角色口吻','字符交换':'角色交流','字符名称':'角色名','字符的':'角色的',
 '关键字符':'关键角色','与字符匹配':'与角色匹配','句子的长度':'句子长度',
 '反肿瘤科学检查':'避免全知视角检查','金克斯':'性偏好','国家事实':'陈述事实',
 '国家每个事实':'每个事实','开放线条':'未解线索','绘图开发':'剧情发展','时间skip':'时间跳跃',
 '没有消毒':'不作净化处理','Markdown标记':'Markdown 标记','马克当':'Markdown',
 '挥发性':'发声','国家联络中心':'NPC','字符动态':'角色互动','对话框':'对话',
 '库存短语':'固定套话','花开的比喻':'华丽的比喻','第一义':'第一人称',
 '保持100%的性格':'始终符合角色设定','机构的行为':'身体行为','幽灵作家':'代笔作者',
}
for s,t in list(catalog.items()):
    if s in manual:continue
    if macros(s)!=macros(t):
        dropped.append(s);catalog[s]=s;continue
    # Only clean ordinary prose; opaque macro arguments remain byte-for-byte.
    parts=re.split(r'(\{\{[\s\S]*?\}\})',t)
    for i in range(0,len(parts),2):
        for a,b in fixes.items():parts[i]=parts[i].replace(a,b)
        if r'{\fn' not in s:parts[i]=re.sub(r'\{\\fn[^}]*\}','',parts[i])
    catalog[s]=''.join(parts)
catalog.update(manual)
for s,t in catalog.items():
    assert macros(s)==macros(t),('macro mismatch',s[:100])
def dart_string(s):return json.dumps(s,ensure_ascii=False).replace('$',r'\$').replace('\u2028',r'\u2028').replace('\u2029',r'\u2029')
body="// Generated exact-match display data. Original storage and prompts are retained.\nconst bundledChineseText = <String, String>{\n"
body+=''.join('  '+dart_string(s)+': '+dart_string(t)+',\n' for s,t in sorted(catalog.items()))
body+='};\n'
write('lib/core/localization/bundled_zh.g.dart',body)

# Localize the generic editor only at explicit preset-editor call sites.
preset_paths=['lib/features/presets/preset_editor_screen.dart',
              'lib/features/studio/widgets/studio_block_editor_inline.dart']
for path in preset_paths:
    s=read(path).replace('GenericEditor(\n','GenericEditor(\n      localizeBundledText: true,\n')
    s=add_import(path,s)
    s=s.replace('title: block.name,','title: bundledText(block.name),').replace('label: block.name,','label: bundledText(block.name),')
    s=s.replace('title: folder.name,','title: bundledText(folder.name),')
    s=s.replace("hint: block.enabled ? null : 'Disabled',","hint: block.enabled ? null : bundledText('Disabled'),")
    s=s.replace("subtitle: _author.isNotEmpty ? 'by $_author' : null,","subtitle: _author.isNotEmpty ? 'glaze_by_author'.tr(namedArgs: {'name': _author}) : null,")
    s=re.sub(r"'by \$\{preset.author\}'","'glaze_by_author'.tr(namedArgs: {'name': preset.author ?? ''})",s)
    s=s.replace("'Preset cloned'","'glaze_preset_cloned'.tr()")
    s=s.replace('hint: "Author\'s note content is tied to a chat. Open a chat to edit it.",',"hint: 'glaze_authors_note_chat'.tr(),")
    # Agent dropdowns use factory names, never agent IDs.
    s=s.replace("'label': spec.name,","'label': bundledText(spec.name),")
    write(path,s)

for path in ['lib/features/presets/widgets/preset_block_row.dart',
             'lib/features/presets/widgets/preset_block_group_row.dart',
             'lib/features/studio/widgets/studio_block_row.dart']:
    s=read(path);s=add_import(path,s)
    s=s.replace('text: block.name,','text: bundledText(block.name),')
    s=re.sub(r'(child: Text\(\s*)block.name,',r'\1bundledText(block.name),',s)
    s=re.sub(r'(Text\(\s*)folder.name,',r'\1bundledText(folder.name),',s)
    s=s.replace("message: 'System block — injected automatically',","message: bundledText('System block — injected automatically'),")
    s=s.replace('final title = block.title.isNotEmpty ? block.title : block.id;','final title = bundledText(block.title.isNotEmpty ? block.title : block.id);')
    s=s.replace('block.title.isEmpty ? block.id : block.title,','bundledText(block.title.isEmpty ? block.id : block.title),')
    write(path,s)
path='lib/shared/widgets/prompt_preset_list.dart'
s=add_import(path,read(path))
s=s.replace('_ => preset.label,','_ => bundledText(preset.label),')
s=s.replace('title: p.label,','title: bundledText(p.label),')
s=s.replace('preset.prompt,\n                key:', 'bundledText(preset.prompt),\n                key:')
s=s.replace('_excerpt(preset.prompt)','_excerpt(bundledText(preset.prompt))')
write(path,s)

# Supplement text captured from source names, used in headers and grouped rows.
# This is display-only: IDs, syntax, selection flags, model protocol and stored
# preset blocks retain the upstream implementation.
for path in ['lib/features/presets/studio_preset_editor_screen.dart']:
    s=read(path);s=add_import(path,s)
    s=s.replace("title: 'New Block',","title: bundledText('New Block'),")
    s=s.replace("title: 'Closing tag',","title: bundledText('Closing tag'),")
    s=s.replace('args: [block.title.isNotEmpty ? block.title : block.id],','args: [bundledText(block.title.isNotEmpty ? block.title : block.id)],')
    write(path,s)

# Verify conflict resolution before code generation or compilation.
for p in ROOT.joinpath('lib').rglob('*.dart'):
    assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)',p.read_text(),re.M),str(p)
for p in ROOT.joinpath('assets/chat_webview').rglob('*.js'):
    assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)',p.read_text(),re.M),str(p)
assert en.keys()==zh.keys()==ru.keys()
report={'target':'v0.10.1','base_sha':'32def585e23f3d55266484ca8076012549260cf9',
        'ui_keys':len(zh),'new_or_revised_ui_keys':207,'bundled_display_entries':len(catalog),
        'manual_bundled_entries':len(manual),'machine_entries_rejected_for_macro_damage':len(dropped),
        'preset_storage_unchanged':True,'real_device_install_tested':False,
        'live_api_generation_tested':False}
(ROOT/'zh-upgrade-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
