#!/usr/bin/env python
# coding: utf-8

# In[1]:


#load the modules
import keras
from keras import models, layers
from keras.activations import relu, softmax
from keras.applications import VGG19
from keras.models import Sequential, load_model, Model
from keras.optimizers import Adam, SGD
from keras.callbacks import ModelCheckpoint, Callback, EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Activation, Dropout, Dense, Flatten
import matplotlib.pyplot as plt
import sys
from PIL import Image
sys.modules['Image'] = Image


# ### Image generators

# #### The training dataset and the validation dataset should be in seperate folders. In each of the folders  there should be different sub-folders for each of the classes (individuals).  For example if training a model to classify 3 classes the directory of the training pictures should be:
#     PATH/TO/Training_data/
#                          Class_A/
#                                  Class_A_image1.jpg
#                                  Class_A_image2.jpg
#                                  Class_A_image3.jpg
#                                  .
#                                  .
#                                  .
#                                  
#                          Class_B/
#                                  Class_B_image1.jpg
#                                  .
#                                  .
#                                  .
#                          Class_C/
#                                  Class_C_image1.jpg
#                                  .
#                                  .
#                                  .

# In[ ]:


# Keras' data generator can be used to pass the images through the convolutional neural network and apply
#rotation and zoom transformations to the images. Check https://keras.io/preprocessing/image/ for more transformations

train_data = ImageDataGenerator(
        rotation_range=40,
        zoom_range=0.2,
        rescale = 1./255)

train_generator = train_data.flow_from_directory(
        directory=r"/PATH/TO/Training_data_set
        target_size=(224, 224),
        batch_size=8,
        shuffle=True)


# In[ ]:


#defining the validation data generator
val_data = ImageDataGenerator(rescale = 1./255)
                                 
val_generator = val_data.flow_from_directory(
        directory=r"/PATH/TO/Validation_data_set
        target_size=(224, 224),
        batch_size=8,
        shuffle=True)


# ### Convolutional neural network

# In[4]:


#load the pre-trained VGG19 from keras
vgg19 = VGG19(input_shape=(224,224,3), weights='imagenet', include_top=False)
x = vgg19.layers[-1].output
#add dropout and the fully connected layer
x = Dropout(0.5)(x)
x = Flatten()(x)
x = Dense(256, activation='relu')(x)
#add a dense layer with a value equal to the number of classes
predictors = Dense(30, activation='softmax')(x)
# Create the model
vgg19model = Model(input=vgg19.input, output=predictors)


# In[5]:


#check the model
vgg19model.summary()


# ### Model training

# In[8]:


# define where to save the model after each epoch
filepath = "PATH/TO/Saved_model.h5"
# add a critera to save only if there was an improvement in the model comparing
# to the previous epoch (in this caset the model is saved if there was a decrease in the loss value)
checkpoint = ModelCheckpoint(filepath, monitor='val_loss', verbose=1, save_best_only=True, mode='min')
# stop training if there is no improvement in model for 3 consecutives epochs.
early_stopping_monitor = EarlyStopping(patience=10)
callbacks_list = [checkpoint, early_stopping_monitor]


# In[9]:


# Compile the model
vgg19model.compile(loss='categorical_crossentropy',
              optimizer=Adam(lr=1e-5),#define the optimizer and the learning rate
              metrics=['acc'])


# In[9]:


#train the model
batch_size=8
model_history=vgg19model.fit_generator(
        train_generator,
        steps_per_epoch=27000//batch_size,#number of pictures in training data set divided by the batch size
        epochs=512,
        validation_data=val_generator,
        validation_steps= 3000// batch_size,#number of pictures in validation data set divided by the batch size
        callbacks=callbacks_list)


# #### After training the model it is possible to re-train the model with different hyperparamenters (e.g. different optimizer or learning rate) using the best trained model as a starting point. Simply, load the last saved model, compile it and start training again.
# 

# In[13]:


#load the model
model=load_model("PATH/TO/Saved_model.h5")

# Compile the model
model.compile(loss='categorical_crossentropy',
             optimizer=SGD(lr=1e-6),
             metrics=['acc'])
#train the model
batch_size=8
model_history_2=model.fit_generator(
        train_generator,
        steps_per_epoch=27000//batch_size,
        epochs=30,
        validation_data=val_generator,
        validation_steps= 3000// batch_size,
        callbacks=callbacks_list)


# #### After training it is possible to visualize the training process and check for overfitting by checking if there are large differences between the training and validation accuracy and loss values.

# In[17]:


#size of the plots
fig=plt.figure(figsize=(15,5))
columns = 2
rows = 1

#plot loss
#the accuracy and loss are stored in the "model_history"
fig.add_subplot(rows, columns, 1)
plt.plot(model_history.history['loss']+ model_history_2.history['loss']) #merge the loss from the two training steps
plt.plot(model_history.history['val_loss']+ model_history_2.history['val_loss'])
plt.title('loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')

#plot accuracy
fig.add_subplot(rows, columns, 2)
plt.plot(model_history.history['acc']+ model_history_2.history['acc'])
plt.plot(model_history.history['val_acc']+ model_history_2.history['val_acc'])
plt.title('accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()


# ### Model Generalization
# 
# #### In order to evaluate the model generalization capability, check how the model performs when exposed to images collected in diferent conditions and that were not in the training and validation datasets. Here this testing dataset will be loaded using the same image generators used at the beginning of this script for the training and validation dataset

# In[2]:


#load the best saved trained model
model=load_model("PATH/TO/Saved_model.h5")


# In[17]:


#load the testing images
#As in the training and validation datasets, the testing pictures folder should be organized in
#different sub-folders with the pictures of each individual in a different sub-folder.
#Note that a sub-folder for each of the individuals used in the training dataset should be present
#even if there are no pictures for some individuals.
val_sony_datagen1 = ImageDataGenerator(rescale = 1./255)
val_sony_datagen = val_sony_datagen1.flow_from_directory(
        directory=r"/PATH/TO/Testing_images_folder", #This folder should contain pictures of each bird in a different subfolder (similar to the training data set)
        target_size=(224, 224),
        batch_size=95,#number of images in the testing dataset
        shuffle=False)

#load the pictures in the testing folder. The x_batch contains the pictures and the y_batch contains the
#identities of the individuals
x_batch, y_batch=next(val_sony_datagen)

#create lists to store the right and the wrong classifications
right_classification=[]
wrong_classification=[]
#loop through all the testing pictures and predict the identity of the individuals
for i in range(0,len(x_batch)):
    image=np.expand_dims(x_batch[i], axis=0)
    result=model.predict(image)
    #if the predicted identity matches the real identity (from the y_batch) store the 
    #index of this pcitures in the right classification list. If different store it
    #in the wrong classification list
    if np.where(y_batch[i] == np.amax(y_batch[i]))[0][0]==np.where(result == np.amax(result))[1][0]:
        right_classification.append(i)
    else:
        wrong_classification.append(i)
#print the results
print(len(right_classification)/(len(wrong_classification)+len(right_classification)))

