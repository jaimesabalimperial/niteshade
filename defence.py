
# Written by: Mart
# Last edited: 2022/01/23
# Description: Defender class, outlines various defender classes


# =============================================================================
#  IMPORTS AND DEPENDENCIES
# =============================================================================

from typing import Type
import numpy as np
from data import DataLoader
from model import IrisClassifier
from abc import ABC, abstractmethod
import inspect
import torch
from copy import deepcopy
from sklearn.neighbors import KNeighborsClassifier


# =============================================================================
#  GLOBAL VARIABLES
# =============================================================================


# =============================================================================
#  DefenderGroup class
# =============================================================================
class DefenderGroup():
    # A class which allows the grouping of defenders through a input list containing defenders 
    def __init__(self,defender_list, ensemble_rate = 0.0) -> None:
        # Input validation
        if not isinstance(defender_list, list):
            raise TypeError ("The defender_list is not a list object.")
        if not isinstance(ensemble_rate, float):
            raise TypeError ("The ensemble_rate needs to be a float.")
        for defender in defender_list:
            if not isinstance(defender, Defender):
                raise TypeError ("All of the defenders in the defender_list need to be Defender objects.")
        
        self.defender_list = defender_list
        self.ensemble_rate = ensemble_rate
        
    def defend(self, X, y, **input_kwargs):
        # A defend method, where each defender in the list will defend (call .defend method) sequentially
        # If ensemble rate is >0, the point will only be allowed if larger proportion of defenders will pass the point (comp to ensemble rate)
        if self.ensemble_rate > 0:
            input_datapoints = deepcopy(X)
            input_labels = deepcopy(y)
            point_dict = self._initiate_dict(X, y) # Initiate a dictionary with input points, their counts and labels
            for defender in self.defender_list: # loop through the defenders for defending the points
                X, y = defender.defend(X, y, **input_kwargs)
                point_dict = self._update_dict(point_dict, X) # Update the point dictionary 
                X = deepcopy(input_datapoints)
                y = deepcopy(input_labels)
            output_x, output_y = self._get_final_points(point_dict) # Get final output points
            return (output_x, output_y)
            
        else:
            for defender in self.defender_list:
                if len(X)>0:
                    X, y = defender.defend(X, y, **input_kwargs) # Normal defending if ensemble rate =0
        return X, y
    
    def _initiate_dict(self,X, y):
        # Initiate a dictionary with points, targets and accept counts
        point_dict = {}
        for idx, points in enumerate(X):
            point_dict[str(points)] = {"point": points, "target": y[idx], "Accept_count": 0}
        return point_dict

    def _update_dict(self, point_dict, X):
        # Update point dictionary using defender decisions
        for points in X:
            if str(points) in point_dict.keys():
                point_dict[str(points)]["Accept_count"] += 1
        return point_dict

    def _get_final_points(self, point_dict):
        # Compare point dictionary accept rate with ensemble rate and output the final points that will be allowed to pass
        accepted_X = []
        accepted_Y = []
        for key, values in point_dict.items():
            if (values["Accept_count"] / len(self.defender_list)) > self.ensemble_rate:
                accepted_X.append(values["point"])
                accepted_Y.append(values["target"])
        return np.array(accepted_X), np.array(accepted_Y)
        

        
# =============================================================================
#  Defender class
# =============================================================================

class Defender(ABC):
    # General Defender abstract class
    def __init__(self) -> None:
        pass
    
    @abstractmethod
    def defend(self):
        raise NotImplementedError("Defend method needs to be implemented for a defender")


# =============================================================================
#  OutlierDefender class
# =============================================================================
class OutlierDefender(Defender):
    # Abstract class with inits for outlier defender
    def __init__(self, initial_dataset_x, initial_dataset_y) -> None:
        super().__init__()
        self._init_x = initial_dataset_x
        self._init_y = initial_dataset_y

# =============================================================================
#  ModelDefender class
# =============================================================================
class ModelDefender(Defender):
    # Abstract class for ModelDefender - Defenders that need the model to defend
    def __init__(self) -> None:
        super().__init__()

# =============================================================================
#  PointModifierDefender class
# =============================================================================
class PointModifierDefender(Defender):
    # Abstract class for PointModifierDefender - Defenders modify the points 
    def __init__(self) -> None:
        super().__init__()

# =============================================================================
#  KNN Defender class
# =============================================================================

class KNN_Defender(PointModifierDefender):
    # KNN defender that flips the points labels if the proportion of K nearest nghbs is over confidence threshold
    def __init__(self, init_x, init_y, nearest_neighbours, confidence_threshold) -> None:
        super().__init__()
        nr_of_datapoints = init_x.shape[0]
        self.training_dataset_x = init_x.reshape((nr_of_datapoints, -1))
        self.training_dataset_y = init_y.reshape((nr_of_datapoints, ))
        self.nearest_neighbours = nearest_neighbours
        self.confidence_threshold = confidence_threshold
    
    def defend(self, datapoints, input_labels):
        nr_of_datapoints = datapoints.shape[0]
        datapoints = datapoints.reshape((nr_of_datapoints, -1)) # Reshape for KNeighborsClassifier
        labels = deepcopy(input_labels).reshape((nr_of_datapoints, )) # Reshape for KNeighborsClassifier
        KNN_classifier = KNeighborsClassifier(self.nearest_neighbours) # Initiate the KNNclassifier
        KNN_classifier.fit(self.training_dataset_x, self.training_dataset_y)
        nearest_indeces = KNN_classifier.kneighbors(datapoints, return_distance=False) # Get nearest nghbs
        nearest_labels = self._get_closest_labels(nearest_indeces) # Get labels of nghbs
        confidence_list = self._calculate_confidence(nearest_labels) # Calculate the confidences for the labels
        output_labels = self._confidence_flip(labels, confidence_list) # Flip points if confidence high enough
        self.training_dataset_x = np.append(self.training_dataset_x, datapoints, axis = 0)
        self.training_dataset_y = np.append(self.training_dataset_y, output_labels, axis = 0)
        return (datapoints, output_labels)

    def _get_closest_labels(self, indeces):
        # Get labels for closest nghbs
        general_label_list = []
        for nghbs in indeces:
            label_list = []
            for index in nghbs:
                label_list.append(self.training_dataset_y[index])
            general_label_list.append(label_list)
        return np.array(general_label_list)
    
    def _calculate_confidence(self, labels):
        # Get the label with maximum nghb coount and calculate the confidence
        output_list = []
        for points in labels:
            unique_labels = list(set(points))
            max_count = 0
            max_label = -1
            for label in unique_labels:
                if list(points).count(label)>max_count:
                    max_count = list(points).count(label)
                    max_label = label
            output_list.append((max_label, max_count/len(points)))
        return output_list
    
    def _confidence_flip(self, labels, confidence_list):
        # Flip labels for points if confidence high enough
        for idx, _ in enumerate(labels):
            if confidence_list[idx][1]>self.confidence_threshold:
                labels[idx] = confidence_list[idx][0]
        return labels
# =============================================================================
#  Softmax Defender class
# =============================================================================

class SoftmaxDefender(ModelDefender):
    # Class for SoftMaxDefender
    def __init__(self, threshold = 0.05) -> None:
        super().__init__()
        #Input validation
        if not (isinstance(threshold, float) or isinstance(threshold, int)):
            raise TypeError ("The threshold input for the SoftmaxDefender needs to be either float or a integer type.")
        self.threshold = threshold

    def defend(self, datapoints, labels, model, **input_kwargs):
        # Rejects points if the softmax output of the label is lower than threshold. 

        #convert np.ndarray to tensor for the NN
        X_batch = torch.tensor(datapoints)
        # Assume onehot for labels currently!!
        class_labels = torch.tensor(np.argmax(labels, axis = 1).reshape(-1,1))# Get class labels from onehot
        #zero gradients so they are not accumulated across batches
        model.optimizer.zero_grad()
        # Performs forward pass through classifier
        outputs = model.forward(X_batch.float())
        confidence = torch.gather(outputs, 1 , class_labels) # Get softmax output for class labels
        mask = (confidence>self.threshold).squeeze(1) #mask for points true if confidence>threshold
        X_output = X_batch[mask].detach().numpy() # Get output points using mask
        y_output = labels[mask.numpy()]
        return (X_output, y_output)

# =============================================================================
#  FeasibleSetDefender class
# =============================================================================

class FeasibleSetDefender(OutlierDefender):
    #Extremely simple class_mean_based outlier detector
    def __init__(self, initial_dataset_x, initial_dataset_y, threshold, one_hot = False, dist_metric = "Eucleidian") -> None:
        super().__init__(initial_dataset_x, initial_dataset_y)
        #Input validation
        if not (isinstance(threshold, float) or isinstance(threshold, int)):
            raise TypeError ("The threshold input for the FeasibleSetDefender needs to be either float or a integer type.")
        self.one_hot = one_hot
        if self.one_hot: # Perform encoding of labels into ints if input is onehot
            self._label_encoding()
        else:
            initial_dataset_y = initial_dataset_y.reshape(-1,)        
        self._feasible_set_construction() # Construct the feasible set
        self._threshold = threshold
        if isinstance(dist_metric, str): # Check if input is a dist_metric type (string) or a custom defined distance metric object
            self.distance_metric = Distance_metric(dist_metric)
        elif isinstance(dist_metric, Distance_metric): 
            self.distance_metric = dist_metric
        else:
            raise TypeError ("The Distance metric input for the FeasibleSetDefender needs to be either a string or a Distance_metric object.")
    
    @property 
    def distance_metric(self): # Make distance metric into a property
        return self.__distance_metric._type

    @distance_metric.setter # Setter function for the distance metric
    def distance_metric(self, new_distance_metric):
        self.__distance_metric = new_distance_metric


    def _label_encoding(self):
        # Label encoding from onehot
        self._init_y=np.argmax(self._init_y, axis = 1)

    def _feasible_set_construction(self):
        #Construct centroids using init_x and init_y
        # centroids are just means of all points with a label
        # Also implement label counts for later centroid adjustment
        labels = np.unique(self._init_y)
        feasible_set = {}
        label_counts = {}
        for label in labels:
            label_rows = (self._init_y == label)
            label_counts[label] = np.sum(label_rows)
            feasible_set[label] = np.mean(self._init_x[label_rows], 0)
        self.feasible_set = feasible_set
        self._label_counts = label_counts

    def _feasible_set_adjustment(self, datapoint, label):
        #Adjust running means of feasible set (the centroids) using previous label counts and input new datapoints and labels
        label_mean = self.feasible_set[label]
        self._label_counts[label]+=1
        new_mean = label_mean + (datapoint-label_mean)/self._label_counts[label]
        self.feasible_set[label] = new_mean
    
    def _distance_metric_calculator(self,datapoint, label):
        #Calculate the distance metric for the datapoint from the feasible set mean
        label_mean = self.feasible_set[label]
        distance = self.__distance_metric.distance(datapoint, label_mean)
        return distance
    
    def defend(self, datapoints, labels, **input_kwargs):
        #Reject datapoint using the feasible set centroids for labels
        if self.one_hot: #Change labels if onehot
            one_hot_length = len(labels[0])
            labels = np.argmax(labels, axis = 1)
        else:
            labels = labels.reshape(-1,)
        cleared_datapoints = []
        cleared_labels = []
        for id, datapoint in enumerate(datapoints): # loop through datapoints
            data_label = labels[id]
            # Calculate distances for datapoints from label means in feasible set
            distance = self._distance_metric_calculator(datapoint, data_label)
            if distance < self._threshold:
                # If distance is less than threshold, accept point and adjust feasible set using the new point
                self._feasible_set_adjustment(datapoint, data_label)
                cleared_datapoints.append(datapoint)
                cleared_labels.append(data_label)
        if len(cleared_labels) == 0:
            # If no points cleared, return empty arrays
            return (np.array([]), np.array([]))
        cleared_labels_stack = np.stack(cleared_labels)

        if self.one_hot: # If onehot, construct onehot output
            output_labels = np.zeros((len(cleared_labels_stack), one_hot_length))
            for id,label in enumerate(cleared_labels_stack):
                output_labels[id][label] = 1
            cleared_labels_stack = output_labels
        # Returns a tuple of np array of cleared datapoints and np array of cleared labels
        return (np.stack(cleared_datapoints), cleared_labels_stack)
        

# =============================================================================
#  Distance_metric class
# =============================================================================
class Distance_metric:
    # Distance metric class for the feasibleset defender
    # Allows to define custom distance metrics, they need to have distance method
    def __init__(self, type = None) -> None:
        self._type = type
        
    def distance(self, input_1, Input_2):
        # Calculate distance given the type, currently only L2 norm implemented
        if self._type == "Eucleidian":
            return np.sqrt(np.sum((input_1 - Input_2)**2))
        else:
            raise NotImplementedError ("This distance metric type has not been implemented")

# =============================================================================
#  FUNCTIONS
# =============================================================================

# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import defender_tests
    import unittest
    suite = unittest.TestLoader().loadTestsFromModule(defender_tests)
    unittest.TextTestRunner(verbosity=2).run(suite)