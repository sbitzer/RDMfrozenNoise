# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 09:06:41 2015

@author: Sebastian Bitzer (sebastian.bitzer@tu-dresden.de)

Copyright (C) 2015 Sebastian Bitzer

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import urllib2
import re
import os
import numpy as np
import matplotlib.pyplot as plt


class RDMfrozenNoise():
    folder = "data/NSA2009.1/"
    url = 'http://www.neuralsignal.org/data/09/nsa2009.1/'
    navailfiles = 52

    choicesvar = []
    choicesfro = []
    nvar = 0
    nfro = 0

    def __init__(self):
        nfiles = 0
        if os.path.exists(self.folder):
            nfiles = len([name for name in os.listdir(self.folder) if
                          os.path.isfile(self.folder + name)])

        if nfiles == self.navailfiles:
            print 'Found all %d available data files.' % (self.navailfiles, )
        else:
            self.downloadData()

        self.extractChoices()


    def downloadData(self):
        if not os.path.exists(self.folder): # Directory that I want to save the data to
            os.mkdir(self.folder) # If no directory create it

        source = urllib2.urlopen(self.url).read()

        datafiles = re.findall('a href="(e\d+h?[cv])"', source)

        for df in datafiles:
            remote = self.url + df;
            filename = self.folder + df
            if not os.path.exists(filename):
                print "Copying from " + remote + " to " + filename
                with open(filename, 'wb') as f:
                    f.write(urllib2.urlopen(remote).read())

        nfiles = len([name for name in os.listdir(self.folder) if
                      os.path.isfile(self.folder + name)])
        if nfiles == self.navailfiles:
            print 'Downloaded all available data files.'
        else:
            print 'Unexpected number of files after downloading: %d instead of %d.'\
                (nfiles, self.navailfiles)


    def extractChoices(self):
        """Extract animal choices from data files.

            Each file contains several trials which are indicated by "T #"
            where # is the current trial count for that file. On the same line
            two more numbers follow: "direction" (D) and "correct" (C) where D
            indicates the direction that was assigned to this 0% coherence
            trial and C indicates whether the animal has chosen this direction
            in that trial. As there were only two possible choices, if D was
            not chosen, the other option (direction) must have been chosen.
            Each "T"-line is followed by "R"-line which gives spike timings
            within that trial. Each file corresponds to one measured neural
            unit (presumably one neuron).

            Trials in which the random seed of the random dot motion stimulus
            was constant, i.e., in which the noise in the stimulus was frozen
            were collected in files ending with "c". Trials in which noise in
            the stimulus was always different are in "v".

            Strangely, in "c"-files D is either 2 or 3 whereas D is 0 or 1 in
            "v"-files. I have no clue why. It is also unclear whether the
            noise was frozen across or only within "c"-files and it is unclear
            whether all choices in the files are distinct, i.e., whether
            several units were recorded at the same time such that trials in
            different files are actually the same. Varying trial numbers in
            different files suggest that this was not the case.

            Check neuralsignal.org for more info, but I didn't find any.
        """
        self.choicesvar = []
        self.choicesfro = []

        for fname in os.listdir(self.folder):
            if fname[-1] == 'c':
                frozen = True
            elif fname[-1] == 'v':
                frozen = False
            else:
                # skip unidentified file
                continue

            trials = []

            with open(self.folder + fname, 'r') as f:
                for line in f:
                    if line[:2] == 'T ':
                        elements = line.split()

                        if frozen:
                            # transform frozen directions from [2,3] to [0,1]
                            corrchoice = int(elements[2]) - 2

                        assert corrchoice in [0, 1], 'correct choice is not in [0, 1]'

                        # put as "correct" defined direction to index 1 and the
                        # other direction to index 0
                        corrchoice = bool(corrchoice)
                        choice = [not corrchoice, corrchoice]

                        # collect choice of animal depending on whether it
                        # chose "correct" (1) or "incorrect" (0) in this trial
                        trials.append(choice[int(elements[3])])

            if frozen:
                self.choicesfro.append(np.array(trials))
            else:
                self.choicesvar.append(np.array(trials))

        self.nfro = len(self.choicesfro)
        self.nvar = len(self.choicesvar)

        return self.choicesvar, self.choicesfro


    def plotChoiceFractions(self):
        # compute means and their standard errors
        cfro = np.c_[ map(np.mean, self.choicesfro),
                      map(np.std, self.choicesfro) /
                      np.sqrt(map(len, self.choicesfro)) ]
        cvar = np.c_[ map(np.mean, self.choicesvar),
                      map(np.std, self.choicesvar) /
                      np.sqrt(map(len, self.choicesvar)) ]

        randxfro = np.random.rand(self.nfro) * 0.5 + 0.75
        randxvar = np.random.rand(self.nvar) * 0.5 + 1.75

        xl = [0.5, 2.5]

        ax = plt.axes()

        ax.errorbar(randxfro, cfro[:, 0], cfro[:, 1], fmt='xk')
        ax.errorbar(randxvar, cvar[:, 0], cvar[:, 1], fmt='xk')
        ax.plot(xl, [0.5, 0.5], ':k')

        ax.set_ylabel('fraction of response 1')
        ax.set_xlabel('experiment blocks')
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['frozen noise', 'variable noise'])
        ax.set_xlim(xl)

        return ax


if __name__ == "__main__":
    rdmdata = RDMfrozenNoise()
    ax = rdmdata.plotChoiceFractions()
