#!/usr/bin/env python
# ======================================================================

import LensingFunc as LF
import Relations as Rel
import LensingProfiles as LP
import grid as GRID


import sys,getopt,atpy,pyfits
import pylab,matplotlib.pyplot as plt
import numpy
import numpy.random as rnd
from scipy import optimize
from scipy import stats

#import time

arcmin2rad = (1.0/60.0)*numpy.pi/180.0
rad2arcmin = 1.0/arcmin2rad

# ======================================================================

def smooth(zl,zs,catalogues,truncationscale=10,magnitudecut=99,band='r',nplanes=200,hardcut="RVir",cosmo=[0.25,0.75,0.73],scaling="tom",errors=True,grid=None,eMhalo=0.000000001):
   #print time.clock()
   if grid==None:
      lg=GRID.lensgrid(zl,zs,nplanes=nplanes,cosmo=cosmo)
      lg.populatelensgrid()
   else: lg=grid
   smoothcomponentindiv=numpy.zeros((lg.nplanes,len(catalogues)))
   smoothcomponent=numpy.zeros(lg.nplanes)
   
   #print "grid",time.clock() 


   if band == "u" or band ==  "g" or band == "r" or band ==  "i" or band == "z":
      col = "mag_SDSS_%s" % band
       #elif band == "F814" or band == "F814W" or band == "814" or band == 814:
       #    col = "mag_F814W"
   else:
      col = "mag_%s" % band

   i=0
   for datafile in catalogues:
      cat = datafile#atpy.Table(datafile, type='ascii')
      #print "cat read in", time.clock()

      xmax = cat['pos_0[rad]'].max()
      xmin = cat['pos_0[rad]'].min()
      ymax = cat['pos_1[rad]'].max()
      ymin = cat['pos_1[rad]'].min() 
      catarea=(xmax-xmin)*(ymax-ymin) #in square radians (steradians?)
      physicalarea=catarea*(lg.Da_p+1e-9)**2

      cat=cat.where(cat["%s"%col]<magnitudecut)

      M200 = cat['M_Subhalo[M_sol/h]']
      if errors == True:
         #print numpy.min(M200),numpy.max(M200)
         M200= 10**(numpy.log10(M200)+rnd.normal(0,eMhalo))
         #print numpy.min(M200),numpy.max(M200)
      #M200 = 10**(numpy.log10(cat['M_Subhalo[M_sol/h]'])*rnd.normal(1,0.5))
      c200 = Rel.MCrelation(M200,MCerror=errors)
      cat.add_column('NetoC', c200)
      snappedz,planes=lg.snap(cat['z_spec'])
      cat.add_column("snappedplane",planes)
      cat.add_column("snapped_redshift",snappedz)

      rhocrit=lg.rho_crit_p[planes]
      r200 = (3*M200/(800*3.14159*rhocrit))**(1./3)
      cat.add_column('r200TRUE', r200)

      rs = r200/c200
      rhos = LP.delta_c(c200)*rhocrit 

      if hardcut == "Rvir" or hardcut=="RVir" or hardcut == "r_vir" or hardcut == "rvir":
         R_trunc=truncationscale*r200
      elif hardcut == "rs" or hardcut=="Rs" or hardcut == "R_s" or hardcut == "r_s":
         R_trunc=truncationscale*rs
      else: print "what hardcut did you mean?"  


      mass=4*3.14159*rhos*(rs**3)  *     \
          (  numpy.log(1+(R_trunc)/rs) - \
                R_trunc/(rs+R_trunc)    \
                )
      cat.add_column('Mtrunc', mass)
      #print cat.Mtrunc

      for p in range(lg.nplanes):
         ontheplane=cat.where(cat.snappedplane==p)
         smoothcomponentindiv[p,i]=numpy.sum(ontheplane.Mtrunc)/physicalarea[p]
      i+=1

   for p in range(lg.nplanes):
      smoothcomponent[p]=numpy.sum(smoothcomponentindiv[p,:])/len(catalogues)
   
   lg.smoothcomponent=smoothcomponent
   lg.kappa=lg.smoothcomponent/lg.sigma_crit_p
   lg.kappaScaled=LF.KappaScale_beta(lg.beta_p,lg.kappa,0)
   lg.kappaScaled_keeton=LF.KappaScale_beta(lg.beta_p,lg.kappa,0,scaling="keeton")
   #plt.plot(lg.kappakeeton)
   #plt.show()

   
   if scaling == "keeton":
      print "smooth component correction is: ",numpy.sum(lg.kappaScaled)
      return numpy.sum(lg.kappaScaled_keeton)
   
   if scaling == "tom":
      print "smooth component correction is: ",numpy.sum(lg.kappa-(lg.beta_p*lg.kappa))
      return numpy.sum(lg.kappa-(lg.beta_p*lg.kappa))

#d1= "../../data/GGL_los_8_0_0_1_1_N_4096_ang_4_STARS_SA_galaxies_ANALYTIC_SA_galaxies_on_plane_27_to_63.images.txt"
#datafile=[d1]
#Smooth(0.6,1.4,datafile,truncationscale=5,nplanes=20)
   #print "finished",time.clock()


#test=False
test=False
#-------------------------------------------
if test ==True:
# Kappa Smooth as a function of magnitude cut:
   d1= "../../data/GGL_los_8_0_0_1_1_N_4096_ang_4_STARS_SA_galaxies_ANALYTIC_SA_galaxies_on_plane_27_to_63.images.txt"
   datafile=[ atpy.Table(d1, type='ascii')]
   """
   maglist=numpy.linspace(19,25,15,endpoint=True)
   smoothlist=numpy.zeros(len(maglist))
   for i in range(len(maglist)):
      magcut=maglist[i]
      smoothlist[i]=smooth(0.6,1.4,datafile,truncationscale=5,magnitudecut=magcut,band="i",nplanes=50)
   
   plt.plot(maglist,smoothlist)
   plt.xlabel("i band depth")
   plt.ylabel("$\kappa_{\mathrm{smooth}}$")
   plt.title("Truncation at 5 R$\mathrm{_{Vir}}$, $z_l = 0.6$, $z_s = 1.4$")
   plt.savefig("../figure3.png")
   plt.show()
   """
   n=1000
   smoothlist1=numpy.zeros(n)
   smoothlist2=numpy.zeros(n)
   smoothlist3=numpy.zeros(n)
   for i in range(n):
      smoothlist1[i]=smooth(0.6,1.4,datafile,truncationscale=3,nplanes=50,eMhalo=0.1)
      smoothlist2[i]=smooth(0.6,1.4,datafile,truncationscale=3,nplanes=50,eMhalo=0.3)
      smoothlist3[i]=smooth(0.6,1.4,datafile,truncationscale=3,nplanes=50,eMhalo=0.5)
      print i

   a= numpy.std(smoothlist1)
   b= numpy.std(smoothlist2)
   c= numpy.std(smoothlist3)

   bins=numpy.linspace(0,0.3,60)
   plt.subplot(311)
   plt.hist(smoothlist1,bins,label="$\sigma\mathrm{[Mhalo]}=0.1$")
   plt.legend(title="$\sigma(\kappa)$=%.3f"%a)
   plt.subplot(312)
   plt.hist(smoothlist2,bins,label="$\sigma\mathrm{[Mhalo]}=0.3$")
   plt.legend(title="$\sigma(\kappa)$=%.3f"%b)
   plt.subplot(313)
   plt.hist(smoothlist3,bins,label="$\sigma\mathrm{[Mhalo]}=0.5$")
   plt.legend(title="$\sigma(\kappa)$=%.3f"%c)
   plt.xlabel("$\kappa_{\mathrm{smooth}}$")
   plt.savefig("smoothvsmasserror")
   plt.show()
