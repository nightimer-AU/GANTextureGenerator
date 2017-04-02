import tensorflow as tf


# Helper Functions

def lerp_int(value_a: int, value_b: int, perc: float, epsilon :float=0.01):
	"""Returns a lerp from the minimum to the maximum (inclusive int)"""
	if perc < epsilon:
		return value_a
	elif perc >= 1-epsilon:
		return value_b
	else:
		return int(value_a + perc*(value_b-value_a))


# Variable Creation

def weight_bias(shape, stddev: float=0.02, const: float=0.01):
	"""Create Weight and Bias tensors for a layer in the nn"""
	w_var = tf.get_variable('weight', shape, tf.float32, tf.random_normal_initializer(0, stddev), trainable=True)
	b_var = tf.get_variable('bias', [shape[-1]], tf.float32, tf.constant_initializer(const,), trainable=True)
	return w_var, b_var

def filter_bias(shape, stddev: float=0.02, const: float=0.1):
	"""Create Filter and Bias tensors for a conv2d-transpose layer"""
	w_var = tf.get_variable('filter', shape, tf.float32, tf.random_normal_initializer(0, stddev), trainable=True)
	b_var = tf.get_variable('bias', [shape[-2]], tf.float32, tf.constant_initializer(const,), trainable=True)
	return w_var, b_var


# Operator Functions

def lrelu(tensor, leak: float=0.2):
	"""Create a leaky relu node"""
	return tf.maximum(tensor, tensor*leak, name='lrelu')


# Network Layers

def conv2d(tensor, output_size: int, name: str='conv2d', stddev: float=0.02, term: float=0.01):
	"""Create a convolutional layer"""
	with tf.variable_scope(name):
		weight, bias = weight_bias([5, 5, int(tensor.get_shape()[-1]), output_size], stddev, term)
		conv = tf.nn.conv2d(tensor, weight, [1, 2, 2, 1], "SAME")
		#Batch norm before relu?
		return lrelu(tf.nn.bias_add(conv, bias))

def relu(tensor, output_size: int, name: str='relu', stddev: float=0.02, term: float=0.01):
	"""Create a relu layer"""
	with tf.variable_scope(name):
		weight, bias = weight_bias([int(tensor.get_shape()[-1]), output_size], stddev, term)
		return tf.nn.relu(tf.matmul(tensor, weight) + bias)

def relu_dropout(tensor, output_size: int, dropout: float=0.4, name: str='relu_dropout', stddev: float=0.02, term: float=0.01):
	"""Create a relu layer with dropout"""
	with tf.variable_scope(name):
		weight, bias = weight_bias([int(tensor.get_shape()[-1]), output_size], stddev, term)
		relu_layer = tf.nn.relu(tf.matmul(tensor, weight) + bias)
		return tf.nn.dropout(relu_layer, dropout)

def linear(tensor, output_size: int, name: str='linear', stddev: float=0.02, term: float=0.01):
	'''Create a fully connected layer'''
	with tf.variable_scope(name):
		weight, bias = weight_bias([tensor.get_shape()[-1], output_size], stddev, term)
		return tf.matmul(tensor, weight) + bias

def conv2d_transpose(tensor, batch_size=1, conv_size=32, name: str='conv2d_transpose', stddev: float=0.02, term: float=0.01):
	"""Create a transpose convolutional layer"""
	with tf.variable_scope(name):
		tensor_shape = tensor.get_shape()
		filt, bias = filter_bias([5, 5, conv_size, tensor_shape[-1]], stddev, term)
		conv_shape = [batch_size, int(tensor_shape[1]*2), int(tensor_shape[2]*2), conv_size]
		deconv = tf.nn.conv2d_transpose(tensor, filt, conv_shape, [1, 2, 2, 1])
		#Batch norm before relu?
		return tf.nn.relu(tf.nn.bias_add(deconv, bias))

def conv2d_transpose_tanh(tensor, batch_size=1, conv_size=32, name: str='conv2d_transpose_tanh', stddev: float=0.02, factor: float=255.0):
	"""Create a transpose convolutional layer"""
	with tf.variable_scope(name):
		tensor_shape = tensor.get_shape()
		filt = tf.get_variable('filter', [5, 5, conv_size, tensor_shape[-1]], tf.float32, tf.random_normal_initializer(0, stddev), trainable=True)
		conv_shape = [batch_size, int(tensor_shape[1]*2), int(tensor_shape[2]*2), conv_size]
		deconv = tf.nn.conv2d_transpose(tensor, filt, conv_shape, [1, 2, 2, 1])
		return tf.nn.tanh(deconv)*factor

