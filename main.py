
# Written by: Oskar
# Last edited: 2022/01/22
# Description: Example main pipeline execution script. This is a rough example
# of how the pipeline could look, and how the various classes could interact
# with one another. We can write this script properly on Tuesday :)


# =============================================================================
#  IMPORTS AND DEPENDENCIES
# =============================================================================

import numpy as np

from datastream import DataStream
from attack import RandomAttacker
from defence import RandomDefender
from model import IrisClassifier
#from postprocessing import PostProcessor
from learner import Learner


from sklearn import datasets
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


# =============================================================================
#  GLOBAL VARIABLES
# =============================================================================
# Load dataset
data = np.loadtxt("datasets/iris.dat") #already contains one-hot encoding for targets

# batch size
BATCH_SIZE = 10

# Model
# HIDDEN_NEURONS = (4, 16, 3) automicatically set in IrisClassifier
# ACTIVATIONS = ("relu", "softmax")  automicatically set in IrisClassifier
OPTIMISER = "adam"
LOSS_FUNC = "cross_entropy"
LEARNING_RATE = 0.01
EPOCHS = 100


# =============================================================================
#  FUNCTIONS
# =============================================================================

def main():
    """ Main pipeline execution. (Trial with Iris dataset) """

    #define input and target data
    X, y = data[:, :4], data[:, 4:]

    #split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    #normalise data using sklearn module
    scaler = MinMaxScaler()

    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    X_train, y_train = shuffle(X_train, y_train)

    # Instantiate necessary classes
    defender = defender_initiator(defender_type = "RandomDefender", reject_rate = 0.1)
    attacker = RandomAttacker()
    model = IrisClassifier(OPTIMISER, LOSS_FUNC, LEARNING_RATE)
    #postprocessor = PostProcessor()

    #implement attack and defense strategies through learner
    learner = Learner(X_train, y_train, model, attacker=None,
                      defender=None, batch_size=BATCH_SIZE)
    
    learner.learn_online()

    learner.model.test(X_test, y_test, BATCH_SIZE)  

def defender_initiator(**kwargs):
    # Returns a defender class depending on which strategy we are using
    # Currently only the RandomDefender is implemented, for who a reject_rate arg needs to be passed in
    for key, value in kwargs.items():
        if key == "defender_type":
            if value =="RandomDefender":
                rate = kwargs["reject_rate"]
                return RandomDefender(rate)


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()


