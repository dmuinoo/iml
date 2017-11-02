from scipy.io import arff
from sklearn.cluster import KMeans
from sklearn.preprocessing import scale, Imputer
from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import sys

#np.random.seed(0)

if len(sys.argv) != 2:
	print("\nUsage: {} FILE.arff\n".format(sys.argv[0]))
	print("Runs sklearn.cluster.KMeans over the file FILE.arff\n")
	exit(1)

#DATASET = "datasets/wine.arff"
DATASET = sys.argv[1]
GRAPH = False
PRINT_CLASSES = False
CONFUSION = False
SKLEARN = False

def max_class_match(original, computed):
	# Compute the best names of the classes to match 'original'

	classes = np.sort(np.unique(original))
	for rep in range(len(classes)):
		swap = False
		for i in classes:
			for j in classes:
				if i >= j: continue

				a = [computed == i]
				b = [computed == j]

				# Compute actual matches
				m1 = sum(original[a] == computed[a])
				m2 = sum(original[b] == computed[b])
				m = m1 + m2
				
				# Compute matches after swap
				s1 = sum(original[a] == j)
				s2 = sum(original[b] == i)
				s = s1 + s2

				score = s - m
				if score > 0: # Then the swap is better than the actual order
					computed[a] = j
					computed[b] = i
					swap = True
					#print('Swapping {} by {}'.format(i, j))

		if not swap: break
		#print('Iterating')
	
	return computed

def extract_columns(dataset, column_list):
	# Extract the columns as a np.array with len(column_list) columns
	return np.array(data[column_list].tolist())

def extract_columns_type(dataset, meta, column_type, exclude=[]):

	col_list = np.array(meta.names())[np.array(meta.types()) == column_type]
	col_list = list(col_list)

	for e in exclude:
		col_list.remove(e)

	return extract_columns(dataset, col_list)

def do_kmeans(X, n_clusters, Xn = np.array([[]]), iterations=500, gamma=1.1):
	DIST_MIN = 0.1
	if(X.shape[0] == 0):
		print('{}: Zero numerical values not supported yet'.format(DATASET))
		exit(1)
	n_samples, n_features = X.shape
	#centroids = np.zeros(n_clusters, n_features)
	centroids = np.random.normal(size=[n_clusters, n_features])
	y = np.zeros(n_samples, dtype=np.int)
	if len(xn.shape) < 2: Xn = np.array([[]])
	n_nominals = Xn.shape[1]
	if n_nominals != 0:
		indexes = np.random.choice(range(n_samples), n_clusters)
		centroids_nomimal = Xn[indexes, :]
	for iter in range(iterations):
		changes = False
		#print('Iteration {}/{}'.format(iter+1, iterations))
		for i in range(n_samples):
			distances = np.linalg.norm(X[i,:] - centroids, axis=1)
			distances_nominal = np.zeros(n_clusters, dtype=np.int)
			for c in range(n_clusters):
				for j in range(n_nominals):
					if(Xn[i][j] != centroids_nomimal[c][j]):
						distances_nominal[c] += 1
			distances += gamma * distances_nominal

			new_y = np.argmin(distances)
			if(y[i] != new_y): changes = True
			y[i] = new_y
	
		if not changes: break
		#print('centroids {}'.format(centroids))

		for c in range(n_clusters):
			class_vectors = X[y == c]
			#print('class_vectors.shape = {}'.format(class_vectors.shape))
			#print('Number of samples for class {} is {}'.format(c, class_vectors.shape[0]))
			if class_vectors.shape[0] != 0:
				centroid_mean = np.mean(class_vectors, axis=0)
				#print('centroid_mean = {}'.format(centroid_mean))
				centroids[c] = centroid_mean

				# Nominal
				for j in range(n_nominals):
					col = Xn[:,j]
					table = np.unique(col, return_counts=True)
					most_freq = np.argmax(table[1])
					centroids_nomimal[c][j] = table[0][most_freq]
					

				# Check the centroid is not very close to others
				centroid_diff = centroids[c] - centroids
				#print('centroids {}'.format(centroids))
				#print('For {} centroid_diff = {}'.format(c, centroid_diff))
				centroid_dist = np.linalg.norm(centroid_diff, axis=1)
				centroid_dist[c] = float('infinity')
				#print('For {} centroid_dist = {}'.format(c, centroid_dist))
				if(np.min(centroid_dist) < DIST_MIN):
					centroids[c] = np.random.normal(size=n_features)
					#print('Centroid {} is reallocated'.format(c))
			else:
				#print('Centroid {} is reallocated because the number of samples = 0'.format(c))
				centroids[c] = np.random.normal(size=n_features)
		
	return (y, centroids)
		

#print('Reading dataset: {}'.format(DATASET))
data, meta = arff.loadarff(DATASET)

# Remove NaN
remove_rows = []
keep_rows = []
for i in range(data.shape[0]):
	row = data[i]
	if any([np.isnan(e) for e in row if type(e) == np.float64]):
		remove_rows.append(i)
	else:
		keep_rows.append(i)


remove_rows = np.array(remove_rows)
data = data[keep_rows]


class_name = meta.names()[-1]

classes = meta[class_name][1]

y = np.array([classes.index(e.decode('utf-8')) for e in data[class_name]])
n_classes = len(classes)

names = meta.names()
names = list(names)
names.remove(class_name)

#for c in meta.types()[0:-1]:
#	if c != 'numeric':
#		#print('The dataset contains non-numerical data, and is by now unsupported')
#		exit(1)

data_noclass = np.array(data[names].tolist())

# shape=(n_samples, n_features)
x = data_noclass

#x_scaled = scale(x)

if SKLEARN:
	kmeans = KMeans(n_clusters = n_classes).fit(x_scaled)
	y_computed = kmeans.labels_
	centroids = kmeans.cluster_centers_
else:

	xn = extract_columns_type(data, meta, 'nominal', [class_name])
	x = extract_columns_type(data, meta, 'numeric')

	# If there are no numeric don't scale
	if(x.shape[0] != 0): x = scale(x)

	y_computed, centroids = do_kmeans(x, n_classes, Xn=xn, iterations=100)

# Match each class before computing the error
y_computed = max_class_match(y, y_computed)

if PRINT_CLASSES:
	print("Original classes")
	print(y)
	print("Computed classes")
	print(y_computed)

# Compute the error
per = sum(y==y_computed) / float(y.shape[0])

print("{}: Correct {:.2f}%".format(DATASET, per*100))


if GRAPH:
	cc = centroids
	plt.scatter(x[:,0], x[:,1], c=y)
	plt.plot(cc[:,0], cc[:,1], c='red', ls='None', marker='^', markersize=20)
	plt.show()

if CONFUSION:
	print(confusion_matrix(y, y_computed))
