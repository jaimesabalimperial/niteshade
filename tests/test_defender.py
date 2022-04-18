#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for various defender classes.
"""


# =============================================================================
#  IMPORTS AND DEPENDENCIES
# =============================================================================

import unittest
import torch
import pytest
import numpy as np

from niteshade.defence import FeasibleSetDefender, Distance_metric, DefenderGroup, KNN_Defender


# =============================================================================
#  CLASSES
# =============================================================================

class FeasibleSetDefender_test(unittest.TestCase):
    def setUp(self) -> None:
        self.x = np.ones((16,3,4,4))
        self.y = np.zeros((16))

    def test_point_accept_reject(self):
        defender = FeasibleSetDefender(self.x,self.y, 3, False)
        test_datapoint_pass = np.ones((2,3,4,4))
        test_label_pass = np.zeros((2))
        x, _ = defender.defend(test_datapoint_pass, test_label_pass)
        self.assertEqual(x.shape, test_datapoint_pass.shape)
        self.assertIsInstance(x, np.ndarray)
        test_datapoint_fail = np.array( [[[2,2,2,6],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,7,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]]]).reshape(1,3,4,4)
        test_label_fail = np.array([0])
        _, y = defender.defend(test_datapoint_fail, test_label_fail)
        self.assertEqual(y.shape, (0,)) 
    
    def test_point_accept_reject_onehot(self):
        init_y_onehot = np.tile(np.array([0,1,0]), 16).reshape(16,3)
        defender = FeasibleSetDefender(self.x, init_y_onehot, 3, True)
        test_datapoint_pass = np.ones((2,3,4,4))
        test_label_pass = np.tile([0,1,0], 2).reshape(2,3)
        x, _ = defender.defend(test_datapoint_pass, test_label_pass)
        self.assertEqual(x.shape, test_datapoint_pass.shape)
        test_datapoint_fail = np.array([[[2,2,2,6],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,7,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]]]).reshape(1,3,4,4)
        test_label_fail = np.array([0,1,0]).reshape((1,3))
        _, y = defender.defend(test_datapoint_fail, test_label_fail)
        self.assertEqual(y.shape, (0,)) 
    
    def test_Distance_metric(self):
        test_point_1 = np.random.rand(16,3,4,4)
        test_point_2 = np.random.rand(16,3,4,4)
        L2_dist_obj = Distance_metric("Eucleidian")
        L2_dist = L2_dist_obj.distance(test_point_1, test_point_2)
        dist = np.linalg.norm(test_point_1-test_point_2)
        self.assertAlmostEqual(L2_dist, dist)
        
    def test_custom_dist_metric(self):
        class CustomDistanceMetric(Distance_metric):
            def __init__(self, random_counter, type=None) -> None:
                super().__init__(type)
                self.nr = random_counter
        
            def distance(self, input1, input2):
                return self.nr * np.sqrt(np.sum((input1 - input2)**2))
        
        customdist_obj = CustomDistanceMetric(2)
        test_point_1 = np.random.rand(16,3,4,4)
        test_point_2 = np.random.rand(16,3,4,4)
        Custom_dist = customdist_obj.distance(test_point_1, test_point_2)
        dist = np.linalg.norm(test_point_1-test_point_2)
        self.assertAlmostEqual(Custom_dist, 2*dist)
        
    def test_check_types(self):
        defender = FeasibleSetDefender(self.x,self.y, 3, False)
        test_datapoint_np = np.ones((2,3,4,4))
        test_label_np = np.zeros((2))
        x, y = defender.defend(test_datapoint_np, test_label_np)
        self.assertIsInstance(x, np.ndarray)
        self.assertIsInstance(y, np.ndarray)
        test_datapoint_torch = torch.ones((2,3,4,4))
        test_label_torch = torch.zeros((2))
        x, y = defender.defend(test_datapoint_torch, test_label_torch)
        self.assertIsInstance(x, torch.Tensor)
        self.assertIsInstance(y, torch.Tensor)

class GroupDefender_test(unittest.TestCase):
    def setUp(self) -> None:
        self.x = np.ones((16,3,4,4))
        self.y = np.zeros((16))

    def test_GroupDefender(self):
        grp = DefenderGroup([FeasibleSetDefender(self.x,self.y, 3, False),
                             FeasibleSetDefender(self.x,self.y, 20, False)])
        
        test_datapoint_pass = np.ones((2,3,4,4))
        test_label_pass = np.zeros((2))
        x, _ = grp.defend(test_datapoint_pass, test_label_pass)
        self.assertEqual(x.shape, test_datapoint_pass.shape)
        self.assertIsInstance(x,np.ndarray)
        test_datapoints = np.array( [[[2,2,2,6],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,7,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]], 
                            [[2,2,2,6],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,7,2,2],
                            [2,2,120,2],[2,2,2,2]],
                            [[2,1222,2,2],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]]]).reshape(2,3,4,4)
        test_labels = np.array([0,0]).reshape(2,)
        grp = DefenderGroup([FeasibleSetDefender(self.x,self.y, 18, False),
                             FeasibleSetDefender(self.x,self.y, 20, False)])
        x, _ = grp.defend(test_datapoints, test_labels)
        self.assertEqual(np.unique(x == test_datapoints[0]), True)
        grp = DefenderGroup([FeasibleSetDefender(self.x,self.y, 2, False),
                             FeasibleSetDefender(self.x,self.y, 3, False)])
        x, _ = grp.defend(test_datapoints, test_labels)  
        self.assertEqual(x.shape, (0,))  

    def test_GroupDefenderEnsemble(self):
        grp = DefenderGroup([FeasibleSetDefender(self.x,self.y, 20, False),
                             FeasibleSetDefender(self.x,self.y, 20000000000, False)]
                             ,ensemble_accept_rate=0.6)
        
        test_datapoints = np.array( [[[2,2,2,6],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,7,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]], 
                            [[2,2,2,6],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]],
                            [[2,2,2,2],[2,7,2,2],
                            [2,2,120,2],[2,2,2,2]],
                            [[2,1222,2,2],[2,2,2,2],
                            [2,2,2,2],[2,2,2,2]]]).reshape(2,3,4,4)
        test_labels = np.array([0,0]).reshape(2,)
        x, _ = grp.defend(test_datapoints, test_labels)
        self.assertIsInstance(x,np.ndarray)
        self.assertEqual(np.unique(x == test_datapoints[0]), True)
        grp = DefenderGroup([FeasibleSetDefender(self.x,self.y, 20, False),
                             FeasibleSetDefender(self.x,self.y, 20000000000, False)]
                             ,ensemble_accept_rate=0.4)
        x, _ = grp.defend(test_datapoints, test_labels)  
        self.assertEqual(x.shape, test_datapoints.shape)
        grp = DefenderGroup([FeasibleSetDefender(self.x,self.y, 20000000000, False),
                             FeasibleSetDefender(self.x,self.y, 2, False)]
                             ,ensemble_accept_rate=0.4)
        x, _ = grp.defend(test_datapoints, test_labels)  
        self.assertEqual(x.shape, test_datapoints.shape)


class PointModifier_test(unittest.TestCase):
    def setUp(self) -> None:
        self.x = np.ones((16,3,4,4))
        self.y = np.zeros((16))

    def test_KNN_Defender_update_dataset(self):
        defender = KNN_Defender(init_x = self.x, init_y = self.y,
                                nearest_neighbours = 3 , confidence_threshold = 0.5)
        datapoint = np.random.rand(2,3,4,4).reshape(2,-1)
        label = np.array([0,0]).reshape(2,)
        _, _ = defender.defend(datapoint, label)
        self.assertIn(datapoint[0], defender.training_dataset_x)
        self.assertIn(datapoint[1], defender.training_dataset_x)
        self.assertEqual(defender.training_dataset_y.shape[0], self.y.shape[0] + label.shape[0])
    
    def test_KNN_Defender_same_label_output(self):

        defender = KNN_Defender(init_x = self.x, init_y = self.y,
                                nearest_neighbours = 3 , confidence_threshold = 1.0)
        datapoint = np.random.rand(2,3,4,4).reshape(2,-1)
        label = np.array([0, 1]).reshape(2,)
        model_datapoints, model_labels = defender.defend(datapoint, label)
        self.assertEqual(label.shape, model_labels.shape)
        self.assertEqual(model_datapoints.shape, datapoint.shape)
        self.assertNotIn(False, np.unique(label == model_labels))

        defender = KNN_Defender(init_x = self.x, init_y = self.y,
                                nearest_neighbours = 3 , confidence_threshold = 0.5)
        model_datapoints, model_labels = defender.defend(datapoint, label)
        self.assertNotIn(1, model_labels)
        self.assertEqual(model_datapoints.shape, datapoint.shape)

    def test_check_types(self):
        defender = KNN_Defender(init_x = self.x, init_y = self.y,
                                nearest_neighbours = 3 , confidence_threshold = 1.0)
        datapoint = np.random.rand(2,3,4,4).reshape(2,-1)
        label = np.array([0, 1]).reshape(2,)
        model_datapoints, model_labels = defender.defend(datapoint, label)
        self.assertIsInstance(model_datapoints, np.ndarray)
        self.assertIsInstance(model_labels, np.ndarray)
        test_datapoint_torch = torch.ones((2,3,4,4))
        test_label_torch = torch.zeros((2))
        model_datapoints, model_labels = defender.defend(test_datapoint_torch, test_label_torch)
        self.assertIsInstance(model_datapoints, torch.Tensor)
        self.assertIsInstance(model_labels, torch.Tensor)

# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    unittest.main()
