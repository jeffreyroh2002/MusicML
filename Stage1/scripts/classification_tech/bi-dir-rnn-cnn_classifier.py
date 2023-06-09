import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels
import tensorflow as tf
import tensorflow.keras as keras
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

####EDIT BEFORE RUNNING ###########
# path to json file that stores MFCCs and genre labels for each processed segment
DATA_PATH = "../../audio_file/preprocessed/full_dataset0510.json"
SAVE_MODEL = True
SAVE_HM = True

#OUTPUT DIR/FILE NAMES
NEWDIR_NAME = "genre_bi-dir-rnn-cnn-0708-50epochs"

MODEL_NAME = "saved_model"
HM_NAME = "heatmap.png"
A_PLOT_NAME = 'accuracy.png'
L_PLOT_NAME = 'loss.png'

# Hyperparameters
LEARNING_RATE = 0.0001
EPOCHS = 100

####################################

#create new dir in results dir for results
NEWDIR_PATH = os.path.join("../../results", NEWDIR_NAME)
if not os.path.exists(NEWDIR_PATH):
    os.makedirs(NEWDIR_PATH)

def load_data(data_path):
    with open(data_path, "r") as fp:
        data = json.load(fp)

    # convert lists to numpy arrays
    X = np.array(data["mfcc"])
    y = np.array(data["labels"])
    label_list = data.get("mapping", {})   #Jazz, Classical, etc

    print(label_list)

    print("Data successfully loaded!")

    return X, y, label_list

def save_plot(history, newdir_path=NEWDIR_PATH, a_plot_name=A_PLOT_NAME, l_plot_name=L_PLOT_NAME):
    # Outputting graphs for Accuracy
    plt.figure()
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('model train_accuracy vs val_accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'val'], loc='upper left')
    plt.savefig(os.path.join(newdir_path, a_plot_name))
    plt.close()

    # Outputting graphs for Loss
    plt.figure()
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model train_loss vs val_loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'val'], loc='upper left')
    plt.savefig(os.path.join(newdir_path, l_plot_name))
    plt.close()

def get_heatmap(model, X_test, y_test, newdir_path, hm_name, label_list):
    prediction = model.predict(X_test)
    y_pred = np.argmax(prediction, axis=1)

    labels = sorted(label_list)  # Sort the labels
    column = [f'Predicted {label}' for label in labels]
    indices = [f'Actual {label}' for label in labels]
    table = pd.DataFrame(confusion_matrix(y_test, y_pred), columns=column, index=indices)

    plt.figure()
    hm = sns.heatmap(table, annot=True, fmt='d', cmap='viridis')
    plt.savefig(os.path.join(newdir_path, hm_name))
    plt.close()
    print("Heatmap generated and saved in {path}".format(path=NEWDIR_PATH))

def prepare_cnn_datasets(test_size, validation_size):
    # load data
    X, y, label_list = load_data(DATA_PATH)

    # create train, validation, and test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
    X_train, X_validation, y_train, y_validation = train_test_split(X_train, y_train, test_size=validation_size)

    
    # add an axis to input sets (CNN requires 3D array)
    X_train = X_train[..., np.newaxis]    #4d array -> (num_samples, 130, 13, 1)
    X_validation = X_validation[..., np.newaxis]
    X_test = X_test[..., np.newaxis]

    return X_train, X_validation, X_test, y_train, y_validation, y_test, label_list
    
def prepare_rnn_datasets(test_size, validation_size):

    # load data
    X, y, label_list = load_data(DATA_PATH)

    # create train, validation, and test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
    X_train, X_validation, y_train, y_validation = train_test_split(X_train, y_train, test_size=validation_size)

    return X_train, X_validation, X_test, y_train, y_validation, y_test, label_list

def create_combined_model(cnn_input_shape, rnn_input_shape, num_classes, hidden_size):
    cnn_input = keras.Input(shape=cnn_input_shape)
    rnn_input = keras.Input(shape=rnn_input_shape)

    cnn_model = keras.layers.Conv1D(filters=64, kernel_size=3, strides=1, padding='same')(cnn_input)
    cnn_model = keras.layers.ReLU()(cnn_model)
    cnn_model = keras.layers.MaxPooling1D(pool_size=2, strides=2)(cnn_model)
    cnn_model = keras.layers.Conv1D(filters=128, kernel_size=3, strides=1, padding='same')(cnn_model)
    cnn_model = keras.layers.ReLU()(cnn_model)
    cnn_model = keras.layers.MaxPooling1D(pool_size=2, strides=2)(cnn_model)
    cnn_model = keras.layers.Flatten()(cnn_model)
    cnn_model = keras.layers.Dense(128)(cnn_model)
    cnn_model = keras.layers.ReLU()(cnn_model)

    #rnn_model = keras.layers.LSTM(units=hidden_size, return_sequences=True)(rnn_input)
    
    rnn_model = keras.layers.Bidirectional(keras.layers.GRU(units=hidden_size, return_sequences=True))(rnn_input)
    rnn_model = keras.layers.Bidirectional(keras.layers.GRU(units=hidden_size))(rnn_model)
    rnn_model = keras.layers.Dense(128, activation='relu')(rnn_model)
    rnn_model = keras.layers.Dropout(0.3)(rnn_model)

    combined = keras.layers.concatenate([cnn_model, rnn_model])
    output = keras.layers.Dense(num_classes, activation='softmax')(combined)

    model = keras.Model(inputs=[cnn_input, rnn_input], outputs=output)
    return model

    
"""
def create_cnn(input_shape):
    cnn_model = keras.Sequential()

    cnn_model.add(keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
    cnn_model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
    cnn_model.add(keras.layers.BatchNormalization())

    cnn_model.add(keras.layers.Conv2D(32, (3, 3), activation='relu'))
    cnn_model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
    cnn_model.add(keras.layers.BatchNormalization())

    cnn_model.add(keras.layers.Conv2D(32, (3, 3), activation='relu'))
    cnn_model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
    cnn_model.add(keras.layers.BatchNormalization())

    cnn_model.add(keras.layers.Flatten())
    return cnn_model

# Define the bi-directional RNN model
def create_rnn(input_shape):
    rnn_model = keras.Sequential()
    rnn_model.add(keras.layers.Bidirectional(keras.layers.GRU(128, return_sequences=True), input_shape=input_shape))
    rnn_model.add(keras.layers.Bidirectional(keras.layers.GRU(128)))
    return rnn_model



# Define the combined model
def create_combined_model(cnn_input_shape, rnn_input_shape, num_classes):
    cnn_model = create_cnn(cnn_input_shape)
    rnn_model = create_rnn(rnn_input_shape)

    combined_model = keras.Sequential()
    combined_model.add(keras.layers.concatenate([cnn_model.output, rnn_model.output]))
    combined_model.add(keras.layers.Dense(128, activation='relu'))
    combined_model.add(keras.layers.Dense(num_classes, activation='softmax'))

    return combined_model
"""

def predict(model, X, y):
    """Predict a single sample using the trained model

    :param model: Trained classifier
    :param X: Input data
    :param y (int): Target
    """
    # add a dimension to input data for sample - model.predict() expects a 4d array in this case

    X = X[np.newaxis, ...] # array shape (1, 130, 13, 1)

    # perform prediction
    prediction = model.predict(X)

    # get index with max value
    predicted_index = np.argmax(prediction, axis=1)

    print("Target: {}, Predicted label: {}".format(y, predicted_index))

    
if __name__ == "__main__":
    # create train, val, test sets
    cnn_X_train, cnn_X_validation, cnn_X_test, cnn_y_train, cnn_y_validation, cnn_y_test, cnn_label_list = prepare_cnn_datasets(0.25, 0.2)
    rnn_X_train, rnn_X_validation, rnn_X_test, rnn_y_train, rnn_y_validation, rnn_y_test, rnn_label_list = prepare_rnn_datasets(0.25, 0.2)

    # Set random seed for reproducibility
    np.random.seed(42)
    tf.random.set_seed(42)

    # Define the input shapes and number of classes
    cnn_input_shape = (cnn_X_train.shape[1], cnn_X_train.shape[2], 1) # Assumes input audiofeatures of shape (num_timesteps, num_features)
    rnn_input_shape = (rnn_X_train.shape[1], rnn_X_train.shape[2])
    
    # Define the hidden size for LSTM layers
    hidden_size = 64
    
    num_classes = 9  # Number of music genres
    
    # Create the combined model
    model = create_combined_model(cnn_input_shape, rnn_input_shape, num_classes, hidden_size)

    optimiser = keras.optimizers.Adam(learning_rate=LEARNING_RATE)

    # Compile the model
    model.compile(optimizer=optimiser,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    # Print the model summary
    model.summary()

    # Train the model
    history = model.fit([cnn_X_train, rnn_X_train], cnn_y_train, validation_data=([cnn_X_validation, rnn_X_validation], cnn_y_validation),
                        batch_size=32, epochs=EPOCHS, verbose=1)
    
    print("Finished Training Model!")

    
    # Print validation loss and accuracy
    val_loss, val_acc = model.evaluate(cnn_X_validation, cnn_y_validation)
    print("Validation Loss:", val_loss)
    print("Validation Accuracy:", val_acc)

    # Plot history
    save_plot(history)

    # Evaluate model on test set
    test_loss, test_acc = model.evaluate(cnn_X_test, cnn_y_test, verbose=2)
    print('\nTest accuracy:', test_acc)

    # Pick a sample to predict from the test set
    X_to_predict = cnn_X_test[10]
    y_to_predict = cnn_y_test[10]

    # Predict sample
    #predict(model, X_to_predict, y_to_predict)

    # Save model
    if SAVE_MODEL:
        model.save(os.path.join(NEWDIR_PATH, MODEL_NAME))
        print("Model saved to disk at:", os.path.join(NEWDIR_PATH, MODEL_NAME))

    # Output heatmap
    if SAVE_HM:
        get_heatmap(model, cnn_X_test, cnn_y_test, NEWDIR_PATH, HM_NAME, label_list)