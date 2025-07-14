import os.path

import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Dropout
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import joblib
from datetime import datetime
import regex as re
import json
import shutil


def anamoly_limits(data, multiplier=3):
    try:
        data = sorted(data)
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = round(q1 - int(multiplier) * iqr, 2)
        upper_bound = round(q3 + int(multiplier) * iqr, 2)
        #print("#######################################",lower_bound, upper_bound, round(57.81259999999999,2))
        return {
            'status': True,
            'upper_limit': upper_bound,
            'lower_limit': lower_bound,
            'q3': q3,
            'q1': q1,
        }
    except Exception as E:
        return {
            'status': False,
            'error': E
        }


def predictor(prediction_data, path, sequence_length, no_of_pred=1, result=False):
    model_path = ''
    scaler_path = ''
    predictions = []
    if os.path.exists(path):
        print(path)
        for file in os.listdir(path):
            if file.split('.')[-1] == 'h5':
                model_path = f'{path}/{file}'
            elif file.split('.')[-1] == 'pkl':
                scaler_path = f'{path}/{file}'
        if model_path != '' and scaler_path != '':

            if len(prediction_data) == sequence_length:
                try:
                    for i in range(no_of_pred):
                        data = np.array(prediction_data).reshape(-1, 1)
                        train_data_scaler = joblib.load(scaler_path)
                        scaled = train_data_scaler.transform(data)
                        shaped = np.array(scaled).reshape((1, sequence_length, 1))
                        model = load_model(model_path)
                        prediction = model.predict(shaped)
                        descaled_prediction = train_data_scaler.inverse_transform(prediction)
                        predictions.append(descaled_prediction.tolist()[0][0])
                        prediction_data.pop(0)
                        prediction_data.append(descaled_prediction.tolist()[0][0])
                    if result: return True, predictions
                    return True, path
                except Exception as e:
                    return False, f'Error : {e}'
            else:
                return False, f'expected sequence length {sequence_length} got {len(prediction_data)}'
        else:
            return False, f'Model/scaler files not found'
    else:
        return False, f'{path} path not exist'

class ModelBuilder:
    def __init__(self, element, path='default/', epochs=100, sequence_length=10):
        self.scaler = None
        self.batch_size = 32
        self.epochs = epochs
        self.loss = 'mean_squared_error'
        self.optimizer = 'adam'
        self.sequence_length = sequence_length
        self.path = path
        self.train_split_percentage = 0.8
        self.data = None
        self.element = element
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_path = ''
        if self.path[-1] != '/':
            self.path = path + '/'
        print(self.path)

    def pre_checks(self):
        if os.path.exists(self.path):
            return 'something wrong default path not exists'

    def preprocessing_data(self, data):
        data = np.array(data)
        data = data.reshape(-1, 1)
        normalised_data = self.scaler.fit_transform(data)
        print("fit transform", normalised_data[:10])
        print("Inverse ", self.scaler.inverse_transform(normalised_data[:10]))
        X, y = [], []
        for i in range(len(normalised_data) - self.sequence_length):
            X.append(normalised_data[i:(i + self.sequence_length)])
            y.append(normalised_data[i + self.sequence_length])
        print("Preprocessing completed")
        return np.array(X), np.array(y)

    def create_model(self, X, y):
        try:
            model_metrics = {}
            model = Sequential()
            model.add(LSTM(50, activation='relu', input_shape=(self.sequence_length, 1)))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            model.summary()
            history = model.fit(X, y, epochs=self.epochs)
            main_path = f'{self.path}{str(datetime.now().strftime("%Y%m%d%H%M%S"))}'
            if not os.path.exists(main_path): os.makedirs(main_path)
            model_metrics = {'loss': history.history['loss'], }
            with open(f'{main_path}/{self.element}_metrics.json', 'w') as json_file:
                json.dump(model_metrics, json_file, indent=4)
            model.save(f'{main_path}/{self.element}-{self.epochs}-{self.sequence_length}.h5')
            joblib.dump(self.scaler, f'{main_path}/{self.element}_scaler.pkl')
            self.model_path = main_path
            return predictor(self.data[-self.sequence_length:], main_path, self.sequence_length)
        except Exception as e:
            return False, e

    def build_model(self, input_data):
        self.data = input_data
        X, y = self.preprocessing_data(self.data)
        return self.create_model(X, y)


if __name__ == '__main__':
    data = [i for i in range(1000)]

    test = [900, 901, 902, 903, 904, 905, 906, 907, 908, 909]
    LSTM_B = ModelBuilder('n15', 'sanjay/', data, 100)
    anamoly_limits(test)
    # # LSTM_B.build_model()
    A = predictor([3.0 , 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.25], 'all_models/AZD/20250128114030/', 10,
             no_of_pred= 10 , result=True)
    print(A)