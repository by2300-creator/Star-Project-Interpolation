"""One-time, audited P0010 -> P010 correction. Never change trial data or seed."""
from pathlib import Path
import csv
import io
import json
import hashlib

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
ARCHIVE=ROOT/'data/archive/P0010_label_correction_20261023'
stem='P0010_identification_s1_20261022_171637_367762'
prepared=[]
for kind in ('trials','presses'):
    src=ROOT/'data'/f'{stem}_{kind}.csv'
    dst=src.with_name(src.name.replace('P0010_','P010_',1))
    backup=ARCHIVE/src.name
    assert src.exists() and not dst.exists() and not backup.exists()
    raw=src.read_bytes()
    before=list(csv.reader(io.StringIO(raw.decode('utf-8'))))
    assert len(before)==309
    if kind=='trials':
        col=before[0].index('participant_id')
        assert all(row[col]=='P0010' for row in before[1:])
        assert raw.count(b',P0010,')==308
        changed=raw.replace(b',P0010,',b',P010,')
    else:
        assert 'participant_id' not in before[0] and b'P0010' not in raw
        col=None;changed=raw
    after=list(csv.reader(io.StringIO(changed.decode('utf-8'))))
    assert before[0]==after[0]
    for old,new in zip(before[1:],after[1:]):
        assert len(old)==len(new)
        for i,(a,b) in enumerate(zip(old,new)):
            assert b==('P010' if i==col else a)
    prepared.append((src,dst,backup,raw,changed,kind))

ARCHIVE.mkdir(parents=True,exist_ok=True)
log=[]
for src,dst,backup,raw,changed,kind in prepared:
    # Keep exact originals in archive, outside active-data discovery.
    with backup.open('xb') as f:f.write(raw)
    assert backup.read_bytes()==raw
    with dst.open('xb') as f:f.write(changed)
    assert dst.read_bytes()==changed
    # Remove the obsolete active copy only after both copies are verified.
    assert src.read_bytes()==raw
    src.unlink()
    log.append(dict(original_filename=src.name,corrected_filename=dst.name,
        archived_original=str(backup.relative_to(ROOT)),rows=308,
        changed_cells=308 if kind=='trials' else 0,
        changed_column='participant_id' if kind=='trials' else None,
        original_sha256=hashlib.sha256(raw).hexdigest(),corrected_sha256=hashlib.sha256(changed).hexdigest(),
        all_other_cells_identical=True))
(OUT/'id_correction_log.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))
