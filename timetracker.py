#!/usr/bin/env python3
"""timetracker - Simple time tracking CLI."""
import json, argparse, os, time, sys

DB = os.path.expanduser('~/.timetracker.json')

def load():
    if os.path.exists(DB):
        with open(DB) as f: return json.load(f)
    return {'current': None, 'entries': []}

def save(data):
    with open(DB, 'w') as f: json.dump(data, f, indent=2)

def fmt_dur(seconds):
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {s:02d}s"

def main():
    p = argparse.ArgumentParser(description='Time tracker')
    sub = p.add_subparsers(dest='cmd')
    
    st = sub.add_parser('start', help='Start tracking')
    st.add_argument('task')
    st.add_argument('-t', '--tags', nargs='*', default=[])
    
    sp = sub.add_parser('stop', help='Stop tracking')
    
    ss = sub.add_parser('status', help='Current status')
    
    ls = sub.add_parser('list', help='List entries')
    ls.add_argument('-n', type=int, default=20)
    ls.add_argument('--today', action='store_true')
    ls.add_argument('--tag', help='Filter by tag')
    
    sm = sub.add_parser('summary', help='Time summary')
    sm.add_argument('--today', action='store_true')
    sm.add_argument('--week', action='store_true')
    
    args = p.parse_args()
    if not args.cmd: args.cmd = 'status'
    
    data = load()
    
    if args.cmd == 'start':
        if data['current']:
            # Auto-stop previous
            entry = data['current']
            entry['end'] = time.time()
            entry['duration'] = entry['end'] - entry['start']
            data['entries'].append(entry)
        data['current'] = {
            'task': args.task, 'tags': args.tags,
            'start': time.time(), 'start_str': time.strftime('%Y-%m-%d %H:%M')
        }
        save(data)
        print(f"▶ Started: {args.task}")
    
    elif args.cmd == 'stop':
        if not data['current']:
            print("Nothing to stop."); return
        entry = data['current']
        entry['end'] = time.time()
        entry['duration'] = entry['end'] - entry['start']
        entry['end_str'] = time.strftime('%Y-%m-%d %H:%M')
        data['entries'].append(entry)
        data['current'] = None
        save(data)
        print(f"⏹ Stopped: {entry['task']} ({fmt_dur(entry['duration'])})")
    
    elif args.cmd == 'status':
        if data['current']:
            c = data['current']
            elapsed = time.time() - c['start']
            print(f"▶ {c['task']} — {fmt_dur(elapsed)} (since {c['start_str']})")
        else:
            print("⏸ Not tracking")
    
    elif args.cmd == 'list':
        entries = data['entries']
        if args.today:
            today = time.strftime('%Y-%m-%d')
            entries = [e for e in entries if e.get('start_str', '').startswith(today)]
        if args.tag:
            entries = [e for e in entries if args.tag in e.get('tags', [])]
        for e in entries[-args.n:]:
            tags = ' '.join(f'#{t}' for t in e.get('tags', []))
            print(f"  {e.get('start_str','?'):<18} {fmt_dur(e['duration']):>8}  {e['task']} {tags}")
    
    elif args.cmd == 'summary':
        entries = data['entries']
        if args.today:
            today = time.strftime('%Y-%m-%d')
            entries = [e for e in entries if e.get('start_str', '').startswith(today)]
        elif args.week:
            week_ago = time.time() - 604800
            entries = [e for e in entries if e.get('start', 0) >= week_ago]
        
        by_task = {}
        for e in entries:
            by_task[e['task']] = by_task.get(e['task'], 0) + e.get('duration', 0)
        
        total = sum(by_task.values())
        for task, dur in sorted(by_task.items(), key=lambda x: -x[1]):
            pct = dur / total * 100 if total else 0
            print(f"  {fmt_dur(dur):>10}  ({pct:>5.1f}%)  {task}")
        print(f"\n  Total: {fmt_dur(total)}")

if __name__ == '__main__':
    main()
