# ===========================================================================

import os, glob

# ======================================================================

class Configuration(object):

    def __init__(self,configfile):
        self.file = configfile
        self.parameters = {}
        self.read()
        self.convert()
        self.prepare()
        return

    # ------------------------------------------------------------------
    # Read in values by keyword and populate the parameters dictionary.

    def read(self):
        thisfile = open(self.file)
        for line in thisfile:
            # Ignore empty lines and comments:
            if line[0:2] == '\n': continue
            if line[0] == '#': continue
            line.strip()
            line = line.split('#')[0]
            # Remove whitespace and interpret Name:Value pairs:
            line = ''.join(line.split())
            line = line.split(':')
            Name, Value = line[0], line[1]
            self.parameters[Name] = Value
        thisfile.close()
        return

    # ------------------------------------------------------------------
    # Convert string values into floats/ints where necessary, and expand
    # environment variables.

    def convert(self):

        # Some values need to be floats or integers:
        for key in self.parameters.keys():
            try:
                self.parameters[key] = float(self.parameters[key])
            except ValueError:
                pass
        intkeys = ['NCalibrationLightcones']
        for key in intkeys:
            self.parameters[key] = int(self.parameters[key])

        # Now sort out filenames etc:

        pathkeys = ['CalibrationCatalogs', 'CalibrationKappamaps',
                                'ObservedCatalog', 'CalibrationFolder']
        for key in pathkeys:
            paths = self.parameters[key]
            # Expand environment variables (eg $PANGLOSS_DIR)
            paths = os.path.expandvars(paths)
            # Expand wildcards - glob returns [] if no files found...
            found = glob.glob(paths)
            if len(found) > 0: paths = found
            # Make sure all paths are lists, for consistency:
            if len(paths[0]) == 1: paths = [paths] 
            # Replace parameters:
            self.parameters[key] = paths

        # Calibration catalogs and kappa maps must come in pairs...
        assert len(self.parameters['CalibrationCatalogs']) == \
               len(self.parameters['CalibrationKappamaps'])

        return

    # ------------------------------------------------------------------
    # Perform various other preparations.

    def prepare(self):

        # Make directories if necessary:
        folderkeys = ['CalibrationFolder']
        for key in folderkeys:
            folder = self.parameters[key]
            fail = os.system('mkdir -p '+folder[0])

        return

# ======================================================================

