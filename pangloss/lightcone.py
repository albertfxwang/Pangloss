# ===========================================================================

import pangloss

#import pylab
#import matplotlib.pyplot as plt
#from mpl_toolkits.axes_grid1 import ImageGrid
import cPickle
import numpy
import Relations as Rel
import LensingProfiles as LP
import LensingFunc as LF
import numpy.random as rnd
import pylab as plt

# ============================================================================

class Lightcone(object):
    """
    TEST DOCSTRING
    """

# ----------------------------------------------------------------------------

    def __init__(self,catalog,flavor,position,radius,magnitudecut=99,band="r"):
        
        self.name = 'Lightcone through the Universe'
        self.flavor = flavor   # 'real' or 'simulated'
        self.catalog = catalog
        
        # Simulated lightcones have "true" (ray-traced) convergence:
        self.kappa_hilbert = None # until set!
        
        self.xmax = self.catalog['pos_0[rad]'].max()
        self.xmin = self.catalog['pos_0[rad]'].min()
        self.ymax = self.catalog['pos_1[rad]'].max()
        self.ymin = self.catalog['pos_1[rad]'].min() 
        self.rmax = radius
        self.xc = [position[0],position[1]]

        dx = self.rmax*pangloss.arcmin2rad
        self.galaxies = self.catalog.where((self.catalog['pos_0[rad]'] > (self.xc[0]-dx)) & \
                                           (self.catalog['pos_0[rad]'] < (self.xc[0]+dx)) & \
                                           (self.catalog['pos_1[rad]'] > (self.xc[1]-dx)) & \
                                           (self.catalog['pos_1[rad]'] < (self.xc[1]+dx))   )

 
        x = (self.galaxies['pos_0[rad]'] - self.xc[0])*pangloss.rad2arcmin
        y = (self.galaxies['pos_1[rad]'] - self.xc[1])*pangloss.rad2arcmin
        r = numpy.sqrt(x*x + y*y)
        phi=numpy.arctan(y/x)
        self.galaxies.add_column('x',x)
        self.galaxies.add_column('y',y)
        self.galaxies.add_column('r',r)
        self.galaxies.add_column('phi',phi)


        self.galaxies = self.galaxies.where(self.galaxies.r < self.rmax)
        self.galaxies = self.galaxies.where(self.galaxies.Type != 2) 

        #log the mass:
        self.galaxies.add_column('Mh',numpy.log10(self.galaxies['M_Subhalo[M_sol/h]']))
        self.galaxies.add_column('Mh_obs',self.galaxies.Mh*1)
        #self.galaxies.add_column('Ms',numpy.log10(self.galaxies['M_Stellar[M_sol/h]']))

        self.galaxies.add_column('z_obs',self.galaxies.z_spec)
        self.galaxies.add_column('spec_flag',False)
        
        if len(self.galaxies) == 0: 
            print "Lightcone: WARNING: no galaxies here!"

        del self.catalog
        del catalog
        
        """
        F814 = (self.galaxies.mag_SDSS_i + self.galaxies.mag_SDSS_z)/2. #approximate F814 colour.
        self.galaxies.add_column("mag_F814W",F814)
        if band == "u" or band ==  "g" or band == "r" or band ==  "i" or band == "z":
            col = "mag_SDSS_%s" % band
        elif band == "F814" or band == "F814W" or band == "814" or band == 814:
            col = "mag_F814W"
        else:
            col = "mag_%s" % band
        self.galaxies=self.galaxies.where(self.galaxies["%s"%col] < magnitudecut)
        """
        return None

# ----------------------------------------------------------------------------

    def __str__(self):
        return 'Lightcone of radius %.2f arcmin, centred on (%.3f,%.3f) rad' % (self.rmax,self.xc[0],self.xc[1])

# ----------------------------------------------------------------------------

   #Tell me the number of galaxies within a certain radius, that pass a certain magnitude cut.
    def N_radius_cat(self,radius,cut=[18.5,24.5], band="F814W", radius_unit="arcsec"):
        if band == "u" or band ==  "g" or band == "r" or band ==  "i" or band == "z":
            col = "mag_SDSS_%s" % band
        elif band == "F814" or band == "F814W" or band == "814" or band == 814:
            col = "mag_F814W"
        else:
            col = "mag_%s" % band
        if radius < 10: print "Warning: Default units for N_radius are arcsec!"
        if radius_unit == "arcsec":
            radius = radius/60.
        if col != "warning":
            self.N_cut=self.galaxies.where((self.galaxies.r < radius)  & \
                                              (self.galaxies["%s"%col] < cut[1])& \
                                          (self.galaxies["%s"%col] > cut[0]))

            return self.galaxies.where((self.galaxies.r < radius) & \
                                          (self.galaxies["%s"%col] < cut[1])& \
                                          (self.galaxies["%s"%col] > cut[0]))

    def N_radius(self,radius,cut=[18.5,24.5],band="F814W", radius_unit="arcsec"):
        Ntable=self.N_radius_cat(radius,cut,band, radius_unit)
        return len(Ntable.r)

# ----------------------------------------------------------------------------

    def define_system(self,zl,zs,cosmo=[0.25,0.75,0.73]):
        self.zl=zl
        self.zs=zs
        self.cosmo=cosmo
        self.galaxies=self.galaxies.where(self.galaxies.z_spec<zs)

# ----------------------------------------------------------------------------
    def load_grid(self, Grid):
        if numpy.abs(self.zl-Grid.zltrue)>0.05: print "Grid zl != lens zl" 
        if numpy.abs(self.zs-Grid.zs)    >0.05: print "Grid zs != lens zs" 
        self.redshifts,self.dz=Grid.redshifts,Grid.dz
        self.Da_l,self.Da_s,self.Da_ls=Grid.Da_l,Grid.Da_s,Grid.Da_ls

# ----------------------------------------------------------------------------
# Following functions are designed to be run multiple times
# (Previous functions are single use/lightcone)
# ----------------------------------------------------------------------------

    def mimic_photoz_error(self,sigma=0.1):
        print "Make me vary for each galaxy"
        #this code is not written well at the moment.

        e=sigma
        flag=self.galaxies.spec_flag==False ## Will give true for objects that have no spectrum
        z_obs=self.galaxies.z_spec*1.0
        for i in range(len(z_obs)):
            z=z_obs[i]
            if flag[i]==True: z=rnd.normal(z,e*(1+z))
            z_obs[i]=z
        self.galaxies.z_obs=z_obs

# ----------------------------------------------------------------------------

    # shortcut function for adding columns that might already exist
    def try_column(self,string,values):
        try:
            self.galaxies.add_column('%s'%string,values)
        except ValueError:
            self.galaxies["%s"%string]=values

# ----------------------------------------------------------------------------

    def snap_to_grid(self, Grid):
        z=self.galaxies.z_obs
        sz,p=Grid.snap(z)
        self.try_column('Da_p',Grid.Da_p[p])
        self.try_column('rho_crit',Grid.rho_crit[p])
        self.try_column('sigma_crit',Grid.sigma_crit[p])
        self.try_column('beta',Grid.beta[p])
        rphys=self.galaxies.r*pangloss.arcmin2rad*self.galaxies.Da_p
        self.try_column('rphys',rphys)

# ----------------------------------------------------------------------------
#  One line description here!

    def drawMStars(self,model):
        Mhlist=self.galaxies.Mh
        redshiftList=self.galaxies.z_obs
        # REPLACE WITH SHMR.drawMstars([Mhlist,redshiftList])...
        Ms = model.eval(numpy.array([Mhlist,redshiftList]).T)

        #Ms = numpy.log10(self.galaxies['M_Stellar[M_sol/h]'])

        #now add uncertainties:
        Ms[self.galaxies.spec_flag==False]+=rnd.randn(Ms[self.galaxies.spec_flag==False].size)*0.45
        Ms[self.galaxies.spec_flag==True]+=rnd.randn(Ms[self.galaxies.spec_flag==True].size)*0.15

        try:
            self.galaxies.add_column('Ms_obs',Ms)
        except ValueError:
            self.galaxies.Ms_obs=Ms
            
# ----------------------------------------------------------------------------
#  One line description here!

    def drawMHalos(self,modelT):
        Mslist=self.galaxies.Ms_obs
        redshiftList=self.galaxies.z_obs
        R = rnd.random(len(Mslist))
        Mhlist=modelT.eval(numpy.array([Mslist,R,redshiftList]).T)
        self.galaxies.Mh_obs=Mhlist

# ----------------------------------------------------------------------------

    def drawConcentrations(self,errors=False):
        M200=10**self.galaxies.Mh_obs        
        r200 = (3*M200/(800*3.14159*self.galaxies.rho_crit))**(1./3)
        self.try_column("r200",r200)
        c200 = Rel.MCrelation(M200,scatter=errors)
        self.try_column("c200",c200)
        r_s = r200/c200        
        self.try_column('rs',r_s)
        x=self.galaxies.rphys/r_s
        self.try_column('X',x)

# ----------------------------------------------------------------------------

    def Make_kappas(self,errors=False,truncationscale=5,profile="BMO1"):
        #M200=10**self.galaxies.Mh_obs     
        c200=self.galaxies.c200
        r200=self.galaxies.r200
        x=self.galaxies.X
        r_s=self.galaxies.rs
        rho_s = LP.delta_c(c200)*self.galaxies.rho_crit
        kappa_s = rho_s * r_s /self.galaxies.sigma_crit
        r_trunc=truncationscale*r200
        xtrunc=r_trunc/r_s
        kappaHalo=kappa_s*1.0
        gammaHalo=kappa_s*1.0
        if profile=="BMO1":
            F=LP.BMO1Ffunc(x,xtrunc)
            G=LP.BMO1Gfunc(x,xtrunc)
        if profile=="BMO2":
            F=LP.BMO2Ffunc(x,xtrunc)
            G=LP.BMO2Gfunc(x,xtrunc)
        kappaHalo*=F
        gammaHalo*=(G-F)

        phi=self.galaxies.phi

        kappa = kappaHalo 
        gamma = gammaHalo
        gamma1 = gamma*numpy.cos(2*phi)
        gamma2 = gamma*numpy.sin(2*phi)

        self.try_column('kappa',kappa)
        self.try_column('gamma',gamma)
        self.try_column('gamma1',-gamma1)
        self.try_column('gamma2',-gamma2)
# ----------------------------------------------------------------------------

    def Scale_kappas(self):
        B=self.galaxies.beta
        K=self.galaxies.kappa
        G=self.galaxies.gamma
        G1=self.galaxies.gamma1
        G2=self.galaxies.gamma2
        D= K**2-G**2

        kappa_keeton  = (1.-B) * (K- B*(D)) /  ( (1-B*K)**2   - (B*G)**2   )    
        gamma1_keeton = (1.-B) * (G1) /  ( (1-B*K)**2   - (B*G)**2   )  
        gamma2_keeton = (1.-B) * (G2) /  ( (1-B*K)**2   - (B*G)**2   )  

        kappa_tom  = (1.-B) * K
        gamma1_tom = (1.-B) * G1
        gamma2_tom = (1.-B) * G2

        self.try_column('kappa_keeton',kappa_keeton)
        self.try_column('gamma1_keeton',gamma1_keeton)
        self.try_column('gamma2_keeton',gamma2_keeton)

        self.try_column('kappa_tom',kappa_tom)
        self.try_column('gamma1_tom',gamma1_tom)
        self.try_column('gamma2_tom',gamma2_tom)

        self.try_column('kappa_add',K)
        self.try_column('gamma1_add',G1)
        self.try_column('gamma2_add',G2)


        self.kappa_add_total=numpy.sum(self.galaxies.kappa_add)
        self.kappa_keeton_total=numpy.sum(self.galaxies.kappa_keeton)
        self.kappa_tom_total=numpy.sum(self.galaxies.kappa_tom)

        self.gamma1_add_total=numpy.sum(self.galaxies.gamma1_add)
        self.gamma1_keeton_total=numpy.sum(self.galaxies.gamma1_keeton)
        self.gamma1_tom_total=numpy.sum(self.galaxies.gamma1_tom)

        self.gamma2_add_total=numpy.sum(self.galaxies.gamma2_add)
        self.gamma2_keeton_total=numpy.sum(self.galaxies.gamma2_keeton)
        self.gamma2_tom_total=numpy.sum(self.galaxies.gamma2_tom)

#=============================================================================
