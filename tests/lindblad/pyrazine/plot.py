from pylab import *

dalb = loadtxt('pyr2_lindblad.dat')
plot(dalb[:,0],dalb[:,1],'-b')
plot(dalb[:,0],dalb[:,2],'-r')
#da = loadtxt('db_pops_lindblad_jumps.dat')
#times = arange(0.0,1000.,1.0)
#plot(times,da[:,0],'--b',mfc='none',markevery=25)
#plot(times,da[:,1],'--r',mfc='none',markevery=25)
#plot(times,da[:,0],'ob',mfc='none',markevery=25)
#plot(times,da[:,1],'or',mfc='none',markevery=25)
#da = loadtxt('db_pops_lin_qsd.dat')
#plot(da[:,0],da[:,1])
#plot(da[:,0],da[:,2])
#da = loadtxt('db_pops_nonlin_qsd.dat')
#plot(da[:,0],da[:,1])
#plot(da[:,0],da[:,2])
xlim(0.,1000.)
ylim(0.,1.)
show()
#da = loadtxt('db_pops_lindblad.dat')
#plot(da[:,0],da[:,1]+da[:,2])
##da = loadtxt('db_pops_lin_qsd.dat')
##plot(da[:,0],da[:,1]+da[:,2])
#da = loadtxt('db_pops_nonlin_qsd.dat')
#plot(da[:,0],da[:,1]+da[:,2])
#xlim(0.,1000.)
#ylim(-0.1,1.1)
#show()
