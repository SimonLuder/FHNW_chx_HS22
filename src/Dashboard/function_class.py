from asyncio.windows_events import NULL
import datetime
import requests
import pandas as pd
import openrouteservice as ors
import json
from torch import nn
import torch
import os
import torch.nn.functional as F

class CNNForecaster(nn.Module):
    def __init__(self, kernel_size=3, pool_size=2, padding=0, conv1_channels = 120, 
                 conv2_channels=120, conv3_channels=120, fc_linear_1=180, dropout=0.4):
        '''Convolutional Net class'''
        super(CNNForecaster, self).__init__()
        
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=conv1_channels, kernel_size=kernel_size, padding=padding) 
        self.conv2 = nn.Conv1d(in_channels=conv1_channels, out_channels=conv2_channels, kernel_size=kernel_size, padding=padding) 
        self.conv3 = nn.Conv1d(in_channels=conv2_channels, out_channels=conv3_channels, kernel_size=kernel_size, padding=padding) 
        
        self.pool = nn.MaxPool1d(kernel_size=pool_size, stride=1)
        
        self.fc1 = nn.Linear(in_features=conv3_channels*15, out_features=fc_linear_1)
        self.fc2 = nn.Linear(in_features=fc_linear_1, out_features=1)
        
        self.conv3_channels = conv3_channels
        
        self.dropout = nn.Dropout(p=dropout)
        
        self.flatten = nn.Flatten()
        
    def forward(self, x):
        '''
        Applies the forward pass
        Args:
            x (torch.tensor): input feature tensor
        Returns:
            x (torch.tensor): output tensor of size num_classes
        '''
        x = x.reshape(x.shape[0], 1, x.shape[1])
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = self.flatten(x)
        
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class prediction:
    def __init__(self):
        self.parkings = {}
        self.current_occupation = {}
        self.max_parkings = {'Parkhaus Aeschen': 97.0,
                            'anfos': 162.0,
                            'badbahnhof': 750.0,
                            'bahnhofsued': 100.0,
                            'centralbahnparking': 286.0,
                            'city': 1114.0,
                            'clarahuus': 52.0,
                            'Parkhaus Claramatte': 170.0,
                            'elisabethen': 840.0,
                            'europe': 120.0,
                            'kunstmuseum': 350.0,
                            'messe': 752.0,
                            'postbasel': 72.0,
                            'rebgasse': 250.0, 
                            'steinen': 526.0,
                            'storchen': 142.0}
        self.vocab = {'Parkhaus Aeschen': 'Parkhaus Aeschen',
                        'Parkhaus Anfos': 'anfos',
                        'Parkhaus Bad. Bahnhof': 'badbahnhof',
                        'Parkhaus Bahnhof Süd': 'bahnhofsued',
                        'Parkhaus Centralbahnparking': 'centralbahnparking',
                        'Parkhaus City': 'city',
                        'Parkhaus Clarahuus': 'clarahuus',
                        'Parkhaus Claramatte': 'Parkhaus Claramatte',
                        'Parkhaus Elisabethen': 'elisabethen',
                        'Parkhaus Europe': 'europe',
                        'Parkhaus Kunstmuseum': 'kunstmuseum',
                        'Parkhaus Messe': 'messe',
                        'Parkhaus Post Basel': 'postbasel',
                        'Parkhaus Rebgasse': 'rebgasse',
                        'Parkhaus Steinen': 'steinen',
                        'Parkhaus Storchen': 'storchen'}
        self.vocab_i = {i: j for j, i in self.vocab.items()}

    def predict(self):
        data = self._get_data()
        for i in list(data.parkings):
            model = CNNForecaster()
            model.load_state_dict(torch.load(os.path.join(os.getcwd(), 'src', 'Dashboard', 'models', self.vocab_i[i] + '_cnn.pth')))
            model.eval()
            data_park = data[data['parkings'] == i]['available'].to_list()[0].strip().strip('][').split(',')
            self.parkings[i] = model(torch.FloatTensor([[float(i.strip())] for i in data_park]).reshape(1, -1)).item()
        av_data = list(map(lambda x: x.strip().strip(']').strip('[').split(','), data['available'].values))
        av_data = list(map(lambda x: float(x[-1]), av_data))
        self.current_occupation = dict(zip(data.parkings.values, av_data))
        return self.current_occupation

    def get_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_data(self):
        data = pd.read_csv(os.path.join(os.getcwd(), 'src', 'Dashboard', 'test_data.csv'), sep=':')
        data.columns = ["parkings", "available"]
        data.parkings = data.parkings.apply(lambda x: self.vocab[x.strip("'")])
        return data

    def get_free_parkings(self):
        available = self.predict()
        free_parkings = [park[0] for park in self.parkings.items() if park[1] < (self.max_parkings[park[0]]-5)]
        return free_parkings, self.parkings, available, self.max_parkings
        # return ['aeschen', 'anfos', 'badbahnhof', 'bahnhofsued', 'centralbahnparking', 'city', 'clarahuus', 'elisabethen', 'europe', 'kunstmuseum', 'messe', 'postbasel', 'rebgasse', 'steinen', 'storchen']


class distance:
    def __init__(self, location: list, parkings_with_free_spots: list):
        self.all_parkings = {'aeschen': [7.5943046, 47.5504299],
                            'anfos': [7.593512, 47.5515968],
                            'badbahnhof': [7.6089067, 47.5651794],
                            'bahnhofsued': [7.5884556, 47.5458851],
                            'centralbahnparking': [7.5922975, 47.547299],
                            'city': [7.5824076, 47.561101],
                            'clarahuus': [7.5917937, 47.5622725],
                            'elisabethen': [7.5874932, 47.5506254],
                            'europe': [7.5967098, 47.5630411],
                            'kunstmuseum': [7.5927014, 47.5545146],
                            'messe': [7.602175, 47.563241],
                            'postbasel': [7.5929374, 47.5468617],
                            'rebgasse': [7.594263, 47.5607142],
                            'steinen': [7.5858936, 47.5524554],
                            'storchen': [7.58658, 47.5592347]}
        self.parkings = {k: v for k, v in self.all_parkings.items() if k in parkings_with_free_spots}
        self.location = location
        self.distance = {}
        self.__client = '5b3ce3597851110001cf624861b0095d93d34e199ad718c53eb21e01'

    def get_distances(self):
        '''
        Calculates the distance between two points.
        Args:
            parking (str): name of the parking
        '''
        body = {"locations":[self.location, *self.parkings.values()]}
        headers = {'Authorization': self.__client}
        
        # get distance in seconds
        call = requests.post('https://api.openrouteservice.org/v2/matrix/foot-walking', json=body, headers=headers)
        output = call.json()
        self.distance = {j:i for i, j in zip(output['durations'][0][1:], list(self.parkings.keys()))}

    def get_closest_parking(self):
        '''
        Returns the closest parking.
        '''
        self.get_distances()
        return min(self.distance, key=self.distance.get), min(self.distance.values())


class route:
    def __init__(self, location: list):
        self.__client = ors.Client(key='5b3ce3597851110001cf624861b0095d93d34e199ad718c53eb21e01')
        self.all_parkings = {'aeschen': [7.5943046, 47.5504299],
                            'anfos': [7.593512, 47.5515968],
                            'badbahnhof': [7.6089067, 47.5651794],
                            'bahnhofsued': [7.5884556, 47.5458851],
                            'centralbahnparking': [7.5922975, 47.547299],
                            'city': [7.5824076, 47.561101],
                            'clarahuus': [7.5917937, 47.5622725],
                            'elisabethen': [7.5874932, 47.5506254],
                            'europe': [7.5967098, 47.5630411],
                            'kunstmuseum': [7.5927014, 47.5545146],
                            'messe': [7.602175, 47.563241],
                            'postbasel': [7.5929374, 47.5468617],
                            'rebgasse': [7.594263, 47.5607142],
                            'steinen': [7.5858936, 47.5524554],
                            'storchen': [7.58658, 47.5592347]}
        self.location = location

    def get_route(self, parking: str):
        '''
        Calculates the route between two points.
        Args:
            parking (str): name of the parking
        '''
        route = self.__client.directions(
            coordinates=[self.location, self.all_parkings[parking]],
            profile='driving-car',
            format='geojson')
        return route['features'][0]['geometry']['coordinates']


class parking_route:
    def __init__(self, current_location_: list, wanted_location_: list):
        self.current_location_ = current_location_
        self.wanted_location_ = wanted_location_
    
    def get_free_parkings_prediction(self):
        '''
        Returns all parkings with free spots. (list with names)
        '''
        valid_parkings, preds, available, max_parkings = prediction().get_free_parkings()
        return valid_parkings, available, preds, max_parkings

    def get_closest_parking_calculation(self):
        '''
        Returns the closest parking.
        '''
        valid_parkings, available, preds, max_parkings = self.get_free_parkings_prediction()
        closest_parking = distance(self.wanted_location_, valid_parkings).get_closest_parking()
        return *closest_parking, available[closest_parking[0]], preds[closest_parking[0]], max_parkings[closest_parking[0]]

    def get_route_to(self):
        '''
        Returns the route to the closest parking.
        '''
        close, time, available, preds, max_parking = self.get_closest_parking_calculation()
        return route(self.current_location_).get_route(close), time, close, available, preds, max_parking