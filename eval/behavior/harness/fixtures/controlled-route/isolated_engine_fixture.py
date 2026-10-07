#!/usr/bin/env python3
"""Finite source simulator. Records CLI arguments; NEVER executes tool command text."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

IMAGE = 'sha256:ee2c320efc696d510c4579d9d40d5e2ece061a6cd0adc4b966db84b581bc8be0'
FAULTS = (None, 'create_uncertain', 'cid_conflict', 'extra_mount', 'live_after_start', 'wrong_exit', 'bad_absence', 'finalize_stall')


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def image_record():
    return [dict(Id=IMAGE, Os='linux', Architecture='arm64',
        Config=dict(Volumes=None, Env=['PATH=/usr/local/bin:/usr/bin:/bin', 'LANG=C.UTF-8', 'PYTHON_VERSION=3.12.15']))]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',required=True)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    argv=args.command[1:] if args.command[:1]==['--'] else args.command
    assert argv and argv[0]=='/opt/homebrew/Cellar/docker/29.8.1/bin/docker'
    command=argv[1:]
    path=Path(args.state)
    state=json.loads(path.read_bytes())
    assert state['fault'] in FAULTS
    state.setdefault('commands',[]).append(command)
    def save():path.write_bytes(encoded(state))
    def output(value):sys.stdout.buffer.write(value);sys.stdout.buffer.flush()
    def error(value):sys.stderr.buffer.write(value);sys.stderr.buffer.flush()
    if command==['image','inspect',IMAGE]:
        save();output(encoded(image_record())+b'\n');return 0
    if command[0]=='create':
        assert 'container' not in state
        options={};mounts=[];index=1
        while index<len(command):
            part=command[index]
            if part=='--mount':
                fields=dict(x.split('=',1) if '=' in x else (x,True) for x in command[index+1].split(','))
                mounts.append(dict(Type='bind',Source=fields['src'],Destination=fields['dst'],RW='readonly' not in fields))
                index+=2;continue
            if not part.startswith('--'):break
            if '=' in part:
                key,value=part[2:].split('=',1)
                if key=='env':options.setdefault('env',[]).append(value)
                else:options[key]=value
            else:options[part[2:]]=True
            index+=1
        assert command[index]==IMAGE
        name=options['name'];cid=hashlib.sha256(name.encode()).hexdigest()
        env=dict(x.split('=',1) for x in image_record()[0]['Config']['Env'])
        env.update(dict(x.split('=',1) for x in options['env']))
        if state['fault']=='extra_mount':mounts.append(dict(Type='bind',Source=str(path.parent/'host-control'),Destination='/control',RW=True))
        state['container']=dict(Id=cid,Name='/'+name,Image=IMAGE,Mounts=mounts,
            Config=dict(Labels=dict([options['label'].split('=',1)]),User=options['user'],Tty=False,
                WorkingDir=options['workdir'],Entrypoint=[options['entrypoint']],Cmd=command[index+1:],
                Hostname=options['hostname'],Env=[key+'='+value for key,value in env.items()]),
            HostConfig=dict(NetworkMode=options['network'],ReadonlyRootfs=options['read-only'],Privileged=False,
                CapDrop=[options['cap-drop']],CapAdd=None,SecurityOpt=[options['security-opt']],IpcMode=options['ipc'],
                PidsLimit=int(options['pids-limit']),Memory=268435456,MemorySwap=268435456,NanoCpus=1000000000,
                LogConfig=dict(Type=options['log-driver']),Devices=[],DeviceRequests=None,GroupAdd=None,PortBindings=None,ExtraHosts=None),
            State=dict(Running=False,Pid=0,ExitCode=0,OOMKilled=False))
        Path(options['cidfile']).write_text(cid+'\n');save();output((cid+'\n').encode())
        if state['fault']=='create_uncertain':error(b'synthetic uncertain create\n');return 3
        return 0
    if command[:2]==['inspect','--type=container']:
        if 'container' not in state:
            save()
            if state['fault']=='bad_absence':error(b'synthetic unrelated engine failure\n');return 2
            output(b'[]\n');error(('Error: No such object: '+command[2]+'\n').encode());return 1
        container=state['container']
        assert command[2] in (container['Id'],container['Name'][1:])
        displayed=json.loads(json.dumps(container))
        if state['fault']=='cid_conflict':displayed['Id']='a'*64
        save();output(encoded([displayed])+b'\n');return 0
    if command[:3]==['start','--attach','--interactive']:
        container=state['container'];assert command[3]==container['Id']
        if container['Config']['Entrypoint']==['/bin/sh']:
            # Command text is retained above in create, but is never interpreted.
            stdout=base64.b64decode(state['stdout_b64'],validate=True)
            stderr=base64.b64decode(state['stderr_b64'],validate=True)
        else:
            request=json.loads(sys.stdin.buffer.read(1048577))
            assert request['schema']=='tackle-isolated-file-request/1'
            value=request['arguments'];kind=request['function_name']
            if kind=='Write':
                data=value['content'].encode();facts=dict(file_path=value['file_path'],bytes_written=len(data),content_sha256=hashlib.sha256(data).hexdigest())
                returned=encoded(facts)
            else:
                original=base64.b64decode(state.get('read_b64',''),validate=True)
                data=original[value['byte_offset']:value['byte_offset']+value['max_bytes']]
                facts=dict(file_path=value['file_path'],byte_offset=value['byte_offset'],requested_max_bytes=value['max_bytes'],
                    returned_bytes=len(data),content_utf8=data.decode(),content_sha256=hashlib.sha256(data).hexdigest(),
                    eof=value['byte_offset']+len(data)>=len(original));returned=data
            stdout=encoded(dict(schema='tackle-isolated-file-claim/1',request_id=request['request_id'],kind=kind,facts=facts,
                returned_utf8_b64=base64.b64encode(returned).decode(),returned_sha256=hashlib.sha256(returned).hexdigest(),complete=True))+b'\n'
            stderr=b''
        container['State'].update(Running=state['fault']=='live_after_start',Pid=444 if state['fault']=='live_after_start' else 0,
            ExitCode=state['exit_code'])
        save();output(stdout);error(stderr)
        return 1 if state['fault']=='wrong_exit' else state['exit_code']
    if command[0]=='wait':
        assert command[1]==state['container']['Id'];save();output((str(state['container']['State']['ExitCode'])+'\n').encode());return 0
    if command[0]=='kill':
        assert command[1]==state['container']['Id'];state['container']['State'].update(Running=False,Pid=0)
        save();output((command[1]+'\n').encode());return 0
    if command[:2]==['rm','--force']:
        assert command[2]==state['container']['Id'];del state['container'];save();output((command[2]+'\n').encode());return 0
    raise AssertionError('unknown synthetic CLI command')


if __name__=='__main__':
    if sys.argv[1:] == ['--finalization-control=stall']:
        import time
        time.sleep(120)
        raise SystemExit(0)
    if sys.argv[1:] == ['--finalization-control=fast']:
        sys.stdout.buffer.write(b'fixed own finalization control\n')
        raise SystemExit(0)
    raise SystemExit(main())
