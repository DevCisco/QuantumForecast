import json, numpy as np, pandas as pd
R='../results'
S=json.load(open(f'{R}/summary.json'))
g=lambda k: S['quality'][k]
def c3(t,d=3): return f'{t[0]:.{d}f} [{t[1]:.{d}f}, {t[2]:.{d}f}]'
L={'random':'uniform random $k$-subset','penalty_auto':'penalty, $P_{\\rm auto}$','penalty_tight':'penalty, $P_{\\rm tight}$',
   'native':'XY, basis start','native_dicke':'XY, Dicke start'}
out=[]
# Table 1: quality R n=12 and H n=12 at p=3
rows=[]
for m in ['random','penalty_auto','penalty_tight','native','native_dicke']:
    p=0 if m=='random' else 3
    r=g(f'R|n=12|{m}|p={p}|ratio_cond'); h=g(f'H|n=12|{m}|p={p}|ratio_cond')
    po=g(f'R|n=12|{m}|p={p}|p_opt')
    pf='1' if m=='random' else f"{g(f'R|n=12|{m}|p={p}|p_feasible')[0]:.2f}"
    rows.append(f"{L[m]} & {pf} & {c3(r)} & {c3(po)} & {c3(h)} \\\\")
out.append('\\newcommand{\\TabQuality}{'+'\n'.join(rows)+'}')
# Table 2: slopes
sl=pd.read_csv(f'{R}/variance_slopes.csv')
names={'penalty_auto':'penalty, $P_{\\rm auto}$','penalty_tight':'penalty, $P_{\\rm tight}$','native':'XY, basis start','native_dicke':'XY, Dicke start','hea':'RealAmplitudes (HEA)'}
rows=[]
for k,nm in names.items():
    a=sl[(sl.statistic=='cost')&(sl.kind==k)].iloc[0]; b=sl[(sl.statistic=='grad')&(sl.kind==k)].iloc[0]
    rows.append(f"{nm} & ${a.slope_ln_var_per_qubit:.2f}$ [${a.ci_lo:.2f}$, ${a.ci_hi:.2f}$] & ${b.slope_ln_var_per_qubit:.2f}$ [${b.ci_lo:.2f}$, ${b.ci_hi:.2f}$] \\\\")
out.append('\\newcommand{\\TabSlopes}{'+'\n'.join(rows)+'}')
# Table 3: two-qubit gates
cost=pd.read_csv(f'{R}/hardware_cost_fakemarrakesh.csv'); c1=cost[cost.opt_level==1]
rows=[]
for n in [8,10,12,14]:
    cells=[]
    for p in [1,2,3]:
        a=c1[(c1.n==n)&(c1.p==p)&(c1.ansatz=='penalty')].two_qubit_gates.mean(); b=c1[(c1.n==n)&(c1.p==p)&(c1.ansatz=='native')].two_qubit_gates.mean()
        cells.append(f"{a:.0f} / {b:.0f} ({a/b:.2f})")
    rows.append(f"{n} & "+' & '.join(cells)+" \\\\")
out.append('\\newcommand{\\TabCost}{'+'\n'.join(rows)+'}')
# Table 4: hardware
hw=pd.read_csv(f'{R}/hardware_reanalysis.csv').set_index('circuit'); emu=pd.read_csv(f'{R}/hardware_noisy_emulation.csv').set_index('circuit')
rows=[]
for lab,r in hw.iterrows():
    kind,p=lab.split('_p'); kn='penalty' if kind=='penalty' else 'XY (basis)'
    rows.append(f"{kn}, $p={p}$ & {r['hardware best-of-top10 (archived)']} & {r['simulator best-of-top10 (mean)']:.1f} {r['simulator 95% range']} & {r['P(uniform >= hardware)']:.2f} & {r['simulator E[ratio|feasible]']:.2f} & {emu.loc[lab,'p_feasible']:.3f} & {emu.loc[lab,'p_feasible (mitigated)']:.3f} \\\\")
out.append('\\newcommand{\\TabHW}{'+'\n'.join(rows)+'}')
# macros for text
base=pd.read_csv(f'{R}/classical_baselines.csv'); lam=pd.read_csv(f'{R}/qubo_lambda_sweep.csv')
pair=pd.read_csv(f'{R}/quality_paired_tests.csv'); rc=pair[pair.metric=='ratio_cond']
dk=rc[rc.comparison=='native_dicke - penalty_tight']; bs=rc[rc.comparison=='native - penalty_tight']
nu=hw['uniform-noise best-of-top10 (mean)'].iloc[0]
lamex=lam[lam['lambda']==1.0].groupby('family')['exact'].mean()
lam0=lam[lam['lambda']==0.0].groupby('family')['exact'].mean()
ws=pd.read_csv(f'{R}/appendixD_warm_start.csv'); w3=ws[ws.p==3].groupby(['family','variant'])['ratio_cond'].mean()
ma=pd.read_csv(f'{R}/appendixC_ma_qaoa.csv')
mac={
 'NR': S['n_instances']['R'], 'NH': S['n_instances']['H'], 'HardRate': f"{100*S['hard_family_acceptance_rate']:.1f}",
 'DickeWins': int(dk.wins.sum()), 'DickeTot': int((dk.wins+dk.losses).sum()), 'BasisSig': int((bs.wilcoxon_p<0.05).sum()), 'BasisTot': len(bs),
 'RandBestK': f"{g('R|n=12|random|p=0|best_of_1000')[0]:.3f}", 'PenBestK': f"{g('R|n=12|penalty_tight|p=3|best_of_1000')[0]:.3f}",
 'PenTopOne': f"{g('R|n=12|penalty_tight|p=1|ratio_top1')[0]:.2f}",
 'NullMean': f"{nu:.1f}", 'GreedyFailR': int((base[base.family=='R'].greedy<1).sum()),
 'GreedyH': f"{base[base.family=='H'].greedy.mean():.3f}", 'LPH': f"{base[base.family=='H'].lp_topk.mean():.3f}",
 'LamSparse': f"{100*lamex['sparse (radius 2.2)']:.1f}", 'LamDense': f"{100*lamex['dense (radius 3.0)']:.1f}",
 'LamZeroSparse': f"{100*lam0['sparse (radius 2.2)']:.0f}", 'LamZeroDense': f"{100*lam0['dense (radius 3.0)']:.0f}",
 'WsR': f"{w3[('R','warm start')]:.3f}", 'StdR': f"{w3[('R','standard')]:.3f}", 'WsH': f"{w3[('H','warm start')]:.3f}", 'StdH': f"{w3[('H','standard')]:.3f}",
 'MaStdOne': f"{ma[(ma.ansatz=='standard QAOA')&(ma.p==1)].var_cost.iloc[0]:.1e}", 'MaStdFortyFive': f"{ma[(ma.ansatz=='standard QAOA')&(ma.p==45)].var_cost.iloc[0]:.1e}",
 'MaOne': f"{ma[(ma.ansatz=='ma-QAOA')&(ma.p==1)].var_cost.iloc[0]:.1e}",
}
def sci(x):
    m,e=f'{float(x):.1e}'.split('e'); return f'${m}\\times10^{{{int(e)}}}$'
for k in ['MaStdOne','MaStdFortyFive','MaOne']: mac[k]=sci(mac[k])
for k,v in mac.items(): out.append(f'\\newcommand{{\\{k}}}{{{v}}}')
open('numbers.tex','w').write('\n'.join(out)+'\n'); print(open('numbers.tex').read()[-1500:])
