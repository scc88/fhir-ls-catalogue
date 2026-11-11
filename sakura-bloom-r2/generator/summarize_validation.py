import json,collections,sys,re
d=json.load(open(sys.argv[1]))
sev=collections.Counter(); msgs=collections.Counter(); files=set()
for e in d.get('entry',[]):
    oo=e['resource']
    f=[x.get('valueString') for x in oo.get('extension',[]) if 'valueString' in x]
    for i in oo.get('issue',[]):
        if i['severity'] in('error','fatal','warning'):
            m=i.get('details',{}).get('text','')
            m=re.sub(r"'[^']*'","'…'",m); m=re.sub(r"\(at [^)]*\)","",m); m=re.sub(r"http\S+","URL",m)
            sev[i['severity']]+=1; msgs[(i['severity'],m[:200])]+=1
print(sev)
for k,v in msgs.most_common(60): print(v,k)
