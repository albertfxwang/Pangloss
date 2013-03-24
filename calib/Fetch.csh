#!/bin/tcsh
#=============================================================================
#+
# NAME:
#   Fetch.csh
#
# PURPOSE:
#   Download all the calibration data you need to run the Pangloss 
#   example.
#
# COMMENTS:
#
# USAGE:
#   Fetch.csh
#
# INPUTS:
#
# OPTIONAL INPUTS:
#   -h --help
#   -v --verbose
#   -x --clobber                      Overwrite data already owned.
#
# OUTPUTS:
#   Millennium/Kappa_8_1_1.fits       Ray-traced convergence map
#   Millennium/Catalogue_8_1_1.txt    Catalog of galaxy and halo properties
#
#   SHMR/H2S.behroozi                 Stellar/halo mass relation look-up tables
#   SHMR/S2H.behroozi
#   SHMR/H2S.moster
#
# DEPENDENCIES:
#
#   wget
#
# BUGS:
#  
# REVISION HISTORY:
#   2013-03-21  started Marshall & Collett (Oxford)
#-
#=======================================================================

unset noclobber

# Set defaults:

set help = 0
set vb = 0
set klobber = 0
set urls = ()

# Parse command line:

while ( $#argv > 0 )
   switch ($argv[1])
   case -h:           #  print help
      set help = 1
      shift argv
      breaksw
   case --{help}:  
      set help = 1
      shift argv
      breaksw
   case -x:           #  clobber
      set klobber = 1
      shift argv
      breaksw
   case --{clobber}:  
      set klobber = 1
      shift argv
      breaksw
   case *:
      shift argv
      breaksw
   endsw
end

#-----------------------------------------------------------------------

if ($help) then
  more $0
  goto FINISH
endif

set BACK = `echo $cwd`

set website = "http://www.ast.cam.ac.uk/~tcollett/Pangloss/calib"

  echo "${0:t}: Downloading data files from Tom's website:"
  echo "${0:t}:   $website"
  echo "${0:t}: into current working directory:"
  echo "${0:t}:   $HERE"
  if ($klobber) echo "${0:t}: Clobbering contents of existing directories!"

#-----------------------------------------------------------------------

set targets = (\
Millennium/kappa_example.fits \
Millennium/catalog_example.txt \
SHMR/H2S.behroozi \
SHMR/S2H.behroozi \
SHMR/H2S.moster )

foreach file ( $targets )

  set dir = $file:h
  mkdir -p $dir
  chdir $dir

  if ($klobber) \rm -rf $file

  set now = `date '+%Y%m%d-%H%M%S'`
  set logfile = ".wget.$file:t.$now.log"
  
  set url = "$website/$file"
  
  wget "$url" \
    -O $file:t \
    -e robots=off \
    >& $logfile
  
  chdir $BACK
  echo "${0:t}: log stored in $dir/$logfile"
          
  echo "${0:t}: result:"
  du -sh $file

end

FINISH:

#=======================================================================
