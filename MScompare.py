#!/usr/bin/env python
# ======================================================================

import Pangloss

import sys,getopt,atpy,pyfits
import pylab,matplotlib.pyplot as plt
import numpy
import numpy.random as rnd
import distances
from scipy import optimize
from scipy import stats
import cPickle

arcmin2rad = (1.0/60.0)*numpy.pi/180.0
rad2arcmin = 1.0/arcmin2rad

N_45mean = 41.8
N_60mean = 74.475
N_90mean = 166.864
N_30mean = 18.831
N_15mean = 4.812

# ======================================================================

def MScompare(argv):
   """
   NAME
     MScompare.py

   PURPOSE
     Compare reconstructed convergence with "true" convergence for a set of 
     lightcones. Truth comes from Stefan Hilbert's ray tracing work in 
     the Millenium Simulation, in the form of a pixellated convergence
     map. Reconstructions are made from simulated catalogs in the same
     field. 

   COMMENTS

   FLAGS
     -u            Print this message [0]

   INPUTS
     catalog       Catalog containing halos, stellar mass distributions etc
     kappafile     FITS file containing true kappa values.

   OPTIONAL INPUTS
     -n Ncones     No. of cones to compare
     -r Rcone      Cone radius used in reconstruction
     -zd zd        Deflector redshift (to match kappafile)
     -zs zs        Source redshift (to match kappafile)
     -t truncationscale number of virial radii to truncate NFW halos at.

   OUTPUTS
     stdout        Useful information
     pngfiles      Output plots in png format

   EXAMPLES

     MScompare.py -n 1000 catalog.txt kappa.fits

   BUGS

   AUTHORS
     This file is part of the Pangloss project.
     Copyright 2012 Tom Collett (IoA) and Phil Marshall (Oxford).
     
   HISTORY
     2012-04-06 started Marshall (Oxford)
   """

   # --------------------------------------------------------------------

   try:
      opts, args = getopt.getopt(argv,"hvn:r:",["help","verbose","zd","zs"])
   except getopt.GetoptError, err:
      print str(err) # will print something like "option -a not recognized"
      print MScompare.__doc__  # will print the big comment above.
      return

   vb = False
   Ncones = 1000
   Rcone = 6 # arcmin
   truncationscale=3   # *R_200 halo truncation
  
   # Defaults are for B1608 (CHECK):
   zl = 0.62
   zs = 1.39
  
   for o,a in opts:
      if o in ("-v", "--verbose"):
         vb = True
      elif o in ("-n"):
         Ncones = int(a)
      elif o in ("-r"):
         Rcone = a
      elif o in ("-t"):
         truncationscale = a 

      elif o in ("--zl"):
         zl = a
      elif o in ("--zs"):
         zs = a
      elif o in ("-h", "--help"):
         print MScompare.__doc__
         return
      else:
         assert False, "unhandled option"

   # Check for datafiles in array args:
   if len(args) == 2:
      catalog = args[0]
      kappafile = args[1]
      if vb:
         print "Reconstructing convergence in lightcones from:",catalog
         print "Comparing to convergence in:",kappafile
         print "Number of lightcones to be reconstructed:",Ncones
   else:
      print MScompare.__doc__
      return

   # --------------------------------------------------------------------

   # Read in master catalog, and kappa map:
    
   master = atpy.Table(catalog, type='ascii')
   if vb: print "Read in master catalog, length",len(master)

   xmax = master['pos_0[rad]'].max()
   xmin = master['pos_0[rad]'].min()
   ymax = master['pos_1[rad]'].max()
   ymin = master['pos_1[rad]'].min()
   if vb: print "Catalog extent:",xmin,xmax,ymin,ymax
    
   MSconvergence = Pangloss.kappamap(kappafile)
   if vb: print "Read in true kappa map, dimension",MSconvergence.NX


   # Calculate kappasmooth
   data=["%s"%catalog]
   kappa_empty = Pangloss.smooth(zl,zs,data,truncationscale=truncationscale,hardcut="RVir",nplanes=100,scaling="keeton")
   kappa_empty_tom= Pangloss.smooth(zl,zs,data,truncationscale=truncationscale,hardcut="RVir",nplanes=100,scaling="tom")

   # --------------------------------------------------------------------

   # Generate Ncones random positions, and reconstruct kappa_keeton in
   # each one. Also look up true kappa_hilbert at that position:
   
   x = rnd.uniform(xmin+Rcone*arcmin2rad,xmax-Rcone*arcmin2rad,Ncones)
   y = rnd.uniform(ymin+Rcone*arcmin2rad,ymax-Rcone*arcmin2rad,Ncones)
   


   kappa_Scaled = numpy.zeros(Ncones)
   kappa_tom = numpy.zeros(Ncones)
   kappa_hilbert = numpy.zeros(Ncones)
   N_45 = numpy.zeros(Ncones)
   N_60 = numpy.zeros(Ncones)
   N_90 = numpy.zeros(Ncones)
   N_30 = numpy.zeros(Ncones)
   N_15 = numpy.zeros(Ncones)
   other = numpy.zeros(Ncones)
   other2 = numpy.zeros(Ncones)
   
   Rbins=numpy.linspace(0,Rcone,30,endpoint=True)
   kappa_Scaled_R=numpy.zeros((len(Rbins),Ncones))
   delta_kappa_R=numpy.zeros((len(Rbins),Ncones))


   for k in range(Ncones):
      if k % 100 == 0: print ("evaluating cone %i of %i" %(k,Ncones))
      xc = [x[k],y[k]]

      # Truth:
      kappa_hilbert[k] = MSconvergence.at(y[k],x[k],coordinate_system='physical')
      # THE CATALOGUES NEED TRANSPOSING!!!! (don't make that mistake again!)

      # Reconstruction:
      lc = Pangloss.lens_lightcone(master,Rcone,xc,zl,zs,nplanes=100)
      col="mag_SDSS_i"
      magcutcat=lc.galaxies.where((lc.galaxies["%s"%col] < 22))
      other[k]=numpy.min(magcutcat.rphys)
      other2[k]=numpy.min(lc.galaxies.rphys)
      
      lc.make_kappa_contributions(hardcut="RVir",truncationscale=truncationscale,scaling="tom")
      kappa_Scaled[k] = lc.kappa_Scaled_total-kappa_empty
      kappa_tom[k] = numpy.sum((1-lc.galaxies.beta)*lc.galaxies.kappa)-kappa_empty_tom


      # calculate for smaller Rcone.
      for j in range(len(Rbins)):
         mc=lc.galaxies.where(lc.galaxies.r<Rbins[j])
         kappa_Scaled_R[j,k]=numpy.sum(mc.kappa_Scaled)-kappa_empty
         delta_kappa_R[j,k]=numpy.sum(mc.kappa_Scaled)-kappa_empty-kappa_hilbert[k]

   # --------------------------------------------------------------------
   # Basic statistics of two arrays:
   
   difference = kappa_Scaled - kappa_hilbert
   bias = numpy.average(difference)
   scatter = numpy.std(difference)
   difference2 = kappa_tom - kappa_hilbert
   scatter2 = numpy.std(difference2)
   bias2 = numpy.average(difference2)

   y=difference
   x=kappa_Scaled

   #scatterprime = numpy.std(kappa_hilbert)
   #print scatterprime

   print "$\kappa_{\mathrm{Scaled}}-\kappa_{\mathrm{Hilbert}}$ = ",bias,"+/-",scatter

   bias_R=numpy.zeros(len(Rbins))
   scatter_R=numpy.zeros(len(Rbins))
   for j in range(len(Rbins)):
      scatter_R[j]=numpy.std(delta_kappa_R[j,:])
      bias_R[j]=numpy.mean(delta_kappa_R[j,:])
#========================================================================
   #Now lots of plotting routines
#========================================================================  
   FILE = open("radcutbias.txt", 'w')
   FILE2 = open("radcutscatter.txt", 'w')
   cPickle.dump(bias_R , FILE )
   cPickle.dump(scatter_R , FILE2)
   plt.plot(Rbins,scatter_R,c='k',label="scatter")
   plt.xlabel("Radius out to which LoS is reconstructed(arcmin)")
   plt.ylabel("$\kappa_{\mathrm{TC}}-\kappa_{\mathrm{Hilbert}}$")
   plt.plot(Rbins,bias_R,c='k', ls = 'dashed',label="bias")
   plt.text(3,0.35,"Truncation at 5 R_Vir")
   plt.axhline(y=0,xmin=0,xmax=1,ls="dotted")
   plt.legend(loc=4,title ="%i LoS"%Ncones)
   plt.savefig("DeltaKappa_vs_Rcone.png")
 
   plt.show()



   list=numpy.linspace(-0.05,0.25,30)
   plt.subplot(311)
   plt.title("$\kappa_{\mathrm{TC}}-\kappa_{\mathrm{Hilbert}}$ = %.3f +/- %.3f" % (bias2,scatter2))
   plt.hist(kappa_tom, bins=list,normed=True, label="$\kappa_{\mathrm{TC}}$")
   plt.legend(title='Cut at %.0f R_vir.'%truncationscale, loc=1)
   plt.subplot(312)
   plt.hist(kappa_hilbert, bins=list,normed=True,label="$\kappa_{\mathrm{Hilbert}}$")
   plt.legend(loc=1)
   plt.subplot(313)
   plt.hist(difference2, bins=20,normed=True,label="$\kappa_{\mathrm{TC}}-\kappa_{\mathrm{Hilbert}}$")
   plt.legend(loc=2)
   plt.savefig("kappatom.png")
   plt.show()


   """ #I'm not keeton anymore!!!
   list=numpy.linspace(-0.05,0.25,30)
   plt.subplot(311)
   plt.title("$\kappa_{\mathrm{Keeton}}-\kappa_{\mathrm{Hilbert}}$ = %.3f +/- %.3f" % (bias,scatter))
   plt.hist(kappa_Scaled, bins=list,normed=True, label="$\kappa_{\mathrm{Keeton}}$")
   plt.legend(title='Cut at %.0f R_vir.'%truncationscale, loc=1)
   plt.subplot(312)
   plt.hist(kappa_hilbert, bins=list,normed=True,label="$\kappa_{\mathrm{Hilbert}}$")
   plt.legend(loc=1)
   plt.subplot(313)
   plt.hist(difference, bins=20,normed=True,label="$\kappa_{\mathrm{Keeton}}-\kappa_{\mathrm{Hilbert}}$")
   plt.legend(loc=2)
   plt.savefig("kappakeeton.png")
   plt.show()
   """


   """
   plt.subplot(121)
   plt.scatter(difference,other2,s=1,c='k',edgecolor='none', label="Any halo")
   plt.xlabel("$\kappa_{\mathrm{Keeton}}-\kappa_{\mathrm{Hilbert}}$")
   #plt.ylabel("LOS distance to most important object (arcmin)")
   plt.ylabel("Closest halo to LOS (arcmin)")
   plt.xlim([-0.4,0.2])
   plt.subplot(121).xaxis.set_ticklabels(["",-0.3,"",-0.1,"",0.1])
   plt.ylim([0,0.8])
   plt.legend()

   plt.subplot(122)
   plt.scatter(difference,other,s=1,c='g',edgecolor='none', label="Halo with i<22")
   plt.legend()
   plt.xlabel("$\kappa_{\mathrm{Keeton}}-\kappa_{\mathrm{Hilbert}}$")
   plt.xlim([-0.4,0.2])
   plt.ylim([0,0.8])
   plt.subplot(122).xaxis.set_ticklabels(["",-0.3,"",-0.1,"",0.1])

   plt.savefig("other.png")
   plt.show()  
   """
   plt.subplot(121)
   plt.scatter(difference,other2,s=1,c='k',edgecolor='none', label="Any halo")
   plt.xlabel("$\kappa_{\mathrm{TC}}-\kappa_{\mathrm{Hilbert}}$")
   plt.ylabel("Closest halo to LOS (Mpc)")
   #plt.xlim([-0.4,0.2])
   #plt.subplot(121).xaxis.set_ticklabels(["",-0.3,"",-0.1,"",0.1])
   #plt.ylim([0,0.8])
   plt.legend()

   plt.subplot(122)
   plt.scatter(difference,other,s=1,c='g',edgecolor='none', label="Halo with i<22")
   plt.legend()
   plt.xlabel("$\kappa_{\mathrm{TC}}-\kappa_{\mathrm{Hilbert}}$")
   #plt.xlim([-0.4,0.2])
   #plt.ylim([0,0.8])
   #plt.subplot(122).xaxis.set_ticklabels(["",-0.3,"",-0.1,"",0.1])

   plt.savefig("other.png")
   plt.show()    
   
   plt.clf()
   plt.subplot(111)
   plt.scatter(kappa_Scaled,difference,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Scaled}}-\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("$\kappa_{\mathrm{Scaled}$")
   plt.xlim([-0.08,0.25])
   plt.ylim([-0.2,0.1])
   plt.savefig("Fig3.png")

   

   plt.clf()
   plt.subplot(111)
   plt.scatter(kappa_hilbert,kappa_Scaled,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Scaled}}$")
   plt.xlabel("$\kappa_{\mathrm{Hilbert}}$")
   plt.savefig("Fig1.png")
   plt.show()  

   """

   #print numpy.std(scatter)
   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.plot(z, fitfunc(pfinal,z))
   plt.scatter(x,y,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Keeton}}-\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("$\kappa_{\mathrm{Keeton}}$")
   plt.xlim([-0.08,0.25])
   plt.ylim([-0.2,0.1])
   plt.savefig("Fig4.png")
   plt.show() 
   


   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.scatter(N_45,y,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Keeton}}-\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("N$_{45}$")
   plt.savefig("Fig5.png")
   plt.show() 

   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.scatter(N_45,kappa_hilbert,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("N$_{45}$")
   plt.savefig("Fig6.png")
   plt.show()
   


   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.scatter(N_60,kappa_hilbert,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("N$_{60}$")
   plt.savefig("Fig6b.png")
   plt.show()


   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.scatter(N_90,kappa_hilbert,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("N$_{90}$")
   plt.savefig("Fig6c.png")
   plt.show()

   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.scatter(N_30,kappa_hilbert,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("N$_{30}$")
   plt.savefig("Fig6d.png")
   plt.show()

   plt.clf()
   plt.subplot(111)
   z=numpy.linspace(-0.05,0.2,30)
   plt.scatter(N_15,kappa_hilbert,s=1,c='k',edgecolor='none')
   plt.ylabel("$\kappa_{\mathrm{Hilbert}}$")
   plt.xlabel("N$_{15}$")
   plt.savefig("Fig6e.png")
   plt.show()
   """
# ======================================================================



if __name__ == '__main__':
  MScompare(sys.argv[1:])
  #print "check your fiducial cosmology?"


# ======================================================================
