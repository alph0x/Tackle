"""Bounded local release edits; no Git commit, tag, network or publication."""
import atexit,argparse,hashlib,json,sys
from pathlib import Path

import importlib.util
_support_spec=importlib.util.spec_from_file_location('release_support',Path(__file__).with_name('release_support.py'))
support=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(support)
parser=argparse.ArgumentParser()
parser.add_argument('--config',required=True)
for name in ('repo','workspace','candidate','records','version','from-version','part'):
    parser.add_argument('--'+name,required=True)
args=parser.parse_args();
_config_spec=importlib.util.spec_from_file_location('release_config',Path(__file__).with_name('config.py'));config=importlib.util.module_from_spec(_config_spec);_config_spec.loader.exec_module(config);cfg=config.load(args.config)
if args.version != cfg['version'] or Path(args.workspace).resolve() != Path(cfg['workspace']).resolve():raise SystemExit('configuration version or workspace mismatch')
root=Path(args.repo).resolve(strict=True)
workspace=Path(args.workspace).resolve(strict=True);records=Path(args.records)
OLD,NEW=args.from_version,args.version;part=args.part
if NEW!=cfg['version'] or OLD!=cfg['from_version']:raise SystemExit('release version mismatch')
if root==workspace.parents[2]:raise SystemExit('editor refuses source checkout')
import subprocess
if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=args.candidate:
    raise SystemExit('candidate HEAD mismatch')
support.require_candidate(root,args.candidate)
if records.exists():raise SystemExit('record destination must be new')
ORIG,DONE={},[]
def remember(path):
    ORIG.setdefault(path, path.read_bytes() if path.exists() else None)


@atexit.register
def rollback():
    """A part that stops after its first write restores every file it touched: a failed run leaves no half edit."""
    if not DONE:
        for path, data in ORIG.items():
            if data is None:path.unlink(missing_ok=True)
            else:path.write_bytes(data)
        if ORIG:
            print('rolled back %d file(s); nothing written' % len(ORIG), file=sys.stderr)


def check(plan):
    for rel, old, new in plan:
        found = (root / rel).read_text().count(old)
        if found != 1:
            raise SystemExit('%s: expected 1 of %r, found %d; nothing written' % (rel, old[:70], found))


def apply(plan):
    check(plan)
    for rel, old, new in plan:
        p = root / rel
        remember(p)
        p.write_text(p.read_text().replace(old, new))


def load_cud():
    sys.path.insert(0, str(root / 'eval/rules'))
    import check_unit_diff as cud  # noqa: E402
    return cud


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class Dispositions:
    """Unit dispositions of the changed version text: re-derive live notes, add one `reworded` record per unit."""

    def __init__(self, replacements, reason):
        self.cud = load_cud()
        self.replacements = replacements      # [(old fragment, new fragment)] tried in order on a unit or note
        self.reason = reason
        self.path = root / 'eval/rules/unit-dispositions.json'
        self.text = self.path.read_text()
        self.data = json.loads(self.text)
        if json.dumps(self.data, indent=2, ensure_ascii=True) + '\n' != self.text:
            raise SystemExit('unit-dispositions.json: unexpected formatting; nothing written')
        self.records = self.data['records']
        self.base = self.cud.resolve_base(root, 'auto')
        self.fixed = 0
        self.dropped_added = 0
        self.added = 0
        self.allowed = set(self.cud.check_tokens(OLD, NEW, []))

    def holds(self, dest_path, note):
        """The destination holds the note, projected exactly as the unit gate projects it."""
        cud = self.cud
        dest = cud.read_current(root, dest_path)
        if dest is None:
            return False
        texts = cud.catalog_texts(dest) if dest_path == cud.CATALOG_PATH else [dest]
        return any(cud.collapse(note) in cud.collapse(x) for x in texts)

    def derive(self, text, dest_path):
        """The first replacement of the old version text that the destination holds, else None."""
        for old, new in self.replacements:
            if old in text:
                candidate = text.replace(old, new)
                if self.holds(dest_path, candidate):
                    return candidate
        return None

    def excuse(self, rec, removed_text):
        """Add a dropped entry for each version token the note no longer carries, and nothing else."""
        missing = self.cud.check_tokens(removed_text, rec['note'], rec.get('dropped'))
        if not set(missing) <= self.allowed:
            raise SystemExit('dropped tokens beyond the version in %s:%s: %s' % (rec['path'], rec['line'], missing))
        for token in missing:
            rec.setdefault('dropped', []).append({'token': token, 'reason': self.reason})
            self.dropped_added += 1

    def rederive_live_notes(self):
        cud = self.cud
        for rec in self.records:
            note = rec.get('note')
            if rec['disposition'] != 'reworded' or not note or not any(old in note for old,new in self.replacements) or self.holds(rec['destination'], note):
                continue
            new_note = self.derive(note, rec['destination'])
            if new_note is None:
                raise SystemExit('underivable note for %s:%s' % (rec['path'], rec['line']))
            rec['note'] = new_note
            removed = cud.recover_removed_text(root, self.base, rec['path'], rec['unit_sha256'])
            if removed is not None:
                self.excuse(rec, removed)
            self.fixed += 1

    def account(self, files):
        """files: covered paths. One record per removed unit that quotes the old version and has none yet."""
        cud = self.cud
        known = {(r['path'], r['unit_sha256']) for r in self.records}
        for path in files:
            base_text, now = cud.git_show(root, self.base, path), cud.read_current(root, path)
            if base_text is None:
                continue
            for line, unit in cud.removed_units_for_file(base_text, now, path):
                uh = cud.sha(unit)
                if (path, uh) in known:
                    continue
                note = self.derive(unit, path)
                if note is None:
                    raise SystemExit('no exact note for %s:%s' % (path, line))
                rec = {'path': path, 'line': line, 'unit_sha256': uh, 'disposition': 'reworded', 'destination': path,
                       'note': note, 'destination_unit_sha256': None}
                self.excuse(rec, unit)
                self.records.append(rec)
                known.add((path, uh))
                self.added += 1

    def write(self):
        text = json.dumps(self.data, indent=2, ensure_ascii=True) + '\n'
        json.loads(text)
        remember(self.path)
        self.path.write_text(text)
        print('dispositions: %d live notes re-derived, %d records added, %d dropped-token entries added'
              % (self.fixed, self.added, self.dropped_added))


if part=='format':
    # Layout only: the file must parse to the same data before and after, and only its JSON layout may change.
    path=root/'eval/rules/unit-dispositions.json';text=path.read_text();data=json.loads(text)
    canonical=json.dumps(data,indent=2,ensure_ascii=True)+'\n'
    if text==canonical:raise SystemExit('unit-dispositions.json is already canonical; nothing written')
    if json.loads(canonical)!=data or list(json.loads(canonical))!=list(data):raise SystemExit('canonical form changes data')
    remember(path);path.write_text(canonical)
elif part=='stamp':
    plan=[('skills/tackle/SKILL.md','**Tackle '+OLD+'** is a model-agnostic','**Tackle '+NEW+'** is a model-agnostic'),
      ('skills/tackle/references/AGENTS.tmpl.md','**Methodology: Tackle '+OLD+'**','**Methodology: Tackle '+NEW+'**'),
      ('skills/tackle/references/README.tmpl.md','> **Methodology: Tackle '+OLD+'.**','> **Methodology: Tackle '+NEW+'.**')]
    apply(plan)
    d=Dispositions([('Tackle '+OLD,'Tackle '+NEW)],'release version stamp bumped to '+NEW)
    d.rederive_live_notes();d.account([x[0][len('skills/tackle/'):] for x in plan]);d.write()
elif part=='changelog':
    entry=Path(cfg['changelog']['path']);report=Path(cfg['record']['path'])
    if hashlib.sha256(entry.read_bytes()).hexdigest()!=cfg['changelog']['sha256'] or hashlib.sha256(report.read_bytes()).hexdigest()!=cfg['record']['sha256']:
        raise SystemExit('release prose drift')
    destination=root/cfg['record']['destination']
    if destination.exists() or destination.is_symlink():raise SystemExit('release report already exists')
    head='# Tackle changelog\n\n## Tackle '+OLD+'\n'
    replacement='# Tackle changelog\n\n'+entry.read_text()+'\n## Tackle '+OLD+'\n'
    apply([('CHANGELOG.md',head,replacement)])
    remember(destination);destination.write_bytes(report.read_bytes())
    claims=root/'eval/records/claims.json';text=claims.read_text();data=json.loads(text)
    if json.dumps(data,indent=1,ensure_ascii=False)+'\n'!=text:raise SystemExit('claims.json: unexpected formatting; nothing written')
    if any(c.get('section')=='Tackle '+NEW for c in data['claims']):raise SystemExit('claims for the release already exist')
    data['claims'][0:0]=cfg['claims'];remember(claims);claims.write_text(json.dumps(data,indent=1,ensure_ascii=False)+'\n')
elif part=='migrate':
    g='skills/tackle/references/guides/';c='skills/tackle/scripts/migrate/compact.py';k='maintaining/check_migration_catalog.py'
    plan=[(g+'migration-catalog.json','"target_methodology": "'+OLD+'"','"target_methodology": "'+NEW+'"'),
      (g+'migration-catalog.json','"revision": '+str(cfg['catalog_revision'][0])+',','"revision": '+str(cfg['catalog_revision'][1])+','),
      (g+'migration-catalog.json','set the `**Methodology: Tackle '+OLD+'**` line in the candidate AGENTS.md only','set the `**Methodology: Tackle '+NEW+'**` line in the candidate AGENTS.md only'),
      (c,'catalog["revision"] != '+str(cfg['catalog_revision'][0]),'catalog["revision"] != '+str(cfg['catalog_revision'][1])),
      (c,'catalog["target_methodology"] != "'+OLD+'"','catalog["target_methodology"] != "'+NEW+'"'),
      (c,'context["target"] != "'+OLD+'"','context["target"] != "'+NEW+'"'),
      (c,'args.target != "'+OLD+'"','args.target != "'+NEW+'"'),
      (k,'cat["revision"] != '+str(cfg['catalog_revision'][0]),'cat["revision"] != '+str(cfg['catalog_revision'][1])),
      (k,'cat["target_methodology"] != "'+OLD+'"','cat["target_methodology"] != "'+NEW+'"'),
      (k,'`**Methodology: Tackle '+OLD+'**` line in the candidate AGENTS.md only','`**Methodology: Tackle '+NEW+'**` line in the candidate AGENTS.md only'),
      (k,"'Z-final-stamp': ['**Methodology: Tackle "+OLD+"**']","'Z-final-stamp': ['**Methodology: Tackle "+NEW+"**']"),
      (k,'"migration-catalog.json", "Tackle '+OLD+'",','"migration-catalog.json", "Tackle '+NEW+'",'),
      (g+'migrate.md','supported workspace structure to Tackle '+OLD+'.','supported workspace structure to Tackle '+NEW+'.'),
      (g+'migrate.md','--target '+OLD+' --context','--target '+NEW+' --context'),
      ('MAINTAINING.md','supported workspace structures to '+OLD+'.','supported workspace structures to '+NEW+'.')]
    check(plan)
    apply(plan)
    script=root/c;manifest=root/'skills/tackle/scripts/README.md';remember(manifest)
    prefix='| [migrate/compact.py](migrate/compact.py) | `';text=manifest.read_text()
    assert text.count(prefix)==1;at=text.index(prefix)+len(prefix);assert text[at+64]=='`'
    assert text[at:at+64]==hashlib.sha256(ORIG[script]).hexdigest()
    manifest.write_text(text[:at]+hashlib.sha256(script.read_bytes()).hexdigest()+text[at+64:])
    d=Dispositions([('Tackle '+OLD,'Tackle '+NEW),('to '+OLD,'to '+NEW),('--target '+OLD,'--target '+NEW),
      (hashlib.sha256(ORIG[script]).hexdigest(),hashlib.sha256(script.read_bytes()).hexdigest())],
      'migration catalog target bumped to '+NEW)
    d.rederive_live_notes();d.account(['references/guides/migrate.md','references/guides/migration-catalog.json','MAINTAINING.md','skills/tackle/scripts/README.md']);d.write()
elif part=='readme':
    if json.loads((root/'skills/tackle/references/guides/migration-catalog.json').read_text())['target_methodology']!=NEW:raise SystemExit('catalog target mismatch')
    apply([('README.md','**Tackle '+OLD+'** · Model-agnostic','**Tackle '+NEW+'** · Model-agnostic'),
      ('README.md',"Tackle.git#v"+OLD+"' --skill tackle","Tackle.git#v"+NEW+"' --skill tackle"),
      ('README.md','have not been probed for '+OLD+'.','have not been probed for '+NEW+'.'),
      ('README.md','migration catalog targets Tackle '+OLD+' and','migration catalog targets Tackle '+NEW+' and')])
else:raise SystemExit('unsupported sealed release part')
allowed={'format': {'eval/rules/unit-dispositions.json'}, 'stamp': {'skills/tackle/SKILL.md', 'skills/tackle/references/README.tmpl.md', 'eval/rules/unit-dispositions.json', 'skills/tackle/references/AGENTS.tmpl.md'}, 'changelog': {cfg['record']['destination'], 'CHANGELOG.md', 'eval/records/claims.json'}, 'migrate': {'skills/tackle/references/guides/migration-catalog.json', 'MAINTAINING.md', 'maintaining/check_migration_catalog.py', 'eval/rules/unit-dispositions.json', 'skills/tackle/scripts/README.md', 'skills/tackle/scripts/migrate/compact.py', 'skills/tackle/references/guides/migrate.md'}, 'readme': {'README.md'}}
changed=set(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=root,text=True).splitlines())
changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=root,text=True).splitlines())
support.require_candidate(root,args.candidate,clean=False)
if changed!=allowed[part]:raise SystemExit('release part changed unexpected or incomplete paths: '+repr(sorted(changed)))
records=records.resolve()
records.mkdir(parents=True)
receipt={'candidate':args.candidate,'version':NEW,'part':part,'files':{str(x.relative_to(root)):{'before':hashlib.sha256(raw).hexdigest() if raw is not None else None,'after':hashlib.sha256(x.read_bytes()).hexdigest()} for x,raw in ORIG.items()},'publication':False}
raw=json.dumps(receipt,indent=2)+'\n';(records/'receipt.json').write_text(raw)
assert (records/'receipt.json').read_text()==raw
DONE.append(True)
