import math
import numpy as np
import h5py
import matplotlib.pyplot as plt
import scipy
# from PIL import Image
from scipy import ndimage
# from PIL.Image import core as _imaging
import tensorflow as tf
from tensorflow.python.framework import ops
# from cnn_utils import *
import GetFeature as GF
import CNNUtils as CU
import CNNTrain as CT





# 创建占位符
def create_placeholders(n_H0, n_W0, n_C0, n_y):

    X = tf.placeholder('float', shape=[None, n_H0, n_W0, n_C0])
    Y = tf.placeholder('float', shape=[None, n_y])

    return X, Y


# 初始化参数
def initialize_parameters():
    seed = 5
    print("卷积层的seed为"+str(seed))

    # tf.set_random_seed(1)  # so that your "random" numbers match ours
    W1 = tf.get_variable("W1", [5, 5, 3, 6], initializer=tf.contrib.layers.xavier_initializer(seed=seed))
    W2 = tf.get_variable("W2", [5, 5, 6, 8], initializer=tf.contrib.layers.xavier_initializer(seed=seed))
    W3 = tf.get_variable("W3", [5, 5, 8, 16], initializer=tf.contrib.layers.xavier_initializer(seed=seed))
    # W4 = tf.get_variable("W4", [2, 2, 16, 32], initializer=tf.contrib.layers.xavier_initializer(seed=0))

    parameters = {"W1": W1,
                  "W2": W2,
                  "W3": W3,
                  # "W4": W4
                  }

    return parameters


def forward_propagation(X, parameters, num, isTrain=True):
    seed = 5
    # Retrieve the parameters from the dictionary "parameters"
    W1 = parameters['W1']
    W2 = parameters['W2']
    W3 = parameters['W3']
    # W4 = parameters['W4']

    # CONV2D: stride of 1, padding 'SAME'
    Z1 = tf.nn.conv2d(X, W1, strides=[1, 1, 1, 1], padding='VALID')
    print(Z1)
    # RELU
    A1 = tf.nn.relu(Z1)
    # MAXPOOL: window 8x8, sride 8, padding 'SAME'
    P1 = tf.nn.max_pool(A1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='VALID')
    print(P1)

    # CONV2D: filters W2, stride 1, padding 'SAME'
    Z2 = tf.nn.conv2d(P1, W2, strides=[1, 1, 1, 1], padding='VALID')
    print(Z2)
    # RELU
    A2 = tf.nn.relu(Z2)
    # MAXPOOL: window 4x4, stride 4, padding 'SAME'
    P2 = tf.nn.max_pool(A2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='VALID')
    print(P2)

    # CONV2D: filters W2, stride 1, padding 'SAME'
    Z3 = tf.nn.conv2d(P2, W3, strides=[1, 1, 1, 1], padding='VALID')
    print(Z3)
    # RELU
    A3 = tf.nn.relu(Z3)
    # MAXPOOL: window 4x4, stride 4, padding 'SAME'
    P3 = tf.nn.max_pool(A3, ksize=[1, 3, 3, 1], strides=[1, 3, 3, 1], padding='VALID')
    # print(P3)
    print(P3.get_shape().as_list())

    pool_shape = P3.get_shape().as_list()
    nodes = pool_shape[1] * pool_shape[2]* pool_shape[3]
    reshaped = tf.reshape(P3, [num, nodes])
    # if isTrain:        # 防止过拟合
    #     reshaped = tf.nn.dropout(reshaped, 0.80)
    # initializer=tf.truncated_normal_initializer(stddev=0.1)
    # initializer=tf.contrib.layers.xavier_initializer(seed=2)

    print("卷积层的seed为" + str(seed))
    fc1_weights = tf.get_variable("weight1", [nodes, 64], initializer=tf.truncated_normal_initializer(stddev=0.1, seed=seed))
    fc1_biases = tf.get_variable("bias1", [64], initializer=tf.constant_initializer(0.1))
    fc1 = tf.nn.relu(tf.matmul(reshaped, fc1_weights)+fc1_biases)
    # if isTrain:        # 防止过拟合
    #     fc1 = tf.nn.dropout(fc1, 0.66)

    fc2_weights = tf.get_variable("weight2", [64, 10], initializer=tf.truncated_normal_initializer(stddev=0.1, seed=seed))
    fc2_biases = tf.get_variable("bias2", [10], initializer=tf.constant_initializer(0.1))
    logit = (tf.matmul(fc1, fc2_weights)+fc2_biases)
    return logit, fc1_weights, fc2_weights


def compute_cost(Z3, Y):
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=Z3, labels=Y))
    return cost


def model(X_train, Y_train, X_test, Y_test, learning_rate=0.0005, l2_rate=0.010,
          num_epochs=500, minibatch_size=64, print_cost=True, save_session= False):
    print("l2_rate="+str(l2_rate)+" and learning_rate="+str(learning_rate))
    ops.reset_default_graph()  # to be able to rerun the model without overwriting tf variables
    # tf.set_random_seed(1)  # to keep results consistent (tensorflow seed)
    seed = 3  # to keep results consistent (numpy seed)
    (m, n_H0, n_W0, n_C0) = X_train.shape
    m_test = X_test.shape[0]
    n_y = Y_train.shape[1]
    costs = []  # To keep track of the cost
    isTrain = tf.placeholder(tf.bool)
    num = tf.placeholder(tf.int32)
    X, Y = create_placeholders(n_H0, n_W0, n_C0, n_y)
    parameters = initialize_parameters()
    Z3, fc1w, fc2w = forward_propagation(X, parameters, num)
    cost = compute_cost(Z3, Y)
    # 采用L2正则化，避免过拟合
    regularizer = tf.contrib.layers.l2_regularizer(l2_rate)
    regularization = regularizer(fc1w)+regularizer(fc2w)
    cost = cost + regularization
    # 定义global_step
    global_step = tf.Variable(0, trainable=False)
    # 通过指数衰减函数来生成学习率
    learning_rate = tf.train.exponential_decay(learning_rate, global_step, 100, 0.96, staircase=False)
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost, global_step)
    init = tf.global_variables_initializer()
    saver = tf.train.Saver()
    with tf.Session() as sess:
        sess.run(init)
        for epoch in range(num_epochs):
            _, minibatch_cost = sess.run([optimizer, cost], feed_dict={X: X_train, Y: Y_train, num: m})
            if print_cost is True and epoch % 5 == 0:
                print("损失函数经过%i次遍历后: %f" % (epoch, minibatch_cost))
                predict_op = tf.argmax(Z3, 1)  # 返回每行最大值的索引
                correct_prediction = tf.equal(predict_op, tf.argmax(Y, 1))
                accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
                train_accuracy = accuracy.eval({X: X_train, Y: Y_train, num: m})
                test_accuracy = accuracy.eval({X: X_test, Y: Y_test, num: m_test, isTrain: False})
                print("训练集识别率:", train_accuracy)
                print("测试集识别率:", test_accuracy)
                if save_session is True and test_accuracy > 0.874:
                    save_files = './session/model_forloop'+str(epoch)+'.ckpt'
                    saver.save(sess, save_files)
                    print("模型"+save_files+"保存成功.")
            if print_cost is True and epoch % 1 == 0:
                costs.append(minibatch_cost)
        return parameters

# 初期特殊取文件方法
def loadDataSets():
    XTrain = GF.readH5File('./datasets/train_model.h5', 'data')
    YLabels = GF.readH5File('./datasets/train_labels.h5', 'labels')
    YLabels = YLabels.reshape(1, len(YLabels)).astype('int64')
    YLabels = GF.convert_to_one_hot(YLabels, 10).T
    XTest = GF.readH5File('./datasets/test_model.h5', 'data')
    YTestLabels = GF.readH5File('./datasets/test_labels.h5', 'labels')
    YTestLabels = YTestLabels.reshape(1, len(YTestLabels)).astype('int64')
    YTestLabels = GF.convert_to_one_hot(YTestLabels, 10).T
    return XTrain, YLabels, XTest, YTestLabels

def cnnTrain():
    print("采用正则化的加权深层图像特征")
    # trainFile = './datasets/3dModelTrainBeta4ModelNet10.h5'
    trainFile = './logs/3dModelTrainSBeta_8_2.h5'
    # testFile = './datasets/3dModelTestBeta4ModelNet10.h5'
    testFile = './logs/3dModelTestSBeta_8_2.h5'
    XTrain, YTrain, XTest, YTest = CU.loadDataSets(trainFile, testFile)
    # XTrain, YTrain, XTest, YTest = loadDataSets()
    XTrain[:,:,:,0] *= 0.6
    XTrain[:,:,:,1] *= 0.2
    XTrain[:,:,:,2] *= 0.2
    XTest[:,:,:,0] *= 0.6
    XTest[:,:,:,1] *= 0.2
    XTest[:,:,:,2] *= 0.2
    # XTrain[:,:,:,0] /= 64
    # XTrain[:,:,:,1] /= 64
    # XTrain[:,:,:,2] /= 64
    # XTest[:,:,:,0] /= 64
    # XTest[:,:,:,1] /= 64
    # XTest[:,:,:,2] /= 64
    parameters = model(XTrain, YTrain, XTest, YTest, num_epochs=10000, save_session=True)
    return XTrain, YTrain, XTest, YTest



if __name__ == '__main__':
    # 三维模型测试
    XTrain, YTrain, XTest, YTest = cnnTrain()