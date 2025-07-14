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


def predictor( prediction_data, path):
    model_path = ''
    scaler_path = ''
    seq_length = ''
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.split('.')[-1] == 'h5':
                model_path = f'{path}/{file}'
                match = re.search(r'-(\d+)\.', file)
                if match:
                    seq_length = match.group(1)
                else:
                    return [False , 'Model name doest contain seq length']
            elif file.split('.')[-1] == 'pkl':
                scaler_path = f'{path}/{file}'
        if model_path != '' and scaler_path != '':
            print(f'Raw data {prediction_data}')
            train_data_scaler = joblib.load(scaler_path)
            model = load_model(model_path)
            input_data = np.array(prediction_data).reshape((1, int(seq_length), 1))
            prediction = model.predict(input_data)
            descaled_prediction = train_data_scaler.inverse_transform(prediction)
            print(descaled_prediction)
            return [True, path , descaled_prediction]
        else:
            return [False, 'model/scaler not exists']
    else:
        return [False, 'path not exists']


class ModelBuilder:
    def __init__(self, element, path, input_data, epochs=100, ):
        self.scaler = None
        self.batch_size = 32
        self.epochs = epochs
        self.loss = 'mean_squared_error'
        self.optimizer = 'adam'
        self.sequence_length = 10
        self.path = path
        self.train_split_percentage = 0.8
        self.data = input_data
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
        # normalised_data = self.scaler.fit_transform(data)
        normalised_data = np.array(data)
        normalised_data = normalised_data.reshape(-1, 1)
        print(f"reshape data and {normalised_data.shape} {normalised_data}")
        X, y = [], []
        for i in range(len(normalised_data) - self.sequence_length):
            X.append(normalised_data[i:(i + self.sequence_length)])
            y.append(normalised_data[i + self.sequence_length])
        print("Preprocessing completed")
        return np.array(X), np.array(y)

    def create_model(self, X, y):
        model = Sequential()
        model.add(LSTM(50, activation='relu', input_shape=(self.sequence_length, 1)))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mean_squared_error')
        model.summary()
        model.fit(X, y, epochs=self.epochs)
        main_path = f'{self.path}{str(datetime.now().strftime("%Y%m%d%H%M%S"))}'
        if not os.path.exists(main_path):os.makedirs(main_path)
        model.save(f'{main_path}/{self.element}-{self.epochs}-{self.sequence_length}.h5')
        joblib.dump(self.scaler, f'{main_path}/{self.element}_scaler.pkl')
        self.model_path = main_path
        return self.predict(self.data[-self.sequence_length:], main_path)

    def predict(self, prediction_data, path):
        model_path = ''
        scaler_path = ''
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.split('.')[-1] == 'h5':
                    model_path = f'{path}/{file}'
                elif file.split('.')[-1] == 'pkl':
                    scaler_path = f'{path}/{file}'
            if model_path != '' and scaler_path != '':
                print(f'Raw data {prediction_data}')
                # train_data_scaler = joblib.load(scaler_path)

                model = load_model(model_path)
                input_data = np.array(prediction_data).reshape((1, self.sequence_length, 1))
                prediction = model.predict(input_data)
                # descaled_prediction = self.scaler.inverse_transform(prediction)
                print(prediction)
                return True , path
            else:
                return False , 'model/scaler not exists'
        else:
            return False , 'path not exists'

    def build_model(self):
        X, y = self.preprocessing_data(self.data)
        return self.create_model(X, y)


if __name__ == '__main__':
    data = [i for i in range(100)]
    LSTM_B = ModelBuilder('n15', 'sanjay/', data, 100).build_model()

