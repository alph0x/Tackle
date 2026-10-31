"""Owned local release processes and explicit candidate/runtime bindings."""
from pathlib import Path
import datetime,hashlib,json,os,signal,subprocess,time

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require_candidate(root,candidate,*,clean=True):
    root=Path(root).resolve(strict=True)
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=candidate:
        raise ValueError('candidate HEAD drift')
    if clean and subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True):
        raise ValueError('candidate worktree is not clean')
    return root

def probe(interpreter):
    selected=Path(interpreter).resolve(strict=True)
    output=subprocess.check_output([str(selected),'-I','-B','-c','import json,sys; print(json.dumps(list(sys.version_info[:3])))'],text=True,timeout=30)
    version=json.loads(output)
    return {'resolved':str(selected),'version':version,'binary_sha256':sha(selected)}

def stop_group(child,grace):
    errors=[]
    def send(sig):
        try:
            if os.name=='posix':os.killpg(child.pid,sig)
            elif sig==signal.SIGTERM:child.terminate()
            else:child.kill()
        except ProcessLookupError:pass
        except OSError as error:errors.append(str(error))
    send(signal.SIGTERM)
    try:child.wait(timeout=grace)
    except subprocess.TimeoutExpired:pass
    # Always address the group: its parent may already have exited while a
    # descendant retains inherited streams or ignores TERM.
    send(signal.SIGKILL)
    try:child.wait(timeout=grace)
    except subprocess.TimeoutExpired:errors.append('owned parent not reaped within kill grace')
    return errors

def capture(name,argv,cwd,out,*,env=None,timeout=600,grace=2,silent=False):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    stdout_path=out/(name+'.stdout');stderr_path=out/(name+'.stderr');meta=out/(name+'.json')
    if meta.exists() or stdout_path.exists() or stderr_path.exists():raise ValueError('capture destination already exists')
    record={'argv':[os.fsdecode(x) for x in argv],'cwd':str(Path(cwd).resolve()),'start':now(),'timeout_seconds':timeout,'timeout':False,'launch_error':None,'native_exit':None,'cleanup_errors':[]}
    child=None
    with stdout_path.open('xb') as stdout,stderr_path.open('xb') as stderr:
        try:
            child=subprocess.Popen(argv,cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            record['pid']=child.pid
            try:child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record['timeout']=True;record['cleanup_errors']=stop_group(child,grace)
            record['native_exit']=child.returncode
        except OSError as error:record['launch_error']=str(error)
    record['finish']=now();record['stdout_sha256']=sha(stdout_path);record['stderr_sha256']=sha(stderr_path)
    record['exit']=124 if record['timeout'] else (127 if record['native_exit'] is None else record['native_exit'])
    record['signal']=-record['native_exit'] if record['native_exit'] is not None and record['native_exit']<0 else None
    record['complete']=not record['timeout'] and record['launch_error'] is None and record['native_exit'] is not None and not record['cleanup_errors']
    record['passed']=record['complete'] and record['native_exit']==0 and (not silent or stdout_path.stat().st_size==stderr_path.stat().st_size==0)
    meta.write_text(json.dumps(record,indent=2)+'\n');return record

def registry(record,version,interpreter,candidate):
    record=Path(record).resolve(strict=True);data=json.loads(record.read_text());actual=probe(interpreter)
    if tuple(actual['version'])!=tuple(version):raise ValueError('selected interpreter version mismatch')
    if data.get('interpreter_identity')!=actual:raise ValueError('registry executable identity mismatch')
    if not data.get('argv') or Path(data['argv'][0]).resolve()!=Path(actual['resolved']):raise ValueError('registry argv interpreter mismatch')
    if data.get('revision')!=candidate or data.get('revision_after')!=candidate:raise ValueError('registry candidate mismatch')
    if type(data.get('exit')) is not int or data['exit']!=0 or data.get('passed') is not True or data.get('complete') is not True or data.get('timeout') is not False:
        raise ValueError('failed or incomplete registry')
    results=Path(data['results']).resolve(strict=True)
    if sha(results)!=data.get('results_sha256'):raise ValueError('registry result bytes drift')
    result=json.loads(results.read_text())
    if result.get('passed') is not True or result.get('complete') is not True:raise ValueError('registry result is not complete and passing')
    return {'record':str(record),'sha256':sha(record),'passed':True,'complete':True,'interpreter':actual,'candidate':candidate,'tests':result['tests']}
