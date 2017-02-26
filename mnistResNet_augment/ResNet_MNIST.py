# coding: utf-8

# # Assignment 2 - MNIST
# 
# ## 3 Read the data
# The images are provided in a non-standardized binary format. You can download a python script from studip (03 mnist.py), which reads the data for you, or you can implement your own script, following the description of the file format on the MNIST database homepage.
# Make sure to modify the script such that you retrieve a training dataset, a validation dataset and the test dataset separately.

# In[84]:

import tensorflow as tf
import numpy as np
import os
from scipy import misc
from PIL import Image
import time
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.core.protobuf import saver_pb2

mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)





#dir_train = r"C:\Users\mpariani\Documents\UnivOsnabrueck\Third_Semester\ANNs_TensorFlow\TrainData/"
dir_train = "TrainDataSmall/"
#dir_test = r"C:\Users\mpariani\Documents\UnivOsnabrueck\Third_Semester\ANNs_TensorFlow\TestData/"
dir_test = "TestDataSmall/"

netName = 'mnistResNet_augment'
if not os.path.exists('./'+netName):
    os.makedirs('./'+netName)


def augment(batch,mu=0,sigma=0.0001):
        '''
        This augmentation function is inspired by: Krizhevsky et al. (2012): ImageNet 
            Classification with Deep Convolutional Neural Networks
        This function receives a batch of images (np.array of size [BatchSize,112,112,3]) 
        and performs the following augmentation steps (on the fly, for each img):
            1. Color Augmentation based on channel-wise PCA of entire dataset.
                VarianceIncreaser + NoiseAdder
            2. Binarizes about flipping vertically
            3. Rotation within range of [-25,25] degree
        The optional parameters mu and sigma define the average and the spread in the noise added
        to each RGB channel  '''


        batchSize = batch.shape[0]

        # Allocate array for augmented images 
        batchP = np.empty([batchSize,batch.shape[1],batch.shape[2],batch.shape[3]],dtype=np.uint8)

        # Restore PCA results that has been performed beforehand on entire dataset
        eigenvalues = np.loadtxt('eigenvalues.txt')
        eigenvectors = np.loadtxt('eigenvectors.txt')

        # generate stochastic noise (alpha samples)
        samples = np.random.normal(mu,sigma,[batchSize,3])
        augmentation = samples * eigenvalues # scale by eigenvalue

        # augment every image
        for ind,img in enumerate(batch):
            # RGB augmentation via PCA (increase variance, tune luminance+color invariance)
            noise = np.dot(eigenvectors,augmentation[ind])
            #img = img + noise # Add color perturbation to image

            # Flip horizontally (eventually)
            #img = np.fliplr(img) if np.random.randint(2) else img

            # Rotate randomly 
            dg = np.random.randint(0,15) if np.random.randint(2) else -np.random.randint(0,15)
            batchP[ind] = misc.imrotate(img, dg)

        return batchP







#sess = tf.InteractiveSession()


def weight_variable(shape):
  initial = tf.truncated_normal(shape, stddev=0.1)
  return tf.Variable(initial)

def bias_variable(shape):
  initial = tf.constant(0.1, shape=shape)
  return tf.Variable(initial)

'''
def conv2d(x, W):
  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')
'''
def conv2d(x, W, strideX = 1, strideY = 1):
  '''
  Convolution and batch normalization
  '''
  conv = tf.nn.conv2d(x, W, strides=[1, strideX, strideY, 1], padding='SAME')
  mean, var = tf.nn.moments(conv, [0, 1, 2])
  activation = tf.nn.batch_normalization(conv, mean, var, None, None, 1e-3)
  return activation

def max_pool_2x2(x):
  return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                        strides=[1, 2, 2, 1], padding='SAME')




x = tf.placeholder(tf.float32, shape=[None, 28, 28, 3])
y_ = tf.placeholder(tf.float32, shape=[None, 10])
lr = tf.placeholder(tf.float32)
keep_prob = tf.placeholder(tf.float32)




#image  = tf.reshape(x,[-1,28,28,3])

# For "global normalization" used with convolutional
#   filters with shape [batch, height, width, depth], pass axes=[0, 1, 2].
mean, var = tf.nn.moments(x, [0, 1, 2])
image = tf.nn.batch_normalization(x, mean, var, None, None, 1e-3)
#image = x


# 6 convolutions - 64 kernels (3x3)
W_conv1 = weight_variable([3,3,3,64])
b_conv1 = bias_variable([64])
#image = tf.reshape(image,[-1,112,112,3])
# Feature map size is halved by stride of 2
activation = conv2d(image, W_conv1, 2, 2) + b_conv1
h_conv1 = tf.nn.relu(activation)

W_conv2 = weight_variable([3,3,64,64])
b_conv2 = bias_variable([64])
activation = conv2d(h_conv1, W_conv2, 1, 1) + b_conv2
h_conv2 = tf.nn.relu(activation)

W_conv3 = weight_variable([3,3,64,64])
b_conv3 = bias_variable([64])
activation = conv2d(h_conv2, W_conv3, 1, 1) + b_conv3
residual = activation + h_conv1
h_conv3 = tf.nn.relu(activation)

W_conv4 = weight_variable([3,3,64,64])
b_conv4 = bias_variable([64])
activation = conv2d(h_conv3, W_conv4, 1, 1) + b_conv4
h_conv4 = tf.nn.relu(activation)

W_conv5 = weight_variable([3,3,64,64])
b_conv5 = bias_variable([64])
activation = conv2d(h_conv4, W_conv5, 1, 1) + b_conv5
h_conv5 = tf.nn.relu(activation)

W_conv6 = weight_variable([3,3,64,64])
b_conv6 = bias_variable([64])
activation = conv2d(h_conv5, W_conv6, 1, 1) + b_conv6
residual = activation + h_conv4
h_conv6 = tf.nn.relu(activation)

# 3 convolutions - 128 kernels (3x3)
W_conv7 = weight_variable([3,3,64,128])
b_conv7 = bias_variable([128])
# Halve size of map features
activation = conv2d(h_conv6, W_conv7, 2, 2) + b_conv7
h_conv7 = tf.nn.relu(activation)

W_conv8 = weight_variable([3,3,128,128])
b_conv8 = bias_variable([128])
activation = conv2d(h_conv7, W_conv8, 1, 1) + b_conv8
h_conv8 = tf.nn.relu(activation)

W_conv9 = weight_variable([3,3,128,128])
b_conv9 = bias_variable([128])
activation = conv2d(h_conv8, W_conv9, 1, 1) + b_conv9
residual = activation + h_conv7
h_conv9 = tf.nn.relu(activation)


#W_fc1 = weight_variable([28*28*128, 1024])
W_fc1 = weight_variable([7*7*128, 1024])

b_fc1 = bias_variable([1024])
h_pool2_flat = tf.reshape(h_conv8, [-1, 7*7*128])
#h_pool2_flat = tf.reshape(h_conv8, [-1, 28*28*128])


h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

W_fc2 = weight_variable([1024, 10])
b_fc2 = bias_variable([10])

y_conv = tf.matmul(h_fc1_drop, W_fc2) + b_fc2
OUT = tf.nn.softmax(y_conv)

################### END NETWORK ####################




cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y_conv))
train_step = tf.train.AdamOptimizer(lr).minimize(cross_entropy)
correct_prediction = tf.equal(tf.argmax(OUT,1), tf.argmax(y_,1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
#sess.run(tf.global_variables_initializer())






# Hyperparameter
epochs = 100
batchSize = 30
batchesPerEpoch = mnist.train.images.shape[0] // batchSize


# Learning Rate Parameter
learningRate = 0.01
threshold = 0.01
nextTest = 10
step = 10

# Memory Allocation
accur = np.zeros([epochs,batchesPerEpoch]) # batch-wise
ACCS = np.empty([epochs,2]) # First column: TrainData, second: ValData

# Read in Dataset
valLabels = mnist.validation.labels
valImgs = np.empty([5000,28,28,3])
for k in range(3):
    valImgs[:,:,:,k] = mnist.validation.images.reshape([5000,28,28])

testLabels = mnist.test.labels
testImgs = np.empty([10000,28,28,3])
for i in range(3):
    testImgs[:,:,:,i] = mnist.test.images.reshape([10000,28,28])

#restoreTimePoint = 600
#restorePath = 'mnistResNet'
with tf.Session() as session:
    
    saver = tf.train.Saver(write_version = saver_pb2.SaverDef.V1)

    #saver.restore(session, "./"+restorePath+"/weights.ckpt-"+str(restoreTimePoint))
    session.run(tf.global_variables_initializer())
    



    for epoch in range(epochs):
        for batchN in range(batchesPerEpoch):
            t, trainingLabels = mnist.train.next_batch(50)

            trainImgs = np.empty([50,28,28,3])
            for k in range(3):
                trainImgs[:,:,:,k] = t.reshape([50,28,28])
            trainImgs = augment(trainImgs)


            _,accur[epoch,batchN] = session.run([train_step,accuracy],feed_dict={x: trainImgs, y_: trainingLabels,
                keep_prob: 0.5, lr:learningRate})


        ACCS[epoch,0] = np.mean(accur[epoch,:])
        print('Training acuracy after epoch: ', epoch+1, ' = ' , ACCS[epoch,0])

        # Check Validation Performance
        ACCS[epoch,1] = accuracy.eval(feed_dict={x:valImgs, y_:valLabels, keep_prob:1.0})
        print('Validation acuracy after epoch: ', epoch+1, ' = ' , ACCS[epoch,1])

        # Check Test Performance
        if epoch % 5 == 0:
            print('Testing accuracy after epoch ',epoch+1, ' = ', accuracy.eval(feed_dict = {x: testImgs, y_: testLabels,keep_prob:1.0}))



        # Feedback based decay of LR
        # Divide LR by 10 whenever there was not improvement 

        if epoch > nextTest and np.mean(ACCS[epoch-(step//2):epoch,1]) < np.mean(ACCS[epoch-step:epoch-(step//2),1]) + threshold:
            learningRate /= 5
            threshold /= 6
            nextTest += 10
            print('New Learning Rate = ', learningRate)

        if epoch > 0 and epoch % 10 == 0:
            saver.save(session, "./"+netName+"/weights.ckpt",global_step=epoch)
            np.savetxt('./'+netName+'/Accuracy.txt',ACCS)
            print('Weights and Accuracies saved')


        #print("test accuracy %g"%accuracy.eval(feed_dict={x: mnist.test.images, y_: mnist.test.labels, keep_prob: 1.0}))

'''# To restore weights

restoreTimePoint = 600
with tf.Session() as session:

    saver = tf.train.Saver(write_version = saver_pb2.SaverDef.V1)
    # Requires files resnet.ckpt-NUM and resnet.ckp-NUM.meta and NOT MORE FILES
    saver.restore(session, "./"+netName+"/weights.ckpt-"+str(restoreTimePoint))

    # Evaluate Training Accuracy. Memory Error with single batch of size 55000, therefore we use 5 batches of size 11000
    # If that is still do much for your system, set the splitter variable accordingly (i.e. 55000%splitter == 0 --> TRUE) 

    splitter = 11    
    size = mnist.train.images.shape[0]
    step = size // splitter

    # Read in images and extend to 3D (we work with color images)
    trainImgs = np.empty([size,28,28,3])
    for k in range(3):
        trainImgs[:,:,:,k] = mnist.train.images.reshape([size,28,28])

    # Now check performance on train set
    p = []
    for k in range(splitter):
        p.append(accuracy.eval(feed_dict = {x: trainImgs[k*step:(k+1)*step], y_:mnist.train.labels[k*step:(k+1)*step], keep_prob:1.0}))
    print()
    print('Train Accuracy MNIST = ', np.mean(p))

    # Testing Accuracy
    size = mnist.test.images.shape[0]
    testImgs = np.empty([size,28,28,3])
    for i in range(3):
        testImgs[:,:,:,i] = mnist.test.images.reshape([size,28,28])
    print('Test Accuracy MNIST ', accuracy.eval(feed_dict = {x: testImgs, y_: mnist.test.labels,keep_prob:1.0}))'''