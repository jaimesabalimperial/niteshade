#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for out-of-the-box model classes.
"""


# =============================================================================
#  IMPORTS AND DEPENDENCIES
# =============================================================================

import unittest

import pytest

from niteshade.model import IrisClassifier, MNISTClassifier
from niteshade.simulation import Simulator
from niteshade.utils import train_test_iris, train_test_MNIST


# =============================================================================
#  CLASSES
# =============================================================================

class Model_test(unittest.TestCase):
    def setUp(self) -> None:
        self.batch_size = 32
        self.num_episodes = 10
    
    def test_iris(self):
        """No attack and defense trial on Iris dataset."""
        #split iris dataset into train and test
        X_train, y_train, X_test, y_test = train_test_iris(num_stacks=10)

        #implement attack and defense strategies through learner
        model = IrisClassifier()
        simulator = Simulator(X_train, y_train, model, attacker=None,
                            defender=None, batch_size=self.batch_size, num_episodes=self.num_episodes)

        #simulate attack and defense separately using run() method
        simulator.run()

        #evaluate on test set
        test_loss, test_accuracy = simulator.model.evaluate(X_test, y_test, self.batch_size)  
        print(f"TEST LOSS; {test_loss}, TEST ACCURACY; {test_accuracy}")

    def test_MNIST(self):
        X_train, y_train, X_test, y_test = train_test_MNIST()

        #implement attack and defense strategies through learner
        model = MNISTClassifier()
        simulator = Simulator(X_train, y_train, model, attacker=None, defender=None, 
                            batch_size=self.batch_size, num_episodes=self.num_episodes)

        #simulate attack and defense separately using run() method
        simulator.run()

        #evaluate on test set
        test_loss, test_accuracy = simulator.model.evaluate(X_test, y_test, self.batch_size)  
        #print(f"TEST LOSS; {test_loss}, TEST ACCURACY; {test_accuracy}")


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    unittest.main()