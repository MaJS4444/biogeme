"""File 13panel.py

:author: Michel Bierlaire, EPFL
:date: Sun Sep  8 18:55:38 2019

 Example of a mixture of logit models, using Monte-Carlo integration.
 The datafile is organized as panel data.  Same as 12panel, where the
 error component for Swissmetro has been normalized to zero, and it
 corresponds to the lowest variance, according to the estimation
 rresults of 12panel.py. Moreover, the starting values for the
 parameters are close to optimal.  Useful for a faster estimation of
 the model with a large number of draws.  Three alternatives: Train,
 Car and Swissmetro SP data

"""

import pandas as pd
import biogeme.database as db
import biogeme.biogeme as bio
from biogeme import models
import biogeme.messaging as msg
from biogeme.expressions import (
    Beta,
    DefineVariable,
    bioDraws,
    PanelLikelihoodTrajectory,
    MonteCarlo,
    log,
)

# Read the data
df = pd.read_csv('swissmetro.dat', sep='\t')
database = db.Database('swissmetro', df)

# They are organized as panel data. The variable ID identifies each individual.
database.panel("ID")

# The Pandas data structure is available as database.data. Use all the
# Pandas functions to invesigate the database
# print(database.data.describe())

# The following statement allows you to use the names of the variable
# as Python variable.
globals().update(database.variables)

# Removing some observations can be done directly using pandas.
# remove = (((database.data.PURPOSE != 1) &
#           (database.data.PURPOSE != 3)) |
#          (database.data.CHOICE == 0))
# database.data.drop(database.data[remove].index,inplace=True)

# Here we use the "biogeme" way for backward compatibility
exclude = ((PURPOSE != 1) * (PURPOSE != 3) + (CHOICE == 0)) > 0
database.remove(exclude)


# Parameters to be estimated
B_COST = Beta('B_COST', -3.32, None, None, 0)

# Define a random parameter, normally distributed across individuals,
# designed to be used for Monte-Carlo simulation
B_TIME = Beta('B_TIME', -5.4, None, None, 0)

# It is advised not to use 0 as starting value for the following parameter.
B_TIME_S = Beta('B_TIME_S', 1.55, None, None, 0)
B_TIME_RND = B_TIME + B_TIME_S * bioDraws('B_TIME_RND', 'NORMAL_ANTI')

# We do the same for the constants, to address serial correlation.
ASC_CAR = Beta('ASC_CAR', 0.357, None, None, 0)
ASC_CAR_S = Beta('ASC_CAR_S', 3.37, None, None, 0)
ASC_CAR_RND = ASC_CAR + ASC_CAR_S * bioDraws('ASC_CAR_RND', 'NORMAL_ANTI')

ASC_TRAIN = Beta('ASC_TRAIN', -0.617, None, None, 0)
ASC_TRAIN_S = Beta('ASC_TRAIN_S', 3.13, None, None, 0)
ASC_TRAIN_RND = ASC_TRAIN + ASC_TRAIN_S * bioDraws(
    'ASC_TRAIN_RND', 'NORMAL_ANTI'
)

# Definition of new variables
SM_COST = SM_CO * (GA == 0)
TRAIN_COST = TRAIN_CO * (GA == 0)

# Definition of new variables: adding columns to the database
CAR_AV_SP = DefineVariable('CAR_AV_SP', CAR_AV * (SP != 0), database)
TRAIN_AV_SP = DefineVariable('TRAIN_AV_SP', TRAIN_AV * (SP != 0), database)
TRAIN_TT_SCALED = DefineVariable('TRAIN_TT_SCALED', TRAIN_TT / 100.0, database)
TRAIN_COST_SCALED = DefineVariable(
    'TRAIN_COST_SCALED', TRAIN_COST / 100, database
)
SM_TT_SCALED = DefineVariable('SM_TT_SCALED', SM_TT / 100.0, database)
SM_COST_SCALED = DefineVariable('SM_COST_SCALED', SM_COST / 100, database)
CAR_TT_SCALED = DefineVariable('CAR_TT_SCALED', CAR_TT / 100, database)
CAR_CO_SCALED = DefineVariable('CAR_CO_SCALED', CAR_CO / 100, database)

# Definition of the utility functions
V1 = ASC_TRAIN_RND + B_TIME_RND * TRAIN_TT_SCALED + B_COST * TRAIN_COST_SCALED
V2 = B_TIME_RND * SM_TT_SCALED + B_COST * SM_COST_SCALED
V3 = ASC_CAR_RND + B_TIME_RND * CAR_TT_SCALED + B_COST * CAR_CO_SCALED

# Associate utility functions with the numbering of alternatives
V = {1: V1, 2: V2, 3: V3}

# Associate the availability conditions with the alternatives
av = {1: TRAIN_AV_SP, 2: SM_AV, 3: CAR_AV_SP}

# Conditional to the random parameters, the likelihood of one observation is
# given by the logit model (called the kernel)
obsprob = models.logit(V, av, CHOICE)

# Conditional to the random parameters, the likelihood of all observations for
# one individual (the trajectory) is the product of the likelihood of
# each observation.
condprobIndiv = PanelLikelihoodTrajectory(obsprob)

# We integrate over the random parameters using Monte-Carlo
logprob = log(MonteCarlo(condprobIndiv))

# Define level of verbosity
logger = msg.bioMessage()
# logger.setSilent()
# logger.setWarning()
# logger.setGeneral()
logger.setDetailed()
# logger.setDebug()

# Create the Biogeme object
biogeme = bio.BIOGEME(database, logprob, numberOfDraws=100000)
biogeme.modelName = '13panelNormalized'

# Estimate the parameters.
results = biogeme.estimate()
pandasResults = results.getEstimatedParameters()
print(pandasResults)
