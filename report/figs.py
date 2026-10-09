import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
R='../results'
S=json.load(open(f'{R}/summary.json'))
q=pd.read_csv(f'{R}/quality_per_instance.csv')
plt.rcParams.update({'font.family':'serif','font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':'#555','axes.labelcolor':'#222','xtick.color':'#444','ytick.color':'#444','axes.grid':True,
    'grid.color':'#e6e6e6','grid.linewidth':0.6,'legend.frameon':False,'lines.linewidth':1.6,'pdf.fonttype':42})
C={'native_dicke':'#2a78d6','penalty_tight':'#eb6834','native':'#1baf7a','penalty_auto':'#eda100','hea':'#e87ba4','random':'#8a8a8a'}
M={'native_dicke':'o','penalty_tight':'s','native':'^','penalty_auto':'D','hea':'v','random':''}
L={'native_dicke':'XY mixer, Dicke start','native':'XY mixer, basis start','penalty_tight':r'penalty, $P_{\rm tight}$',
   'penalty_auto':r'penalty, $P_{\rm auto}$','hea':'RealAmplitudes (HEA)','random':'uniform random $k$-subset'}
ORDER=['native_dicke','native','penalty_tight','penalty_auto']
def ci(key): return S['quality'][key]
# Figure 1
fig,ax=plt.subplots(1,2,figsize=(6.6,2.5))
ns=[8,10,12,14]
for m in ORDER+['random']:
    p=0 if m=='random' else 3
    v=np.array([ci(f'R|n={n}|{m}|p={p}|ratio_cond') for n in ns])
    ax[0].errorbar(ns,v[:,0],yerr=[v[:,0]-v[:,1],v[:,2]-v[:,0]],color=C[m],marker=M[m] or None,ms=4.5,capsize=2,
                   ls='--' if m=='random' else '-',label=L[m])
ax[0].set_xlabel('$n$ (candidate stations = qubits)'); ax[0].set_ylabel(r'$E[f/f^\star \mid$ feasible$]$'); ax[0].set_xticks(ns)
ax[0].set_title('(a) single-shot quality, family R, $p=3$',fontsize=8.5,loc='left')
Ss=[1,10,100,1000]
sub=q[(q.family=='R')&(q.n==12)]
for m in ORDER+['random']:
    p=0 if m=='random' else 3
    s=sub[(sub.method==m)&(sub.p==p)]
    ax[1].plot(Ss,[s[f'best_of_{k}'].mean() for k in Ss],color=C[m],marker=M[m] or None,ms=4.5,ls='--' if m=='random' else '-')
ax[1].set_xscale('log'); ax[1].set_xlabel('shots $S$'); ax[1].set_ylabel('E[best of $S$ shots]')
ax[1].set_title('(b) best-of-$S$ saturates, $n=12$, $p=3$',fontsize=8.5,loc='left')
fig.legend(*ax[0].get_legend_handles_labels(),loc='lower center',ncol=5,fontsize=7.2,bbox_to_anchor=(0.5,-0.04))
fig.tight_layout(rect=(0,0.09,1,1)); fig.savefig('fig_quality.pdf',bbox_inches='tight')
# Figure 2
sz=pd.read_csv(f'{R}/variance_size_scan.csv'); dp=pd.read_csv(f'{R}/variance_depth_scan.csv')
fig,ax=plt.subplots(1,2,figsize=(6.6,2.5))
for m in ORDER+['hea']:
    s=sz[(sz.statistic=='cost')&(sz.kind==m)]
    ax[0].errorbar(s.n,s['var'],yerr=[s['var']-s.ci_lo,s.ci_hi-s['var']],color=C[m],marker=M[m],ms=4.5,capsize=2,label=L[m])
    d=dp[(dp.statistic=='cost')&(dp.kind==m)]
    ax[1].errorbar(d.p,d['var'],yerr=[d['var']-d.ci_lo,d.ci_hi-d['var']],color=C[m],marker=M[m],ms=4.5,capsize=2)
for a in ax: a.set_yscale('log'); a.set_ylabel(r'Var$_\theta[E]$,  $E=\langle C\rangle/\|C\|_1$')
ax[0].set_xlabel('$n$'); ax[0].set_title('(a) size, $p=2$',fontsize=8.5,loc='left')
ax[1].set_xlabel('$p$'); ax[1].set_title('(b) depth, $n=12$',fontsize=8.5,loc='left')
fig.legend(*ax[0].get_legend_handles_labels(),loc='lower center',ncol=5,fontsize=7.2,bbox_to_anchor=(0.5,-0.04))
fig.tight_layout(rect=(0,0.09,1,1)); fig.savefig('fig_variance.pdf',bbox_inches='tight')
print('ok')
