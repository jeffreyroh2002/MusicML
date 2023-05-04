import json
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow.keras as keras
import pickle
import os

# path to json file that stores MFCCs and genre labels for each processed segment
DATA_PATH = "../../audio_file/preprocessed/short_dataset.json"
SAVE_MODEL = True
MODEL_NAME = "model_pickle"
PICKLE_PATH = "../../saved_models/{model_name}".format(model_name = MODEL_NAME)


def load_data(data_path):

    with open(data_path, "r") as fp:
        data = json.load(fp)

    # convert lists to numpy arrays
    X = np.array(data["mfcc"])
    y = np.array(data["labels"])

    print("Data succesfully loaded!")

    return  X, y


if __name__ == "__main__":

    # load data
    X, y = load_data(DATA_PATH)

    # create train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

    # build network topology
    model = keras.Sequential([

        # input layer
        keras.layers.Flatten(input_shape=(X.shape[1], X.shape[2])),

        # 1st dense layer
        keras.layers.Dense(512, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
        keras.layers.Dropout(0.3),

        # 2nd dense layer
        keras.layers.Dense(256, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
        keras.layers.Dropout(0.3),

        # 3rd dense layer
        keras.layers.Dense(64, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
        keras.layers.Dropout(0.3),

        # output layer
        keras.layers.Dense(10, activation='softmax')
    ])

    # compile model
    optimiser = keras.optimizers.Adam(learning_rate=0.0001)
    model.compile(optimizer=optimiser,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    model.summary()

    # train model
    history = model.fit(X_train, y_train, validation_data=(X_test, y_test), batch_size=32, epochs=100, verbose=0)
	
	#extracting predictions of X_test
    prediction = model.predict(X_test)
    X_pred = np.argmax(prediction[0])
    print('X_pred = ',X_pred)
	
    if (SAVE_MODEL == True):
	    with open(MODEL_NAME,'wb') as f:
	        pickle.dump(model, f)
	    os.rename(MODEL_NAME, PICKLE_PATH)
	    print("File {model} moved to {path}".format(model = MODEL_NAME, path = PICKLE_PATH))